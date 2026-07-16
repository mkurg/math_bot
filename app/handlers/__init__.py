from aiogram import Router

from app.handlers import (
    admin,
    daily,
    learning,
    menu,
    practice,
    privacy,
    progress,
    questions,
    settings,
    start,
    tests,
)


def build_router() -> Router:
    router = Router(name="root")
    for child in (
        start.router,
        daily.router,
        practice.router,
        tests.router,
        learning.router,
        questions.router,
        progress.router,
        settings.router,
        privacy.router,
        admin.router,
        menu.router,
    ):
        router.include_router(child)
    return router
