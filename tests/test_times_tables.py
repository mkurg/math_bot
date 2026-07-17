from __future__ import annotations

import json
import re
from collections import Counter
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
        ("mul:6:7", "movement_distance"),
        ("div:6:7", "movement_speed"),
        ("div:6:7", "movement_time"),
        ("mul:6:7", "rectangle_area"),
        ("div:6:7", "rectangle_length"),
        ("div:6:7", "rectangle_width"),
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


@pytest.mark.parametrize(
    ("skill", "question_type", "direction", "formula", "unit"),
    [
        ("mul:6:7", "movement_distance", "distance", "S=vt", "м"),
        ("div:6:7", "movement_speed", "speed", "v=S/t", "м/мин"),
        ("div:6:7", "movement_time", "time", "t=S/v", "мин"),
        ("mul:6:7", "rectangle_area", "area", "S=ab", "см²"),
        ("div:6:7", "rectangle_length", "length", "a=S/b", "см"),
        ("div:6:7", "rectangle_width", "width", "b=S/a", "см"),
    ],
)
def test_formula_word_problems_cover_all_directions_with_one_action(
    skill: str, question_type: str, direction: str, formula: str, unit: str
) -> None:
    module = TimesTablesModule()
    question = module.generate_question(skill, question_type, Random(42))
    metadata = question.metadata
    assert metadata["direction"] == direction
    assert metadata["formula"] == formula
    assert re.search(r"[А-Яа-яЁё]", question.rendered_prompt)
    assert unit in question.explanation_payload["equation"]
    equation = question.explanation_payload["equation"]
    assert equation.count("×") + equation.count("÷") == 1
    expected = {
        "distance": metadata.get("distance"),
        "speed": metadata.get("speed"),
        "time": metadata.get("time"),
        "area": metadata.get("area"),
        "length": metadata.get("length"),
        "width": metadata.get("width"),
    }[direction]
    assert question.correct_answer == {"value": expected}


@pytest.mark.parametrize(
    ("skill", "question_type"),
    [
        ("div:6:7", "movement_distance"),
        ("mul:6:7", "movement_speed"),
        ("mul:6:7", "movement_time"),
        ("div:6:7", "rectangle_area"),
        ("mul:6:7", "rectangle_length"),
        ("mul:6:7", "rectangle_width"),
    ],
)
def test_formula_word_problem_direction_matches_mastery_operation(
    skill: str, question_type: str
) -> None:
    module = TimesTablesModule()
    with pytest.raises(ValueError):
        module.generate_question(skill, question_type, Random(42))


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
        "weak",
        "movement",
        "rectangle",
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
    mixed_types = {kind for _, kind in with_mastery}
    assert any(kind.startswith("movement_") for kind in mixed_types)
    assert any(kind.startswith("rectangle_") for kind in mixed_types)
    table = module.session_blueprint("table", 10, {}, {"table": 7}, Random(3))
    assert sum(7 in parse_skill_key(key)[1:] for key, _ in table) >= 7
    multiplication = module.session_blueprint("multiplication", 10, {}, {}, Random(4))
    assert {kind for _, kind in multiplication} <= {
        "direct_multiplication",
        "missing_factor",
    }
    division = module.session_blueprint("division", 10, {}, {}, Random(5))
    assert {kind for _, kind in division} <= {"direct_division", "missing_divisor"}


@pytest.mark.parametrize(
    ("mode_id", "expected_types"),
    [
        (
            "movement",
            {"movement_distance", "movement_speed", "movement_time"},
        ),
        (
            "rectangle",
            {"rectangle_area", "rectangle_length", "rectangle_width"},
        ),
    ],
)
def test_explicit_formula_sections_balance_all_directions(
    mode_id: str, expected_types: set[str]
) -> None:
    module = TimesTablesModule()
    blueprint = module.session_blueprint(mode_id, 6, {}, {}, Random(8))
    assert len(blueprint) == 6
    assert Counter(kind for _, kind in blueprint) == Counter(
        {question_type: 2 for question_type in expected_types}
    )
    assert len({parse_skill_key(key)[1:] for key, _ in blueprint}) == 6
    for skill_key, question_type in blueprint:
        operation, _, _ = parse_skill_key(skill_key)
        expected_operation = (
            "mul" if question_type in {"movement_distance", "rectangle_area"} else "div"
        )
        assert operation == expected_operation
        question = module.generate_question(skill_key, question_type, Random(9))
        assert question.question_type == question_type


