from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.database.models import ClassSettings, StudentSettings, User


async def get_user(session: AsyncSession, telegram_user_id: int) -> User | None:
    result: User | None = await session.scalar(
        select(User)
        .options(selectinload(User.settings))
        .where(User.telegram_user_id == telegram_user_id)
    )
    return result


async def ensure_initial_records(session: AsyncSession, settings: Settings) -> None:
    class_settings = await session.get(ClassSettings, 1)
    if class_settings is None:
        session.add(
            ClassSettings(
                id=1,
                timezone=settings.default_timezone,
                default_topic_id=settings.default_topic_id,
                default_reminders_enabled=settings.default_reminder_days != "OFF",
                default_days_mask=settings.default_reminder_days,
                default_local_hour=settings.default_reminder_hour,
            )
        )
    admin = await get_user(session, settings.admin_telegram_id)
    if admin is None:
        session.add(
            User(
                telegram_user_id=settings.admin_telegram_id,
                telegram_chat_id=settings.admin_telegram_id,
                role="admin",
                display_name="Teacher",
                selected_topic_id=settings.default_topic_id,
            )
        )
    elif admin.role != "admin":
        admin.role = "admin"
    await session.flush()


async def create_student(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    telegram_chat_id: int,
    first_name: str,
    username: str | None,
) -> User:
    class_settings = await session.get(ClassSettings, 1)
    if class_settings is None:
        raise RuntimeError("class settings have not been initialized")
    user = User(
        telegram_user_id=telegram_user_id,
        telegram_chat_id=telegram_chat_id,
        role="student",
        display_name=first_name[:128],
        telegram_username=username,
        selected_topic_id=class_settings.default_topic_id,
    )
    session.add(user)
    await session.flush()
    session.add(
        StudentSettings(
            user_id=user.id,
            reminders_enabled=class_settings.default_reminders_enabled,
            days_mask=class_settings.default_days_mask,
            local_hour=class_settings.default_local_hour,
            timezone=class_settings.timezone,
        )
    )
    return user


def touch_user(user: User, chat_id: int, first_name: str, username: str | None) -> None:
    user.telegram_chat_id = chat_id
    user.display_name = first_name[:128]
    user.telegram_username = username
    user.last_seen_at = datetime.now(UTC)
