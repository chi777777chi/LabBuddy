from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.security import decode_token
from ...db.database import get_db
from ...db.models import User

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