def test_formula_problem_retries_stay_in_the_selected_section() -> None:
    module = TimesTablesModule()
    assert (
        module.retry_question_type("mul:6:7", "movement_distance", Random(1)) == "movement_distance"
    )
    assert module.retry_question_type("div:6:7", "movement_speed", Random(1)) == "movement_time"
    assert module.retry_question_type("mul:6:7", "rectangle_area", Random(1)) == "rectangle_area"
    assert module.retry_question_type("div:6:7", "rectangle_length", Random(1)) == "rectangle_width"


def test_weak_pairs_mode_uses_unresolved_mistakes_from_both_operations() -> None:
    module = TimesTablesModule()
    mastery = {
        "mul:6:7": MasteryState("mul:6:7", box=0, attempt_count=5, correct_count=2),
        "div:7:8": MasteryState("div:7:8", box=1, attempt_count=4, correct_count=2),
        "mul:8:8": MasteryState("mul:8:8", box=3, attempt_count=4, correct_count=4),
        "mul:5:9": MasteryState(
            "mul:5:9",
            box=5,
            attempt_count=5,
            correct_count=4,
            consecutive_correct=3,
            correct_dates=("2026-07-14", "2026-07-15", "2026-07-16"),
        ),
    }
    blueprint = module.session_blueprint("weak", 10, mastery, {}, Random(6))
    selected = [key for key, _ in blueprint]
    assert set(selected) == {"mul:6:7", "mul:7:8"}
    assert selected[0] == "mul:6:7"
    assert {kind for _, kind in blueprint} == {"direct_multiplication", "missing_factor"}
    assert "mul:8:8" not in selected
    assert "mul:5:9" not in selected


def test_weak_pairs_mode_falls_back_safely_before_first_mistake() -> None:
    module = TimesTablesModule()
    blueprint = module.session_blueprint("weak", 10, {}, {}, Random(7))
    assert len(blueprint) == 10
    assert all(key.startswith("mul:") for key, _ in blueprint)
    assert {kind for _, kind in blueprint} <= {
        "direct_multiplication",
        "missing_factor",
    }


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


def test_times_tables_student_experience_is_fully_russian() -> None:
    module = TimesTablesModule()
    russian_ui_keys = (
        "topic.title",
        "menu.practice",
        "menu.learn",
        "menu.tests",
        "menu.daily",
        "menu.progress",
        "menu.settings",
        "practice.title",
        "tests.title",
        "learn.title",
        "welcome",
        "returning",
        "main_menu",
        "use_buttons",
        "question.position",
        "question.next",
        "question.hint",
        "session.summary",
        "test.summary",
        "daily.title",
        "progress.title",
        "settings.title",
        "privacy",
        "delete.warning",
        "help",
    )
    format_values = {
        "name": "Ученик",
        "position": 1,
        "total": 5,
        "correct": 4,
        "skills": 3,
        "percentage": 80,
    }
    for key in russian_ui_keys:
        assert re.search(r"[А-Яа-яЁё]", module.content(key, **format_values))
    assert all(
        re.search(r"[А-Яа-яЁё]", story)
        for kind in ("mul", "div")
        for story in module.catalog.raw(f"story.{kind}")
    )
    view = module.render_learning_unit("table:7")
    assert "Таблица умножения" in view.title
    progress = module.progress_view({}, {})
    assert all(re.search(r"[А-Яа-яЁё]", metric.label) for metric in progress.headline_metrics)


def test_topic_validation_and_invalid_inputs() -> None:
    module = TimesTablesModule()
    assert module.validate() == []
    with pytest.raises(ValueError):
        module.generate_question("mul:6:7", "unknown", Random(1))
    with pytest.raises(ValueError):
        module.render_media("unknown", {})
    with pytest.raises(ValueError):
        module.render_learning_unit("unknown")
