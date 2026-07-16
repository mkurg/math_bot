from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.content.loader import ContentCatalog


def main_menu(content: ContentCatalog) -> ReplyKeyboardMarkup:
    rows = (
        (content.get("menu.practice"), content.get("menu.learn")),
        (content.get("menu.tests"), content.get("menu.daily")),
        (content.get("menu.progress"), content.get("menu.settings")),
    )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label) for label in row] for row in rows],
        resize_keyboard=True,
        is_persistent=True,
    )


def back_button(callback_data: str = "m:menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Back", callback_data=callback_data)]]
    )


def table_grid(prefix: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=f"×{table}", callback_data=f"{prefix}:{table}")
        for table in range(1, 11)
    ]
    rows = [buttons[index : index + 5] for index in range(0, 10, 5)]
    rows.append([InlineKeyboardButton(text="Back", callback_data="m:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
