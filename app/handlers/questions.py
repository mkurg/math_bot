from __future__ import annotations

from html import escape
from typing import cast

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.bot import Application
from app.core.questions.callbacks import (
    parse_answer_callback,
    parse_hint_callback,
    parse_pad_callback,
)
from app.database.models import Attempt, PracticeSession, Question, User
from app.handlers.common import callback_actor, next_keyboard, send_question, show_main_menu
from app.keyboards.questions import answer_keyboard
from app.services.answers import (
    AlreadyAnswered,
    AnswerOutcome,
    ExpiredQuestion,
    InvalidConstructedAnswer,
    NotQuestionOwner,
    submit_answer,
    submit_constructed_answer,
)
from app.services.sessions import next_question, start_session
from app.services.statistics import progress_for_user

router = Router(name="questions")


@router.callback_query(F.data.regexp(r"^a:[A-Za-z0-9_-]{4,16}:[0-3]$"))
async def answer(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id, option_index = parse_answer_callback(callback.data)
    topic_id: str | None = None
    try:
        async with app.sessions() as session, session.begin():
            user = await callback_actor(session, callback)
            if not user:
                return
            question = await session.scalar(select(Question).where(Question.public_id == public_id))
            topic_id = question.topic_id if question else user.selected_topic_id
            outcome = await submit_answer(session, app.registry, user, public_id, option_index)
    except AlreadyAnswered:
        await callback.answer(app.text("question.already", topic_id), show_alert=True)
        return
    except ExpiredQuestion:
        await callback.message.answer(app.text("question.expired", topic_id))
        return
    except NotQuestionOwner:
        await callback.message.answer(app.text("question.owner", topic_id))
        return
    try:
        await cast(Message, callback.message).edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _show_outcome(callback, app, outcome)


@router.callback_query(F.data.regexp(r"^p:[A-Za-z0-9_-]{4,16}:(?:-|[0-9A-F]{1,16}):[0-9A-Fxcsn]$"))
async def numeral_pad(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id, current, action = parse_pad_callback(callback.data)
    async with app.sessions() as session:
        user = await callback_actor(session, callback)
        question = await session.scalar(select(Question).where(Question.public_id == public_id))
    if not user or not question:
        await callback.message.answer(
            app.text("question.expired", user.selected_topic_id if user else None)
        )
        return
    if question.user_id != user.id:
        await callback.message.answer(app.text("question.owner", question.topic_id))
        return
    if action == "n":
        return
    max_length = int(question.prompt_payload.get("metadata", {}).get("max_length", 8))
    if action in "0123456789ABCDEF":
        if len(current) >= max_length:
            await callback.answer(
                app.text("question.max_length", question.topic_id), show_alert=True
            )
            return
        current += action
    elif action == "x":
        current = current[:-1]
    elif action == "c":
        current = ""
    elif action == "s":
        if not current:
            await callback.answer(
                app.text("question.build_first", question.topic_id), show_alert=True
            )
            return
        try:
            async with app.sessions() as session, session.begin():
                user = await callback_actor(session, callback)
                if not user:
                    return
                outcome = await submit_constructed_answer(
                    session, app.registry, user, public_id, current
                )
        except AlreadyAnswered:
            await callback.answer(app.text("question.already", question.topic_id), show_alert=True)
            return
        except ExpiredQuestion:
            await callback.message.answer(app.text("question.expired", question.topic_id))
            return
        except NotQuestionOwner:
            await callback.message.answer(app.text("question.owner", question.topic_id))
            return
        except InvalidConstructedAnswer:
            await callback.answer(
                app.text("question.invalid_numeral", question.topic_id), show_alert=True
            )
            return
        try:
            await cast(Message, callback.message).edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await _show_outcome(callback, app, outcome)
        return
    try:
        await cast(Message, callback.message).edit_reply_markup(
            reply_markup=answer_keyboard(
                question,
                current,
                content=lambda key: app.text(key, question.topic_id),
            )
        )
    except Exception:
        await callback.message.answer(app.text("question.newest_pad", question.topic_id))


@router.callback_query(F.data.regexp(r"^h:[A-Za-z0-9_-]{4,16}$"))
async def show_hint(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id = parse_hint_callback(callback.data)
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        question = await session.scalar(
            select(Question).where(Question.public_id == public_id).with_for_update()
        )
        if not user or not question or question.user_id != user.id or question.status != "pending":
            topic_id = question.topic_id if question else (user.selected_topic_id if user else None)
            await callback.answer(app.text("question.expired", topic_id), show_alert=True)
            return
        hints = list(question.prompt_payload.get("metadata", {}).get("hints", []))[:3]
        used = int(question.prompt_payload.get("hint_count", 0))
        if used >= len(hints):
            await callback.answer(
                app.text("question.hints_done", question.topic_id), show_alert=True
            )
            return
        hint = str(hints[used])
        question.prompt_payload = {**question.prompt_payload, "hint_count": used + 1}
        flag_modified(question, "prompt_payload")
    await callback.message.answer(
        app.text(
            "question.hint_number",
            question.topic_id,
            number=used + 1,
            hint=escape(hint),
        )
    )


async def _show_outcome(callback: CallbackQuery, app: Application, outcome: AnswerOutcome) -> None:
    if not callback.message:
        return
    topic = app.registry.get(outcome.question.topic_id)
    if outcome.session and outcome.session.session_kind == "test":
        if outcome.completed:
            await _session_summary(callback, app, outcome)
            return
        text = f"{app.text('question.saved', outcome.question.topic_id)}\n\n" + app.text(
            "question.position",
            outcome.question.topic_id,
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
            text += "\n\n" + app.text(
                "question.position",
                outcome.question.topic_id,
                position=outcome.session.answered_count,
                total=outcome.session.planned_question_count,
            )
            if outcome.completed:
                await callback.message.answer(text)
                await _session_summary(callback, app, outcome)
                return
    if outcome.source == "daily":
        rows = [
            [
                InlineKeyboardButton(
                    text=app.text("daily.more", outcome.question.topic_id),
                    callback_data="daily:more",
                )
            ],
            [
                InlineKeyboardButton(
                    text=app.text("daily.five", outcome.question.topic_id),
                    callback_data="pm:quick",
                )
            ],
        ]
        if topic.metadata.daily_extended_actions:
            rows.extend(
                [
                    [
                        InlineKeyboardButton(
                            text=app.text("question.practise_skill", outcome.question.topic_id),
                            callback_data=f"dps:{outcome.question.public_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=app.text("question.open_explanation", outcome.question.topic_id),
                            callback_data=f"dex:{outcome.question.public_id}",
                        )
                    ],
                ]
            )
        rows.append(
            [
                InlineKeyboardButton(
                    text=app.text("daily.done", outcome.question.topic_id),
                    callback_data="m:menu",
                )
            ]
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
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
        text = app.text(
            "test.summary",
            practice_session.topic_id,
            correct=practice_session.correct_count,
            total=practice_session.planned_question_count,
            percentage=percentage,
            skills=skills,
        )
        again_label = app.text("test.weak", practice_session.topic_id)
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
        text = app.text(
            "session.summary",
            practice_session.topic_id,
            correct=practice_session.correct_count,
            total=practice_session.planned_question_count,
            skills=skills,
        )
        again_label = app.text("session.again", practice_session.topic_id)
    async with app.sessions() as session:
        user = await session.get(User, practice_session.user_id)
        view = await progress_for_user(session, app.registry, user) if user else None
    if view and view.strengths:
        text += "\n" + app.text("progress.strong_inline", practice_session.topic_id) + ": "
        text += ", ".join(item.label for item in view.strengths[:3])
    if view and view.current_targets:
        text += "\n" + app.text("progress.next_inline", practice_session.topic_id) + ": "
        text += ", ".join(item.label for item in view.current_targets[:3])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=again_label, callback_data="pm:quick")],
            [
                InlineKeyboardButton(
                    text=app.text("session.menu", practice_session.topic_id),
                    callback_data="m:menu",
                )
            ],
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
        await show_main_menu(callback.message, app, user.selected_topic_id)


@router.callback_query(F.data.regexp(r"^dps:[A-Za-z0-9_-]{4,16}$"))
async def practise_daily_skill(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id = callback.data.split(":", 1)[1]
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        question = await session.scalar(select(Question).where(Question.public_id == public_id))
        if not user or not question or question.user_id != user.id:
            return
        practice_session = await start_session(
            session,
            app.registry,
            user,
            "quick",
            "practice",
            {"focus_skill": question.skill_key},
        )
        next_item = await next_question(session, app.registry, practice_session)
    if next_item:
        await send_question(callback.bot, callback.message, app, next_item, practice_session)


@router.callback_query(F.data.regexp(r"^dex:[A-Za-z0-9_-]{4,16}$"))
async def daily_explanation(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    public_id = callback.data.split(":", 1)[1]
    async with app.sessions() as session:
        user = await callback_actor(session, callback)
        question = await session.scalar(select(Question).where(Question.public_id == public_id))
    if user and question and question.user_id == user.id:
        explanation = escape(str(question.evaluation_payload.get("equation", "")))
        await callback.message.answer(
            f"<b>{app.text('question.explanation_title', question.topic_id)}</b>\n\n{explanation}"
        )
