from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from random import Random

import pytest

from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import MasteryState
from app.database.models import Question
from app.keyboards.questions import answer_choices_text
from app.topics.python_foundations import PythonFoundationsModule
from app.topics.python_foundations.lessons import LESSON_CODE
from app.topics.python_foundations.module import (
    ALL_SKILLS,
    GAME_SKILLS,
    MODE_SKILLS,
)
from app.topics.python_foundations.questions import (
    CONCEPTS,
    QUESTION_TYPES,
    STDOUT_SKILLS,
    question_parts,
)
from app.topics.python_foundations.russian_tasks import (
    CHECKS,
    DETAILS,
    EDITS,
    MISCONCEPTION_LABELS,
)
from app.topics.python_foundations.skills import GROUP_LABELS, skill_catalogue, skill_label


def mastered_state(skill_key: str) -> MasteryState:
    return MasteryState(
        skill_key,
        box=5,
        attempt_count=8,
        correct_count=8,
        consecutive_correct=3,
        correct_dates=("2026-10-16", "2026-10-17", "2026-10-18"),
        state={"correct_formats": ["recognize", "predict", "apply"]},
    )


def test_complete_contract_curriculum_and_stable_skill_map() -> None:
    module = PythonFoundationsModule()
    assert module.metadata.topic_id == "python_foundations"
    assert module.metadata.daily_extended_actions
    assert len(module.skills()) == 53
    assert len(module.learning_units()) == 22
    assert len(module.practice_modes()) == 10
    assert len(module.test_definitions()) == 4
    assert tuple(item.skill_key for item in skill_catalogue()) == ALL_SKILLS
    assert set(CONCEPTS) == set(ALL_SKILLS)
    assert set(GROUP_LABELS) == {item.group_key for item in module.skills()}
    assert all(item.prerequisites or item.skill_key == "PY.EXEC.ORDER" for item in module.skills())
    assert all(
        module.content(item.title_key) and module.content(item.description_key)
        for item in module.skills()
    )
    assert module.validate() == []
    assert skill_label("PY.CLASS.SELF_OTHER") == "self и other"
    with pytest.raises(ValueError):
        skill_label("missing")


def test_learning_sequence_is_russian_code_first_and_contains_nine_labs() -> None:
    module = PythonFoundationsModule()
    combined = ""
    lab_ids: list[str] = []
    for unit in module.learning_units():
        view = module.render_learning_unit(unit.unit_id)
        assert view.title and view.body
        assert view.related_text is None
        assert view.code == LESSON_CODE[unit.unit_id]
        compile(view.code, f"<lesson:{unit.unit_id}>", "exec")
        assert view.practice_configuration["focus_skill"] in unit.skill_keys
        combined += f"\n{view.title}\n{view.body}"
        if unit.unit_id.startswith("lab"):
            lab_ids.append(unit.unit_id)
        for key in unit.skill_keys:
            assert key in ALL_SKILLS
    assert lab_ids == [
        f"lab{number}_{name}"
        for number, name in enumerate(
            (
                "init",
                "weapons",
                "attack",
                "armor",
                "objects",
                "loop",
                "initiative",
                "refactor",
                "critical",
            ),
            start=1,
        )
    ]
    for required in ("сверху вниз", "отдельный", "сравнивает", "возвращает", "критический"):
        assert required in combined.lower()
    assert "p1.attack(p2)" in LESSON_CODE["lab3_attack"]
    assert "other.defense -= damage" in LESSON_CODE["lab9_critical"]
    assert "% 3 == 0" in module.content("learn.lab9_critical.body")
    assert "dataclass" not in combined.lower()
    assert "json" not in combined.lower()
    with pytest.raises(ValueError):
        module.render_learning_unit("missing")


