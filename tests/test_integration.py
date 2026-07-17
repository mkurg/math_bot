from __future__ import annotations

from datetime import UTC, datetime
from random import Random
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bot import Application
from app.config import Settings
from app.content.loader import ContentCatalog
from app.core.topics.registry import TopicRegistry
from app.database.models import (
    Attempt,
    DailyDelivery,
    PracticeSession,
    SkillMastery,
    StudentSettings,
    User,
)
from app.services.answers import AlreadyAnswered, submit_answer, submit_constructed_answer
from app.services.daily import prepare_daily_question
from app.services.invitations import InvitationService
from app.services.privacy import delete_student_data
from app.services.sessions import independent_question, next_question, start_session
from app.services.statistics import progress_for_user, topic_group_metrics, user_metrics
from app.services.users import create_student, ensure_initial_records
from app.topics.numeral_systems import NumeralSystemsModule
from app.topics.times_tables import TimesTablesModule
from app.topics.times_tables.skills import parse_skill_key
from app.workers.daily_questions import deliver_due
from tests.sample_topic import SampleTopic


def settings() -> Settings:
    return Settings(
        bot_token="1234567890:abcdefghijklmnopqrstuvwxyz123456",
        bot_username="TimesBot",
        admin_telegram_id=999,
        database_url="postgresql+asyncpg://unused",
        default_timezone="Europe/Zurich",
        default_reminder_hour=datetime.now().hour if 7 <= datetime.now().hour <= 20 else 17,
        default_reminder_days="DAILY",
        enabled_topic_ids="times_tables",
        default_topic_id="times_tables",
    )


def registry(with_sample: bool = False, with_numeral: bool = False) -> TopicRegistry:
    result = TopicRegistry()
    result.register(TimesTablesModule())
    enabled = ["times_tables"]
    if with_sample:
        result.register(SampleTopic())
        enabled.append("sample_topic")
    if with_numeral:
        result.register(NumeralSystemsModule())
        enabled.append("numeral_systems")
    result.configure(tuple(enabled), "times_tables")
    return result


async def seed_student(maker: async_sessionmaker[AsyncSession], telegram_id: int = 100) -> User:
    async with maker() as session, session.begin():
        await ensure_initial_records(session, settings())
        user = await create_student(
            session,
            telegram_user_id=telegram_id,
            telegram_chat_id=telegram_id,
            first_name="Student",
            username="student",
        )
    return user


