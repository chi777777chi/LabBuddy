from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.security import decode_token
from db.database import get_db
from db.models import Answer, ExamSession, Question, Subject, User

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    return user


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "role": user.role,
    }


@router.get("/me/stats")
def get_my_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 完成場數
    total_sessions = (
        db.query(ExamSession)
        .filter(ExamSession.user_id == user.id, ExamSession.score.isnot(None))
        .count()
    )

    # 總答題數 & 答對數
    answers = (
        db.query(Answer)
        .join(ExamSession, Answer.session_id == ExamSession.id)
        .filter(ExamSession.user_id == user.id, Answer.chosen.isnot(None))
        .all()
    )
    total_answered = len(answers)
    total_correct = sum(1 for a in answers if a.is_correct)
    overall_accuracy = round(total_correct / total_answered * 100, 1) if total_answered > 0 else None

    # 最常練習科目（出現次數最多的 subject_id）
    row = (
        db.query(ExamSession.subject_id, func.count(ExamSession.id).label("cnt"))
        .filter(ExamSession.user_id == user.id)
        .group_by(ExamSession.subject_id)
        .order_by(func.count(ExamSession.id).desc())
        .first()
    )
    favorite_subject = ""
    if row:
        subj = db.query(Subject).filter(Subject.id == row.subject_id).first()
        favorite_subject = subj.name if subj else ""

    return {
        "joined_date": user.created_at.strftime("%Y/%m/%d"),
        "total_sessions": total_sessions,
        "total_answered": total_answered,
        "overall_accuracy": overall_accuracy,
        "favorite_subject": favorite_subject,
    }