@pytest.mark.parametrize("skill_key", ALL_SKILLS)
def test_each_skill_has_three_difficulty_levels_and_evaluable_questions(
    skill_key: str,
) -> None:
    module = PythonFoundationsModule()
    levels: set[int] = set()
    for question_type in QUESTION_TYPES:
        for seed in range(4):
            question = module.generate_question(skill_key, question_type, Random(seed))
            validate_options(question.answer_mode, question.answer_options)
            json.dumps(asdict(question), ensure_ascii=False)
            assert question.topic_id == "python_foundations"
            assert question.skill_key == skill_key
            assert len(question.answer_options) == 4
            assert len({item.label for item in question.answer_options}) == 4
            assert 1 <= len(question.metadata["hints"]) <= 3
            assert '<pre><code class="language-python">' in question.rendered_prompt
            assert question.metadata["prompt_format"] == "html"
            assert re.search(r"[А-Яа-яЁё]", question.rendered_prompt.split("<pre>")[0])
            assert re.search(r"[А-Яа-яЁё]", question.explanation_payload["explanation"])
            stored = Question(
                prompt_payload={"metadata": question.metadata},
                options=[asdict(option) for option in question.answer_options],
            )
            assert len(question.rendered_prompt) + len(answer_choices_text(stored)) + 100 < 4096
            levels.add(int(question.metadata["difficulty_level"]))
            assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct
            wrong = next(
                option.value
                for option in question.answer_options
                if option.value != question.correct_answer
            )
            outcome = module.evaluate_answer(asdict(question), wrong)
            assert not outcome.is_correct
            assert outcome.feedback_payload["misconception"]
            assert outcome.hint_payload and outcome.hint_payload["hint"]
    assert levels == {1, 2, 3}


def test_all_tasks_have_full_context_and_distinct_edit_exercises() -> None:
    assert set(DETAILS) == set(CONCEPTS) == set(EDITS)
    assert {item.misconception for item in CONCEPTS.values()} <= set(MISCONCEPTION_LABELS)
    assert set(CHECKS) == {key for key, concept in CONCEPTS.items() if concept.stdout_code is None}
    for key, check in CHECKS.items():
        compile(check.code, f"<check:{key}>", "exec")
    for key in CONCEPTS:
        prediction = question_parts(key, "predict")
        edit = question_parts(key, "apply")
        assert prediction.prompt != edit.prompt
        assert prediction.answers != edit.answers
        assert "<pre><code" in prediction.prompt
        assert "<pre><code" in edit.prompt


def test_python_choices_render_as_separate_blocks_with_code_highlighting_only_for_code() -> None:
    module = PythonFoundationsModule()

    def rendered(skill_key: str, question_type: str) -> str:
        generated = module.generate_question(skill_key, question_type, Random(7))
        stored = Question(
            prompt_payload={"metadata": generated.metadata},
            options=[asdict(option) for option in generated.answer_options],
        )
        return answer_choices_text(stored)

    output = rendered("PY.EXEC.ORDER", "predict")
    assert output.count("<b>Вариант ") == 4
    assert "<pre>A\nC</pre>" in output
    assert '<code class="language-python">' not in output
    assert "</pre>\n\n<b>Вариант " in output

    edit = rendered("PY.IO.PRINT", "apply")
    assert '<pre><code class="language-python">print(&quot;hp&quot;)</code></pre>' in edit
    assert edit.count('<code class="language-python">') == 4

    mixed = rendered("PY.CLASS.SELF", "apply")
    assert '<pre><code class="language-python">cat1</code></pre>' in mixed
    assert mixed.count('<code class="language-python">') == 1
    assert mixed.count("<pre>") == 4

    check = rendered("PY.INDENTATION", "predict")
    assert '<pre><code class="language-python">print(&quot;жив&quot;)</code></pre>' in check
    assert check.count('<code class="language-python">') == 2


