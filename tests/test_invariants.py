from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from random import Random

import pytest

from app.core.mastery.engine import is_mastered
from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import MasteryState
from app.topics.invariants import InvariantsModule
from app.topics.invariants.module import (
    GUIDED_BLUEPRINT,
    MODE_SKILLS,
    QUESTION_TYPES,
    _odd_part,
)
from app.topics.invariants.skills import GROUP_LABELS, skill_catalogue, skill_label


def test_module_contract_curriculum_and_validation() -> None:
    module = InvariantsModule()
    assert module.metadata.topic_id == "invariants"
    assert module.metadata.daily_extended_actions
    assert len(module.skills()) == 11
    assert len(module.practice_modes()) == 7
    assert len(module.test_definitions()) == 3
    assert len(module.learning_units()) == 8
    assert skill_catalogue() == module.skills()
    assert set(GROUP_LABELS) == {item.group_key for item in module.skills()}
    assert module.validate() == []
    assert skill_label("prove:impossible") == "Prove that a target is impossible"
    with pytest.raises(ValueError):
        skill_label("missing")


def test_theory_covers_the_complete_lesson_arc_and_links_to_practice() -> None:
    module = InvariantsModule()
    combined = ""
    for unit in module.learning_units():
        view = module.render_learning_unit(unit.unit_id)
        assert view.title and view.body
        assert unit.related_practice_mode_id
        assert view.practice_configuration["focus_skill"] in unit.skill_keys
        combined += f"\n{view.title}\n{view.body}"
    for required_idea in (
        "10 coins",
        "starting state",
        "4 black",
        "remainder modulo 3",
        "every type of allowed move",
        "not proved reachable",
        "Experiments",
        "odd part",
    ):
        assert required_idea.lower() in combined.lower()
    with pytest.raises(ValueError):
        module.render_learning_unit("missing")


@pytest.mark.parametrize(("skill_key", "question_types"), tuple(QUESTION_TYPES.items()))
def test_every_question_family_is_varied_serializable_and_evaluable(
    skill_key: str, question_types: tuple[str, ...]
) -> None:
    module = InvariantsModule()
    for question_type in question_types:
        prompts: set[str] = set()
        for seed in range(30):
            question = module.generate_question(skill_key, question_type, Random(seed))
            prompts.add(question.rendered_prompt)
            validate_options(question.answer_mode, question.answer_options)
            json.dumps(asdict(question))
            assert question.topic_id == "invariants"
            assert question.skill_key == skill_key
            assert len(question.metadata["hints"]) == 1
            assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct
            wrong = next(
                option.value
                for option in question.answer_options
                if option.value != question.correct_answer
            )
            evaluation = module.evaluate_answer(asdict(question), wrong)
            assert not evaluation.is_correct
            assert evaluation.feedback_payload["misconception"]
            assert evaluation.hint_payload
        assert prompts


def test_core_reachability_and_invariant_answers_are_mathematically_sound() -> None:
    module = InvariantsModule()
    for seed in range(200):
        for skill_key, question_type in (
            ("discover:parity", "parity_reachable"),
            ("preserve:remainders", "remainder_reachable"),
            ("preserve:card_flips", "card_flip_reachable"),
            ("extend:odd_part", "odd_part_reachable"),
        ):
            question = module.generate_question(skill_key, question_type, Random(seed))
            assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct
            explanation = question.explanation_payload["equation"].lower()
            assert any(
                word in explanation
                for word in (
                    "route",
                    "impossible",
                    "multiple",
                    "divisible",
                    "parity",
                    "odd part",
                    "black count",
                    "power of 2",
                )
            )

    assert {_odd_part(value) for value in (3, 6, 12, 24, 48)} == {3}
    assert _odd_part(18) == 9


