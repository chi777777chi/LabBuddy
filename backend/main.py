from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from core.config import settings
from db.database import Base, engine
from api.routes import auth, users, subjects, questions, exam, ai, analytics, admin, teacher

Base.metadata.create_all(bind=engine)


def _migrate_user_is_active():
    """SQLite: 對舊 DB 補上 users.is_active 欄位（如果不存在）。"""
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        cols = [row[1] for row in rows]
        if "is_active" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"))
            conn.commit()


def _migrate_questions_tags():
    """SQLite: 對舊 DB 補上 questions.tags 欄位（如果不存在）。"""
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(questions)")).fetchall()
        cols = [row[1] for row in rows]
        if "tags" not in cols:
            conn.execute(text("ALTER TABLE questions ADD COLUMN tags TEXT"))
            conn.commit()


def _migrate_classes_announcement():
    """SQLite: 對舊 DB 補上 classes.announcement 欄位（如果不存在）。"""
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(classes)")).fetchall()
        cols = [row[1] for row in rows]
        if "announcement" not in cols:
            conn.execute(text("ALTER TABLE classes ADD COLUMN announcement TEXT"))
            conn.commit()


_migrate_user_is_active()
_migrate_questions_tags()
_migrate_classes_announcement()

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
app.include_router(subjects.router)
app.include_router(questions.router)
app.include_router(exam.router)
app.include_router(ai.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(teacher.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
