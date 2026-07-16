from datetime import timedelta

BOX_INTERVALS = {
    0: timedelta(minutes=0),
    1: timedelta(minutes=10),
    2: timedelta(days=1),
    3: timedelta(days=3),
    4: timedelta(days=7),
    5: timedelta(days=14),
}


def interval_for_box(box: int) -> timedelta:
    if box not in BOX_INTERVALS:
        raise ValueError("mastery box must be from 0 through 5")
    return BOX_INTERVALS[box]