def test_stdout_questions_are_compiled_executed_and_exact() -> None:
    module = PythonFoundationsModule()
    assert len(STDOUT_SKILLS) >= 20
    for skill_key in STDOUT_SKILLS:
        concept = CONCEPTS[skill_key]
        assert concept.stdout_code is not None
        actual = module._execute_stdout(concept.stdout_code, concept.stdout_inputs)
        assert actual == concept.stdout_expected
        question = module.generate_question(skill_key, "predict", Random(7))
        assert question.metadata["validated_stdout"] is True
        assert question.metadata["stdout_expected"] == actual
        assert '<pre><code class="language-python">' in question.rendered_prompt
        assert question.metadata["prompt_format"] == "html"
    assert CONCEPTS["PY.IO.INPUT"].stdout_inputs == ("Rak",)
    assert CONCEPTS["PY.RANDOM.RANDINT"].stdout_code is None


def test_modes_are_specific_adaptive_prerequisite_aware_and_varied() -> None:
    module = PythonFoundationsModule()
    for mode in module.practice_modes():
        blueprint = module.session_blueprint(
            mode.mode_id, mode.default_question_count, {}, {}, Random(42)
        )
        assert 1 <= len(blueprint) <= mode.default_question_count
        assert len({key for key, _ in blueprint}) == len(blueprint)
        if mode.mode_id not in {"fighting_lab", "mini_script", "challenge"}:
            assert all(key in MODE_SKILLS[mode.mode_id] for key, _ in blueprint)
        assert all(kind in QUESTION_TYPES for _, kind in blueprint)
        if mode.mode_id == "predict_output":
            assert all(key in STDOUT_SKILLS and kind == "predict" for key, kind in blueprint)
        if mode.mode_id in {"fix_bug", "mini_script"}:
            assert all(kind == "apply" for _, kind in blueprint)

    initial = module.session_blueprint("quick", 6, {}, {}, Random(4))
    assert not {key for key, _ in initial}.intersection(GAME_SKILLS)
    assert all(kind in {"predict", "apply"} for _, kind in initial)

    focus = module.session_blueprint(
        "fighting_lab", 4, {}, {"focus_skill": "GAME.DEBUG_INITIATIVE"}, Random(4)
    )
    assert focus[0][0] != "GAME.DEBUG_INITIATIVE"
    assert not focus[0][0].startswith("GAME.")

    all_mastered = {key: mastered_state(key) for key in ALL_SKILLS}
    focused = module.session_blueprint(
        "fighting_lab",
        4,
        all_mastered,
        {"focus_skill": "GAME.DEBUG_INITIATIVE"},
        Random(4),
    )
    assert focused[0][0] == "GAME.DEBUG_INITIATIVE"
    with pytest.raises(ValueError):
        module.session_blueprint("missing", 5, {}, {}, Random(1))
    with pytest.raises(ValueError):
        module.session_blueprint("quick", 5, {}, {"focus_skill": "missing"}, Random(1))


