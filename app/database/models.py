from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, utcnow


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[str] = mapped_column(String(16), default="student")
    display_name: Mapped[str] = mapped_column(String(128))
    telegram_username: Mapped[str | None] = mapped_column(String(64))
    selected_topic_id: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    delivery_failure_count: Mapped[int] = mapped_column(Integer, default=0)

    settings: Mapped[StudentSettings | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        foreign_keys="StudentSettings.user_id",
    )

    __table_args__ = (CheckConstraint("role IN ('student', 'admin')", name="valid_role"),)


class StudentSettings(Base):
    __tablename__ = "student_settings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    days_mask: Mapped[str] = mapped_column(String(16), default="DAILY")
    local_hour: Mapped[int] = mapped_column(Integer, default=17)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Zurich")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    user: Mapped[User] = relationship(back_populates="settings", foreign_keys=[user_id])


class ClassSettings(Base):
    __tablename__ = "class_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    timezone: Mapped[str] = mapped_column(String(64))
    default_topic_id: Mapped[str] = mapped_column(String(64))
    default_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    default_days_mask: Mapped[str] = mapped_column(String(16), default="DAILY")
    default_local_hour: Mapped[int] = mapped_column(Integer, default=17)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class InviteToken(TimestampMixin, Base):
    __tablename__ = "invite_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class SkillMastery(Base):
    __tablename__ = "skill_mastery"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[str] = mapped_column(String(64))
    skill_key: Mapped[str] = mapped_column(String(128))
    box: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, default=0)
    last_answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_correct_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    topic_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", "skill_key"),
        CheckConstraint("box >= 0 AND box <= 5", name="valid_box"),
    )


class PracticeSession(TimestampMixin, Base):
    __tablename__ = "practice_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[str] = mapped_column(String(64))
    mode_id: Mapped[str] = mapped_column(String(64))
    session_kind: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="active")
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    planned_question_count: Mapped[int] = mapped_column(Integer)
    answered_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("session_kind IN ('practice', 'test')", name="valid_session_kind"),
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned', 'expired')",
            name="valid_session_status",
        ),
        Index(
            "uq_one_active_session_per_user",
            "user_id",
            unique=True,
            postgresql_where=(status == "active"),
        ),
    )


class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[str] = mapped_column(String(64))
    skill_key: Mapped[str] = mapped_column(String(128))
    position: Mapped[int] = mapped_column(Integer)
    question_type: Mapped[str] = mapped_column(String(32))
    answer_mode: Mapped[str] = mapped_column(String(32))
    prompt_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    media_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    correct_answer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    evaluation_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Attempt(TimestampMixin, Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[str] = mapped_column(String(64))
    skill_key: Mapped[str] = mapped_column(String(128))
    selected_answer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    response_time_ms: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(16))

    __table_args__ = (UniqueConstraint("question_id", "user_id"),)


class DailyDelivery(Base):
    __tablename__ = "daily_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[str] = mapped_column(String(64))
    local_date: Mapped[date] = mapped_column(Date)
    question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("user_id", "local_date"),)
