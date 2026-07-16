from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.bot import Application
from app.handlers.common import actor, callback_actor, show_main_menu

router = Router(name="menu")


@router.message(Command("menu"))
async def menu_command(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if user:
        if user.role == "admin":
            from app.handlers.admin import admin_keyboard

            await message.answer("Teacher profile", reply_markup=ReplyKeyboardRemove())
            await message.answer(app.content.get("admin.title"), reply_markup=admin_keyboard(app))
            return
        await show_main_menu(message, app, user.selected_topic_id)
    else:
        await message.answer(app.content.get("invite_required"))


@router.callback_query(F.data == "m:menu")
async def menu_callback(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if callback.message:
        async with app.sessions() as session, session.begin():
            user = await callback_actor(session, callback)
        if user:
            if user.role == "admin":
                from app.handlers.admin import admin_keyboard

                await callback.message.answer(
                    app.content.get("admin.title"), reply_markup=admin_keyboard(app)
                )
                return
            await show_main_menu(callback.message, app, user.selected_topic_id)


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
    if user.role == "admin":
        from app.handlers.admin import admin_keyboard

        await message.answer("Teacher profile", reply_markup=ReplyKeyboardRemove())
        await message.answer(app.content.get("admin.title"), reply_markup=admin_keyboard(app))
        return
    await message.answer(app.content.get("use_buttons"))
    await show_main_menu(message, app, user.selected_topic_id)
