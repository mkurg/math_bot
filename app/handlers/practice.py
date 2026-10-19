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
from app.core.topics.contracts import TopicModule
from app.handlers.common import actor, callback_actor, send_question
from app.keyboards.common import table_grid
from app.services.live_lessons import record_live_event
from app.services.sessions import next_question, start_session
from app.topics.python_foundations.module import CATALOG_PAGE_SIZE
from app.topics.python_foundations.questions import QUESTION_TYPES

router = Router(name="practice")


def _catalog_page(topic: TopicModule, page: int) -> tuple[str, InlineKeyboardMarkup]:
    skills = topic.skills()
    page_count = (len(skills) + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE
    if not 0 <= page < page_count:
        raise ValueError("invalid catalog page")
    start = page * CATALOG_PAGE_SIZE
    end = min(start + CATALOG_PAGE_SIZE, len(skills))
    rows = [
        [
            InlineKeyboardButton(
                text=f"{index + 1}. {topic.content(skills[index].title_key)}",
                callback_data=f"ps:{index}",
            )
        ]
        for index in range(start, end)
    ]
    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text=topic.content("catalog.previous"), callback_data=f"pc:{page - 1}"
            )
        )
    if page + 1 < page_count:
        navigation.append(
            InlineKeyboardButton(text=topic.content("catalog.next"), callback_data=f"pc:{page + 1}")
        )
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text=topic.content("menu.back"), callback_data="m:practice")])
    return (
        topic.content("catalog.title", start=start + 1, end=end, total=len(skills)),
        InlineKeyboardMarkup(inline_keyboard=rows),
    )


def _catalog_skill(topic: TopicModule, index: int) -> tuple[str, InlineKeyboardMarkup]:
    skills = topic.skills()
    if not 0 <= index < len(skills):
        raise ValueError("invalid catalog skill")
    rows = [
        [
            InlineKeyboardButton(
                text=topic.content(f"catalog.{kind}"), callback_data=f"pq:{index}:{kind}"
            )
        ]
        for kind in QUESTION_TYPES
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=topic.content("catalog.back"),
                callback_data=f"pc:{index // CATALOG_PAGE_SIZE}",
            )
        ]
    )
    return (
        topic.content(
            "catalog.skill",
            number=index + 1,
            total=len(skills),
            skill=topic.content(skills[index].title_key),
        ),
        InlineKeyboardMarkup(inline_keyboard=rows),
    )


async def show_practice(
    message: Message | InaccessibleMessage,
    app: Application,
    topic_id: str,
    student_id: int | None = None,
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
    if topic_id == "python_foundations":
        rows.append(
            [InlineKeyboardButton(text=topic.content("catalog.button"), callback_data="pc:0")]
        )
    rows.append(
        [InlineKeyboardButton(text=app.text("menu.back", topic_id), callback_data="m:menu")]
    )
    await message.answer(
        topic.content("practice.title"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    if student_id is not None:
        await record_live_event(
            message.bot,
            app,
            student_id,
            "practice_menu",
            "Ученик открыл тренировки",
            "\n".join(topic.content(mode.title_key) for mode in topic.practice_modes()),
        )


@router.callback_query(F.data.startswith("pc:"))
async def catalog_page(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    try:
        page = int(callback.data.split(":", 1)[1])
    except ValueError:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
    if not user or user.selected_topic_id != "python_foundations":
        return
    topic = app.registry.get(user.selected_topic_id)
    try:
        title, keyboard = _catalog_page(topic, page)
    except ValueError:
        return
    await callback.message.answer(title, reply_markup=keyboard)


@router.callback_query(F.data.startswith("ps:"))
async def catalog_skill(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    try:
        index = int(callback.data.split(":", 1)[1])
    except ValueError:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
    if not user or user.selected_topic_id != "python_foundations":
        return
    topic = app.registry.get(user.selected_topic_id)
    try:
        title, keyboard = _catalog_skill(topic, index)
    except ValueError:
        return
    await callback.message.answer(title, reply_markup=keyboard)


@router.callback_query(F.data.startswith("pq:"))
async def catalog_question(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    try:
        _, index_text, question_type = callback.data.split(":", 2)
        index = int(index_text)
    except ValueError:
        return
    if question_type not in QUESTION_TYPES:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user or user.selected_topic_id != "python_foundations":
            return
        topic = app.registry.get(user.selected_topic_id)
        skills = topic.skills()
        if not 0 <= index < len(skills):
            return
        practice_session = await start_session(
            session,
            app.registry,
            user,
            "quick",
            "practice",
            {
                "question_count_override": 1,
                "catalog_skill": skills[index].skill_key,
                "catalog_type": question_type,
            },
        )
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)


@router.message(Command("practice"))
@router.message(F.text.in_({"▶️ Practice", "▶️ Practise", "▶️ Тренировка"}))
async def practice_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_practice(message, app, user.selected_topic_id, user.id)
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
        await show_practice(callback.message, app, user.selected_topic_id, user.id)


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
