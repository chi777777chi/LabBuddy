import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.security import create_access_token
from ...db.database import get_db
from ...db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login():
    params = (
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile"
    )
    return RedirectResponse(GOOGLE_AUTH_URL + params)


@router.get("/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri,
        })
        token_data = token_resp.json()

        if "error" in token_data:
            raise HTTPException(status_code=400, detail="Google OAuth 失敗")

        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        google_user = user_resp.json()

    user = db.query(User).filter(User.google_id == google_user["id"]).first()
    if not user:
        user = User(
            google_id=google_user["id"],
            email=google_user["email"],
            name=google_user["name"],
            avatar_url=google_user.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
    return RedirectResponse(f"{settings.frontend_url}/callback/{token}/")
