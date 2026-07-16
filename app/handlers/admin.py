from __future__ import annotations

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
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.bot import Application
from app.database.models import ClassSettings, PracticeSession, StudentSettings, User
from app.handlers.common import actor, callback_actor
from app.handlers.progress import render_progress
from app.handlers.settings import FREQUENCIES
from app.services.statistics import (
    difficult_skills,
    group_metrics,
    progress_for_user,
    user_metrics,
)

router = Router(name="admin")


def admin_keyboard(app: Application) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=app.content.get("admin.students"), callback_data="ad:students:0"
                )
            ],
            [InlineKeyboardButton(text=app.content.get("admin.group"), callback_data="ad:group")],
            [
                InlineKeyboardButton(
                    text=app.content.get("admin.defaults"), callback_data="ad:defaults"
                )
            ],
            [InlineKeyboardButton(text=app.content.get("admin.invite"), callback_data="ad:invite")],
            [InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="m:menu")],
        ]
    )


def is_admin(user: User | None, app: Application) -> bool:
    return bool(
        user and user.role == "admin" and user.telegram_user_id == app.settings.admin_telegram_id
    )


@router.message(Command("admin"))
async def admin_menu(message: Message, app: Application) -> None:
    async with app.sessions() as session, session.begin():
        user = await actor(session, message)
    if not is_admin(user, app):
        await message.answer(app.content.get("admin.denied"))
        return
    await message.answer(app.content.get("admin.title"), reply_markup=admin_keyboard(app))


@router.callback_query(F.data == "ad:menu")
async def admin_menu_callback(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            app.content.get("admin.title"), reply_markup=admin_keyboard(app)
        )


async def authorized(callback: CallbackQuery, app: Application) -> User | None:
    async with app.sessions() as session, session.begin():
        user = await callback_actor(session, callback)
    if not is_admin(user, app):
        if callback.message:
            await callback.message.answer(app.content.get("admin.denied"))
        return None
    return user


@router.callback_query(F.data.startswith("ad:students:"))
async def student_list(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    page = max(0, int(callback.data.rsplit(":", 1)[1]))
    async with app.sessions() as session:
        students = (
            await session.scalars(
                select(User)
                .options(selectinload(User.settings))
                .where(User.role == "student", User.is_active.is_(True))
                .order_by(User.display_name, User.id)
                .offset(page * 8)
                .limit(9)
            )
        ).all()
        lines: list[str] = []
        for student in students[:8]:
            metrics = await user_metrics(session, student.id, student.selected_topic_id)
            reminder = "on" if student.settings and student.settings.reminders_enabled else "off"
            lines.append(
                app.content.get(
                    "admin.student_line",
                    name=student.display_name,
                    last_active=student.last_seen_at.date().isoformat(),
                    questions=metrics["total"],
                    accuracy=metrics["accuracy"],
                    reminder=reminder,
                )
            )
    if not students:
        await callback.message.answer(app.content.get("admin.student_empty"))
        return
    rows = [
        [InlineKeyboardButton(text=student.display_name, callback_data=f"adstu:{student.id}")]
        for student in students[:8]
    ]
    navigation: list[InlineKeyboardButton] = []
    if page:
        navigation.append(
            InlineKeyboardButton(text="Previous", callback_data=f"ad:students:{page - 1}")
        )
    if len(students) > 8:
        navigation.append(
            InlineKeyboardButton(text="Next", callback_data=f"ad:students:{page + 1}")
        )
    if navigation:
        rows.append(navigation)
    rows.append([InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="ad:menu")])
    await callback.message.answer(
        "\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("adstu:"))
async def student_detail(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    student_id = int(callback.data.split(":")[1])
    async with app.sessions() as session:
        student = await session.scalar(
            select(User).options(selectinload(User.settings)).where(User.id == student_id)
        )
        if not student or student.role != "student":
            return
        view = await progress_for_user(session, app.registry, student)
        recent_tests = (
            await session.scalars(
                select(PracticeSession)
                .where(
                    PracticeSession.user_id == student.id,
                    PracticeSession.session_kind == "test",
                    PracticeSession.status == "completed",
                )
                .order_by(PracticeSession.completed_at.desc())
                .limit(3)
            )
        ).all()
        reminder = (
            f"{student.settings.days_mask} at {student.settings.local_hour}:00"
            if student.settings and student.settings.reminders_enabled
            else "Off"
        )
    text = render_progress(view, app.content.get("admin.student.title", name=student.display_name))
    text += f"\n\nReminder: {reminder}"
    if recent_tests:
        test_lines = "\n".join(
            f"{item.mode_id}: {item.correct_count}/{item.planned_question_count}"
            for item in recent_tests
        )
        text += f"\n\n<b>{app.content.get('admin.student.recent_tests')}</b>\n{test_lines}"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=app.content.get("admin.student.reminder"),
                    callback_data=f"adsf:{student.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=app.content.get("menu.back"), callback_data="ad:students:0"
                )
            ],
        ]
    )
    await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("adsf:"))
