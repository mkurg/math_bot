from datetime import date


def day_matches(days_mask: str, day: date) -> bool:
    if days_mask == "OFF":
        return False
    if days_mask == "DAILY":
        return True
    if days_mask == "WEEKDAYS":
        return day.weekday() < 5
    if days_mask == "MWF":
        return day.weekday() in {0, 2, 4}
    raise ValueError(f"invalid reminder schedule: {days_mask}")