@pytest.mark.asyncio
async def test_invitation_onboarding_rotation_and_invalid_link(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessions() as session, session.begin():
        await ensure_initial_records(session, settings())
        admin = await session.scalar(select(User).where(User.role == "admin"))
        assert admin
        service = InvitationService("secret", "TimesBot")
        first_link = await service.rotate(session, admin.id)
        raw = first_link.split("join_", 1)[1]
        assert await service.validate(session, raw)
        assert await service.current_link(session) == first_link
        second_link = await service.rotate(session, admin.id)
        assert not await service.validate(session, raw)
        assert second_link != first_link


@pytest.mark.asyncio
async def test_five_question_session_mastery_and_idempotency(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_student(db_sessions)
    module_registry = registry()
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, user.id)
        assert stored
        practice = await start_session(session, module_registry, stored, "quick", "practice")
        seen_skills: list[str] = []
        first_public_id = ""
        for position in range(1, 6):
            question = await next_question(session, module_registry, practice)
            assert question and question.position == position
            seen_skills.append(question.skill_key)
            option = next(
                index
                for index, value in enumerate(question.options)
                if value["value"] == question.correct_answer
            )
            outcome = await submit_answer(
                session, module_registry, stored, question.public_id, option
            )
            if position == 1:
                first_public_id = question.public_id
            assert outcome.evaluation.is_correct
        assert practice.status == "completed"
        assert practice.correct_count == 5
        assert len(seen_skills) == 5
        with pytest.raises(AlreadyAnswered):
            await submit_answer(session, module_registry, stored, first_public_id, 0)
    async with db_sessions() as session:
        assert await session.scalar(select(func.count(Attempt.id))) == 5
        assert (await session.scalar(select(func.count(SkillMastery.id))) or 0) >= 1


@pytest.mark.parametrize(
    ("mode_id", "question_prefix"),
    [("movement", "movement_"), ("rectangle", "rectangle_")],
)
@pytest.mark.asyncio
async def test_formula_problem_answers_update_pair_mastery_and_all_statistics(
    db_sessions: async_sessionmaker[AsyncSession],
    mode_id: str,
    question_prefix: str,
) -> None:
    user = await seed_student(db_sessions)
    module_registry = registry()
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, user.id)
        assert stored
        practice = await start_session(session, module_registry, stored, mode_id, "practice")
        answered: list[tuple[str, str, bool]] = []
        for position in range(1, 7):
            question = await next_question(session, module_registry, practice)
            assert question and question.question_type.startswith(question_prefix)
            operation, low, high = parse_skill_key(question.skill_key)
            metadata = question.prompt_payload["metadata"]
            factors = (
                (int(metadata["speed"]), int(metadata["time"]))
                if mode_id == "movement"
                else (int(metadata["length"]), int(metadata["width"]))
            )
            assert (low, high) == tuple(sorted(factors))
            expected_operation = (
                "mul"
                if question.question_type in {"movement_distance", "rectangle_area"}
                else "div"
            )
            assert operation == expected_operation
            answer_index = next(
                index
                for index, option in enumerate(question.options)
                if (option["value"] == question.correct_answer) is (position < 6)
            )
            outcome = await submit_answer(
                session,
                module_registry,
                stored,
                question.public_id,
                answer_index,
            )
            assert outcome.evaluation.is_correct is (position < 6)
            answered.append(
                (question.skill_key, question.question_type, outcome.evaluation.is_correct)
            )

        assert practice.status == "completed"
        assert practice.answered_count == 6
        assert practice.correct_count == 5
        attempts = (
            await session.scalars(select(Attempt).where(Attempt.user_id == stored.id))
        ).all()
        assert len(attempts) == 6
        assert {(item.skill_key, item.source, item.is_correct) for item in attempts} == {
            (skill_key, "practice", is_correct) for skill_key, _, is_correct in answered
        }
        mastery_rows = (
            await session.scalars(
                select(SkillMastery).where(
                    SkillMastery.user_id == stored.id,
                    SkillMastery.topic_id == "times_tables",
                )
            )
        ).all()
        mastery_by_skill = {item.skill_key: item for item in mastery_rows}
        assert set(mastery_by_skill) == {skill_key for skill_key, _, _ in answered}
        for skill_key, question_type, is_correct in answered:
            row = mastery_by_skill[skill_key]
            assert row.attempt_count == 1
            assert row.correct_count == int(is_correct)
            assert row.box == int(is_correct)
            assert (question_type in row.topic_state.get("correct_formats", [])) is is_correct

        metrics = await user_metrics(session, stored.id, "times_tables")
        assert metrics["total"] == 6
        assert metrics["recent"] == 6
        assert metrics["accuracy"] == 83
        view = await progress_for_user(session, module_registry, stored)
        headline = {item.label: item.value for item in view.headline_metrics}
        assert headline["Всего вопросов"] == "6"
        assert headline["За последние 7 дней"] == "6"
        assert headline["Точность за 7 дней"] == "83%"
        operation_progress = {item.label: item.percentage for item in view.progress_groups[:2]}
        assert operation_progress["Деление"] > 0
        table_progress = view.progress_groups[2]
        assert any(item.value != "0%" for item in table_progress.items)
        topic_breakdown = await topic_group_metrics(session)
        assert topic_breakdown == [("times_tables", 1, 6, 83)]


@pytest.mark.asyncio
async def test_wrong_answer_returns_later_and_progress_survives_restart(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_student(db_sessions)
    module_registry = registry()
    first_skill = ""
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, user.id)
        assert stored
        practice = await start_session(session, module_registry, stored, "quick", "practice")
        question = await next_question(session, module_registry, practice)
        assert question
        first_skill = question.skill_key
        wrong = next(
            index
            for index, value in enumerate(question.options)
            if value["value"] != question.correct_answer
        )
        await submit_answer(session, module_registry, stored, question.public_id, wrong)
        session_id = practice.id
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, user.id)
        resumed = await session.get(PracticeSession, session_id)
        assert stored and resumed
        later: list[str] = []
        while resumed.status == "active":
            question = await next_question(session, module_registry, resumed)
            if not question:
                break
            later.append(question.skill_key)
            correct = next(
                index
                for index, value in enumerate(question.options)
                if value["value"] == question.correct_answer
            )
            await submit_answer(session, module_registry, stored, question.public_id, correct)
        assert first_skill in later[2:]
        view = await progress_for_user(session, module_registry, stored)
        assert int(view.headline_metrics[0].value) == 5


