from html import escape
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
from app.services.live_lessons import mirror_photo, record_live_event
from app.services.sessions import next_question, start_session

router = Router(name="learning")

LEARNING_MENU_LABELS = {"📚 Learn tables", "🧭 Learn", "📚 Учить таблицу", "📚 Теория"}


async def show_learning(
    message: Message | InaccessibleMessage,
    app: Application,
    topic_id: str,
    student_id: int | None = None,
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
    width = 1 if len(buttons) > 10 else 2
    rows = [buttons[index : index + width] for index in range(0, len(buttons), width)]
    rows.append(
        [InlineKeyboardButton(text=app.text("menu.back", topic_id), callback_data="m:menu")]
    )
    await message.answer(
        topic.content("learn.title"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    if student_id is not None:
        await record_live_event(
            message.bot,
            app,
            student_id,
            "learning_menu",
            "Ученик открыл раздел теории",
            "\n".join(topic.content(unit.title_key) for unit in units),
        )


@router.message(Command("learn"))
@router.message(F.text.in_(LEARNING_MENU_LABELS))
async def learning_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_learning(message, app, user.selected_topic_id, user.id)


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
                    text=app.text("learn.practice", user.selected_topic_id),
                    callback_data=f"lp:{index}",
                )
            ]
        )
    if view.image_renderer_id:
        rows.append(
            [
                InlineKeyboardButton(
                    text=app.text("learn.picture", user.selected_topic_id),
                    callback_data=f"li:{index}",
                )
            ]
        )
    if view.related_text:
        rows.append(
            [
                InlineKeyboardButton(
                    text=app.text("learn.division", user.selected_topic_id),
                    callback_data=f"ld:{index}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=app.text("menu.back", user.selected_topic_id), callback_data="m:learn"
            )
        ]
    )
    await callback.message.answer(
        f"<b>{escape(view.title)}</b>\n\n{escape(view.body)}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )
    await record_live_event(
        callback.bot,
        app,
        user.id,
        "theory",
        f"Теория: {view.title}",
        view.body,
    )


@router.callback_query(F.data == "m:learn")
async def learning_back(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
    if user:
        await show_learning(callback.message, app, user.selected_topic_id, user.id)


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
    user, topic, _, view = result
    if view.image_renderer_id:
        data = topic.render_media(view.image_renderer_id, view.image_payload)
        await callback.message.answer_photo(BufferedInputFile(data, filename="table.png"))
        await record_live_event(
            callback.bot,
            app,
            user.id,
            "theory_image",
            f"Ученик открыл иллюстрацию: {view.title}",
            view.body,
        )
        await mirror_photo(
            callback.bot,
            app,
            user.id,
            data,
            f"Иллюстрация к теории: {view.title}",
            filename="theory.png",
        )


@router.callback_query(F.data.startswith("ld:"))
async def learning_division(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    result = await _learning_context(callback, app)
    if result and result[3].related_text:
        await callback.message.answer(
            f"<b>{escape(app.text('learn.related_title', result[0].selected_topic_id))}</b>"
            f"\n\n{escape(result[3].related_text)}"
        )
        await record_live_event(
            callback.bot,
            app,
            result[0].id,
            "related_theory",
            f"Дополнительный материал: {result[3].title}",
            result[3].related_text,
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
