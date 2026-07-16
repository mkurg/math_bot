from typing import cast

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot import Application
from app.handlers.common import actor, callback_actor

router = Router(name="settings")

FREQUENCIES = (
    ("DAILY", "settings.daily"),
    ("WEEKDAYS", "settings.weekdays"),
    ("MWF", "settings.mwf"),
    ("OFF", "settings.off"),
)


def frequency_keyboard(app: Application, prefix: str = "sf") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=app.content.get(label), callback_data=f"{prefix}:{value}")]
        for value, label in FREQUENCIES
    ]
    rows.append([InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="m:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hour_keyboard(prefix: str = "sh") -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=f"{hour:02d}:00", callback_data=f"{prefix}:{hour}")
        for hour in range(7, 21)
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[index : index + 4] for index in range(0, len(buttons), 4)]
    )


async def show_settings(message: Message | InaccessibleMessage, app: Application) -> None:
    message = cast(Message, message)
    await message.answer(app.content.get("settings.title"), reply_markup=frequency_keyboard(app))


@router.message(Command("settings"))
@router.message(F.text == "⚙️ Settings")
async def settings_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        await show_settings(message, app)


@router.callback_query(F.data == "m:settings")
async def settings_callback(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if callback.message:
        await show_settings(callback.message, app)


@router.callback_query(F.data.startswith("sf:"))
async def set_frequency(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    value = callback.data.split(":", 1)[1]
    if value not in {item[0] for item in FREQUENCIES}:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user or not user.settings:
            return
        user.settings.days_mask = value
        user.settings.reminders_enabled = value != "OFF"
        user.settings.updated_by_user_id = user.id
    if value == "OFF":
        await callback.message.answer(app.content.get("settings.saved"))
    else:
        await callback.message.answer(
            app.content.get("settings.hour"), reply_markup=hour_keyboard()
        )


@router.callback_query(F.data.startswith("sh:"))
async def set_hour(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    hour = int(callback.data.split(":", 1)[1])
    if not 7 <= hour <= 20:
        return
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
        if not user or not user.settings:
            return
        user.settings.local_hour = hour
        user.settings.updated_by_user_id = user.id
    await callback.message.answer(app.content.get("settings.saved"))
