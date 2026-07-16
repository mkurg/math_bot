from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from random import Random

import pytest

from app.core.mastery.engine import apply_answer, is_mastered
from app.core.mastery.intervals import interval_for_box
from app.core.mastery.selection import weighted_skill_order
from app.core.questions.answer_modes import validate_options
from app.core.questions.callbacks import answer_callback, parse_answer_callback
from app.core.topics.contracts import AnswerOption, MasteryState
from app.core.topics.registry import TopicRegistry
from app.services.reminders import day_matches
from tests.sample_topic import SampleTopic


def test_registry_registers_and_resolves_sample_topic() -> None:
    registry = TopicRegistry()
    module = SampleTopic()
    registry.register(module)
    registry.configure(("sample_topic",), "sample_topic")
    assert registry.get("sample_topic") is module
    assert registry.enabled_topics() == (module,)
    with pytest.raises(ValueError, match="duplicate"):
        registry.register(module)
    with pytest.raises(LookupError):
        registry.get("missing")


def test_registry_rejects_configuration_errors() -> None:
    registry = TopicRegistry()
    registry.register(SampleTopic())
    with pytest.raises(ValueError, match="not registered"):
        registry.configure(("missing",), "missing")
    with pytest.raises(ValueError, match="default"):
        registry.configure(("sample_topic",), "missing")


def test_mastery_updates_and_intervals() -> None:
    now = datetime(2026, 7, 16, 12, tzinfo=UTC)
    state = MasteryState("sample", box=1, attempt_count=2, correct_count=1)
    correct = apply_answer(state, True, now)
    assert correct.box == 2
    assert correct.due_at == now + timedelta(days=1)
    assert correct.attempt_count == 3
    assert correct.correct_count == 2
    wrong = apply_answer(replace(state, box=4), False, now)
    assert wrong.box == 2
    assert wrong.consecutive_correct == 0
    assert wrong.correct_dates == ()
    assert interval_for_box(5) == timedelta(days=14)
    with pytest.raises(ValueError):
        interval_for_box(6)


def test_generic_mastered_rule() -> None:
    assert is_mastered(
        MasteryState(
            "skill",
            box=5,
            consecutive_correct=3,
            correct_dates=("2026-07-15", "2026-07-16", "2026-07-16"),
        )
    )
    assert not is_mastered(
        MasteryState("skill", box=5, consecutive_correct=3, correct_dates=("2026-07-16",) * 3)
    )


def test_weighted_selection_prioritizes_due_and_low_skills() -> None:
    now = datetime.now(UTC)
    keys = ("due", "low", "mastered", "easy")
    states = {
        "due": MasteryState("due", 3, now - timedelta(minutes=1)),
        "low": MasteryState("low", 1, now + timedelta(days=1)),
        "mastered": MasteryState("mastered", 5, now + timedelta(days=1)),
        "easy": MasteryState("easy", 4, now + timedelta(days=1)),
    }
    ordered = weighted_skill_order(keys, states, now, Random(4))
    assert ordered.count("due") == 5
    assert ordered.count("low") == 5
    assert ordered.count("mastered") == 2
    assert ordered.count("easy") == 1


def test_answer_mode_and_callback_validation() -> None:
    options = tuple(AnswerOption(str(value), {"value": value}) for value in range(4))
    validate_options("single_choice", options)
    callback = answer_callback("abc_123", 2)
    assert parse_answer_callback(callback) == ("abc_123", 2)
    with pytest.raises(ValueError):
        answer_callback("bad:id", 1)
    with pytest.raises(ValueError):
        parse_answer_callback("not-an-answer")
    with pytest.raises(ValueError):
        validate_options("unknown", options)
    with pytest.raises(ValueError):
        validate_options("single_choice", options[:3])


@pytest.mark.parametrize(
    ("mask", "day", "expected"),
    [
        ("DAILY", date(2026, 7, 18), True),
        ("WEEKDAYS", date(2026, 7, 17), True),
        ("WEEKDAYS", date(2026, 7, 18), False),
        ("MWF", date(2026, 7, 15), True),
        ("MWF", date(2026, 7, 16), False),
        ("OFF", date(2026, 7, 16), False),
    ],
)
def test_reminder_days(mask: str, day: date, expected: bool) -> None:
    assert day_matches(mask, day) is expected


def test_invalid_reminder_mask() -> None:
    with pytest.raises(ValueError):
        day_matches("SOMETIMES", date.today())
