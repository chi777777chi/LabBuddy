import random
import string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.security import decode_token
from db.database import get_db
from db.models import Class, ClassMember, ExamSession, Question, QuestionStats, Subject, User

router = APIRouter(tags=["teacher"])


def get_current_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher only")
    return user


def _gen_code(db: Session) -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not db.query(Class).filter(Class.invite_code == code).first():
            return code


class ClassCreate(BaseModel):
    name: str


class ClassRename(BaseModel):
    name: str


class AnnouncementUpdate(BaseModel):
    announcement: Optional[str] = None


class JoinRequest(BaseModel):
    invite_code: str


# ── 班級 CRUD ──────────────────────────────────────────────────

@router.post("/teacher/classes")
def create_class(
    body: ClassCreate,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="班級名稱不能為空")
    cls = Class(name=body.name.strip(), teacher_id=teacher.id, invite_code=_gen_code(db))
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return {
        "id": cls.id,
        "name": cls.name,
        "invite_code": cls.invite_code,
        "created_at": cls.created_at.strftime("%Y/%m/%d"),
    }


@router.get("/teacher/classes")
def list_classes(
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    classes = (
        db.query(Class)
        .filter(Class.teacher_id == teacher.id)
        .order_by(Class.created_at.desc())
        .all()
    )
    result = []
    for cls in classes:
        member_count = db.query(ClassMember).filter(ClassMember.class_id == cls.id).count()
        result.append({
            "id": cls.id,
            "name": cls.name,
            "invite_code": cls.invite_code,
            "member_count": member_count,
            "created_at": cls.created_at.strftime("%Y/%m/%d"),
        })
    return result


@router.get("/teacher/classes/{class_id}")
def get_class_detail(
    class_id: str,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")

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
        })

    return {
        "id": cls.id,
        "name": cls.name,
        "invite_code": cls.invite_code,
        "announcement": cls.announcement or "",
        "created_at": cls.created_at.strftime("%Y/%m/%d"),
        "students": students,
    }


