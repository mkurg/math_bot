from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mastery.engine import apply_answer
from app.core.topics.contracts import EvaluationResult, MasteryState
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
    if question.status != "pending" or not 0 <= option_index < len(question.options):
        raise AlreadyAnswered
    selected = question.options[option_index]["value"]
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
    mastery.topic_state = {**mastery.topic_state, "correct_dates": list(updated.correct_dates)}

    completed = False
    if practice_session is not None:
        practice_session.answered_count += 1
        practice_session.correct_count += int(evaluation.is_correct)
        if not evaluation.is_correct and practice_session.session_kind == "practice":
            _schedule_retry(practice_session, question)
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


def _schedule_retry(practice_session: PracticeSession, question: Question) -> None:
    target_index = question.position + 2
    if target_index >= practice_session.planned_question_count:
        return
    configuration: dict[str, Any] = dict(practice_session.configuration)
    blueprint = [list(item) for item in configuration.get("blueprint", [])]
    if target_index < len(blueprint):
        current_type = str(blueprint[target_index][1])
        retry_type = (
            "missing_factor"
            if current_type == "direct_multiplication"
            else "direct_multiplication"
            if question.skill_key.startswith("mul:")
            else "missing_divisor"
        )
        blueprint[target_index] = [question.skill_key, retry_type]
        configuration["blueprint"] = blueprint
        practice_session.configuration = configuration
