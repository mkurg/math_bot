from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot import Application
from app.handlers.common import actor, show_main_menu

router = Router(name="menu")


@router.message(Command("menu"))
async def menu_command(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_main_menu(message, app)
    else:
        await message.answer(app.content.get("invite_required"))


@router.callback_query(F.data == "m:menu")
async def menu_callback(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if callback.message:
        await show_main_menu(callback.message, app)


@router.message(Command("help"))
async def help_command(message: Message, app: Application) -> None:
    await message.answer(app.content.get("help"))


@router.message(F.text)
async def unexpected_text(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if not user:
        await message.answer(app.content.get("invite_required"))
        return
    await message.answer(app.content.get("use_buttons"))
    await show_main_menu(message, app)