async def student_reminder_menu(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    student_id = int(callback.data.split(":")[1])
    rows = [
        [
            InlineKeyboardButton(
                text=app.content.get(label), callback_data=f"adsfv:{student_id}:{value}"
            )
        ]
        for value, label in FREQUENCIES
    ]
    await callback.message.answer(
        app.content.get("settings.title"), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("adsfv:"))
async def set_student_frequency(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    _, student_text, value = callback.data.split(":")
    student_id = int(student_text)
    async with app.sessions() as session, session.begin():
        student = await session.scalar(
            select(User).options(selectinload(User.settings)).where(User.id == student_id)
        )
        if not student or not student.settings:
            return
        student.settings.days_mask = value
        student.settings.reminders_enabled = value != "OFF"
    if value == "OFF":
        await callback.message.answer(app.content.get("settings.saved"))
        return
    buttons = [
        InlineKeyboardButton(text=f"{hour}:00", callback_data=f"adsh:{student_id}:{hour}")
        for hour in range(7, 21)
    ]
    await callback.message.answer(
        app.content.get("settings.hour"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[buttons[index : index + 4] for index in range(0, len(buttons), 4)]
        ),
    )


@router.callback_query(F.data.startswith("adsh:"))
async def set_student_hour(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    _, student_text, hour_text = callback.data.split(":")
    async with app.sessions() as session, session.begin():
        settings = await session.get(StudentSettings, int(student_text))
        if settings:
            settings.local_hour = int(hour_text)
    await callback.message.answer(app.content.get("settings.saved"))


@router.callback_query(F.data == "ad:group")
async def group_progress(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not await authorized(callback, app):
        return
    async with app.sessions() as session:
        metrics = await group_metrics(session)
        difficult = await difficult_skills(session)
    difficult_text = "\n".join(f"{key}: {count} mistakes" for key, count in difficult) or "None yet"
    await callback.message.answer(
        app.content.get("admin.group.body", **metrics, difficult=difficult_text)
    )


async def show_defaults(message: Message | InaccessibleMessage, app: Application) -> None:
    message = cast(Message, message)
    async with app.sessions() as session:
        defaults = await session.get(ClassSettings, 1)
    if not defaults:
        return
    text = app.content.get(
        "admin.defaults.body",
        frequency=defaults.default_days_mask,
        hour=defaults.default_local_hour,
        timezone=defaults.timezone,
    )
    rows = [
        [InlineKeyboardButton(text=app.content.get(label), callback_data=f"adf:{value}")]
        for value, label in FREQUENCIES
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=app.content.get("admin.defaults.apply"), callback_data="adapply:ask"
            )
        ]
    )
    rows.append([InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="ad:menu")])
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data == "ad:defaults")
async def defaults_menu(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if callback.message and await authorized(callback, app):
        await show_defaults(callback.message, app)


@router.callback_query(F.data.startswith("adf:"))
async def set_default_frequency(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    value = callback.data.split(":")[1]
    async with app.sessions() as session, session.begin():
        defaults = await session.get(ClassSettings, 1)
        if defaults:
            defaults.default_days_mask = value
            defaults.default_reminders_enabled = value != "OFF"
    if value == "OFF":
        await show_defaults(callback.message, app)
        return
    buttons = [
        InlineKeyboardButton(text=f"{hour}:00", callback_data=f"adh:{hour}")
        for hour in range(7, 21)
    ]
    await callback.message.answer(
        app.content.get("settings.hour"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[buttons[index : index + 4] for index in range(0, 14, 4)]
        ),
    )


@router.callback_query(F.data.startswith("adh:"))
async def set_default_hour(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not callback.data or not await authorized(callback, app):
        return
    async with app.sessions() as session, session.begin():
        defaults = await session.get(ClassSettings, 1)
        if defaults:
            defaults.default_local_hour = int(callback.data.split(":")[1])
    await show_defaults(callback.message, app)


@router.callback_query(F.data == "adapply:ask")
async def apply_defaults_ask(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not await authorized(callback, app):
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Apply", callback_data="adapply:yes")],
            [InlineKeyboardButton(text="Cancel", callback_data="ad:defaults")],
        ]
    )
    await callback.message.answer(app.content.get("admin.defaults.confirm"), reply_markup=keyboard)


@router.callback_query(F.data == "adapply:yes")
async def apply_defaults(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    admin = await authorized(callback, app)
    if not callback.message or not admin:
        return
    async with app.sessions() as session, session.begin():
        defaults = await session.get(ClassSettings, 1)
        if not defaults:
            return
        await session.execute(
            update(StudentSettings).values(
                reminders_enabled=defaults.default_reminders_enabled,
                days_mask=defaults.default_days_mask,
                local_hour=defaults.default_local_hour,
                timezone=defaults.timezone,
                updated_by_user_id=admin.id,
            )
        )
    await callback.message.answer(app.content.get("admin.defaults.applied"))


@router.callback_query(F.data == "ad:invite")
async def invite_menu(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not await authorized(callback, app):
        return
    async with app.sessions() as session:
        link = await app.invitations.current_link(session)
    text = (
        app.content.get("admin.invite.created", link=link)
        if link
        else app.content.get("admin.invite")
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=app.content.get("admin.invite.new"), callback_data="adi:ask"
                )
            ],
            [InlineKeyboardButton(text=app.content.get("menu.back"), callback_data="ad:menu")],
        ]
    )
    await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "adi:ask")
async def invite_ask(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message or not await authorized(callback, app):
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Generate", callback_data="adi:yes")],
            [InlineKeyboardButton(text="Cancel", callback_data="ad:invite")],
        ]
    )
    await callback.message.answer(app.content.get("admin.invite.warning"), reply_markup=keyboard)


@router.callback_query(F.data == "adi:yes")
async def invite_rotate(callback: CallbackQuery, app: Application) -> None:
    await callback.answer()
    if not callback.message:
        return
    async with app.sessions() as session, session.begin():
        admin = await callback_actor(session, callback)
        if not is_admin(admin, app):
            return
        assert admin is not None
        link = await app.invitations.rotate(session, admin.id)
    await callback.message.answer(app.content.get("admin.invite.created", link=link))
