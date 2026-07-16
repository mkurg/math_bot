from __future__ import annotations

from pathlib import Path
from random import Random
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import Application
from app.content.loader import ContentCatalog
from app.database.models import PracticeSession, Question, User
from app.handlers import (
    admin,
    daily,
    learning,
    menu,
    practice,
    privacy,
    progress,
    questions,
    settings,
)
from app.handlers import tests as test_handlers
from app.services.invitations import InvitationService
from app.services.sessions import independent_question
from tests.test_integration import registry, seed_student
from tests.test_integration import settings as integration_settings


def fake_message(telegram_id: int, bot: AsyncMock | None = None) -> Message:
    bot = bot or AsyncMock()
    value = SimpleNamespace(
        from_user=SimpleNamespace(
            id=telegram_id,
            first_name="Student",
            username="student",
        ),
        chat=SimpleNamespace(id=telegram_id, type="private"),
        bot=bot,
        answer=AsyncMock(),
        answer_photo=AsyncMock(),
        edit_reply_markup=AsyncMock(),
    )
    return cast(Message, value)


def fake_callback(
    message: Message, data: str, telegram_id: int, bot: AsyncMock | None = None
) -> CallbackQuery:
    bot = bot or cast(AsyncMock, message.bot)
    value = SimpleNamespace(
        from_user=SimpleNamespace(
            id=telegram_id,
            first_name="Student",
            username="student",
        ),
        message=message,
        data=data,
        bot=bot,
        answer=AsyncMock(),
    )
    return cast(CallbackQuery, value)


def make_app(maker: async_sessionmaker[AsyncSession], *, with_numeral: bool = False) -> Application:
    configured = integration_settings()
    return Application(
        configured,
        maker,
        registry(with_numeral=with_numeral),
        ContentCatalog(Path(__file__).parents[1] / "app" / "content" / "core" / "strings.yaml"),
        InvitationService(configured.bot_token, configured.bot_username),
    )


