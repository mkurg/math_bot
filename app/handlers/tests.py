from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import update

from app.bot import Application
from app.database.models import PracticeSession, Question
from app.handlers.common import actor, callback_actor, send_question
from app.keyboards.common import table_grid
from app.services.sessions import next_question, start_session

router = Router(name="tests")


async def show_tests(message: Message, app: Application, topic_id: str) -> None:
    topic = app.registry.get(topic_id)
    rows = [
        [
            InlineKeyboardButton(
                text=topic.content(item.title_key), callback_data=f"tm:{item.test_id}"
            )
        ]
        for item in topic.test_definitions()
    ]
    rows.append([InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="m:menu")])
    await message.answer(
        app.content.get("tests.title"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.message(Command("test"))
@router.message(F.text == "🎯 Tests")
async def test_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_tests(message, app, user.selected_topic_id)


@router.callback_query(F.data.startswith("tm:"))
async def choose_test(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    test_id = callback.data.split(":", 1)[1]
    if test_id == "table":
        await callback.message.answer(
            app.content.get("tests.choose_table"), reply_markup=table_grid("tt")
        )
        return
    await _start_test(callback, app, test_id, {})


@router.callback_query(F.data.startswith("tt:"))
async def choose_test_table(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if callback.data:
        await _start_test(callback, app, "table", {"table": int(callback.data.split(":")[1])})


async def _start_test(
    callback: CallbackQuery, app: Application, test_id: str, configuration: dict[str, int]
) -> None:
    if not callback.message:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        practice_session = await start_session(
            session, app.registry, user, test_id, "test", configuration
        )
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)


@router.callback_query(F.data.startswith("tx:"))
async def abandon_test_ask(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    session_id = int(callback.data.split(":")[1])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=app.content.get("test.abandon.yes"),
                    callback_data=f"txc:{session_id}",
                )
            ],
            [InlineKeyboardButton(text=app.content.get("delete.cancel"), callback_data="m:menu")],
        ]
    )
    await callback.message.answer(app.content.get("test.abandon.confirm"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("txc:"))
async def abandon_test_confirm(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    session_id = int(callback.data.split(":")[1])
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        practice_session = await session.get(PracticeSession, session_id, with_for_update=True)
        if (
            not user
            or not practice_session
            or practice_session.user_id != user.id
            or practice_session.session_kind != "test"
        ):
            return
        practice_session.status = "abandoned"
        await session.execute(
            update(Question)
            .where(Question.session_id == session_id, Question.status == "pending")
            .values(status="expired")
        )
    await callback.message.answer(app.content.get("test.abandon.done"))
