from typing import cast

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot import Application
from app.handlers.common import actor, callback_actor, send_question
from app.services.sessions import next_question, start_session

router = Router(name="learning")


async def show_learning(
    message: Message | InaccessibleMessage, app: Application, topic_id: str
) -> None:
    message = cast(Message, message)
    topic = app.registry.get(topic_id)
    units = topic.learning_units()
    buttons = [
        InlineKeyboardButton(
            text=topic.content(unit.title_key),
            callback_data=f"lu:{index}",
        )
        for index, unit in enumerate(units)
    ]
    rows = [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="m:menu")])
    await message.answer(
        topic.content("learn.title"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.message(Command("learn"))
@router.message(F.text.in_({"📚 Learn tables", "🧭 Learn"}))
async def learning_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_learning(message, app, user.selected_topic_id)


@router.callback_query(F.data.startswith("lu:"))
async def learning_unit(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    index = int(callback.data.split(":")[1])
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        topic = app.registry.get(user.selected_topic_id)
        units = topic.learning_units()
        if not 0 <= index < len(units):
            return
        unit = units[index]
        view = topic.render_learning_unit(unit.unit_id)
    rows: list[list[InlineKeyboardButton]] = []
    if unit.related_practice_mode_id:
        rows.append(
            [
                InlineKeyboardButton(
                    text=app.content.get("learn.practice"), callback_data=f"lp:{index}"
                )
            ]
        )
    if view.image_renderer_id:
        rows.append(
            [
                InlineKeyboardButton(
                    text=app.content.get("learn.picture"), callback_data=f"li:{index}"
                )
            ]
        )
    if view.related_text:
        rows.append(
            [
                InlineKeyboardButton(
                    text=app.content.get("learn.division"), callback_data=f"ld:{index}"
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="m:learn")])
    await callback.message.answer(
        f"<b>{view.title}</b>\n\n{view.body}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data == "m:learn")
async def learning_back(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
    if user:
        await show_learning(callback.message, app, user.selected_topic_id)


async def _learning_context(callback: CallbackQuery, app: Application):  # type: ignore[no-untyped-def]
    if not callback.data:
        return None
    index = int(callback.data.split(":")[1])
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return None
        topic = app.registry.get(user.selected_topic_id)
        unit = topic.learning_units()[index]
        view = topic.render_learning_unit(unit.unit_id)
        return user, topic, unit, view


@router.callback_query(F.data.startswith("li:"))
async def learning_image(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    result = await _learning_context(callback, app)
    if not result:
        return
    _, topic, _, view = result
    if view.image_renderer_id:
        data = topic.render_media(view.image_renderer_id, view.image_payload)
        await callback.message.answer_photo(BufferedInputFile(data, filename="table.png"))


@router.callback_query(F.data.startswith("ld:"))
async def learning_division(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    result = await _learning_context(callback, app)
    if result and result[3].related_text:
        await callback.message.answer(
            f"<b>{app.content.get('learn.related_title')}</b>\n\n{result[3].related_text}"
        )


@router.callback_query(F.data.startswith("lp:"))
async def learning_practice(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    index = int((callback.data or "").split(":")[1])
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        topic = app.registry.get(user.selected_topic_id)
        unit = topic.learning_units()[index]
        view = topic.render_learning_unit(unit.unit_id)
        practice_session = await start_session(
            session,
            app.registry,
            user,
            unit.related_practice_mode_id or "quick",
            "practice",
            view.practice_configuration,
        )
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)
