from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.core.topics.contracts import TopicModule


def main_menu(topic: TopicModule) -> ReplyKeyboardMarkup:
    rows = (
        (topic.content("menu.practice"), topic.content("menu.learn")),
        (topic.content("menu.tests"), topic.content("menu.daily")),
        (topic.content("menu.progress"), topic.content("menu.settings")),
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
