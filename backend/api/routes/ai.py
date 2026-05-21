from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Question, User
from core.security import decode_token
from services.ai_service import get_hint

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
