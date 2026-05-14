from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db.database import Base, engine
from .api.routes import auth, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="醫檢師國考題庫平台 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
