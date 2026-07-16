from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import BufferedInputFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.bot import Application
from app.database.models import DailyDelivery, Question, User
from app.keyboards.questions import answer_keyboard
from app.services.daily import prepare_daily_question
from app.services.reminders import day_matches

logger = logging.getLogger(__name__)


async def run_daily_worker(bot: Bot, app: Application, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await deliver_due(bot, app)
        except Exception:
            logger.exception("daily worker iteration failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
        except TimeoutError:
            pass


async def deliver_due(bot: Bot, app: Application, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    async with app.sessions() as session:
        users = (
            await session.scalars(
                select(User)
                .options(selectinload(User.settings))
                .where(User.role == "student", User.is_active.is_(True))
            )
        ).all()
    due = []
    for user in users:
        settings = user.settings
        if not settings or not settings.reminders_enabled:
            continue
        local_now = now.astimezone(ZoneInfo(settings.timezone))
        if settings.local_hour == local_now.hour and day_matches(
            settings.days_mask, local_now.date()
        ):
            due.append(user.id)
    sent = 0
    for user_id in due:
        async with app.sessions() as session, session.begin():
            student = await session.scalar(
                select(User).options(selectinload(User.settings)).where(User.id == user_id)
            )
            if not student:
                continue
            delivery, question = await prepare_daily_question(session, app.registry, student, now)
            if delivery.status != "pending" or question is None:
                continue
            delivery_id, question_id, chat_id = (
                delivery.id,
                question.id,
                student.telegram_chat_id,
            )
        try:
            await _send(bot, app, chat_id, question)
        except TelegramForbiddenError:
            await _mark_failed(app, delivery_id, user_id, "blocked", permanent=True)
        except TelegramRetryAfter as exc:
            await asyncio.sleep(min(float(exc.retry_after), 10.0))
            try:
                await _send(bot, app, chat_id, question)
            except TelegramAPIError as retry_exc:
                await _mark_failed(app, delivery_id, user_id, type(retry_exc).__name__)
            else:
                await _mark_sent(app, delivery_id)
                sent += 1
        except TelegramAPIError as exc:
            await _mark_failed(app, delivery_id, user_id, type(exc).__name__)
        else:
            await _mark_sent(app, delivery_id)
            sent += 1
        del question_id
    return sent


async def _send(bot: Bot, app: Application, chat_id: int, question: Question) -> None:
    prompt = (
        f"{app.content.get('daily.title')}\n\n<b>{question.prompt_payload['rendered_prompt']}</b>"
    )
    media = question.media_payload
    if media:
        data = app.registry.get(question.topic_id).render_media(
            str(media["renderer_id"]), dict(media["payload"])
        )
        await bot.send_photo(
            chat_id,
            BufferedInputFile(data, filename=f"{question.public_id}.png"),
            caption=prompt,
            reply_markup=answer_keyboard(question),
        )
    else:
        await bot.send_message(chat_id, prompt, reply_markup=answer_keyboard(question))


async def _mark_sent(app: Application, delivery_id: int) -> None:
    async with app.sessions() as session, session.begin():
        delivery = await session.get(DailyDelivery, delivery_id)
        if delivery:
            delivery.status = "sent"
            delivery.sent_at = datetime.now(UTC)


async def _mark_failed(
    app: Application,
    delivery_id: int,
    user_id: int,
    error_code: str,
    permanent: bool = False,
) -> None:
    async with app.sessions() as session, session.begin():
        delivery = await session.get(DailyDelivery, delivery_id)
        user = await session.get(User, user_id)
        if delivery:
            delivery.status = "failed"
            delivery.error_code = error_code[:128]
        if permanent and user:
            user.delivery_failure_count += 1
            if user.delivery_failure_count >= 3:
                user.is_active = False
