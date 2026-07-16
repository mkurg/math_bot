from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.questions.callbacks import answer_callback
from app.database.models import Question


def answer_keyboard(question: Question) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=str(option["label"]), callback_data=answer_callback(question.public_id, index)
        )
        for index, option in enumerate(question.options)
    ]
    width = 2
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[index : index + width] for index in range(0, len(buttons), width)]
    )
