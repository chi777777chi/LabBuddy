import json, random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Answer, ExamSession, Question, QuestionStats, Subject, User
from core.security import decode_token

router = APIRouter(prefix="/exam", tags=["exam"])

# ── 科目簡稱（題目來源標註用） ──────────────────────────────────
SUBJECT_SHORT = {
    "臨床生理學與病理學":         "臨床生理",
    "臨床血液學與血庫學":          "臨床血液",
    "醫學分子檢驗學與臨床鏡檢學": "分子鏡檢",
    "微生物學與臨床微生物學":      "微生物",
    "生物化學與臨床生化學":        "生物化學",
    "臨床血清免疫學與臨床病毒學":  "血清免疫",
}
SITTING_LABEL = {1: "第一次", 2: "第二次"}


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def build_source(year: int, sitting: int, subject_name: str, number: int) -> str:
    return f"{year}年{SITTING_LABEL.get(sitting, '')} {SUBJECT_SHORT.get(subject_name, subject_name)} 第{number}題"


def shuffle_question_options(q: Question) -> tuple[dict, str]:
    """打亂選項順序，回傳 (新選項dict, 新正確答案字母)"""
    original = {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}
    items = list(original.items())
    random.shuffle(items)
    new_options = {chr(65 + i): text for i, (_, text) in enumerate(items)}
    # 找原本正確答案的文字在新排列的位置
    correct_text = original[q.answer]
    new_answer = next(k for k, v in new_options.items() if v == correct_text)
    return new_options, new_answer


# ── Request / Response schemas ────────────────────────────────
class ExamStartRequest(BaseModel):
    subject_id: int
    mode: str                    # single_full | single_random | multi_random
    question_count: int          # 5 / 10 / 80
    year: int | None = None      # single_full / single_random 必填
    sitting: int | None = None   # single_full / single_random 必填
    shuffle_options: bool = False
    timed: bool = False
    instant_review: bool = True
    save_to_history: bool = True


class AnswerRequest(BaseModel):
    question_id: str
    chosen: str | None = None    # A/B/C/D，None 表示略過
    time_spent_seconds: int | None = None


