from __future__ import annotations

from datetime import datetime
from random import Random

from app.core.topics.contracts import MasteryState


def weighted_skill_order(
    eligible: tuple[str, ...],
    mastery: dict[str, MasteryState],
    now: datetime,
    rng: Random,
) -> list[str]:
    due: list[str] = []
    low: list[str] = []
    mastered: list[str] = []
    easy: list[str] = []
    for key in eligible:
        state = mastery.get(key, MasteryState(key))
        if state.due_at is not None and state.due_at <= now or state.box <= 1:
            due.append(key)
        elif state.box == 5:
            mastered.append(key)
        elif state.box <= 3:
            low.append(key)
        else:
            easy.append(key)
    for bucket in (due, low, mastered, easy):
        rng.shuffle(bucket)
    weighted = due * 5 + low * 3 + mastered * 2 + easy
    rng.shuffle(weighted)
    return weighted or list(eligible)
