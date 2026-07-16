from __future__ import annotations

from html import escape
from typing import cast

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select

from app.bot import Application
from app.core.questions.callbacks import parse_answer_callback
from app.database.models import Attempt, PracticeSession, Question, User
from app.handlers.common import callback_actor, next_keyboard, send_question, show_main_menu
from app.services.answers import (
    AlreadyAnswered,
    AnswerOutcome,
    ExpiredQuestion,
    NotQuestionOwner,
    submit_answer,
)
from app.services.sessions import next_question
from app.services.statistics import progress_for_user

router = Router(name="questions")


@router.callback_query(F.data.regexp(r"^a:[A-Za-z0-9_-]{4,16}:[0-3]$"))
async def answer(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id, option_index = parse_answer_callback(callback.data)
    try:
        async with app.sessions() as session, session.begin():
            user = await callback_actor(session, callback)
            if not user:
                return
            outcome = await submit_answer(session, app.registry, user, public_id, option_index)
    except AlreadyAnswered:
        await callback.answer(app.content.get("question.already"), show_alert=True)
        return
    except ExpiredQuestion:
        await callback.message.answer(app.content.get("question.expired"))
        return
    except NotQuestionOwner:
        await callback.message.answer(app.content.get("question.owner"))
        return
    try:
        await cast(Message, callback.message).edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _show_outcome(callback, app, outcome)


async def _show_outcome(callback: CallbackQuery, app: Application, outcome: AnswerOutcome) -> None:
    if not callback.message:
        return
    topic = app.registry.get(outcome.question.topic_id)
    if outcome.session and outcome.session.session_kind == "test":
        if outcome.completed:
            await _session_summary(callback, app, outcome)
            return
        text = f"{app.content.get('question.saved')}\n\n" + app.content.get(
            "question.position",
            position=outcome.session.answered_count,
            total=outcome.session.planned_question_count,
        )
    else:
        text = topic.content(outcome.evaluation.feedback_key)
        equation = escape(str(outcome.evaluation.feedback_payload["equation"]))
        text = f"{text}\n{equation}"
        if outcome.evaluation.hint_key and outcome.evaluation.hint_payload:
            text += "\n" + topic.content(
                outcome.evaluation.hint_key, **outcome.evaluation.hint_payload
            )
        if outcome.session:
            text += "\n\n" + app.content.get(
                "question.position",
                position=outcome.session.answered_count,
                total=outcome.session.planned_question_count,
            )
            if outcome.completed:
                await callback.message.answer(text)
                await _session_summary(callback, app, outcome)
                return
    if outcome.source == "daily":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=app.content.get("daily.more"), callback_data="daily:more"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=app.content.get("daily.five"), callback_data="pm:quick"
                    )
                ],
                [InlineKeyboardButton(text=app.content.get("daily.done"), callback_data="m:menu")],
            ]
        )
    else:
        keyboard = next_keyboard(outcome.question, app)
    await callback.message.answer(text, reply_markup=keyboard)


async def _session_summary(
    callback: CallbackQuery, app: Application, outcome: AnswerOutcome
) -> None:
    if not callback.message or not outcome.session:
        return
    practice_session = outcome.session
    blueprint = practice_session.configuration.get("blueprint", [])
    skills = len({item[0] for item in blueprint})
    if practice_session.session_kind == "test":
        percentage = round(
            practice_session.correct_count / practice_session.planned_question_count * 100
        )
        text = app.content.get(
            "test.summary",
            correct=practice_session.correct_count,
            total=practice_session.planned_question_count,
            percentage=percentage,
            skills=skills,
        )
        again_label = app.content.get("test.weak")
        async with app.sessions() as session:
            rows = (
                await session.execute(
                    select(Attempt.skill_key, Attempt.is_correct)
                    .join(Question, Question.id == Attempt.question_id)
                    .where(Question.session_id == practice_session.id)
                )
            ).all()
            test_metrics = app.registry.get(practice_session.topic_id).test_result_metrics(
                tuple(
                    {"skill_key": skill_key, "is_correct": is_correct}
                    for skill_key, is_correct in rows
                )
            )
        if test_metrics:
            text += "\n" + "\n".join(f"{metric.label}: {metric.value}" for metric in test_metrics)
    else:
        text = app.content.get(
            "session.summary",
            correct=practice_session.correct_count,
            total=practice_session.planned_question_count,
            skills=skills,
        )
        again_label = app.content.get("session.again")
    async with app.sessions() as session:
        user = await session.get(User, practice_session.user_id)
        view = await progress_for_user(session, app.registry, user) if user else None
    if view and view.strengths:
        text += "\nStrong: " + ", ".join(item.label for item in view.strengths[:3])
    if view and view.current_targets:
        text += "\nPractise next: " + ", ".join(item.label for item in view.current_targets[:3])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=again_label, callback_data="pm:quick")],
            [InlineKeyboardButton(text=app.content.get("session.menu"), callback_data="m:menu")],
        ]
    )
    await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("n:"))
async def next_answer(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id = callback.data.split(":", 1)[1]
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user:
            return
        previous = await session.scalar(select(Question).where(Question.public_id == public_id))
        if not previous or previous.user_id != user.id or not previous.session_id:
            return
        practice_session = await session.get(PracticeSession, previous.session_id)
        if not practice_session or practice_session.status != "active":
            return
        question = await next_question(session, app.registry, practice_session)
    if question:
        await send_question(callback.bot, callback.message, app, question, practice_session)
    else:
        await show_main_menu(callback.message, app)
