from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Answer, ExamSession, Question, QuestionStats, Subject, User
from core.security import decode_token
from services.ai_service import get_weakness_analysis_with_time

router = APIRouter(prefix="/analytics", tags=["analytics"])

SITTING_LABEL = {1: "第一次", 2: "第二次"}
SUBJECT_SHORT = {
    "臨床生理學與病理學":         "臨床生理",
    "臨床血液學與血庫學":          "臨床血液",
    "醫學分子檢驗學與臨床鏡檢學": "分子鏡檢",
    "微生物學與臨床微生物學":      "微生物",
    "生物化學與臨床生化學":        "生物化學",
    "臨床血清免疫學與臨床病毒學":  "血清免疫",
}


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    from fastapi import HTTPException
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me")
async def get_my_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ── 1. 各科目答對率 ──────────────────────────────────────────
    subjects = db.query(Subject).all()
    subject_stats = []
    for subj in subjects:
        answers = (
            db.query(Answer)
            .join(Question, Answer.question_id == Question.id)
            .join(ExamSession, Answer.session_id == ExamSession.id)
            .filter(
                ExamSession.user_id == user.id,
                Question.subject_id == subj.id,
                Answer.chosen.isnot(None),
            )
            .all()
        )
        total = len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        rate = round(correct / total * 100, 1) if total > 0 else None
        color = ("green" if rate >= 70 else "orange" if rate >= 50 else "red") if rate is not None else "gray"
        subject_stats.append({
            "subject_id": subj.id,
            "subject_name": subj.name,
            "subject_short": SUBJECT_SHORT.get(subj.name, subj.name),
            "total_answered": total,
            "correct_count": correct,
            "accuracy_rate": rate,
            "color": color,
        })

    # ── 2. 歷次成績趨勢（最近 20 場已完成、有儲存的） ─────────────
    sessions = (
        db.query(ExamSession)
        .filter(
            ExamSession.user_id == user.id,
            ExamSession.save_to_history == True,
            ExamSession.score.isnot(None),
        )
        .order_by(ExamSession.started_at.desc())
        .limit(20)
        .all()
    )
    score_trend = []
    for s in reversed(sessions):
        subj = db.query(Subject).filter(Subject.id == s.subject_id).first()
        score_trend.append({
            "session_id": s.id,
            "date": s.started_at.strftime("%m/%d"),
            "score": s.score,
            "total": s.question_count,
            "percentage": round(s.score / s.question_count * 100, 1) if s.question_count else 0,
            "subject_name": subj.name if subj else "",
            "mode": s.mode,
        })

    # ── 3. 最常答錯的題目（前 10 題） ───────────────────────────
    weak_stats = (
        db.query(QuestionStats)
        .filter(
            QuestionStats.user_id == user.id,
            QuestionStats.wrong_count > 0,
        )
        .order_by(QuestionStats.wrong_count.desc())
        .limit(10)
        .all()
    )
    weak_questions = []
    for ws in weak_stats:
        q = db.query(Question).filter(Question.id == ws.question_id).first()
        if not q:
            continue
        subj = db.query(Subject).filter(Subject.id == q.subject_id).first()
        weak_questions.append({
            "question_id": q.id,
            "content": q.content[:60] + "…" if len(q.content) > 60 else q.content,
            "wrong_count": ws.wrong_count,
            "correct_count": ws.correct_count,
            "subject_name": subj.name if subj else "",
            "source": f"{q.year}年{SITTING_LABEL.get(q.sitting, '')} 第{q.number}題",
        })

    # ── 4. 時間效率統計 ──────────────────────────────────────────
    EXPECTED_SECONDS = 75  # 國考標準：100 分鐘 / 80 題
    answers_with_time = (
        db.query(Answer)
        .join(ExamSession, Answer.session_id == ExamSession.id)
        .filter(
            ExamSession.user_id == user.id,
            Answer.time_spent_seconds.isnot(None),
            Answer.chosen.isnot(None),
            Answer.time_spent_seconds > 0,
        )
        .all()
    )
    if answers_with_time:
        avg_time = round(sum(a.time_spent_seconds for a in answers_with_time) / len(answers_with_time), 1)
        slow_count = sum(1 for a in answers_with_time if a.time_spent_seconds > 120)
        fast_count = sum(1 for a in answers_with_time if a.time_spent_seconds < 20)
        time_stats = {
            "has_data": True,
            "avg_time_seconds": avg_time,
            "expected_time_seconds": EXPECTED_SECONDS,
            "total_answered_with_time": len(answers_with_time),
            "slow_count": slow_count,
            "fast_count": fast_count,
            "speed_ratio": round(avg_time / EXPECTED_SECONDS, 2),
        }
    else:
        time_stats = {"has_data": False}

    # ── 5. 慢題知識點分析 ────────────────────────────────────────
    slow_tags = []
    if answers_with_time:
        tag_times: dict[str, list[int]] = defaultdict(list)
        q_ids = {a.question_id for a in answers_with_time}
        q_map = {
            q.id: q
            for q in db.query(Question).filter(Question.id.in_(q_ids)).all()
        }
        time_map = {a.question_id: a.time_spent_seconds for a in answers_with_time}
        for qid, q in q_map.items():
            if q.tags and qid in time_map:
                for tag in q.tags.split(","):
                    tag = tag.strip()
                    if tag:
                        tag_times[tag].append(time_map[qid])
        slow_tags = [
            {"tag": tag, "avg_seconds": round(sum(ts) / len(ts), 1), "count": len(ts)}
            for tag, ts in tag_times.items()
            if len(ts) >= 3
        ]
        slow_tags.sort(key=lambda x: x["avg_seconds"], reverse=True)
        slow_tags = slow_tags[:8]

    # ── 6. 成績趨勢方向 ──────────────────────────────────────────
    trend_direction = "none"
    if len(score_trend) >= 3:
        recent = [s["percentage"] for s in score_trend[-3:]]
        first_half = sum(recent[:len(recent)//2 + 1]) / (len(recent)//2 + 1)
        second_half = sum(recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
        if second_half - first_half >= 5:
            trend_direction = "improving"
        elif first_half - second_half >= 5:
            trend_direction = "declining"
        else:
            trend_direction = "stable"

    # ── 7. AI 弱點 + 時間分析 ─────────────────────────────────────
    has_data = any(s["total_answered"] > 0 for s in subject_stats)
    ai_analysis = ""
    if has_data:
        try:
            ai_analysis = await get_weakness_analysis_with_time(
                subject_stats=subject_stats,
                score_trend=score_trend,
                weak_questions=weak_questions,
                time_stats=time_stats,
                slow_tags=slow_tags,
            )
        except Exception:
            ai_analysis = ""

    return {
        "subject_stats": subject_stats,
        "score_trend": score_trend,
        "weak_questions": weak_questions,
        "ai_analysis": ai_analysis,
        "trend_direction": trend_direction,
        "time_stats": time_stats,
        "slow_tags": slow_tags,
    }
