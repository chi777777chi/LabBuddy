import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="student")  # student / teacher / admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions: Mapped[list["ExamSession"]] = relationship(back_populates="user")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)          # 臨床生理學與病理學
    name_en: Mapped[str] = mapped_column(String, unique=True, nullable=False)       # clinical_physiology
    folder: Mapped[str] = mapped_column(String, unique=True, nullable=False)        # Question/clinical_physiology

    questions: Mapped[list["Question"]] = relationship(back_populates="subject")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)       # 114
    sitting: Mapped[int] = mapped_column(Integer, nullable=False)    # 1 or 2
    number: Mapped[int] = mapped_column(Integer, nullable=False)     # 題號 1–80
    content: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(String, nullable=False)      # A / B / C / D
    has_image: Mapped[bool] = mapped_column(Boolean, default=False)
    image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True)  # easy/medium/hard (Phase 5 AI)

    subject: Mapped["Subject"] = relationship(back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(back_populates="question")


class ExamSession(Base):
    __tablename__ = "exam_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sitting: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mode: Mapped[str] = mapped_column(String, nullable=False)         # single_full / single_random / multi_random
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    timed: Mapped[bool] = mapped_column(Boolean, default=False)
    instant_review: Mapped[bool] = mapped_column(Boolean, default=True)
    save_to_history: Mapped[bool] = mapped_column(Boolean, default=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    answers: Mapped[list["Answer"]] = relationship(back_populates="session")


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("exam_sessions.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), nullable=False)
    chosen: Mapped[str | None] = mapped_column(String, nullable=True)   # A/B/C/D 或 None（未作答）
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    session: Mapped["ExamSession"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship(back_populates="answers")
