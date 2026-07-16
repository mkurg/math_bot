from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from random import Random

import pytest

from app.core.mastery.engine import is_mastered
from app.core.questions.answer_modes import validate_options
from app.core.questions.callbacks import (
    hint_callback,
    pad_callback,
    parse_hint_callback,
    parse_pad_callback,
)
from app.core.topics.contracts import MasteryState
from app.database.models import Question
from app.keyboards.questions import answer_choices_text, answer_keyboard
from app.topics.numeral_systems import NumeralSystemsModule
from app.topics.numeral_systems.question_generator import (
    BASE_SUFFIXES,
    CONVERSIONS,
    digits,
    labelled,
)
from app.topics.numeral_systems.skills import GROUP_LABELS, skill_catalogue, skill_label


def test_module_contract_curriculum_and_validation() -> None:
    module = NumeralSystemsModule()
    assert module.metadata.topic_id == "numeral_systems"
    assert len(module.skills()) == 48
    assert len({item.skill_key for item in module.skills()}) == 48
    assert len(module.practice_modes()) == 11
    assert len(module.test_definitions()) == 8
    assert len(module.learning_units()) == 11
    assert module.validate() == []
    assert set(GROUP_LABELS) == {item.group_key for item in module.skills()}
    assert skill_catalogue() == module.skills()
    assert skill_label("rgb:complete_code") == "Complete hexadecimal colour code"
    with pytest.raises(ValueError):
        skill_label("missing")


@pytest.mark.parametrize("base", (2, 8, 10, 16))
def test_every_byte_value_round_trips_in_each_supported_base(base: int) -> None:
    for value in range(256):
        rendered = digits(value, base)
        assert int(rendered, base) == value
        assert labelled(value, base) == f"{rendered}{BASE_SUFFIXES[base]}"
    assert digits(10, base, 8).endswith(digits(10, base))
    with pytest.raises(ValueError):
        digits(256, base)
    with pytest.raises(ValueError):
        digits(-1, base)
    with pytest.raises(ValueError):
        digits(1, 3)


@pytest.mark.parametrize(("skill_key", "bases"), tuple(CONVERSIONS.items()))
def test_all_direct_conversion_directions_are_correct(
    skill_key: str, bases: tuple[int, int]
) -> None:
    module = NumeralSystemsModule()
    source, target = bases
    for seed in range(12):
        question = module.generate_question(skill_key, "direct_conversion", Random(seed))
        assert question.answer_mode.endswith("_pad")
        assert question.correct_answer["value"]
        assert all(
            character in "0123456789ABCDEF" for character in question.correct_answer["value"]
        )
        assert BASE_SUFFIXES[source] in question.rendered_prompt
        assert question.metadata["target_base"] == target
        assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct


@pytest.mark.parametrize(
    "skill_key",
    (
        "octal:bin_to_oct",
        "octal:oct_to_bin",
        "hexadecimal:bin_to_hex",
        "hexadecimal:hex_to_bin",
    ),
)
def test_guided_conversions_use_one_small_group_without_decimal(skill_key: str) -> None:
    module = NumeralSystemsModule()
    source, target = CONVERSIONS[skill_key]
    assert 10 not in {source, target}
    for seed in range(20):
        question = module.generate_question(skill_key, "guided_conversion", Random(seed))
        assert question.answer_mode == "single_choice"
        answer = str(question.correct_answer["value"])
        assert len(answer) <= (4 if target == 2 else 1)
        assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct


