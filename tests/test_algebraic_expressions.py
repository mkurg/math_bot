from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from random import Random

import pytest

from app.core.mastery.engine import is_mastered
from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import MasteryState
from app.topics.algebraic_expressions import AlgebraicExpressionsModule
from app.topics.algebraic_expressions.module import MODE_SKILLS, QUESTION_TYPES
from app.topics.algebraic_expressions.skills import GROUP_LABELS, skill_catalogue, skill_label


def test_contract_curriculum_and_validation() -> None:
    module = AlgebraicExpressionsModule()
    assert module.metadata.topic_id == "algebraic_expressions"
    assert module.metadata.daily_extended_actions
    assert len(module.skills()) == 22
    assert len(module.practice_modes()) == 9
    assert len(module.test_definitions()) == 4
    assert len(module.learning_units()) == 15
    assert skill_catalogue() == module.skills()
    assert set(GROUP_LABELS) == {item.group_key for item in module.skills()}
    assert all(len(formats) >= 2 for formats in QUESTION_TYPES.values())
    assert module.validate() == []
    assert skill_label("simplify:two_groups") == "Упрощать выражение с двумя группами"
    with pytest.raises(ValueError):
        skill_label("missing")


def test_theory_is_russian_and_covers_the_complete_conceptual_arc() -> None:
    module = AlgebraicExpressionsModule()
    combined = ""
    for unit in module.learning_units():
        view = module.render_learning_unit(unit.unit_id)
        assert view.title and view.body
        assert unit.related_practice_mode_id
        assert view.practice_configuration["focus_skill"] in unit.skill_keys
        combined += f"\n{view.title}\n{view.body}"
    for required in (
        "знак относится",
        "скобки объединяют",
        "плюс перед скобками",
        "умножение всей группы на −1",
        "распределительный закон",
        "подобные слагаемые",
        "коэффициент",
        "две переменные",
        "раскрываем обе группы",
        "4x − 11",
    ):
        assert required.lower() in combined.lower()
    assert "(a + b)(" not in combined
    for key in (
        "main_menu",
        "practice.title",
        "tests.title",
        "learn.title",
        "settings.title",
        "test.abandon.confirm",
        "privacy",
        "delete.warning",
        "help",
    ):
        assert any(
            "а" <= character.lower() <= "я" or character.lower() == "ё"
            for character in module.content(key)
        )
    with pytest.raises(ValueError):
        module.render_learning_unit("missing")


@pytest.mark.parametrize(("skill_key", "question_types"), tuple(QUESTION_TYPES.items()))
def test_every_question_format_is_serializable_and_evaluable(
    skill_key: str, question_types: tuple[str, ...]
) -> None:
    module = AlgebraicExpressionsModule()
    for question_type in question_types:
        for seed in range(20):
            question = module.generate_question(skill_key, question_type, Random(seed))
            validate_options(question.answer_mode, question.answer_options)
            json.dumps(asdict(question), ensure_ascii=False)
            assert question.topic_id == "algebraic_expressions"
            assert question.skill_key == skill_key
            assert len(question.answer_options) == 4
            assert len({item.label for item in question.answer_options}) == 4
            assert question.metadata["hints"]
            assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct
            wrong = next(
                option.value
                for option in question.answer_options
                if option.value != question.correct_answer
            )
            outcome = module.evaluate_answer(asdict(question), wrong)
            assert not outcome.is_correct
            assert outcome.feedback_payload["misconception"].startswith("M")
            assert outcome.hint_payload and outcome.hint_payload["hint"]


def test_generated_algebra_answers_and_final_target_are_sound() -> None:
    module = AlgebraicExpressionsModule()
    expected_fragments = {
        "minus_difference": "−x + 4",
        "expand_negative": "−2x + 6",
        "collect_negative": "−2x",
        "collect_constants": "7x + 7",
        "two_variables": "7x + y",
        "subtract_group": "2x + 4",
        "two_groups": "−x + 9",
        "final_target": "4x − 11",
    }
    reverse = {
        question_type: skill_key
        for skill_key, formats in QUESTION_TYPES.items()
        for question_type in formats
    }
    for question_type, expected in expected_fragments.items():
        question = module.generate_question(reverse[question_type], question_type, Random(7))
        correct_label = next(
            item.label for item in question.answer_options if item.value == question.correct_answer
        )
        assert correct_label == expected
        assert expected in question.explanation_payload["equation"]


