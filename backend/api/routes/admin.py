from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.security import decode_token
from db.database import get_db
from db.models import Answer, Class, ClassMember, ExamSession, Question, Subject, User

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


# ── 班級管理 ──────────────────────────────────────────────────────

@router.get("/classes")
def list_all_classes(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    classes = db.query(Class).order_by(Class.created_at.desc()).all()
    result = []
    for cls in classes:
        teacher = db.query(User).filter(User.id == cls.teacher_id).first()
        member_count = db.query(ClassMember).filter(ClassMember.class_id == cls.id).count()
        result.append({
            "id": cls.id,
            "name": cls.name,
            "teacher_name": teacher.name if teacher else "—",
            "teacher_email": teacher.email if teacher else "—",
            "member_count": member_count,
            "invite_code": cls.invite_code,
            "created_at": cls.created_at.strftime("%Y/%m/%d"),
        })
    return result


@router.get("/classes/{class_id}")
def get_class_detail(
    class_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    teacher = db.query(User).filter(User.id == cls.teacher_id).first()
    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()
    students = []
    for m in members:
        student = db.query(User).filter(User.id == m.student_id).first()
        if not student:
            continue
        sessions = (
            db.query(ExamSession)
            .filter(
                ExamSession.user_id == student.id,
                ExamSession.score.isnot(None),
                ExamSession.save_to_history == True,
            )
            .all()
        )
        last_attempt = max((s.started_at for s in sessions), default=None)
        avg_score = (
            str(round(sum(s.score for s in sessions) / len(sessions)))
            if sessions else ""
        )
        students.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "last_attempt": last_attempt.strftime("%Y/%m/%d") if last_attempt else "—",
            "total_sessions": len(sessions),
            "avg_score": avg_score,
            "joined_at": m.joined_at.strftime("%Y/%m/%d"),
        })
    return {
        "id": cls.id,
        "name": cls.name,
        "invite_code": cls.invite_code,
        "teacher_name": teacher.name if teacher else "—",
        "teacher_email": teacher.email if teacher else "—",
        "created_at": cls.created_at.strftime("%Y/%m/%d"),
        "students": students,
    }


class AddMemberBody(BaseModel):
    email: str


@router.post("/classes/{class_id}/members")
def add_class_member(
    class_id: str,
    body: AddMemberBody,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    student = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"找不到 email 為 {body.email} 的使用者")
    if student.id == cls.teacher_id:
        raise HTTPException(status_code=400, detail="不能將授課老師加入自己的班級")
    existing = db.query(ClassMember).filter(
        ClassMember.class_id == class_id, ClassMember.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"「{student.name}」已在此班級中")
    db.add(ClassMember(class_id=class_id, student_id=student.id))
    db.commit()
    return {"ok": True, "name": student.name, "email": student.email}


@router.delete("/classes/{class_id}/members/{student_id}")
def remove_class_member(
    class_id: str,
    student_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    member = db.query(ClassMember).filter(
        ClassMember.class_id == class_id, ClassMember.student_id == student_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="該學生不在此班級")
    db.delete(member)
    db.commit()
    return {"ok": True}
