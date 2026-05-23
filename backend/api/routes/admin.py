from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.security import decode_token
from db.database import get_db
from db.models import Answer, ExamSession, Question, Subject, User

router = APIRouter(prefix="/admin", tags=["admin"])


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# ── 使用者管理 ────────────────────────────────────────────────
@router.get("/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.strftime("%Y/%m/%d"),
        }
        for u in users
    ]


class RoleUpdate(BaseModel):
    role: str


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    body: RoleUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if body.role not in ("student", "teacher", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id and body.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    user.role = body.role
    db.commit()
    return {"ok": True}


@router.patch("/users/{user_id}/ban")
def toggle_ban(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    user.is_active = not user.is_active
    db.commit()
    return {"ok": True, "is_active": user.is_active}


# ── 全平台統計 ────────────────────────────────────────────────
@router.get("/stats")
def get_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    teacher_count = db.query(User).filter(User.role == "teacher").count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    total_sessions = db.query(ExamSession).filter(ExamSession.score.isnot(None)).count()
    total_answers = db.query(Answer).count()
    total_questions = db.query(Question).count()
    subjects = db.query(Subject).all()
    subject_counts = [
        {"subject": s.name, "count": db.query(Question).filter(Question.subject_id == s.id).count()}
        for s in subjects
    ]
    return {
        "total_users": total_users,
        "active_users": active_users,
        "teacher_count": teacher_count,
        "admin_count": admin_count,
        "total_sessions": total_sessions,
        "total_answers": total_answers,
        "total_questions": total_questions,
        "subject_counts": subject_counts,
    }


# ── 題庫管理 ──────────────────────────────────────────────────
@router.get("/questions")
def list_questions(
    subject_id: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Question)
    if subject_id:
        q = q.filter(Question.subject_id == subject_id)
    if year:
        q = q.filter(Question.year == year)
    total = q.count()
    items = (
        q.order_by(Question.year.desc(), Question.sitting, Question.number)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "questions": [
            {
                "id": i.id,
                "subject_id": i.subject_id,
                "year": i.year,
                "sitting": i.sitting,
                "number": i.number,
                "content": i.content,
                "option_a": i.option_a,
                "option_b": i.option_b,
                "option_c": i.option_c,
                "option_d": i.option_d,
                "answer": i.answer,
                "difficulty": i.difficulty or "",
            }
            for i in items
        ],
    }


class QuestionCreate(BaseModel):
    subject_id: int
    year: int
    sitting: int
    number: int
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str


class QuestionUpdate(BaseModel):
    content: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    answer: Optional[str] = None
    difficulty: Optional[str] = None


@router.post("/questions")
def create_question(
    body: QuestionCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if body.answer not in ("A", "B", "C", "D"):
        raise HTTPException(status_code=400, detail="Answer must be A/B/C/D")
    q = Question(**body.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"id": q.id}


@router.patch("/questions/{q_id}")
def update_question(
    q_id: str,
    body: QuestionUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    data = body.model_dump(exclude_none=True)
    if "answer" in data and data["answer"] not in ("A", "B", "C", "D"):
        raise HTTPException(status_code=400, detail="Answer must be A/B/C/D")
    for field, val in data.items():
        setattr(q, field, val)
    db.commit()
    return {"ok": True}


@router.delete("/questions/{q_id}")
def delete_question(
    q_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Question).filter(Question.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"ok": True}
