from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from random import Random
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mastery.engine import apply_answer
from app.core.topics.contracts import EvaluationResult, MasteryState, TopicModule
from app.core.topics.registry import TopicRegistry
from app.database.models import (
    Attempt,
    DailyDelivery,
    PracticeSession,
    Question,
    SkillMastery,
    User,
)


class AnswerError(Exception):
    pass


class AlreadyAnswered(AnswerError):
    pass


class NotQuestionOwner(AnswerError):
    pass


class ExpiredQuestion(AnswerError):
    pass


class InvalidConstructedAnswer(AnswerError):
    pass


@dataclass(frozen=True, slots=True)
class AnswerOutcome:
    evaluation: EvaluationResult
    question: Question
    session: PracticeSession | None
    source: str
    completed: bool


async def submit_answer(
    session: AsyncSession,
    registry: TopicRegistry,
    user: User,
    public_id: str,
    option_index: int,
) -> AnswerOutcome:
    question = await _answerable_question(session, user, public_id)
    if not 0 <= option_index < len(question.options):
        raise AlreadyAnswered
    selected = question.options[option_index]["value"]
    return await _record_answer(session, registry, user, question, selected)


async def submit_constructed_answer(
    session: AsyncSession,
    registry: TopicRegistry,
    user: User,
    public_id: str,
    value: str,
) -> AnswerOutcome:
    question = await _answerable_question(session, user, public_id)
    alphabets = {
        "binary_pad": set("01"),
        "octal_pad": set("01234567"),
        "decimal_pad": set("0123456789"),
        "hexadecimal_pad": set("0123456789ABCDEF"),
    }
    alphabet = alphabets.get(question.answer_mode)
    normalized = value.upper()
    metadata = question.prompt_payload.get("metadata", {})
    max_length = int(metadata.get("max_length", 8))
    if (
        alphabet is None
        or not normalized
        or len(normalized) > max_length
        or any(character not in alphabet for character in normalized)
    ):
        raise InvalidConstructedAnswer
    return await _record_answer(session, registry, user, question, {"value": normalized})


async def _answerable_question(session: AsyncSession, user: User, public_id: str) -> Question:
    question = await session.scalar(
        select(Question).where(Question.public_id == public_id).with_for_update()
    )
    if question is None:
        raise ExpiredQuestion
    if question.user_id != user.id:
        raise NotQuestionOwner
    now = datetime.now(UTC)
    if question.expires_at < now:
        question.status = "expired"
        raise ExpiredQuestion
    if question.status != "pending":
        raise AlreadyAnswered
    return question


async def _record_answer(
    session: AsyncSession,
    registry: TopicRegistry,
    user: User,
    question: Question,
    selected: dict[str, Any],
) -> AnswerOutcome:
    now = datetime.now(UTC)
    topic = registry.get(question.topic_id)
    evaluation = topic.evaluate_answer(question.prompt_payload, selected)
    practice_session = (
        await session.get(PracticeSession, question.session_id, with_for_update=True)
        if question.session_id
        else None
    )
    source = "daily" if practice_session is None else practice_session.session_kind
    response_ms = max(0, int((now - question.created_at).total_seconds() * 1000))
    result = await session.execute(
        insert(Attempt)
        .values(
            question_id=question.id,
            user_id=user.id,
            topic_id=question.topic_id,
            skill_key=question.skill_key,
            selected_answer=selected,
            is_correct=evaluation.is_correct,
            response_time_ms=response_ms,
            source=source,
        )
        .on_conflict_do_nothing(index_elements=["question_id", "user_id"])
        .returning(Attempt.id)
    )
    if result.scalar_one_or_none() is None:
        raise AlreadyAnswered
    question.status = "answered"

    mastery = await session.scalar(
        select(SkillMastery)
        .where(
            SkillMastery.user_id == user.id,
            SkillMastery.topic_id == question.topic_id,
            SkillMastery.skill_key == question.skill_key,
        )
        .with_for_update()
    )
    if mastery is None:
        mastery = SkillMastery(
            user_id=user.id, topic_id=question.topic_id, skill_key=question.skill_key
        )
        session.add(mastery)
        await session.flush()
    state = MasteryState(
        skill_key=mastery.skill_key,
        box=mastery.box,
        due_at=mastery.due_at,
        attempt_count=mastery.attempt_count,
        correct_count=mastery.correct_count,
        consecutive_correct=mastery.consecutive_correct,
        correct_dates=tuple(mastery.topic_state.get("correct_dates", [])),
    )
    updated = apply_answer(state, evaluation.is_correct, now)
    mastery.box = updated.box
    mastery.due_at = updated.due_at
    mastery.attempt_count = updated.attempt_count
    mastery.correct_count = updated.correct_count
    mastery.consecutive_correct = updated.consecutive_correct
    mastery.last_answered_at = now
    mastery.last_correct_at = now if evaluation.is_correct else mastery.last_correct_at
    topic_state = {**mastery.topic_state, "correct_dates": list(updated.correct_dates)}
    if evaluation.is_correct:
        formats = [str(item) for item in topic_state.get("correct_formats", [])]
        formats.append(question.question_type)
        topic_state["correct_formats"] = formats[-6:]
    misconception = evaluation.feedback_payload.get("misconception")
    if not evaluation.is_correct and isinstance(misconception, str) and misconception:
        misconception_counts = dict(topic_state.get("misconceptions", {}))
        misconception_counts[misconception] = int(misconception_counts.get(misconception, 0)) + 1
        topic_state["misconceptions"] = misconception_counts
    mastery.topic_state = topic_state

    completed = False
    if practice_session is not None:
        practice_session.answered_count += 1
        practice_session.correct_count += int(evaluation.is_correct)
        if not evaluation.is_correct and practice_session.session_kind == "practice":
            _schedule_retry(practice_session, question, topic)
        if practice_session.answered_count >= practice_session.planned_question_count:
            practice_session.status = "completed"
            practice_session.completed_at = now
            completed = True
    else:
        delivery = await session.scalar(
            select(DailyDelivery).where(DailyDelivery.question_id == question.id).with_for_update()
        )
        if delivery:
            delivery.status = "answered"
            delivery.answered_at = now
    return AnswerOutcome(evaluation, question, practice_session, source, completed)


def _schedule_retry(
    practice_session: PracticeSession, question: Question, topic: TopicModule
) -> None:
    target_index = question.position + 2
    if target_index >= practice_session.planned_question_count:
        return
    configuration: dict[str, Any] = dict(practice_session.configuration)
    blueprint = [list(item) for item in configuration.get("blueprint", [])]
    if target_index < len(blueprint):
        retry_type = topic.retry_question_type(
            question.skill_key,
            question.question_type,
            Random(question.id * 1000 + target_index),
        )
        blueprint[target_index] = [question.skill_key, retry_type]
        configuration["blueprint"] = blueprint
        practice_session.configuration = configuration
