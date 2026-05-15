from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Question, Subject

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/")
def list_questions(
    subject_id: int | None = Query(None),
    year: int | None = Query(None),
    sitting: int | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Question)
    if subject_id:
        q = q.filter(Question.subject_id == subject_id)
    if year:
        q = q.filter(Question.year == year)
    if sitting:
        q = q.filter(Question.sitting == sitting)
    return q.order_by(Question.year, Question.sitting, Question.number).all()


@router.get("/{question_id}")
def get_question(question_id: str, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@router.get("/exams/list")
def list_exams(subject_id: int | None = Query(None), db: Session = Depends(get_db)):
    """列出所有已匯入的考古題年份與梯次組合"""
    q = db.query(Question.subject_id, Question.year, Question.sitting).distinct()
    if subject_id:
        q = q.filter(Question.subject_id == subject_id)
    rows = q.order_by(Question.subject_id, Question.year.desc(), Question.sitting).all()
    return [{"subject_id": r[0], "year": r[1], "sitting": r[2]} for r in rows]
