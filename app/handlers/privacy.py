from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import Application
from app.handlers.common import actor, callback_actor, show_main_menu
from app.services.privacy import delete_student_data

router = Router(name="privacy")


@router.message(Command("privacy"))
async def privacy(message: Message, app: Application) -> None:
    await message.answer(app.content.get("privacy"))


@router.message(Command("delete_me"))
async def delete_me(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if not user or user.role != "student":
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=app.content.get("delete.confirm"), callback_data="del:yes")],
            [InlineKeyboardButton(text=app.content.get("delete.cancel"), callback_data="del:no")],
        ]
    )
    await message.answer(app.content.get("delete.warning"), reply_markup=keyboard)


@router.callback_query(F.data.startswith("del:"))
async def delete_confirmation(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data:
        return
    if callback.data == "del:no":
        await show_main_menu(callback.message, app)
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user or user.role != "student":
            return
        await delete_student_data(session, user)
    await callback.message.answer(app.content.get("delete.done"))
