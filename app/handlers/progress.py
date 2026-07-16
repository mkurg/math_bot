from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot import Application
from app.core.topics.contracts import TopicProgressView
from app.handlers.common import actor
from app.services.statistics import progress_for_user

router = Router(name="progress")


def render_progress(view: TopicProgressView, title: str) -> str:
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
    lines.extend(("", "<b>Strong areas</b>"))
    lines.extend(item.label for item in view.strengths or ())
    lines.extend(("", "<b>Learning now</b>"))
    lines.extend(item.label for item in view.current_targets or ())
    return "\n".join(lines)


@router.message(Command("progress"))
@router.message(F.text == "📊 My progress")
async def progress(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
        if not user:
            return
        view = await progress_for_user(session, app.registry, user)
    await message.answer(render_progress(view, app.content.get("progress.title")))