@pytest.mark.parametrize(
    ("question_type", "skill_key"),
    (
        ("positional_expansion", "foundation:positional_value"),
        ("base_identification", "foundation:valid_digits"),
        ("direct_conversion", "binary_decimal:dec_to_bin"),
        ("cross_conversion", "cross_base:oct_to_hex"),
        ("equivalent_representation", "cross_base:equivalent"),
        ("comparison", "cross_base:compare"),
        ("missing_digit", "foundation:positional_value"),
        ("error_detection", "foundation:valid_digits"),
        ("method_selection", "cross_base:efficient_route"),
        ("explanation_selection", "hexadecimal:four_bit_mapping"),
        ("bit_count", "data_units:patterns"),
        ("byte_range", "data_units:byte_range"),
        ("byte_decomposition", "data_units:nibble"),
        ("rgb_channel", "rgb:complete_code"),
        ("colour_recognition", "rgb:visual"),
        ("rgb_binary", "rgb:binary"),
        ("character_code", "characters:decimal"),
        ("character_code", "characters:hex"),
        ("character_code", "characters:binary"),
        ("character_code", "characters:code_to_char"),
        ("character_code", "characters:decode"),
        ("interpretation", "characters:numeric_vs_char"),
        ("same_bits_different_meanings", "metaconcept:same_bits"),
        ("mixed_transformation", "cross_base:oct_to_hex"),
        ("construct_representation", "data_units:leading_zeroes"),
        ("binary_addition", "binary_decimal:binary_addition"),
        ("meaning_ten", "foundation:meaning_ten"),
    ),
)
def test_every_question_family_is_serializable_and_evaluable(
    question_type: str, skill_key: str
) -> None:
    module = NumeralSystemsModule()
    for seed in range(4):
        question = module.generate_question(skill_key, question_type, Random(seed + 30))
        validate_options(question.answer_mode, question.answer_options)
        json.dumps(asdict(question))
        assert module.evaluate_answer(asdict(question), question.correct_answer).is_correct
        assert 1 <= len(question.metadata["hints"]) <= 3
        if question.answer_options:
            wrong = next(
                option.value
                for option in question.answer_options
                if option.value != question.correct_answer
            )
        else:
            wrong_value = "0" if question.correct_answer["value"] != "0" else "1"
            wrong = {"value": wrong_value}
        evaluation = module.evaluate_answer(asdict(question), wrong)
        assert not evaluation.is_correct
        assert evaluation.feedback_payload["misconception"]


def test_character_zero_case_and_ascii_width_are_explicit() -> None:
    module = NumeralSystemsModule()
    prompts = []
    for seed in range(500):
        question = module.generate_question("characters:binary", "character_code", Random(seed))
        prompts.append(question.rendered_prompt)
        assert len(question.correct_answer["value"]) == 8
        if "'0'" in question.rendered_prompt:
            assert question.correct_answer["value"] == "00110000"
            break
    else:
        pytest.fail("the reviewed ASCII bank did not produce character 0")
    assert any("'0'" in prompt for prompt in prompts)


def test_generated_content_bank_has_substantial_variation() -> None:
    module = NumeralSystemsModule()
    banks = (
        ("binary_decimal:bin_to_dec", "direct_conversion", 30),
        ("octal:bin_to_oct", "direct_conversion", 30),
        ("hexadecimal:bin_to_hex", "direct_conversion", 40),
        ("rgb:complete_code", "rgb_channel", 25),
        ("characters:hex", "character_code", 20),
        ("metaconcept:same_bits", "same_bits_different_meanings", 20),
    )
    for skill_key, question_type, minimum in banks:
        prompts = {
            module.generate_question(skill_key, question_type, Random(seed)).rendered_prompt
            for seed in range(minimum * 4)
        }
        assert len(prompts) >= minimum