@router.patch("/teacher/classes/{class_id}/announcement")
def update_announcement(
    class_id: str,
    body: AnnouncementUpdate,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    cls.announcement = body.announcement.strip() if body.announcement else None
    db.commit()
    return {"ok": True, "announcement": cls.announcement or ""}


@router.patch("/teacher/classes/{class_id}")
def rename_class(
    class_id: str,
    body: ClassRename,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="班級名稱不能為空")
    cls.name = body.name.strip()
    db.commit()
    return {"id": cls.id, "name": cls.name}


@router.delete("/teacher/classes/{class_id}")
def delete_class(
    class_id: str,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    db.query(ClassMember).filter(ClassMember.class_id == class_id).delete()
    db.delete(cls)
    db.commit()
    return {"ok": True}


@router.delete("/teacher/classes/{class_id}/members/{student_id}")
def remove_member(
    class_id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    member = db.query(ClassMember).filter(
        ClassMember.class_id == class_id, ClassMember.student_id == student_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="學生不在此班級")
    db.delete(member)
    db.commit()
    return {"ok": True}


@router.post("/teacher/classes/{class_id}/regenerate-code")
def regenerate_code(
    class_id: str,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    cls.invite_code = _gen_code(db)
    db.commit()
    return {"invite_code": cls.invite_code}


# ── 學生個人進度 ────────────────────────────────────────────────

@router.get("/teacher/classes/{class_id}/students/{student_id}")
def get_student_progress(
    class_id: str,
    student_id: str,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")
    if not db.query(ClassMember).filter(
        ClassMember.class_id == class_id, ClassMember.student_id == student_id
    ).first():
        raise HTTPException(status_code=404, detail="該學生不在此班級")

    student = db.query(User).filter(User.id == student_id).first()
    subjects = {s.id: s for s in db.query(Subject).all()}

    sessions = (
        db.query(ExamSession)
        .filter(
            ExamSession.user_id == student_id,
            ExamSession.score.isnot(None),
            ExamSession.save_to_history == True,
        )
        .order_by(ExamSession.started_at.desc())
        .limit(20)
        .all()
    )

    session_list = []
    for s in sessions:
        subj = subjects.get(s.subject_id)
        session_list.append({
            "date": s.started_at.strftime("%Y/%m/%d"),
            "subject_name": subj.name if subj else "—",
            "year": str(s.year) if s.year else "—",
            "sitting": str(s.sitting) if s.sitting else "—",
            "score": s.score,
            "question_count": s.question_count,
        })

    subject_stats = []
    for subj_id, subj in subjects.items():
        subj_sessions = (
            db.query(ExamSession)
            .filter(
                ExamSession.user_id == student_id,
                ExamSession.subject_id == subj_id,
                ExamSession.score.isnot(None),
                ExamSession.save_to_history == True,
            )
            .all()
        )
        if not subj_sessions:
            continue
        avg = round(sum(s.score for s in subj_sessions) / len(subj_sessions))
        subject_stats.append({
            "subject_name": subj.name,
            "avg_score": avg,
            "session_count": len(subj_sessions),
        })
    subject_stats.sort(key=lambda x: x["avg_score"])

    return {
        "name": student.name,
        "email": student.email,
        "class_name": cls.name,
        "sessions": session_list,
        "subject_stats": subject_stats,
    }


# ── 全班統計 ───────────────────────────────────────────────────

@router.get("/teacher/classes/{class_id}/stats")
def get_class_stats(
    class_id: str,
    teacher: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.id == class_id, Class.teacher_id == teacher.id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班級不存在")

    member_ids = [
        m.student_id
        for m in db.query(ClassMember).filter(ClassMember.class_id == class_id).all()
    ]
    if not member_ids:
        return {"class_name": cls.name, "subject_stats": [], "top_wrong_questions": []}

    subjects = db.query(Subject).all()
    subject_stats = []
    for subj in subjects:
        subj_sessions = (
            db.query(ExamSession)
            .filter(
                ExamSession.user_id.in_(member_ids),
                ExamSession.subject_id == subj.id,
                ExamSession.score.isnot(None),
                ExamSession.save_to_history == True,
            )
            .all()
        )
        if not subj_sessions:
            continue
        participant_count = len(set(s.user_id for s in subj_sessions))
        avg_score = round(sum(s.score for s in subj_sessions) / len(subj_sessions))
        subject_stats.append({
            "subject_name": subj.name,
            "participant_count": participant_count,
            "total_sessions": len(subj_sessions),
            "avg_score": avg_score,
        })
    subject_stats.sort(key=lambda x: x["avg_score"])

    wrong_rows = (
        db.query(
            QuestionStats.question_id,
            func.sum(QuestionStats.wrong_count).label("total_wrong"),
            func.sum(QuestionStats.correct_count + QuestionStats.wrong_count).label("total_attempts"),
        )
        .filter(QuestionStats.user_id.in_(member_ids))
        .group_by(QuestionStats.question_id)
        .order_by(func.sum(QuestionStats.wrong_count).desc())
        .limit(10)
        .all()
    )

    top_wrong = []
    for row in wrong_rows:
        if not row.total_attempts:
            continue
        q = db.query(Question).filter(Question.id == row.question_id).first()
        if not q:
            continue
        subj = db.query(Subject).filter(Subject.id == q.subject_id).first()
        top_wrong.append({
            "subject_name": subj.name if subj else "—",
            "year": q.year,
            "sitting": q.sitting,
            "number": q.number,
            "content_short": q.content[:40] + ("…" if len(q.content) > 40 else ""),
            "wrong_count": row.total_wrong,
            "total_attempts": row.total_attempts,
            "wrong_rate": round(row.total_wrong / row.total_attempts * 100),
        })

    return {
        "class_name": cls.name,
        "subject_stats": subject_stats,
        "top_wrong_questions": top_wrong,
    }


# ── 學生加入班級（學生端呼叫）─────────────────────────────────

@router.get("/classes/mine")
def my_classes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """學生查詢自己加入的所有班級。"""
    memberships = (
        db.query(ClassMember)
        .filter(ClassMember.student_id == user.id)
        .order_by(ClassMember.joined_at.desc())
        .all()
    )
    result = []
    for m in memberships:
        cls = db.query(Class).filter(Class.id == m.class_id).first()
        if not cls:
            continue
        teacher = db.query(User).filter(User.id == cls.teacher_id).first()
        member_count = db.query(ClassMember).filter(ClassMember.class_id == cls.id).count()
        result.append({
            "id": cls.id,
            "name": cls.name,
            "teacher_name": teacher.name if teacher else "—",
            "member_count": member_count,
            "announcement": cls.announcement or "",
            "joined_at": m.joined_at.strftime("%Y/%m/%d"),
        })
    return result


@router.post("/classes/join")
def join_class(
    body: JoinRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cls = db.query(Class).filter(Class.invite_code == body.invite_code.upper().strip()).first()
    if not cls:
        raise HTTPException(status_code=404, detail="找不到此邀請碼對應的班級")
    if user.id == cls.teacher_id:
        raise HTTPException(status_code=400, detail="老師無法加入自己的班級")
    existing = db.query(ClassMember).filter(
        ClassMember.class_id == cls.id, ClassMember.student_id == user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="你已經在這個班級了")
    db.add(ClassMember(class_id=cls.id, student_id=user.id))
    db.commit()
    return {"ok": True, "class_name": cls.name}
