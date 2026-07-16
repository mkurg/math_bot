from typing import cast

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot import Application
from app.handlers.common import actor, callback_actor, send_question
from app.keyboards.common import table_grid
from app.services.sessions import next_question, start_session

router = Router(name="practice")


async def show_practice(
    message: Message | InaccessibleMessage, app: Application, topic_id: str
) -> None:
    message = cast(Message, message)
    topic = app.registry.get(topic_id)
    rows = [
        [
            InlineKeyboardButton(
                text=topic.content(mode.title_key), callback_data=f"pm:{mode.mode_id}"
            )
        ]
        for mode in topic.practice_modes()
    ]
    rows.append(
        [InlineKeyboardButton(text=app.text("menu.back", topic_id), callback_data="m:menu")]
    )
    await message.answer(
        topic.content("practice.title"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.message(Command("practice"))
@router.message(F.text.in_({"▶️ Practice", "▶️ Practise", "▶️ Тренировка"}))
async def practice_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_practice(message, app, user.selected_topic_id)
    else:
        await message.answer(app.text("invite_required", app.settings.default_topic_id))


@router.callback_query(F.data == "m:practice")
async def practice_callback(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
    if user:
        await show_practice(callback.message, app, user.selected_topic_id)


@router.callback_query(F.data.startswith("pm:"))
async def choose_mode(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    mode_id = callback.data.split(":", 1)[1]
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        if mode_id == "table":
            await callback.message.answer(
                app.text("practice.choose_table", user.selected_topic_id),
                reply_markup=table_grid("pt"),
            )
            return
        practice_session = await start_session(session, app.registry, user, mode_id, "practice")
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)


@router.callback_query(F.data.startswith("pt:"))
async def choose_practice_table(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    table = int(callback.data.split(":", 1)[1])
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        practice_session = await start_session(
            session, app.registry, user, "table", "practice", {"table": table}
        )
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)