def test_challenges_retry_daily_progress_and_teacher_misconceptions() -> None:
    module = PythonFoundationsModule()
    expected_counts = {"foundations": 12, "functions_data": 12, "objects": 10, "fighting": 8}
    for definition in module.test_definitions():
        blueprint = module.test_blueprint(definition.test_id, {}, Random(8))
        assert len(blueprint) == expected_counts[definition.test_id]
        assert all(key in ALL_SKILLS and kind in QUESTION_TYPES for key, kind in blueprint)
        assert len({key for key, _ in blueprint}) == len(blueprint)
    assert tuple(key for key, _ in module.test_blueprint("fighting", {}, Random(8))) == GAME_SKILLS
    assert module.test_blueprint("fighting", {}, Random(8))[-1] == (
        "GAME.CRITICAL_COUNTER",
        "apply",
    )
    with pytest.raises(ValueError):
        module.test_blueprint("missing", {}, Random(1))

    assert module.retry_question_type("PY.FUNC.DEFINE", "predict", Random(1)) != "predict"
    with pytest.raises(ValueError):
        module.retry_question_type("missing", "predict", Random(1))

    start = datetime(2026, 10, 1, tzinfo=UTC)
    daily = {
        module.daily_skill({}, start + timedelta(days=offset), Random(offset))
        for offset in range(12)
    }
    assert len(daily) >= 4
    assert all(kind in {"predict", "apply"} for _, kind in daily)

    state = MasteryState(
        "PY.CLASS.SELF_OTHER",
        box=5,
        attempt_count=9,
        correct_count=7,
        consecutive_correct=3,
        correct_dates=("2026-10-16", "2026-10-17", "2026-10-18"),
        state={
            "correct_formats": ["predict", "apply"],
            "misconceptions": {"self_other_confusion": 3},
            "format_results": {
                "stdout": {"attempts": 4, "correct": 3},
                "debug": {"attempts": 3, "correct": 2},
                "construction": {"attempts": 2, "correct": 2},
            },
        },
    )
    view = module.progress_view(
        {state.skill_key: state},
        {"total": 9, "recent": 5, "accuracy": 78, "active_days": 3},
    )
    assert (
        view.headline_metrics[0]
        == module.progress_view({state.skill_key: state}, {"total": 9}).headline_metrics[0]
    )
    assert view.headline_metrics[0].value == "9"
    assert view.strengths[0].skill_key == state.skill_key
    assert len(view.progress_groups) == len(GROUP_LABELS)
    insights = module.teacher_insights(
        {state.skill_key: state}, {"total": 9, "accuracy": 78, "hints": 2}
    )
    assert any(item.label == "self и other" and item.value == "ошибок: 3" for item in insights)
    assert any(item.label == "Тем с верным прогнозом" and item.value == "1" for item in insights)
    assert any(item.label == "Точный вывод" and item.value == "3/4" for item in insights)
    assert any(item.label == "Исправление кода" and item.value == "4/5" for item in insights)


def test_acceptance_scenario_tracks_definition_self_state_and_initiative() -> None:
    module = PythonFoundationsModule()
    definition = module.generate_question("PY.EXEC.DEF_VS_CALL", "predict", Random(3))
    wrong = next(option.value for option in definition.answer_options if option.label == "A\nB\nC")
    outcome = module.evaluate_answer(asdict(definition), wrong)
    assert not outcome.is_correct
    assert outcome.feedback_payload["misconception"] == "definition_runs_immediately"
    retry_type = module.retry_question_type(
        "PY.EXEC.DEF_VS_CALL", definition.question_type, Random(2)
    )
    assert retry_type != "predict"

    self_other = module.generate_question("PY.CLASS.SELF_OTHER", "predict", Random(2))
    correct_label = next(
        option.label
        for option in self_other.answer_options
        if option.value == self_other.correct_answer
    )
    assert correct_label == "cat2"

    armor = module.generate_question("GAME.ARMOR_DAMAGE", "predict", Random(2))
    armor_label = next(
        option.label for option in armor.answer_options if option.value == armor.correct_answer
    )
    assert armor_label == "520 0"

    initiative = module.generate_question("GAME.DEBUG_INITIATIVE", "predict", Random(2))
    initiative_label = next(
        option.label
        for option in initiative.answer_options
        if option.value == initiative.correct_answer
    )
    assert initiative_label == "p1"

    critical = module.generate_question("GAME.CRITICAL_COUNTER", "predict", Random(2))
    critical_label = next(
        option.label
        for option in critical.answer_options
        if option.value == critical.correct_answer
    )
    assert critical_label == "3"


def test_invalid_questions_and_missing_media_fail_cleanly() -> None:
    module = PythonFoundationsModule()
    with pytest.raises(ValueError):
        module.generate_question("missing", "predict", Random(1))
    with pytest.raises(ValueError):
        module.generate_question("PY.EXEC.ORDER", "missing", Random(1))
    with pytest.raises(ValueError):
        module.render_media("missing", {})