@pytest.mark.asyncio
async def test_student_menu_practice_question_and_daily_handlers(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    student = await seed_student(db_sessions)
    app = make_app(db_sessions)
    bot = AsyncMock()
    message = fake_message(student.telegram_user_id, bot)

    await menu.menu_command(message, app)
    await menu.help_command(message, app)
    await practice.practice_menu(message, app)
    await learning.learning_menu(message, app)
    await test_handlers.test_menu(message, app)
    await progress.progress(message, app)
    await settings.settings_menu(message, app)
    await privacy.privacy(message, app)
    assert cast(AsyncMock, message.answer).await_count >= 8
    rendered_messages = [
        call.args[0]
        for call in cast(AsyncMock, message.answer).await_args_list
        if call.args and isinstance(call.args[0], str)
    ]
    assert any("Выбери занятие" in text for text in rendered_messages)
    assert any("Мой прогресс" in text for text in rendered_messages)

    await practice.practice_callback(
        fake_callback(message, "m:practice", student.telegram_user_id, bot), app
    )
    await practice.choose_mode(
        fake_callback(message, "pm:table", student.telegram_user_id, bot), app
    )
    await practice.choose_practice_table(
        fake_callback(message, "pt:7", student.telegram_user_id, bot), app
    )
    assert cast(AsyncMock, message.answer).await_count >= 11
    assert any(
        "<b>A</b>" in call.args[0] and "Вопрос 1 из" in call.args[0]
        for call in cast(AsyncMock, message.answer).await_args_list
        if call.args and isinstance(call.args[0], str)
    )

    for _ in range(10):
        async with db_sessions() as session:
            stored = await session.scalar(
                select(User).where(User.telegram_user_id == student.telegram_user_id)
            )
            assert stored
            active = await session.scalar(
                select(PracticeSession).where(
                    PracticeSession.user_id == stored.id,
                    PracticeSession.status == "active",
                )
            )
            if not active:
                break
            question = await session.scalar(
                select(Question).where(
                    Question.session_id == active.id, Question.status == "pending"
                )
            )
            assert question
            correct_index = next(
                index
                for index, option in enumerate(question.options)
                if option["value"] == question.correct_answer
            )
        answer_callback = fake_callback(
            message,
            f"a:{question.public_id}:{correct_index}",
            student.telegram_user_id,
            bot,
        )
        await questions.answer(answer_callback, app)
        if active.answered_count + 1 < active.planned_question_count:
            await questions.next_answer(
                fake_callback(
                    message,
                    f"n:{question.public_id}",
                    student.telegram_user_id,
                    bot,
                ),
                app,
            )

    await daily.daily_task(message, app)
    await daily.daily_task(message, app)
    await daily.one_more(fake_callback(message, "daily:more", student.telegram_user_id, bot), app)
    await settings.settings_callback(
        fake_callback(message, "m:settings", student.telegram_user_id, bot), app
    )
    await settings.set_frequency(
        fake_callback(message, "sf:DAILY", student.telegram_user_id, bot), app
    )
    await settings.set_hour(fake_callback(message, "sh:17", student.telegram_user_id, bot), app)


@pytest.mark.asyncio
async def test_learning_test_privacy_and_admin_handlers(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    student = await seed_student(db_sessions)
    app = make_app(db_sessions)
    bot = AsyncMock()
    student_message = fake_message(student.telegram_user_id, bot)

    await learning.learning_unit(
        fake_callback(student_message, "lu:6", student.telegram_user_id, bot), app
    )
    await learning.learning_image(
        fake_callback(student_message, "li:6", student.telegram_user_id, bot), app
    )
    await learning.learning_division(
        fake_callback(student_message, "ld:6", student.telegram_user_id, bot), app
    )
    await learning.learning_practice(
        fake_callback(student_message, "lp:6", student.telegram_user_id, bot), app
    )
    await test_handlers.choose_test(
        fake_callback(student_message, "tm:division", student.telegram_user_id, bot), app
    )
    async with db_sessions() as session:
        active_test = await session.scalar(
            select(PracticeSession).where(
                PracticeSession.user_id == student.id,
                PracticeSession.session_kind == "test",
                PracticeSession.status == "active",
            )
        )
        assert active_test
    await test_handlers.abandon_test_ask(
        fake_callback(student_message, f"tx:{active_test.id}", student.telegram_user_id, bot),
        app,
    )
    await test_handlers.abandon_test_confirm(
        fake_callback(student_message, f"txc:{active_test.id}", student.telegram_user_id, bot),
        app,
    )

    configured = integration_settings()
    admin_message = fake_message(configured.admin_telegram_id, bot)
    await admin.admin_menu(admin_message, app)
    await admin.admin_menu_callback(
        fake_callback(admin_message, "ad:menu", configured.admin_telegram_id, bot), app
    )
    await admin.student_list(
        fake_callback(admin_message, "ad:students:0", configured.admin_telegram_id, bot), app
    )
    await admin.student_detail(
        fake_callback(admin_message, f"adstu:{student.id}", configured.admin_telegram_id, bot),
        app,
    )
    await admin.student_reminder_menu(
        fake_callback(admin_message, f"adsf:{student.id}", configured.admin_telegram_id, bot),
        app,
    )
    await admin.set_student_frequency(
        fake_callback(
            admin_message,
            f"adsfv:{student.id}:WEEKDAYS",
            configured.admin_telegram_id,
            bot,
        ),
        app,
    )
    await admin.set_student_hour(
        fake_callback(
            admin_message,
            f"adsh:{student.id}:16",
            configured.admin_telegram_id,
            bot,
        ),
        app,
    )
    await admin.group_progress(
        fake_callback(admin_message, "ad:group", configured.admin_telegram_id, bot), app
    )
    await admin.defaults_menu(
        fake_callback(admin_message, "ad:defaults", configured.admin_telegram_id, bot), app
    )
    await admin.set_default_frequency(
        fake_callback(admin_message, "adf:MWF", configured.admin_telegram_id, bot), app
    )
    await admin.set_default_hour(
        fake_callback(admin_message, "adh:18", configured.admin_telegram_id, bot), app
    )
    await admin.apply_defaults_ask(
        fake_callback(admin_message, "adapply:ask", configured.admin_telegram_id, bot), app
    )
    await admin.apply_defaults(
        fake_callback(admin_message, "adapply:yes", configured.admin_telegram_id, bot), app
    )
    await admin.invite_menu(
        fake_callback(admin_message, "ad:invite", configured.admin_telegram_id, bot), app
    )
    await admin.invite_ask(
        fake_callback(admin_message, "adi:ask", configured.admin_telegram_id, bot), app
    )
    await admin.invite_rotate(
        fake_callback(admin_message, "adi:yes", configured.admin_telegram_id, bot), app
    )

    await privacy.delete_me(student_message, app)
    await privacy.delete_confirmation(
        fake_callback(student_message, "del:no", student.telegram_user_id, bot), app
    )
    await privacy.delete_confirmation(
        fake_callback(student_message, "del:yes", student.telegram_user_id, bot), app
    )
    async with db_sessions() as session:
        assert await session.get(User, student.id) is None


@pytest.mark.asyncio
async def test_numeral_student_pad_hint_menus_and_admin_assignment(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    student = await seed_student(db_sessions, telegram_id=303)
    app = make_app(db_sessions, with_numeral=True)
    bot = AsyncMock()
    message = fake_message(student.telegram_user_id, bot)
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, student.id)
        assert stored
        stored.selected_topic_id = "numeral_systems"

    await menu.menu_command(message, app)
    await practice.practice_menu(message, app)
    await learning.learning_menu(message, app)
    await test_handlers.test_menu(message, app)
    assert cast(AsyncMock, message.answer).await_count == 4
    menu_markup = cast(AsyncMock, message.answer).await_args_list[0].kwargs["reply_markup"]
    assert menu_markup.keyboard[0][1].text == "🧭 Learn"
    practice_markup = cast(AsyncMock, message.answer).await_args_list[1].kwargs["reply_markup"]
    tier_labels = [row[0].text for row in practice_markup.inline_keyboard[:3]]
    assert tier_labels == [
        "🌱 Tier 1 — Foundations (5)",
        "🧩 Tier 2 — Guided grouping (6)",
        "🏔 Tier 3 — Full curriculum (8)",
    ]
    await learning.learning_unit(fake_callback(message, "lu:7", student.telegram_user_id, bot), app)
    await learning.learning_image(
        fake_callback(message, "li:7", student.telegram_user_id, bot), app
    )

    topic = app.registry.get("numeral_systems")
    generated = topic.generate_question("hexadecimal:dec_to_hex", "direct_conversion", Random(9))
    async with db_sessions() as session, session.begin():
        question = independent_question(generated, student.id)
        session.add(question)
        await session.flush()
        public_id = question.public_id
    await questions.show_hint(
        fake_callback(message, f"h:{public_id}", student.telegram_user_id, bot), app
    )
    await questions.numeral_pad(
        fake_callback(
            message,
            f"p:{public_id}:{generated.correct_answer['value']}:s",
            student.telegram_user_id,
            bot,
        ),
        app,
    )
    async with db_sessions() as session:
        answered = await session.scalar(select(Question).where(Question.public_id == public_id))
        assert answered and answered.status == "answered"
        assert answered.prompt_payload["hint_count"] == 1

    configured = integration_settings()
    admin_message = fake_message(configured.admin_telegram_id, bot)
    await admin.student_topic_menu(
        fake_callback(
            admin_message,
            f"adta:{student.id}",
            configured.admin_telegram_id,
            bot,
        ),
        app,
    )
    await admin.set_student_topic(
        fake_callback(
            admin_message,
            f"adtv:{student.id}:0",
            configured.admin_telegram_id,
            bot,
        ),
        app,
    )
    async with db_sessions() as session:
        reassigned = await session.get(User, student.id)
        assert reassigned and reassigned.selected_topic_id == "times_tables"