def test_practice_blueprints_are_varied_and_mode_specific() -> None:
    module = NumeralSystemsModule()
    for mode in module.practice_modes():
        blueprint = module.session_blueprint(
            mode.mode_id, mode.default_question_count, {}, {}, Random(42)
        )
        assert len(blueprint) == mode.default_question_count
        assert all(skill in {item.skill_key for item in module.skills()} for skill, _ in blueprint)
        assert (
            max(
                sum(1 for item in blueprint[index : index + 5] if item[1] == kind)
                for index in range(len(blueprint))
                for kind in {item[1] for item in blueprint}
            )
            <= 5
        )
    tier_one = module.session_blueprint("quick", 5, {}, {}, Random(1))
    tier_two = module.session_blueprint("guided", 6, {}, {}, Random(1))
    assert all(
        key not in CONVERSIONS or 10 not in CONVERSIONS[key]
        for key, _question_type in (*tier_one, *tier_two)
    )
    assert all(question_type != "direct_conversion" for _, question_type in tier_one)
    assert any(question_type == "guided_conversion" for _, question_type in tier_two)
    deep = module.session_blueprint("deep", 8, {}, {}, Random(1))
    deep_groups = {
        next(item.group_key for item in module.skills() if item.skill_key == key) for key, _ in deep
    }
    assert deep_groups == {
        "foundation",
        "metaconcept",
        "binary_decimal",
        "octal",
        "hexadecimal",
        "cross_base",
        "rgb",
        "characters",
    }
    focused = module.session_blueprint(
        "quick", 5, {}, {"focus_skill": "rgb:complete_code"}, Random(2)
    )
    assert focused[0][0] == "rgb:complete_code"
    with pytest.raises(ValueError):
        module.session_blueprint("missing", 5, {}, {}, Random(1))


def test_adaptive_weak_mode_and_retry_types() -> None:
    module = NumeralSystemsModule()
    mastery = {
        "octal:bin_to_oct": MasteryState("octal:bin_to_oct", box=1, attempt_count=3),
        "rgb:visual": MasteryState("rgb:visual", box=5, attempt_count=9),
    }
    weak = module.session_blueprint("weak", 8, mastery, {}, Random(3))
    assert weak[0][0] == "octal:bin_to_oct"
    retry = module.retry_question_type("octal:bin_to_oct", "direct_conversion", Random(1))
    assert retry == "error_detection"
    with pytest.raises(ValueError):
        module.retry_question_type("missing", "direct_conversion", Random(1))


def test_every_challenge_has_the_defined_length_and_mix() -> None:
    module = NumeralSystemsModule()
    for definition in module.test_definitions():
        blueprint = module.test_blueprint(definition.test_id, {}, Random(8))
        assert len(blueprint) == definition.question_count
    octal = module.test_blueprint("binary_octal", {}, Random(1))
    assert sum(item == ("octal:bin_to_oct", "direct_conversion") for item in octal) == 3
    assert sum(item == ("octal:oct_to_bin", "direct_conversion") for item in octal) == 3
    final = module.test_blueprint("final", {}, Random(1))
    assert sum(kind == "rgb_channel" for _, kind in final) == 1
    assert sum(key.startswith("characters:") for key, _ in final) == 3
    with pytest.raises(ValueError):
        module.test_blueprint("missing", {}, Random(1))


def test_learning_units_and_deterministic_media() -> None:
    module = NumeralSystemsModule()
    for unit in module.learning_units():
        view = module.render_learning_unit(unit.unit_id)
        assert view.title and view.body
        if view.image_renderer_id:
            first = module.render_media(view.image_renderer_id, view.image_payload)
            second = module.render_media(view.image_renderer_id, view.image_payload)
            assert first == second
            assert first.startswith(b"\x89PNG")
    with pytest.raises(ValueError):
        module.render_learning_unit("missing")
    with pytest.raises(ValueError):
        module.render_media("missing", {})
    with pytest.raises(ValueError):
        module.render_media("rgb_swatch", {"hex": "GG0000"})
    with pytest.raises(ValueError):
        module.render_media("rgb_channels", {"red": 256, "green": 0, "blue": 0})


