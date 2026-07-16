from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import Application
from app.core.topics.contracts import TopicProgressView
from app.handlers.common import actor
from app.services.statistics import progress_for_user

router = Router(name="progress")


def render_progress(
    view: TopicProgressView,
    title: str,
    *,
    strong_title: str = "Strong areas",
    learning_title: str = "Learning now",
    recent_title: str = "Recent challenges/tests",
) -> str:
    lines = [f"<b>{title}</b>", ""]
    lines.extend(f"{metric.label}: {metric.value}" for metric in view.headline_metrics)
    for group in view.progress_groups:
        lines.extend(("", f"<b>{group.label}</b>"))
        if group.items:
            for item in group.items:
                try:
                    percent = int(item.value.removesuffix("%"))
                except ValueError:
                    lines.append(f"{item.label}: {item.value}")
                    continue
                filled = min(10, max(0, round(percent / 10)))
                lines.append(f"{item.label}: {'█' * filled}{'░' * (10 - filled)} {percent}%")
        else:
            filled = min(10, max(0, round(group.percentage / 10)))
            lines.append(f"{'█' * filled}{'░' * (10 - filled)} {group.percentage}%")
    lines.extend(("", f"<b>{strong_title}</b>"))
    lines.extend(item.label for item in view.strengths or ())
    lines.extend(("", f"<b>{learning_title}</b>"))
    lines.extend(item.label for item in view.current_targets or ())
    if view.recent_results:
        lines.extend(("", f"<b>{recent_title}</b>"))
        lines.extend(f"{item.label}: {item.value}" for item in view.recent_results)
    return "\n".join(lines)


@router.message(Command("progress"))
@router.message(F.text.in_({"📊 My progress", "📊 Мой прогресс"}))
async def progress(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
        if not user:
            return
        view = await progress_for_user(session, app.registry, user)
    reply_markup = None
    if view.suggested_action:
        action, separator, mode_id = view.suggested_action.action_id.partition(":")
        if action == "practice" and separator and mode_id:
            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=view.suggested_action.label,
                            callback_data=f"pm:{mode_id}",
                        )
                    ]
                ]
            )
    await message.answer(
        render_progress(
            view,
            app.text("progress.title", user.selected_topic_id),
            strong_title=app.text("progress.strong", user.selected_topic_id),
            learning_title=app.text("progress.learning", user.selected_topic_id),
            recent_title=app.text("progress.recent", user.selected_topic_id),
        ),
        reply_markup=reply_markup,
    )
