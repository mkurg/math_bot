from __future__ import annotations

from random import Random


def numeric_options(correct: int, group_size: int, rng: Random) -> tuple[int, ...]:
    candidates = [
        correct - group_size,
        correct + group_size,
        correct - 1,
        correct + 1,
        correct - 2,
        correct + 2,
        correct - 10,
        correct + 10,
    ]
    plausible = [value for value in candidates if 1 <= value <= 100 and value != correct]
    rng.shuffle(plausible)
    chosen: list[int] = []
    for value in plausible:
        if value not in chosen:
            chosen.append(value)
        if len(chosen) == 3:
            break
    if len(chosen) < 3:
        fallback = sorted(range(1, 101), key=lambda value: (abs(value - correct), value))
        for value in fallback:
            if value != correct and value not in chosen:
                chosen.append(value)
            if len(chosen) == 3:
                break
    options = [correct, *chosen]
    rng.shuffle(options)
    return tuple(options)
