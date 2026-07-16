from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot import Application
from app.handlers.common import actor, callback_actor, send_question
from app.services.daily import prepare_daily_question
from app.services.sessions import next_question, start_session

router = Router(name="daily")


@router.message(F.text.in_({"☀️ Daily task", "☀️ Задание дня"}))
async def daily_task(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
        if not user:
            return
        if user.role != "student" or not user.settings:
            await message.answer(app.text("student_only", user.selected_topic_id))
            return
        delivery, question = await prepare_daily_question(
            session, app.registry, user, datetime.now(UTC)
        )
        should_send = delivery.status == "pending" and question is not None
        if should_send:
            delivery.status = "sent"
            delivery.sent_at = datetime.now(UTC)
    if should_send and question:
        await send_question(message.bot, message, app, question, None, daily=True)
    else:
        await message.answer(app.text("daily.already", user.selected_topic_id))


@router.callback_query(F.data == "daily:more")
async def one_more(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        if user.role != "student" or not user.settings:
            await callback.message.answer(app.text("student_only", user.selected_topic_id))
            return
        practice_session = await start_session(
            session,
            app.registry,
            user,
            "quick",
            "practice",
            {"question_count_override": 1},
        )
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)
