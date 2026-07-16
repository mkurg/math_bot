from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from random import Random

import pytest

from app.core.topics.contracts import MasteryState
from app.topics.times_tables import TimesTablesModule
from app.topics.times_tables.distractors import numeric_options
from app.topics.times_tables.skills import fact_key, parse_skill_key, skill_catalogue


def test_skill_catalogue_is_canonical_and_complete() -> None:
    catalogue = skill_catalogue()
    assert len(catalogue) == 110
    assert len({item.skill_key for item in catalogue}) == 110
    assert fact_key("mul", 7, 4) == "mul:4:7"
    assert fact_key("div", 4, 7) == "div:4:7"
    assert parse_skill_key("mul:4:7") == ("mul", 4, 7)
    with pytest.raises(ValueError):
        fact_key("mul", 0, 7)
    with pytest.raises(ValueError):
        parse_skill_key("mul:7:4")


@pytest.mark.parametrize("correct", range(1, 101))
def test_distractors_are_unique_and_bounded(correct: int) -> None:
    options = numeric_options(correct, max(1, correct // 10), Random(correct))
    assert len(options) == 4
    assert len(set(options)) == 4
    assert correct in options
    assert all(1 <= option <= 100 for option in options)


@pytest.mark.parametrize("first", range(1, 11))
@pytest.mark.parametrize("second", range(1, 11))
def test_all_direct_multiplication_and_division_facts(first: int, second: int) -> None:
    module = TimesTablesModule()
    multiplication = module.generate_question(
        fact_key("mul", first, second), "direct_multiplication", Random(first * 10 + second)
    )
    assert multiplication.correct_answer["value"] == first * second
    division = module.generate_question(
        fact_key("div", first, second), "direct_division", Random(first * 100 + second)
    )
    assert division.metadata["product"] % division.metadata["divisor"] == 0
    assert division.correct_answer["value"] == (
        division.metadata["product"] // division.metadata["divisor"]
    )


@pytest.mark.parametrize(
    ("skill", "question_type"),
    [
        ("mul:6:7", "direct_multiplication"),
        ("div:6:7", "direct_division"),
        ("mul:6:7", "missing_factor"),
        ("div:6:7", "missing_divisor"),
        ("mul:6:7", "true_false"),
        ("mul:6:7", "visual"),
        ("mul:6:7", "story"),
        ("div:6:7", "story"),
    ],
)
def test_all_required_question_types(skill: str, question_type: str) -> None:
    module = TimesTablesModule()
    question = module.generate_question(skill, question_type, Random(42))
    assert question.question_type == question_type
    assert sum(option.value == question.correct_answer for option in question.answer_options) == 1
    assert len(question.answer_options) in {2, 4}
    json.dumps(asdict(question))
    correct = module.evaluate_answer(asdict(question), question.correct_answer)
    assert correct.is_correct
    wrong_option = next(
        option.value
        for option in question.answer_options
        if option.value != question.correct_answer
    )
    assert not module.evaluate_answer(asdict(question), wrong_option).is_correct


def test_generation_is_deterministic_with_fixed_seed() -> None:
    module = TimesTablesModule()
    first = module.generate_question("mul:7:8", "story", Random(123))
    second = module.generate_question("mul:7:8", "story", Random(123))
    assert first == second


def test_test_blueprints_have_required_composition() -> None:
    module = TimesTablesModule()
    table = module.test_blueprint("table", {"table": 7}, Random(1))
    assert len(table) == 10
    assert len({skill for skill, _ in table}) == 10
    division = module.test_blueprint("division", {}, Random(2))
    assert len(division) == 10
    assert all(kind == "direct_division" for _, kind in division)
    mixed = module.test_blueprint("mixed", {}, Random(3))
    kinds = [kind for _, kind in mixed]
    assert len(mixed) == 20
    assert kinds.count("direct_multiplication") == 10
    assert kinds.count("direct_division") == 5
    assert kinds.count("missing_factor") == 3
    assert kinds.count("visual") == 1
    assert kinds.count("story") == 1
    tables = {number for key, _ in mixed for number in parse_skill_key(key)[1:]}
    assert len(tables) >= 8
    with pytest.raises(ValueError):
        module.test_blueprint("missing", {}, Random(1))


def test_practice_modes_and_division_prerequisite() -> None:
    module = TimesTablesModule()
    assert {mode.mode_id for mode in module.practice_modes()} == {
        "quick",
        "normal",
        "table",
        "multiplication",
        "division",
        "mixed",
    }
    no_mastery = module.session_blueprint("mixed", 10, {}, {}, Random(1))
    assert all(key.startswith("mul:") for key, _ in no_mastery)
    mastery = {"mul:6:7": MasteryState("mul:6:7", box=2)}
    with_mastery = module.session_blueprint("mixed", 20, mastery, {}, Random(2))
    assert any(key == "div:6:7" for key, _ in with_mastery)
    table = module.session_blueprint("table", 10, {}, {"table": 7}, Random(3))
    assert sum(7 in parse_skill_key(key)[1:] for key, _ in table) >= 7
    multiplication = module.session_blueprint("multiplication", 10, {}, {}, Random(4))
    assert {kind for _, kind in multiplication} <= {
        "direct_multiplication",
        "missing_factor",
    }
    division = module.session_blueprint("division", 10, {}, {}, Random(5))
    assert {kind for _, kind in division} <= {"direct_division", "missing_divisor"}


def test_learning_progress_daily_and_media() -> None:
    module = TimesTablesModule()
    table = module.render_learning_unit("table:7")
    assert "7 × 8 = 56" in table.body
    assert "56 ÷ 7 = 8" in (table.related_text or "")
    full = module.render_learning_unit("full_table")
    assert full.image_renderer_id == "full_table"
    mastery = {
        "mul:7:8": MasteryState(
            "mul:7:8",
            box=5,
            attempt_count=3,
            consecutive_correct=3,
            correct_dates=("2026-07-15", "2026-07-16", "2026-07-16"),
        ),
        "div:7:8": MasteryState("div:7:8", box=1, attempt_count=2),
    }
    progress = module.progress_view(
        mastery, {"total": 5, "recent": 3, "accuracy": 67, "active_days": 2}
    )
    assert progress.strengths[0].skill_key == "mul:7:8"
    assert progress.current_targets[0].skill_key == "div:7:8"
    skill, kind = module.daily_skill(mastery, datetime.now(UTC), Random(5))
    assert skill.startswith("mul:")
    assert kind == "direct_multiplication"
    assert module.render_media("full_table", {}).startswith(b"\x89PNG")
    assert module.render_media("individual_table", {"table": 7}).startswith(b"\x89PNG")
    assert module.render_media("array", {"rows": 4, "columns": 6}).startswith(b"\x89PNG")
    assert module.render_media("mascot", {}).startswith(b"\x89PNG")


def test_topic_validation_and_invalid_inputs() -> None:
    module = TimesTablesModule()
    assert module.validate() == []
    with pytest.raises(ValueError):
        module.generate_question("mul:6:7", "unknown", Random(1))
    with pytest.raises(ValueError):
        module.render_media("unknown", {})
    with pytest.raises(ValueError):
        module.render_learning_unit("unknown")
