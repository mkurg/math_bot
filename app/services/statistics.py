from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.topics.contracts import Metric, ProgressItem, TopicProgressView
from app.core.topics.registry import TopicRegistry
from app.database.models import (
    Attempt,
    DailyDelivery,
    PracticeSession,
    Question,
    SkillMastery,
    User,
)
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
    hint_payloads = (
        await session.scalars(
            select(Question.prompt_payload)
            .join(Attempt, Attempt.question_id == Question.id)
            .where(Attempt.user_id == user_id, Attempt.topic_id == topic_id)
        )
    ).all()
    hints = sum(int(payload.get("hint_count", 0)) for payload in hint_payloads)
    daily = await session.scalar(
        select(func.count(DailyDelivery.id)).where(
            DailyDelivery.user_id == user_id,
            DailyDelivery.topic_id == topic_id,
            DailyDelivery.sent_at >= since,
        )
    )
    return {
        "total": total or 0,
        "recent": recent or 0,
        "accuracy": round((correct or 0) / recent * 100) if recent else 0,
        "active_days": active_days or 0,
        "hints": hints,
        "daily": daily or 0,
    }


async def progress_for_user(
    session: AsyncSession, registry: TopicRegistry, user: User
) -> TopicProgressView:
    mastery = await load_mastery(session, user.id, user.selected_topic_id)
    metrics = await user_metrics(session, user.id, user.selected_topic_id)
    topic = registry.get(user.selected_topic_id)
    view = topic.progress_view(mastery, metrics)
    definitions = {item.test_id: item for item in topic.test_definitions()}
    recent_sessions = (
        await session.scalars(
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user.id,
                PracticeSession.topic_id == user.selected_topic_id,
                PracticeSession.session_kind == "test",
                PracticeSession.status == "completed",
            )
            .order_by(PracticeSession.completed_at.desc())
            .limit(3)
        )
    ).all()
    recent_results = tuple(
        Metric(
            topic.content(definitions[item.mode_id].title_key)
            if item.mode_id in definitions
            else item.mode_id,
            f"{item.correct_count}/{item.planned_question_count}",
        )
        for item in recent_sessions
    )
    return replace(view, recent_results=recent_results)


async def teacher_insights_for_user(
    session: AsyncSession, registry: TopicRegistry, user: User
) -> tuple[ProgressItem, ...]:
    mastery = await load_mastery(session, user.id, user.selected_topic_id)
    metrics = await user_metrics(session, user.id, user.selected_topic_id)
    return registry.get(user.selected_topic_id).teacher_insights(mastery, metrics)


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


async def difficult_skills(session: AsyncSession, limit: int = 5) -> list[tuple[str, str, int]]:
    rows = (
        await session.execute(
            select(
                SkillMastery.topic_id,
                SkillMastery.skill_key,
                func.sum(SkillMastery.attempt_count - SkillMastery.correct_count),
            )
            .group_by(SkillMastery.topic_id, SkillMastery.skill_key)
            .order_by(func.sum(SkillMastery.attempt_count - SkillMastery.correct_count).desc())
            .limit(limit)
        )
    ).all()
    return [(topic_id, key, int(count or 0)) for topic_id, key, count in rows]


async def topic_group_metrics(session: AsyncSession) -> list[tuple[str, int, int, int]]:
    since = datetime.now(UTC) - timedelta(days=7)
    student_rows = (
        await session.execute(
            select(User.selected_topic_id, func.count(User.id))
            .where(User.role == "student", User.is_active.is_(True))
            .group_by(User.selected_topic_id)
        )
    ).all()
    students = {topic_id: int(count) for topic_id, count in student_rows}
    attempt_rows = (
        await session.execute(
            select(
                Attempt.topic_id,
                func.count(Attempt.id),
                func.count(Attempt.id).filter(Attempt.is_correct),
            )
            .where(Attempt.created_at >= since)
            .group_by(Attempt.topic_id)
        )
    ).all()
    attempts = {topic_id: (int(total), int(correct)) for topic_id, total, correct in attempt_rows}
    return [
        (
            topic_id,
            count,
            attempts.get(topic_id, (0, 0))[0],
            round(attempts.get(topic_id, (0, 0))[1] / attempts[topic_id][0] * 100)
            if topic_id in attempts and attempts[topic_id][0]
            else 0,
        )
        for topic_id, count in sorted(students.items())
    ]
