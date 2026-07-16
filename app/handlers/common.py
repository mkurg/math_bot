from __future__ import annotations

from html import escape
from typing import cast

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import Application
from app.database.models import PracticeSession, Question, User
from app.keyboards.common import main_menu
from app.keyboards.questions import answer_keyboard
from app.services.users import get_user, touch_user


async def actor(session: AsyncSession, message: Message) -> User | None:
    if message.from_user is None:
        return None
    user = await get_user(session, message.from_user.id)
    if user and user.is_active:
        touch_user(
            user,
            message.chat.id,
            message.from_user.first_name,
            message.from_user.username,
        )
    return user


async def callback_actor(session: AsyncSession, callback: CallbackQuery) -> User | None:
    user = await get_user(session, callback.from_user.id)
    if user and user.is_active and callback.message:
        touch_user(
            user,
            callback.message.chat.id,
            callback.from_user.first_name,
            callback.from_user.username,
        )
    return user


async def show_main_menu(
    message: Message | InaccessibleMessage, app: Application, text_key: str = "main_menu"
) -> None:
    message = cast(Message, message)
    await message.answer(app.content.get(text_key), reply_markup=main_menu(app.content))


async def send_question(
    bot: Bot | None,
    message: Message | InaccessibleMessage,
    app: Application,
    question: Question,
    practice_session: PracticeSession | None,
    daily: bool = False,
) -> None:
    if bot is None:
        raise RuntimeError("Telegram bot context is unavailable")
    message = cast(Message, message)
    prompt = escape(str(question.prompt_payload["rendered_prompt"]))
    if daily:
        prompt = f"{app.content.get('daily.title')}\n\n<b>{prompt}</b>"
    elif practice_session:
        position = app.content.get(
            "question.position",
            position=question.position,
            total=practice_session.planned_question_count,
        )
        prompt = f"<b>{prompt}</b>\n\n{position}"
    keyboard = answer_keyboard(question)
    if practice_session and practice_session.session_kind == "test":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                *keyboard.inline_keyboard,
                [
                    InlineKeyboardButton(
                        text=app.content.get("test.abandon"),
                        callback_data=f"tx:{practice_session.id}",
                    )
                ],
            ]
        )
    media = question.media_payload
    if media:
        topic = app.registry.get(question.topic_id)
        try:
            data = topic.render_media(str(media["renderer_id"]), dict(media["payload"]))
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(data, filename=f"{question.public_id}.png"),
                caption=prompt,
                reply_markup=keyboard,
            )
            return
        except TelegramAPIError:
            prompt = f"{escape(str(media['fallback_text']))}\n\n{prompt}"
    await message.answer(prompt, reply_markup=keyboard)


def next_keyboard(question: Question, app: Application) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=app.content.get("question.next"), callback_data=f"n:{question.public_id}"
                )
            ]
        ]
    )
