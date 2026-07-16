from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.questions.callbacks import answer_callback, hint_callback, pad_callback
from app.database.models import Question

PAD_LAYOUTS = {
    "binary_pad": (("0", "1"),),
    "octal_pad": (("0", "1", "2", "3"), ("4", "5", "6", "7")),
    "decimal_pad": (("1", "2", "3"), ("4", "5", "6"), ("7", "8", "9"), ("0",)),
    "hexadecimal_pad": (
        ("0", "1", "2", "3"),
        ("4", "5", "6", "7"),
        ("8", "9", "A", "B"),
        ("C", "D", "E", "F"),
    ),
}


def answer_keyboard(question: Question, current: str = "") -> InlineKeyboardMarkup:
    if question.answer_mode in PAD_LAYOUTS:
        rows = [
            [
                InlineKeyboardButton(
                    text=f"Answer: {current or '…'}",
                    callback_data=pad_callback(question.public_id, current, "n"),
                )
            ]
        ]
        rows.extend(
            [
                InlineKeyboardButton(
                    text=digit,
                    callback_data=pad_callback(question.public_id, current, digit),
                )
                for digit in digit_row
            ]
            for digit_row in PAD_LAYOUTS[question.answer_mode]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text="⌫", callback_data=pad_callback(question.public_id, current, "x")
                ),
                InlineKeyboardButton(
                    text="Clear", callback_data=pad_callback(question.public_id, current, "c")
                ),
                InlineKeyboardButton(
                    text="Submit", callback_data=pad_callback(question.public_id, current, "s")
                ),
            ]
        )
        _append_hint(rows, question)
        return InlineKeyboardMarkup(inline_keyboard=rows)
    buttons = [
        InlineKeyboardButton(
            text=str(option["label"]), callback_data=answer_callback(question.public_id, index)
        )
        for index, option in enumerate(question.options)
    ]
    width = 2
    rows = [buttons[index : index + width] for index in range(0, len(buttons), width)]
    _append_hint(rows, question)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _append_hint(rows: list[list[InlineKeyboardButton]], question: Question) -> None:
    hints = question.prompt_payload.get("metadata", {}).get("hints", [])
    if hints:
        rows.append(
            [InlineKeyboardButton(text="💡 Hint", callback_data=hint_callback(question.public_id))]
        )