def test_practice_is_mode_specific_adaptive_focusable_and_varied_for_mastery() -> None:
    module = AlgebraicExpressionsModule()
    all_skills = {item.skill_key for item in module.skills()}
    for mode in module.practice_modes():
        blueprint = module.session_blueprint(
            mode.mode_id, mode.default_question_count, {}, {}, Random(42)
        )
        assert len(blueprint) == mode.default_question_count
        assert all(key in all_skills and kind in QUESTION_TYPES[key] for key, kind in blueprint)
        if mode.mode_id in MODE_SKILLS:
            assert {key for key, _ in blueprint}.issubset(MODE_SKILLS[mode.mode_id])

    mastered = MasteryState(
        "parentheses:plus",
        box=5,
        attempt_count=8,
        correct_count=8,
        consecutive_correct=3,
        correct_dates=("2026-08-05", "2026-08-06", "2026-08-06"),
        state={"correct_formats": ["remove_plus", "plus_reason"]},
    )
    weak_state = MasteryState(
        "parentheses:minus_difference", box=1, attempt_count=4, correct_count=1
    )
    assert is_mastered(mastered)
    weak = module.session_blueprint(
        "weak",
        8,
        {mastered.skill_key: mastered, weak_state.skill_key: weak_state},
        {},
        Random(3),
    )
    assert {key for key, _ in weak} == {weak_state.skill_key}
    focused = module.session_blueprint(
        "quick", 5, {}, {"focus_skill": "collect:two_variables"}, Random(4)
    )
    assert focused[0][0] == "collect:two_variables"
    with pytest.raises(ValueError):
        module.session_blueprint("missing", 5, {}, {}, Random(1))
    with pytest.raises(ValueError):
        module.session_blueprint("quick", 5, {}, {"focus_skill": "missing"}, Random(1))


def test_four_challenges_retry_daily_progress_and_teacher_statistics() -> None:
    module = AlgebraicExpressionsModule()
    expected_counts = {"signs": 10, "distribution": 12, "like_terms": 12, "final": 15}
    for definition in module.test_definitions():
        blueprint = module.test_blueprint(definition.test_id, {}, Random(8))
        assert len(blueprint) == expected_counts[definition.test_id]
        assert all(kind in QUESTION_TYPES[key] for key, kind in blueprint)
    final = module.test_blueprint("final", {}, Random(2))
    assert ("simplify:two_groups", "final_target") in final
    with pytest.raises(ValueError):
        module.test_blueprint("missing", {}, Random(1))

    assert (
        module.retry_question_type("simplify:two_groups", "two_groups", Random(1)) == "final_target"
    )
    with pytest.raises(ValueError):
        module.retry_question_type("missing", "anything", Random(1))

    start = datetime(2026, 8, 1, tzinfo=UTC)
    daily = {
        module.daily_skill({}, start + timedelta(days=offset), Random(offset))
        for offset in range(18)
    }
    assert len({kind for _, kind in daily}) >= 8

    state = MasteryState(
        "simplify:two_groups",
        box=5,
        attempt_count=7,
        correct_count=6,
        consecutive_correct=3,
        correct_dates=("2026-08-05", "2026-08-06", "2026-08-06"),
        state={
            "correct_formats": ["two_groups", "final_target"],
            "misconceptions": {"M8: нарушен порядок": 2},
        },
    )
    view = module.progress_view(
        {state.skill_key: state},
        {"total": 7, "recent": 7, "accuracy": 86, "active_days": 2},
    )
    assert view.headline_metrics[0].label == "Всего ответов"
    assert view.headline_metrics[0].value == "7"
    assert view.strengths[0].skill_key == state.skill_key
    assert len(view.progress_groups) == len(GROUP_LABELS)
    insights = module.teacher_insights({state.skill_key: state}, {"hints": 1, "daily": 2})
    assert any(item.label == "M8: нарушен порядок" for item in insights)
    metrics = module.test_result_metrics(
        (
            {"skill_key": "parentheses:plus", "is_correct": True},
            {"skill_key": "distribution:negative", "is_correct": False},
            {"skill_key": "collect:positive", "is_correct": True},
        )
    )
    assert {item.label for item in metrics} == {
        "Знаки и скобки",
        "Распределительный закон",
        "Подобные слагаемые",
    }


def test_invalid_questions_and_missing_media_fail_cleanly() -> None:
    module = AlgebraicExpressionsModule()
    with pytest.raises(ValueError):
        module.generate_question("missing", "term_count", Random(1))
    with pytest.raises(ValueError):
        module.generate_question("terms:identify", "final_target", Random(1))
    with pytest.raises(ValueError):
        module.render_media("missing", {})
