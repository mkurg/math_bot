from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import Application
from app.handlers.common import show_main_menu
from app.services.users import create_student, get_user, touch_user

router = Router(name="start")


@router.message(CommandStart())
async def start(message: Message, command: CommandObject, app: Application) -> None:
    if message.chat.type != "private":
        await message.answer(app.content.get("private_only"))
        return
    if message.from_user is None:
        return
    async with app.sessions() as session, session.begin():
        user = await get_user(session, message.from_user.id)
        if user and user.is_active:
            touch_user(
                user,
                message.chat.id,
                message.from_user.first_name,
                message.from_user.username,
            )
            await show_main_menu(message, app, "returning")
            return
        argument = command.args or ""
        valid = argument.startswith("join_") and await app.invitations.validate(
            session, argument.removeprefix("join_")
        )
        if not valid:
            await message.answer(app.content.get("invite_required"))
            return
        user = await create_student(
            session,
            telegram_user_id=message.from_user.id,
            telegram_chat_id=message.chat.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=app.content.get("onboarding.quick"), callback_data="pm:quick"
                )
            ],
            [
                InlineKeyboardButton(
                    text=app.content.get("onboarding.reminders"), callback_data="m:settings"
                )
            ],
            [InlineKeyboardButton(text=app.content.get("onboarding.menu"), callback_data="m:menu")],
        ]
    )
    await message.answer(app.content.get("welcome", name=user.display_name), reply_markup=keyboard)


@router.message(F.chat.type != "private")
async def group_message(message: Message, app: Application) -> None:
    await message.answer(app.content.get("private_only"))