def test_practice_blueprints_are_mode_specific_adaptive_and_focusable() -> None:
    module = InvariantsModule()
    skills = {item.skill_key for item in module.skills()}
    for mode in module.practice_modes():
        blueprint = module.session_blueprint(
            mode.mode_id, mode.default_question_count, {}, {}, Random(42)
        )
        assert len(blueprint) == mode.default_question_count
        assert all(key in skills and kind in QUESTION_TYPES[key] for key, kind in blueprint)
        if mode.mode_id in MODE_SKILLS:
            assert {key for key, _ in blueprint}.issubset(MODE_SKILLS[mode.mode_id])
    assert module.session_blueprint("guided", 8, {}, {}, Random(2)) == GUIDED_BLUEPRINT

    mastery = {
        "preserve:remainders": MasteryState(
            "preserve:remainders", box=1, attempt_count=4, correct_count=1
        ),
        "discover:parity": MasteryState(
            "discover:parity",
            box=5,
            attempt_count=8,
            correct_count=8,
            consecutive_correct=3,
            correct_dates=("2026-07-29", "2026-07-30", "2026-07-30"),
            state={"correct_formats": ["parity_reachable", "starting_parity"]},
        ),
    }
    weak = module.session_blueprint("weak", 8, mastery, {}, Random(3))
    assert weak[0][0] == "preserve:remainders"
    focused = module.session_blueprint(
        "quick",
        5,
        {},
        {"focus_skill": "reason:evidence_vs_proof"},
        Random(4),
    )
    assert focused[0][0] == "reason:evidence_vs_proof"
    with pytest.raises(ValueError):
        module.session_blueprint("missing", 5, {}, {}, Random(1))
    with pytest.raises(ValueError):
        module.session_blueprint("quick", 5, {}, {"focus_skill": "missing"}, Random(1))


def test_challenges_retry_daily_progress_and_teacher_insights() -> None:
    module = InvariantsModule()
    for definition in module.test_definitions():
        blueprint = module.test_blueprint(definition.test_id, {}, Random(8))
        assert len(blueprint) == definition.question_count
        assert all(kind in QUESTION_TYPES[key] for key, kind in blueprint)
    with pytest.raises(ValueError):
        module.test_blueprint("missing", {}, Random(1))

    assert (
        module.retry_question_type("prove:same_not_sufficient", "same_not_sufficient", Random(1))
        == "conclusion_strength"
    )
    with pytest.raises(ValueError):
        module.retry_question_type("missing", "anything", Random(1))

    start = datetime(2026, 7, 27, tzinfo=UTC)
    daily = {
        module.daily_skill({}, start + timedelta(days=offset), Random(offset))
        for offset in range(14)
    }
    assert {kind for _, kind in daily} >= {
        "parity_reachable",
        "card_flip_reachable",
        "remainder_reachable",
        "check_all_moves",
        "exit_problem",
        "same_not_sufficient",
        "evidence_vs_proof",
    }

    state = MasteryState(
        "prove:same_not_sufficient",
        box=5,
        attempt_count=6,
        correct_count=5,
        consecutive_correct=3,
        correct_dates=("2026-07-29", "2026-07-30", "2026-07-30"),
        state={
            "correct_formats": ["same_not_sufficient", "conclusion_strength"],
            "misconceptions": {"treats a necessary condition as sufficient": 2},
        },
    )
    assert is_mastered(state)
    view = module.progress_view(
        {state.skill_key: state},
        {"total": 6, "recent": 6, "accuracy": 83, "active_days": 2},
    )
    assert view.headline_metrics[0].value == "6"
    assert view.strengths[0].skill_key == state.skill_key
    assert len(view.progress_groups) == len(GROUP_LABELS)
    insights = module.teacher_insights({state.skill_key: state}, {"hints": 1, "daily": 2})
    assert any(item.label == "treats a necessary condition as sufficient" for item in insights)
    metrics = module.test_result_metrics(
        (
            {"skill_key": "discover:parity", "is_correct": True},
            {"skill_key": "preserve:remainders", "is_correct": False},
            {"skill_key": "prove:impossible", "is_correct": True},
        )
    )
    assert {item.label for item in metrics} == {
        "Spotting what stays the same",
        "Checking every allowed move",
        "Proving possible and impossible",
    }


def test_invalid_questions_and_missing_media_fail_cleanly() -> None:
    module = InvariantsModule()
    with pytest.raises(ValueError):
        module.generate_question("missing", "definition", Random(1))
    with pytest.raises(ValueError):
        module.generate_question("discover:parity", "definition", Random(1))
    with pytest.raises(ValueError):
        module.render_media("missing", {})
