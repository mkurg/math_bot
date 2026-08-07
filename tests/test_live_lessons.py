from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import Application
from app.content.loader import ContentCatalog
from app.database.models import PracticeSession, Question, StudentSettings, User
from app.handlers import admin, learning, practice, questions
from app.services.invitations import InvitationService
from app.services.live_lessons import mirror_photo, record_live_event
from tests.test_handlers import fake_callback, fake_message
from tests.test_integration import registry, seed_student
from tests.test_integration import settings as integration_settings


def _app(maker: async_sessionmaker[AsyncSession]) -> Application:
    configured = integration_settings()
    return Application(
        configured,
        maker,
        registry(with_algebra=True),
        ContentCatalog(Path(__file__).parents[1] / "app" / "content" / "core" / "strings.yaml"),
        InvitationService(configured.bot_token, configured.bot_username),
    )


@pytest.mark.asyncio
async def test_live_context_is_persistent_even_before_teacher_connects(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    student = await seed_student(db_sessions, telegram_id=801)
    app = _app(db_sessions)
    bot = AsyncMock()
    await record_live_event(
        bot,
        app,
        student.id,
        "theory",
        "Теория: Слагаемые",
        "Точный материал, который сейчас читает ученик.",
    )
    bot.send_message.assert_not_awaited()

    async with db_sessions() as session:
        settings = await session.get(StudentSettings, student.id)
        assert settings
        assert not settings.live_lesson_enabled
        assert settings.live_context["event_type"] == "theory"
        assert settings.live_context["title"] == "Теория: Слагаемые"
        assert "Точный материал" in settings.live_context["body"]
        assert settings.live_context["updated_at"]


@pytest.mark.asyncio
async def test_admin_live_mode_mirrors_theory_question_selected_answer_and_progress(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    student = await seed_student(db_sessions, telegram_id=802)
    app = _app(db_sessions)
    bot = AsyncMock()
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, student.id)
        assert stored
        stored.selected_topic_id = "algebraic_expressions"

    admin_message = fake_message(app.settings.admin_telegram_id, bot)
    await admin.toggle_live_lesson(
        fake_callback(
            admin_message,
            f"adlive:{student.id}",
            app.settings.admin_telegram_id,
            bot,
        ),
        app,
    )
    async with db_sessions() as session:
        settings = await session.get(StudentSettings, student.id)
        assert settings and settings.live_lesson_enabled
    assert any(
        call.kwargs.get("chat_id") == student.telegram_chat_id
        and "Учитель подключился" in call.kwargs.get("text", "")
        for call in bot.send_message.await_args_list
    )
    await mirror_photo(bot, app, student.id, b"same-image", "Иллюстрация к вопросу")
    assert any(
        call.kwargs.get("chat_id") == app.settings.admin_telegram_id
        and "Иллюстрация к вопросу" in call.kwargs.get("caption", "")
        for call in bot.send_photo.await_args_list
    )

    student_message = fake_message(student.telegram_user_id, bot)
    await learning.learning_unit(
        fake_callback(student_message, "lu:0", student.telegram_user_id, bot), app
    )
    teacher_messages = [
        call.kwargs["text"]
        for call in bot.send_message.await_args_list
        if call.kwargs.get("chat_id") == app.settings.admin_telegram_id
    ]
    assert any("Теория: 1. Из чего состоит выражение" in text for text in teacher_messages)
    assert any("Знак относится к следующему" in text for text in teacher_messages)

    await practice.choose_mode(
        fake_callback(student_message, "pm:signs", student.telegram_user_id, bot), app
    )
    async with db_sessions() as session:
        active = await session.scalar(
            select(PracticeSession).where(
                PracticeSession.user_id == student.id,
                PracticeSession.status == "active",
            )
        )
        assert active and active.topic_id == "algebraic_expressions"
        question = await session.scalar(
            select(Question).where(
                Question.session_id == active.id,
                Question.status == "pending",
            )
        )
        assert question
        correct_index = next(
            index
            for index, option in enumerate(question.options)
            if option["value"] == question.correct_answer
        )
        selected_label = question.options[correct_index]["label"]
        prompt = question.prompt_payload["rendered_prompt"]

    await questions.answer(
        fake_callback(
            student_message,
            f"a:{question.public_id}:{correct_index}",
            student.telegram_user_id,
            bot,
        ),
        app,
    )
    teacher_messages = [
        call.kwargs["text"]
        for call in bot.send_message.await_args_list
        if call.kwargs.get("chat_id") == app.settings.admin_telegram_id
    ]
    assert any(
        "Тренировка:" in text and prompt in text and "Вопрос 1 из 8" in text
        for text in teacher_messages
    )
    assert any(
        "Ответ ученика" in text
        and selected_label in text
        and "Результат: ✅ Верно" in text
        and "Отвечено 1 из 8" in text
        for text in teacher_messages
    )

    async with db_sessions() as session:
        settings = await session.get(StudentSettings, student.id)
        assert settings
        assert settings.live_context["event_type"] == "answer"
        assert prompt in settings.live_context["body"]
        assert selected_label in settings.live_context["body"]


@pytest.mark.asyncio
async def test_only_one_student_is_live_and_both_are_notified_when_teacher_switches(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    first = await seed_student(db_sessions, telegram_id=803)
    second = await seed_student(db_sessions, telegram_id=804)
    app = _app(db_sessions)
    bot = AsyncMock()
    admin_message = fake_message(app.settings.admin_telegram_id, bot)

    for student in (first, second):
        await admin.toggle_live_lesson(
            fake_callback(
                admin_message,
                f"adlive:{student.id}",
                app.settings.admin_telegram_id,
                bot,
            ),
            app,
        )

    async with db_sessions() as session:
        first_settings = await session.get(StudentSettings, first.id)
        second_settings = await session.get(StudentSettings, second.id)
        assert first_settings and not first_settings.live_lesson_enabled
        assert second_settings and second_settings.live_lesson_enabled
    notices = [
        (call.kwargs.get("chat_id"), call.kwargs.get("text", ""))
        for call in bot.send_message.await_args_list
    ]
    assert (
        first.telegram_chat_id,
        "Индивидуальный урок завершён. Трансляция действий учителю выключена.",
    ) in notices
    assert any(
        chat_id == second.telegram_chat_id and "Учитель подключился" in text
        for chat_id, text in notices
    )

    await admin.toggle_live_lesson(
        fake_callback(
            admin_message,
            f"adlive:{second.id}",
            app.settings.admin_telegram_id,
            bot,
        ),
        app,
    )
    async with db_sessions() as session:
        second_settings = await session.get(StudentSettings, second.id)
        assert second_settings and not second_settings.live_lesson_enabled
