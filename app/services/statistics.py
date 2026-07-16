from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.topics.contracts import TopicProgressView
from app.core.topics.registry import TopicRegistry
from app.database.models import Attempt, SkillMastery, User
from app.services.sessions import load_mastery


async def user_metrics(
    session: AsyncSession, user_id: int, topic_id: str
) -> dict[str, int | float]:
    since = datetime.now(UTC) - timedelta(days=7)
    total = await session.scalar(
        select(func.count(Attempt.id)).where(
            Attempt.user_id == user_id, Attempt.topic_id == topic_id
        )
    )
    recent, correct = (
        await session.execute(
            select(func.count(Attempt.id), func.count(Attempt.id).filter(Attempt.is_correct)).where(
                Attempt.user_id == user_id,
                Attempt.topic_id == topic_id,
                Attempt.created_at >= since,
            )
        )
    ).one()
    active_days = await session.scalar(
        select(func.count(distinct(func.date(Attempt.created_at)))).where(
            Attempt.user_id == user_id,
            Attempt.topic_id == topic_id,
            Attempt.created_at >= since,
        )
    )
    return {
        "total": total or 0,
        "recent": recent or 0,
        "accuracy": round((correct or 0) / recent * 100) if recent else 0,
        "active_days": active_days or 0,
    }


async def progress_for_user(
    session: AsyncSession, registry: TopicRegistry, user: User
) -> TopicProgressView:
    mastery = await load_mastery(session, user.id, user.selected_topic_id)
    metrics = await user_metrics(session, user.id, user.selected_topic_id)
    return registry.get(user.selected_topic_id).progress_view(mastery, metrics)


async def group_metrics(session: AsyncSession) -> dict[str, int]:
    since = datetime.now(UTC) - timedelta(days=7)
    students = await session.scalar(
        select(func.count(User.id)).where(User.role == "student", User.is_active.is_(True))
    )
    active = await session.scalar(
        select(func.count(User.id)).where(
            User.role == "student", User.is_active.is_(True), User.last_seen_at >= since
        )
    )
    questions, correct = (
        await session.execute(
            select(func.count(Attempt.id), func.count(Attempt.id).filter(Attempt.is_correct)).where(
                Attempt.created_at >= since
            )
        )
    ).one()
    reminders = await session.scalar(
        select(func.count(User.id))
        .join(User.settings)
        .where(User.role == "student", User.settings.has(reminders_enabled=True))
    )
    return {
        "students": students or 0,
        "active": active or 0,
        "questions": questions or 0,
        "accuracy": round((correct or 0) / questions * 100) if questions else 0,
        "reminders": reminders or 0,
    }


async def difficult_skills(session: AsyncSession, limit: int = 5) -> list[tuple[str, int]]:
    rows = (
        await session.execute(
            select(
                SkillMastery.skill_key,
                func.sum(SkillMastery.attempt_count - SkillMastery.correct_count),
            )
            .group_by(SkillMastery.skill_key)
            .order_by(func.sum(SkillMastery.attempt_count - SkillMastery.correct_count).desc())
            .limit(limit)
        )
    ).all()
    return [(key, int(count or 0)) for key, count in rows]
