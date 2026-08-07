from __future__ import annotations

import logging
from datetime import UTC, datetime
from html import escape
from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BufferedInputFile

from app.database.models import PracticeSession, Question, StudentSettings, User

if TYPE_CHECKING:
    from app.bot import Application
    from app.services.answers import AnswerOutcome

logger = logging.getLogger(__name__)

MAX_CONTEXT_LENGTH = 12_000
MAX_TELEGRAM_CHUNK = 3_700


def _chunks(value: str, size: int = MAX_TELEGRAM_CHUNK) -> tuple[str, ...]:
    if len(value) <= size:
        return (value,)
    chunks: list[str] = []
    remaining = value
    while remaining:
        split_at = min(size, len(remaining))
        if split_at < len(remaining):
            newline = remaining.rfind("\n", 0, split_at)
            if newline > size // 2:
                split_at = newline
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip("\n")
    return tuple(chunks)


async def _safe_send(bot: Bot, chat_id: int, text: str) -> None:
    try:
        for chunk in _chunks(text):
            await bot.send_message(chat_id=chat_id, text=chunk)
    except TelegramAPIError as exc:
        logger.warning("live lesson delivery failed: %s", type(exc).__name__)


async def record_live_event(
    bot: Bot | None,
    app: Application,
    student_id: int,
    event_type: str,
    title: str,
    body: str,
) -> None:
    """Persist the student's latest activity and mirror it when live mode is active."""
    now = datetime.now(UTC)
    body = body[:MAX_CONTEXT_LENGTH]
    async with app.sessions() as session, session.begin():
        student = await session.get(User, student_id)
        settings = await session.get(StudentSettings, student_id, with_for_update=True)
        if not student or student.role != "student" or not settings:
            return
        settings.live_context = {
            "event_type": event_type,
            "title": title,
            "body": body,
            "updated_at": now.isoformat(),
        }
        enabled = settings.live_lesson_enabled
        student_name = student.display_name
    if not enabled or bot is None:
        return
    header = f"🎥 Урок в реальном времени · {escape(student_name)}\n<b>{escape(title)}</b>"
    await _safe_send(bot, app.settings.admin_telegram_id, f"{header}\n\n{escape(body)}")


async def mirror_photo(
    bot: Bot | None,
    app: Application,
    student_id: int,
    data: bytes,
    title: str,
    *,
    filename: str = "material.png",
) -> None:
    """Send the teacher the same visual material currently shown to the student."""
    if bot is None:
        return
    async with app.sessions() as session:
        student = await session.get(User, student_id)
        settings = await session.get(StudentSettings, student_id)
        if not student or not settings or not settings.live_lesson_enabled:
            return
        student_name = student.display_name
    try:
        await bot.send_photo(
            chat_id=app.settings.admin_telegram_id,
            photo=BufferedInputFile(data, filename=filename),
            caption=f"🎥 {escape(title)} · {escape(student_name)}",
        )
    except TelegramAPIError as exc:
        logger.warning("live lesson photo delivery failed: %s", type(exc).__name__)


def _definition_title(app: Application, session: PracticeSession) -> str:
    topic = app.registry.get(session.topic_id)
    if session.session_kind == "test":
        test_definition = next(
            (item for item in topic.test_definitions() if item.test_id == session.mode_id),
            None,
        )
        prefix = "Проверочная"
        label = topic.content(test_definition.title_key) if test_definition else session.mode_id
    else:
        practice_definition = next(
            (item for item in topic.practice_modes() if item.mode_id == session.mode_id),
            None,
        )
        prefix = "Тренировка"
        label = (
            topic.content(practice_definition.title_key) if practice_definition else session.mode_id
        )
    return f"{prefix}: {label}"


async def mirror_question(
    bot: Bot | None,
    app: Application,
    question: Question,
    practice_session: PracticeSession | None,
    *,
    daily: bool,
) -> None:
    prompt = str(question.prompt_payload.get("rendered_prompt", ""))
    options = "\n".join(
        f"{chr(ord('A') + index)}: {option.get('label', '')}"
        for index, option in enumerate(question.options)
    )
    if daily:
        title = "Задание дня"
        position = ""
    elif practice_session:
        title = _definition_title(app, practice_session)
        position = f"\n\nВопрос {question.position} из {practice_session.planned_question_count}"
    else:
        title = "Вопрос"
        position = ""
    body = prompt
    if options:
        body += f"\n\n{options}"
    body += position
    await record_live_event(bot, app, question.user_id, "question", title, body)


def _answer_label(question: Question, answer: dict[str, object]) -> str:
    for option in question.options:
        if option.get("value") == answer:
            return str(option.get("label", answer.get("value", "")))
    return str(answer.get("value", ""))


async def mirror_answer(bot: Bot | None, app: Application, outcome: AnswerOutcome) -> None:
    question = outcome.question
    selected = _answer_label(question, outcome.selected_answer)
    correct = _answer_label(question, question.correct_answer)
    verdict = "✅ Верно" if outcome.evaluation.is_correct else "🌱 Ошибка"
    body = (
        f"{question.prompt_payload.get('rendered_prompt', '')}\n\n"
        f"Ответ ученика: {selected}\n"
        f"Результат: {verdict}\n"
        f"Правильный ответ: {correct}\n\n"
        f"{outcome.evaluation.feedback_payload.get('equation', '')}"
    )
    if outcome.session:
        body += (
            f"\n\nОтвечено {outcome.session.answered_count} из "
            f"{outcome.session.planned_question_count}"
        )
    await record_live_event(bot, app, question.user_id, "answer", "Ответ ученика", body)


async def notify_student_live_status(
    bot: Bot | None, student_chat_id: int, *, enabled: bool
) -> None:
    if bot is None:
        return
    text = (
        "👩‍🏫 Учитель подключился к индивидуальному уроку. "
        "Он видит открытые материалы, вопросы и твои ответы."
        if enabled
        else "Индивидуальный урок завершён. Трансляция действий учителю выключена."
    )
    await _safe_send(bot, student_chat_id, text)
