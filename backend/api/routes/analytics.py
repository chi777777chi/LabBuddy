from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Answer, ExamSession, Question, QuestionStats, Subject, User
from core.security import decode_token
from services.ai_service import get_weakness_analysis

router = APIRouter(prefix="/analytics", tags=["analytics"])

SITTING_LABEL = {1: "第一次", 2: "第二次"}


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

    # ── 4. AI 弱點分析 ───────────────────────────────────────────
    has_data = any(s["total_answered"] > 0 for s in subject_stats)
    if has_data:
        ai_analysis = await get_weakness_analysis(
            subject_stats=subject_stats,
            score_trend=score_trend,
            weak_questions=weak_questions,
        )
    else:
        ai_analysis = ""

    return {
        "subject_stats": subject_stats,
        "score_trend": score_trend,
        "weak_questions": weak_questions,
        "ai_analysis": ai_analysis,
    }
