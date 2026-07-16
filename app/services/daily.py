from __future__ import annotations

from datetime import UTC, datetime
from random import Random
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.topics.registry import TopicRegistry
from app.database.models import DailyDelivery, Question, StudentSettings, User
from app.services.sessions import independent_question, load_mastery


async def prepare_daily_question(
    session: AsyncSession,
    registry: TopicRegistry,
    user: User,
    now: datetime | None = None,
) -> tuple[DailyDelivery, Question | None]:
    now = now or datetime.now(UTC)
    settings = await session.get(StudentSettings, user.id)
    if settings is None:
        raise RuntimeError("student reminder settings are missing")
    local_date = now.astimezone(ZoneInfo(settings.timezone)).date()
    existing = await session.scalar(
        select(DailyDelivery).where(
            DailyDelivery.user_id == user.id, DailyDelivery.local_date == local_date
        )
    )
    if existing:
        question = (
            await session.get(Question, existing.question_id) if existing.question_id else None
        )
        return existing, question
    mastery = await load_mastery(session, user.id, user.selected_topic_id)
    topic = registry.get(user.selected_topic_id)
    skill_key, question_type = topic.daily_skill(
        mastery, now, Random(user.id * 100_000 + local_date.toordinal())
    )
    generated = topic.generate_question(
        skill_key, question_type, Random(user.id * 1_000_000 + local_date.toordinal())
    )
    question = independent_question(generated, user.id)
    session.add(question)
    await session.flush()
    delivery = DailyDelivery(
        user_id=user.id,
        topic_id=user.selected_topic_id,
        local_date=local_date,
        question_id=question.id,
        status="pending",
    )
    session.add(delivery)
    await session.flush()
    return delivery, question