# ── POST /exam/start ──────────────────────────────────────────
@router.post("/start")
def start_exam(
    body: ExamStartRequest,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # 驗證使用者
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subject = db.query(Subject).filter(Subject.id == body.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # ── 抽題邏輯 ──
    base_q = db.query(Question).filter(Question.subject_id == body.subject_id)

    if body.mode == "single_full":
        if not body.year or not body.sitting:
            raise HTTPException(status_code=422, detail="single_full 模式需提供 year 和 sitting")
        questions = (base_q
                     .filter(Question.year == body.year, Question.sitting == body.sitting)
                     .order_by(Question.number)
                     .limit(body.question_count)
                     .all())

    elif body.mode == "single_random":
        if not body.year or not body.sitting:
            raise HTTPException(status_code=422, detail="single_random 模式需提供 year 和 sitting")
        pool = (base_q
                .filter(Question.year == body.year, Question.sitting == body.sitting)
                .all())
        questions = random.sample(pool, min(body.question_count, len(pool)))

    elif body.mode == "multi_random":
        pool = base_q.all()
        questions = random.sample(pool, min(body.question_count, len(pool)))

    elif body.mode == "wrong_review":
        wrong_stats = (
            db.query(QuestionStats)
            .join(Question, QuestionStats.question_id == Question.id)
            .filter(
                QuestionStats.user_id == user.id,
                QuestionStats.wrong_count > 0,
                Question.subject_id == body.subject_id,
            )
            .all()
        )
        if not wrong_stats:
            raise HTTPException(status_code=404, detail="此科目沒有錯題紀錄")
        stats_map = {s.question_id: s for s in wrong_stats}
        pool = base_q.filter(Question.id.in_(list(stats_map.keys()))).all()
        pool.sort(key=lambda q: stats_map[q.id].wrong_count, reverse=True)
        questions = pool[:body.question_count]

    else:
        raise HTTPException(status_code=422, detail=f"未知的出題模式：{body.mode}")

    if not questions:
        raise HTTPException(status_code=404, detail="找不到符合條件的題目")

    # ── 建立 ExamSession ──
    session = ExamSession(
        user_id=user.id,
        subject_id=body.subject_id,
        year=body.year,
        sitting=body.sitting,
        mode=body.mode,
        question_count=len(questions),
        shuffle_options=body.shuffle_options,
        timed=body.timed,
        instant_review=body.instant_review,
        save_to_history=body.save_to_history,
    )
    db.add(session)
    db.flush()

    # ── 建立 Answer 預留記錄 + 組合回傳題目清單 ──
    session_q_meta = []
    question_list = []

    for order, q in enumerate(questions, start=1):
        if body.shuffle_options:
            options, effective_answer = shuffle_question_options(q)
        else:
            options = {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}
            effective_answer = q.answer

        session_q_meta.append({
            "question_id": q.id,
            "order": order,
            "effective_answer": effective_answer,
        })

        db.add(Answer(
            session_id=session.id,
            question_id=q.id,
            order=order,
        ))

        q_data = {
            "order": order,
            "question_id": q.id,
            "content": q.content,
            "options": options,
            "source": build_source(q.year, q.sitting, subject.name, q.number),
            "has_image": q.has_image,
            "image_path": q.image_path,
        }
        if body.mode == "wrong_review" and q.id in stats_map:
            stat = stats_map[q.id]
            q_data["wrong_count"] = stat.wrong_count
            q_data["correct_count"] = stat.correct_count
        question_list.append(q_data)

    session.session_questions = json.dumps(session_q_meta, ensure_ascii=False)
    db.commit()

    return {
        "session_id": session.id,
        "question_count": len(questions),
        "timed": body.timed,
        "instant_review": body.instant_review,
        "questions": question_list,
    }


# ── POST /exam/{session_id}/answer ───────────────────────────
@router.post("/{session_id}/answer")
def submit_answer(
    session_id: str,
    body: AnswerRequest,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id,
        ExamSession.user_id == payload["sub"],
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.finished_at:
        raise HTTPException(status_code=400, detail="此考試已交卷")

    # 找 effective_answer
    meta = json.loads(session.session_questions or "[]")
    q_meta = next((m for m in meta if m["question_id"] == body.question_id), None)
    if not q_meta:
        raise HTTPException(status_code=404, detail="此題不在本次考試中")

    answer = db.query(Answer).filter(
        Answer.session_id == session_id,
        Answer.question_id == body.question_id,
    ).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer record not found")

    is_correct = (body.chosen == q_meta["effective_answer"]) if body.chosen else False
    answer.chosen = body.chosen
    answer.is_correct = is_correct
    answer.time_spent_seconds = body.time_spent_seconds
    db.commit()

    resp = {"is_correct": is_correct}
    if session.instant_review:
        resp["correct_answer"] = q_meta["effective_answer"]
    return resp


# ── GET /exam/history ────────────────────────────────────────
@router.get("/history")
def get_history(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sessions = (
        db.query(ExamSession)
        .filter(
            ExamSession.user_id == user.id,
            ExamSession.finished_at.isnot(None),
            ExamSession.save_to_history == True,
        )
        .order_by(ExamSession.finished_at.desc())
        .all()
    )

    result = []
    for s in sessions:
        subject = db.query(Subject).filter(Subject.id == s.subject_id).first()
        total = s.question_count
        score = s.score or 0
        pct = round(score / total * 100, 1) if total else 0.0
        result.append({
            "session_id": s.id,
            "subject_name": subject.name if subject else "",
            "year": s.year,
            "sitting": s.sitting,
            "mode": s.mode,
            "question_count": total,
            "score": score,
            "percentage": pct,
            "timed": s.timed,
            "finished_at": s.finished_at.isoformat() if s.finished_at else "",
        })

    return result


# ── GET /exam/wrong-questions ─────────────────────────────────
@router.get("/wrong-questions")
def get_wrong_questions(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    results = (
        db.query(
            Subject.id,
            Subject.name,
            func.count(QuestionStats.id).label("wrong_question_count"),
            func.sum(QuestionStats.wrong_count).label("total_wrong"),
            func.sum(QuestionStats.correct_count).label("total_correct"),
        )
        .join(Question, QuestionStats.question_id == Question.id)
        .join(Subject, Question.subject_id == Subject.id)
        .filter(
            QuestionStats.user_id == user.id,
            QuestionStats.wrong_count > 0,
        )
        .group_by(Subject.id, Subject.name)
        .all()
    )

    return [
        {
            "subject_id": r[0],
            "subject_name": r[1],
            "wrong_question_count": r[2],
            "total_wrong": int(r[3] or 0),
            "total_correct": int(r[4] or 0),
        }
        for r in results
    ]


# ── GET /exam/{session_id}/detail ────────────────────────────
@router.get("/{session_id}/detail")
def get_session_detail(
    session_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id,
        ExamSession.user_id == payload["sub"],
        ExamSession.finished_at.isnot(None),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    subject = db.query(Subject).filter(Subject.id == session.subject_id).first()
    meta = {m["question_id"]: m for m in json.loads(session.session_questions or "[]")}
    answers = db.query(Answer).filter(Answer.session_id == session_id).order_by(Answer.order).all()

    details = []
    for a in answers:
        q = db.query(Question).filter(Question.id == a.question_id).first()
        details.append({
            "order": a.order,
            "content": q.content if q else "",
            "chosen": a.chosen,
            "correct_answer": meta.get(a.question_id, {}).get("effective_answer"),
            "is_correct": a.is_correct,
        })

    return {
        "session_id": session_id,
        "subject_name": subject.name if subject else "",
        "year": session.year,
        "sitting": session.sitting,
        "mode": session.mode,
        "score": session.score or 0,
        "question_count": session.question_count,
        "details": details,
    }


# ── POST /exam/{session_id}/submit ───────────────────────────
@router.post("/{session_id}/submit")
def submit_exam(
    session_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)
    session = db.query(ExamSession).filter(
        ExamSession.id == session_id,
        ExamSession.user_id == payload["sub"],
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.finished_at:
        raise HTTPException(status_code=400, detail="此考試已交卷")

    answers = db.query(Answer).filter(Answer.session_id == session_id).all()
    correct = sum(1 for a in answers if a.is_correct)
    total = len(answers)
    total_time = sum(a.time_spent_seconds or 0 for a in answers)

    session.score = correct
    session.finished_at = datetime.utcnow()

    # ── 更新每題的累計作答統計 ──
    for a in answers:
        if a.is_correct is None:  # 未作答，不計入統計
            continue
        stat = db.query(QuestionStats).filter(
            QuestionStats.user_id == session.user_id,
            QuestionStats.question_id == a.question_id,
        ).first()
        if stat:
            if a.is_correct:
                stat.correct_count += 1
            else:
                stat.wrong_count += 1
            stat.last_attempted_at = datetime.utcnow()
        else:
            db.add(QuestionStats(
                user_id=session.user_id,
                question_id=a.question_id,
                correct_count=1 if a.is_correct else 0,
                wrong_count=0 if a.is_correct else 1,
            ))

    db.commit()

    # 回傳各題詳情
    meta = {m["question_id"]: m for m in json.loads(session.session_questions or "[]")}
    details = []
    for a in sorted(answers, key=lambda x: x.order):
        q = db.query(Question).filter(Question.id == a.question_id).first()
        details.append({
            "order": a.order,
            "question_id": a.question_id,
            "content": q.content if q else "",
            "chosen": a.chosen,
            "correct_answer": meta.get(a.question_id, {}).get("effective_answer"),
            "is_correct": a.is_correct,
            "time_spent_seconds": a.time_spent_seconds,
        })

    return {
        "session_id": session_id,
        "score": correct,
        "total": total,
        "percentage": round(correct / total * 100, 1) if total else 0,
        "total_time_seconds": total_time,
        "details": details,
    }