def test_daily_rotation_progress_teacher_insights_and_test_metrics() -> None:
    module = NumeralSystemsModule()
    start = datetime(2026, 7, 13, tzinfo=UTC)
    daily = {
        module.daily_skill({}, start + timedelta(days=offset), Random(offset))[1]
        for offset in range(8)
    }
    assert "guided_conversion" in daily
    assert not daily & {"direct_conversion", "cross_conversion"}
    assert daily & {"bit_count_easy", "byte_range"}
    assert daily & {"interpretation", "same_bits_different_meanings"}

    state = MasteryState(
        "hexadecimal:bin_to_hex",
        box=5,
        attempt_count=5,
        correct_count=4,
        consecutive_correct=3,
        correct_dates=("2026-07-14", "2026-07-15", "2026-07-16"),
        state={
            "misconceptions": {"groups bits from the wrong side": 2},
            "correct_formats": ["direct_conversion", "error_detection"],
        },
    )
    assert is_mastered(state)
    view = module.progress_view(
        {state.skill_key: state},
        {"total": 5, "active_days": 3, "accuracy": 80, "hints": 2},
    )
    assert view.headline_metrics[0].value == "5"
    assert view.strengths[0].skill_key == state.skill_key
    assert len(view.progress_groups) == len(GROUP_LABELS)
    insights = module.teacher_insights({state.skill_key: state}, {"hints": 2, "daily": 1})
    assert any(item.label == "groups bits from the wrong side" for item in insights)
    assert any(item.label == "Recent mistake pattern" for item in insights)
    metrics = module.test_result_metrics(
        (
            {"skill_key": "hexadecimal:bin_to_hex", "is_correct": True},
            {"skill_key": "hexadecimal:hex_to_bin", "is_correct": False},
            {"skill_key": "rgb:visual", "is_correct": True},
        )
    )
    assert {metric.label for metric in metrics} == {"Binary ↔ Hexadecimal", "RGB colours"}


def _question_model(answer_mode: str) -> Question:
    return Question(
        id=1,
        public_id="Abcd_123",
        session_id=None,
        user_id=1,
        topic_id="numeral_systems",
        skill_key="hexadecimal:dec_to_hex",
        position=1,
        question_type="direct_conversion",
        answer_mode=answer_mode,
        prompt_payload={"metadata": {"hints": ["First hint"]}},
        media_payload=None,
        options=[],
        correct_answer={"value": "AF"},
        evaluation_payload={},
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.mark.parametrize(
    ("mode", "digits_expected"),
    (
        ("binary_pad", set("01")),
        ("octal_pad", set("01234567")),
        ("decimal_pad", set("0123456789")),
        ("hexadecimal_pad", set("0123456789ABCDEF")),
    ),
)
def test_constructed_answer_keyboards_callbacks_and_hint(
    mode: str, digits_expected: set[str]
) -> None:
    question = _question_model(mode)
    keyboard = answer_keyboard(question, "A" if mode == "hexadecimal_pad" else "1")
    labels = {button.text for row in keyboard.inline_keyboard for button in row}
    assert digits_expected <= labels
    assert {"⌫", "Clear", "Submit", "💡 Hint"} <= labels
    value = pad_callback(question.public_id, "AF", "s")
    assert parse_pad_callback(value) == (question.public_id, "AF", "s")
    assert parse_pad_callback(pad_callback(question.public_id, "", "c"))[1] == ""
    hint = hint_callback(question.public_id)
    assert parse_hint_callback(hint) == question.public_id
    for invalid in ("p:bad", "p:Abcd_123:XYZ:s"):
        with pytest.raises(ValueError):
            parse_pad_callback(invalid)
    with pytest.raises(ValueError):
        parse_hint_callback("h:bad")


def test_long_choice_answers_are_fully_shown_in_text_with_compact_buttons() -> None:
    question = _question_model("single_choice")
    long_answer = "3 bits make 2^3 = 8 patterns, matching all eight octal digits."
    question.options = [
        {"label": long_answer, "value": {"value": "correct"}},
        {"label": "Because computers store octal.", "value": {"value": "wrong-1"}},
        {"label": "Because 3 is the largest digit.", "value": {"value": "wrong-2"}},
        {"label": "Because decimal says so.", "value": {"value": "wrong-3"}},
    ]
    keyboard = answer_keyboard(question)
    labels = [button.text for row in keyboard.inline_keyboard[:-1] for button in row]
    assert labels == ["A", "B", "C", "D"]
    rendered = answer_choices_text(question)
    assert long_answer in rendered
    assert "<b>A</b>" in rendered and "<b>D</b>" in rendered
