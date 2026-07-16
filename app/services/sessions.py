from __future__ import annotations

import secrets
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from random import Random
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.topics.contracts import GeneratedQuestion, MasteryState
from app.core.topics.registry import TopicRegistry
from app.database.models import PracticeSession, Question, SkillMastery, User


def _mastery_state(row: SkillMastery) -> MasteryState:
    dates = row.topic_state.get("correct_dates", [])
    return MasteryState(
        skill_key=row.skill_key,
        box=row.box,
        due_at=row.due_at,
        attempt_count=row.attempt_count,
        correct_count=row.correct_count,
        consecutive_correct=row.consecutive_correct,
        correct_dates=tuple(str(day) for day in dates[-3:]),
        state=dict(row.topic_state),
    )


async def load_mastery(
    session: AsyncSession, user_id: int, topic_id: str
) -> dict[str, MasteryState]:
    rows = (
        await session.scalars(
            select(SkillMastery).where(
                SkillMastery.user_id == user_id, SkillMastery.topic_id == topic_id
            )
        )
    ).all()
    return {row.skill_key: _mastery_state(row) for row in rows}


async def start_session(
    session: AsyncSession,
    registry: TopicRegistry,
    user: User,
    mode_id: str,
    kind: str,
    configuration: dict[str, Any] | None = None,
) -> PracticeSession:
    configuration = dict(configuration or {})
    topic = registry.get(user.selected_topic_id)
    await session.execute(
        update(PracticeSession)
        .where(PracticeSession.user_id == user.id, PracticeSession.status == "active")
        .values(status="abandoned", completed_at=datetime.now(UTC))
    )
    if kind == "test":
        test_definition = next(
            (item for item in topic.test_definitions() if item.test_id == mode_id), None
        )
        if test_definition is None:
            raise ValueError("unknown test definition")
        blueprint = topic.test_blueprint(mode_id, configuration, Random(secrets.randbits(64)))
        count = test_definition.question_count
    else:
        practice_definition = next(
            (item for item in topic.practice_modes() if item.mode_id == mode_id), None
        )
        if practice_definition is None:
            raise ValueError("unknown practice mode")
        requested_count = int(
            configuration.get("question_count_override", practice_definition.default_question_count)
        )
        if not 1 <= requested_count <= practice_definition.default_question_count:
            raise ValueError("invalid practice question count")
        count = requested_count
        mastery = await load_mastery(session, user.id, user.selected_topic_id)
        blueprint = topic.session_blueprint(
            mode_id, count, mastery, configuration, Random(secrets.randbits(64))
        )
    configuration["blueprint"] = [list(item) for item in blueprint]
    record = PracticeSession(
        user_id=user.id,
        topic_id=user.selected_topic_id,
        mode_id=mode_id,
        session_kind=kind,
        configuration=configuration,
        planned_question_count=count,
    )
    session.add(record)
    await session.flush()
    return record


def _to_question(
    generated: GeneratedQuestion,
    *,
    session_id: int | None,
    user_id: int,
    position: int,
    expiry: timedelta,
) -> Question:
    media_payload = asdict(generated.media) if generated.media else None
    return Question(
        public_id=secrets.token_urlsafe(6),
        session_id=session_id,
        user_id=user_id,
        topic_id=generated.topic_id,
        skill_key=generated.skill_key,
        position=position,
        question_type=generated.question_type,
        answer_mode=generated.answer_mode,
        prompt_payload={
            "rendered_prompt": generated.rendered_prompt,
            "metadata": generated.metadata,
            "explanation_payload": generated.explanation_payload,
            "correct_answer": generated.correct_answer,
        },
        media_payload=media_payload,
        options=[asdict(option) for option in generated.answer_options],
        correct_answer=generated.correct_answer,
        evaluation_payload=generated.explanation_payload,
        expires_at=datetime.now(UTC) + expiry,
    )


async def next_question(
    session: AsyncSession, registry: TopicRegistry, practice_session: PracticeSession
) -> Question | None:
    pending = await session.scalar(
        select(Question).where(
            Question.session_id == practice_session.id, Question.status == "pending"
        )
    )
    if pending is not None:
        return pending
    position = practice_session.answered_count + 1
    if position > practice_session.planned_question_count:
        if practice_session.status == "active":
            practice_session.status = "completed"
            practice_session.completed_at = datetime.now(UTC)
        return None
    blueprint = practice_session.configuration.get("blueprint", [])
    skill_key, question_type = blueprint[position - 1]
    generated = registry.get(practice_session.topic_id).generate_question(
        str(skill_key), str(question_type), Random(practice_session.id * 1000 + position)
    )
    question = _to_question(
        generated,
        session_id=practice_session.id,
        user_id=practice_session.user_id,
        position=position,
        expiry=timedelta(hours=24),
    )
    session.add(question)
    await session.flush()
    return question


def independent_question(
    generated: GeneratedQuestion, user_id: int, expiry: timedelta = timedelta(days=2)
) -> Question:
    return _to_question(generated, session_id=None, user_id=user_id, position=1, expiry=expiry)
