from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.mastery.intervals import interval_for_box
from app.core.topics.contracts import MasteryState


@dataclass(frozen=True, slots=True)
class MasteryUpdate:
    box: int
    due_at: datetime
    attempt_count: int
    correct_count: int
    consecutive_correct: int
    correct_dates: tuple[str, ...]


def apply_answer(state: MasteryState, is_correct: bool, answered_at: datetime) -> MasteryUpdate:
    box = min(5, state.box + 1) if is_correct else max(0, state.box - 2)
    correct_dates = list(state.correct_dates)
    if is_correct:
        day = answered_at.date().isoformat()
        correct_dates.append(day)
        correct_dates = correct_dates[-3:]
    else:
        correct_dates = []
    return MasteryUpdate(
        box=box,
        due_at=answered_at + interval_for_box(box),
        attempt_count=state.attempt_count + 1,
        correct_count=state.correct_count + int(is_correct),
        consecutive_correct=state.consecutive_correct + 1 if is_correct else 0,
        correct_dates=tuple(correct_dates),
    )


def is_mastered(state: MasteryState) -> bool:
    return (
        state.box == 5
        and state.consecutive_correct >= 3
        and len(set(state.correct_dates[-3:])) >= 2
    )