@pytest.mark.asyncio
async def test_daily_duplicate_prevention_and_deletion(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_student(db_sessions)
    module_registry = registry()
    async with db_sessions() as session, session.begin():
        stored = await session.scalar(select(User).where(User.id == user.id))
        assert stored
        first_delivery, first_question = await prepare_daily_question(
            session, module_registry, stored
        )
        second_delivery, second_question = await prepare_daily_question(
            session, module_registry, stored
        )
        assert first_delivery.id == second_delivery.id
        assert first_question and second_question and first_question.id == second_question.id
        option = next(
            index
            for index, value in enumerate(first_question.options)
            if value["value"] == first_question.correct_answer
        )
        await submit_answer(session, module_registry, stored, first_question.public_id, option)
        assert first_delivery.status == "answered"
        await delete_student_data(session, stored)
    async with db_sessions() as session:
        assert await session.get(User, user.id) is None
        assert await session.scalar(select(func.count(DailyDelivery.id))) == 0
        assert await session.scalar(select(func.count(Attempt.id))) == 0


@pytest.mark.asyncio
async def test_sample_topic_generic_session_and_daily_flow(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_student(db_sessions)
    module_registry = registry(with_sample=True)
    async with db_sessions() as session, session.begin():
        stored = await session.get(User, user.id)
        assert stored
        stored.selected_topic_id = "sample_topic"
        practice = await start_session(session, module_registry, stored, "sample", "practice")
        question = await next_question(session, module_registry, practice)
        assert question and question.topic_id == "sample_topic"
        outcome = await submit_answer(session, module_registry, stored, question.public_id, 0)
        assert outcome.completed and outcome.evaluation.is_correct
        view = await progress_for_user(session, module_registry, stored)
        assert view.current_targets[0].skill_key == "sample:one"
        delivery, daily = await prepare_daily_question(session, module_registry, stored)
        assert daily and daily.topic_id == "sample_topic"
        assert delivery.topic_id == "sample_topic"


@pytest.mark.asyncio
async def test_two_real_topics_are_strictly_isolated_for_sessions_daily_and_progress(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    times_student = await seed_student(db_sessions, telegram_id=701)
    numeral_student = await seed_student(db_sessions, telegram_id=702)
    module_registry = registry(with_numeral=True)
    async with db_sessions() as session, session.begin():
        times_user = await session.get(User, times_student.id)
        numeral_user = await session.get(User, numeral_student.id)
        assert times_user and numeral_user
        numeral_user.selected_topic_id = "numeral_systems"

        times_session = await start_session(
            session, module_registry, times_user, "quick", "practice"
        )
        numeral_session = await start_session(
            session, module_registry, numeral_user, "quick", "practice"
        )
        times_question = await next_question(session, module_registry, times_session)
        numeral_question = await next_question(session, module_registry, numeral_session)
        assert times_question and times_question.topic_id == "times_tables"
        assert numeral_question and numeral_question.topic_id == "numeral_systems"

        times_daily, times_daily_question = await prepare_daily_question(
            session, module_registry, times_user
        )
        numeral_daily, numeral_daily_question = await prepare_daily_question(
            session, module_registry, numeral_user
        )
        assert times_daily.topic_id == "times_tables"
        assert times_daily_question and times_daily_question.topic_id == "times_tables"
        assert numeral_daily.topic_id == "numeral_systems"
        assert numeral_daily_question and numeral_daily_question.topic_id == "numeral_systems"

        generated = module_registry.get("numeral_systems").generate_question(
            "hexadecimal:dec_to_hex", "direct_conversion", Random(7)
        )
        constructed = independent_question(generated, numeral_user.id)
        session.add(constructed)
        await session.flush()
        outcome = await submit_constructed_answer(
            session,
            module_registry,
            numeral_user,
            constructed.public_id,
            str(generated.correct_answer["value"]),
        )
        assert outcome.evaluation.is_correct
        numeral_progress = await progress_for_user(session, module_registry, numeral_user)
        times_progress = await progress_for_user(session, module_registry, times_user)
        assert numeral_progress.headline_metrics[0].value == "1"
        assert times_progress.headline_metrics[0].value == "0"

        breakdown = await topic_group_metrics(session)
        assert {row[0] for row in breakdown} == {"times_tables", "numeral_systems"}


@pytest.mark.asyncio
async def test_daily_worker_sends_only_once(
    db_sessions: async_sessionmaker[AsyncSession],
) -> None:
    user = await seed_student(db_sessions)
    now = datetime.now(UTC).replace(hour=17, minute=0, second=0, microsecond=0)
    async with db_sessions() as session, session.begin():
        student_settings = await session.get(StudentSettings, user.id)
        assert student_settings
        student_settings.local_hour = now.hour
        student_settings.timezone = "UTC"
        student_settings.days_mask = "DAILY"
    content = ContentCatalog(
        __import__("pathlib").Path(__file__).parents[1]
        / "app"
        / "content"
        / "core"
        / "strings.yaml"
    )
    test_settings = settings()
    app = Application(
        test_settings,
        db_sessions,
        registry(),
        content,
        InvitationService(test_settings.bot_token, test_settings.bot_username),
    )
    bot = AsyncMock()
    assert await deliver_due(bot, app, now) == 1
    assert await deliver_due(bot, app, now) == 0
    bot.send_message.assert_awaited_once()
