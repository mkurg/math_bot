from __future__ import annotations

import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from sqlalchemy import text

from app.bot import Application
from app.config import get_settings
from app.content.loader import ContentCatalog
from app.core.topics.registry import TopicRegistry
from app.database.session import create_engine_and_sessionmaker
from app.handlers import build_router
from app.logging import configure_logging
from app.services.invitations import InvitationService
from app.services.users import ensure_initial_records
from app.topics.numeral_systems import NumeralSystemsModule
from app.topics.times_tables import TimesTablesModule
from app.workers.daily_questions import run_daily_worker


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    registry = TopicRegistry()
    registry.register(TimesTablesModule())
    registry.register(NumeralSystemsModule())
    registry.configure(settings.enabled_topics, settings.default_topic_id)
    content = ContentCatalog(Path(__file__).parent / "content" / "core" / "strings.yaml")
    engine, sessions = create_engine_and_sessionmaker(settings.database_url)
    async with sessions() as session, session.begin():
        await session.execute(text("SELECT 1"))
        await ensure_initial_records(session, settings)
    app = Application(
        settings=settings,
        sessions=sessions,
        registry=registry,
        content=content,
        invitations=InvitationService(settings.bot_token, settings.bot_username),
    )
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start or open the menu"),
            BotCommand(command="menu", description="Open the main menu"),
            BotCommand(command="practice", description="Start practice"),
            BotCommand(command="learn", description="Learn tables"),
            BotCommand(command="test", description="Take a test"),
            BotCommand(command="progress", description="View progress"),
            BotCommand(command="settings", description="Reminder settings"),
            BotCommand(command="help", description="Help"),
            BotCommand(command="privacy", description="Privacy information"),
            BotCommand(command="delete_me", description="Delete student data"),
        ]
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router())
    stop = asyncio.Event()
    worker = asyncio.create_task(run_daily_worker(bot, app, stop))
    try:
        await dispatcher.start_polling(
            bot, app=app, allowed_updates=dispatcher.resolve_used_update_types()
        )
    finally:
        stop.set()
        await worker
        await bot.session.close()
        await engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
