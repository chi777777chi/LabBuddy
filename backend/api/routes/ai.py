from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Answer, ExamSession, Question, QuestionStats, Subject, User
from core.security import decode_token
from services.ai_service import get_hint, get_explain

router = APIRouter(prefix="/ai", tags=["ai"])


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class HintRequest(BaseModel):
    question_id: str
    level: int = 1


class HintResponse(BaseModel):
    hint: str


@router.post("/hint", response_model=HintResponse)
async def hint(
    body: HintRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Question).filter(Question.id == body.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    text = await get_hint(
        content=q.content,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d,
        level=body.level,
    )
    return HintResponse(hint=text)


class ExplainRequest(BaseModel):
    question_id: str
    chosen: str | None = None


@router.post("/explain")
async def explain(
    body: ExplainRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Question).filter(Question.id == body.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    # 總答題數（用於判斷快取是否仍有效）
    total_answers: int = (
        db.query(func.count(Answer.id))
        .join(ExamSession, Answer.session_id == ExamSession.id)
        .filter(ExamSession.user_id == user.id, Answer.chosen.isnot(None))
        .scalar()
        or 0
    )

    # 若有快取且答題數未變，直接回傳
    qs_cache = (
        db.query(QuestionStats)
        .filter_by(user_id=user.id, question_id=body.question_id)
        .first()
    )
    if (
        qs_cache
        and qs_cache.explain_text
        and qs_cache.explain_answer_count == total_answers
    ):
        return {"explain": qs_cache.explain_text}

    # 1. 難度答對率
    diff_buckets: dict[str, list[bool]] = {}
    diff_answers = (
        db.query(Answer)
        .join(ExamSession, Answer.session_id == ExamSession.id)
        .join(Question, Answer.question_id == Question.id)
        .filter(ExamSession.user_id == user.id, Answer.chosen.isnot(None))
        .all()
    )
    q_difficulty_map: dict[str, str] = {}
    if diff_answers:
        q_ids = {a.question_id for a in diff_answers}
        for qq in db.query(Question).filter(Question.id.in_(q_ids)).all():
            q_difficulty_map[qq.id] = qq.difficulty or "medium"
        for a in diff_answers:
            diff = q_difficulty_map.get(a.question_id, "medium")
            diff_buckets.setdefault(diff, []).append(bool(a.is_correct))
    diff_label = {"easy": "簡單", "medium": "中等", "hard": "困難"}
    diff_lines = []
    for diff_key in ["easy", "medium", "hard"]:
        bucket = diff_buckets.get(diff_key)
        if bucket:
            rate = round(sum(bucket) / len(bucket) * 100, 1)
            diff_lines.append(f"{diff_label[diff_key]}：{rate}%（{sum(bucket)}/{len(bucket)}）")
    diff_summary = "、".join(diff_lines) if diff_lines else "無難度數據"

    # 2. 各科答對率
    subj_rows = (
        db.query(QuestionStats)
        .filter(QuestionStats.user_id == user.id)
        .all()
    )
    subj_buckets: dict[str, tuple[int, int]] = {}
    if subj_rows:
        qs_q_ids = {r.question_id for r in subj_rows}
        subj_map: dict[str, str] = {}
        for qq in db.query(Question).filter(Question.id.in_(qs_q_ids)).all():
            subj = db.query(Subject).filter(Subject.id == qq.subject_id).first()
            subj_map[qq.id] = subj.name if subj else "未知"
        for r in subj_rows:
            sname = subj_map.get(r.question_id, "未知")
            prev_c, prev_w = subj_buckets.get(sname, (0, 0))
            subj_buckets[sname] = (prev_c + r.correct_count, prev_w + r.wrong_count)
    subj_lines = []
    for sname, (c, w) in subj_buckets.items():
        total = c + w
        rate = round(c / total * 100, 1) if total else 0
        subj_lines.append(f"{sname}：{rate}%（{c}/{total}）")
    subj_summary = "、".join(subj_lines) if subj_lines else "無科目數據"

    # 3. 作答時間模式
    time_answers = (
        db.query(Answer)
        .join(ExamSession, Answer.session_id == ExamSession.id)
        .filter(
            ExamSession.user_id == user.id,
            Answer.time_spent_seconds.isnot(None),
            Answer.time_spent_seconds > 0,
        )
        .all()
    )
    if time_answers:
        times = [a.time_spent_seconds for a in time_answers]
        avg_t = round(sum(times) / len(times), 1)
        slow_c = sum(1 for t in times if t > 120)
        time_summary = f"平均答題 {avg_t} 秒（國考標準 75 秒），慢題（>120秒）共 {slow_c} 題"
    else:
        time_summary = "尚無作答時間記錄"

    # 4. 此題錯誤選項模式
    wrong_answers = (
        db.query(Answer)
        .join(ExamSession, Answer.session_id == ExamSession.id)
        .filter(
            ExamSession.user_id == user.id,
            Answer.question_id == body.question_id,
            Answer.is_correct == False,
            Answer.chosen.isnot(None),
        )
        .all()
    )
    if wrong_answers:
        opts_map = {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}
        cnt: dict[str, int] = {}
        for a in wrong_answers:
            cnt[a.chosen] = cnt.get(a.chosen, 0) + 1
        parts = [f"{ch}（{opts_map.get(ch, '')}）×{n}次" for ch, n in sorted(cnt.items(), key=lambda x: -x[1])]
        wrong_summary = "曾選錯：" + "、".join(parts)
    else:
        wrong_summary = "此題尚無答錯記錄"

    weakness_summary = (
        f"【難度答對率】{diff_summary}\n"
        f"【各科答對率】{subj_summary}\n"
        f"【答題速度】{time_summary}\n"
        f"【此題錯誤模式】{wrong_summary}"
    )

    text = await get_explain(
        content=q.content,
        option_a=q.option_a,
        option_b=q.option_b,
        option_c=q.option_c,
        option_d=q.option_d,
        correct_answer=q.answer,
        chosen=body.chosen or "",
        weakness_summary=weakness_summary,
        tags=q.tags or "",
    )

    # 存快取（只在 QuestionStats 存在時，即使用者曾作答過）
    if qs_cache:
        qs_cache.explain_text = text
        qs_cache.explain_answer_count = total_answers
        db.commit()

    return {"explain": text}
