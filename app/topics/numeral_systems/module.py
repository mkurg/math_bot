from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from random import Random
from typing import Any

from app.content.loader import ContentCatalog
from app.core.mastery.engine import is_mastered
from app.core.mastery.selection import weighted_skill_order
from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import (
    EvaluationResult,
    GeneratedQuestion,
    LearningUnit,
    LearningView,
    MasteryState,
    Metric,
    PracticeModeDefinition,
    ProgressGroup,
    ProgressItem,
    SkillDefinition,
    SuggestedAction,
    TestDefinition,
    TopicMetadata,
    TopicProgressView,
)
from app.core.topics.validation import validate_topic_contract
from app.topics.numeral_systems import images
from app.topics.numeral_systems.question_generator import generate
from app.topics.numeral_systems.skills import GROUP_LABELS, skill_catalogue, skill_label

CONTENT_PATH = Path(__file__).with_name("content") / "strings.yaml"


QUESTION_TYPES: dict[str, tuple[str, ...]] = {
    "foundation:representation_value": ("equivalent_representation", "interpretation"),
    "foundation:positional_value": ("positional_expansion", "missing_digit"),
    "foundation:powers": ("positional_expansion", "meaning_ten"),
    "foundation:valid_digits": ("base_identification", "error_detection"),
    "foundation:meaning_ten": ("meaning_ten", "comparison"),
    "binary_decimal:bin_to_dec": ("direct_conversion", "equivalent_representation"),
    "binary_decimal:dec_to_bin": ("direct_conversion", "construct_representation"),
    "binary_decimal:binary_addition": ("binary_addition", "error_detection"),
    "binary_decimal:bit_length": ("bit_count", "construct_representation"),
    "octal:three_bit_mapping": ("explanation_selection", "method_selection"),
    "octal:bin_to_oct": ("direct_conversion", "error_detection"),
    "octal:oct_to_bin": ("direct_conversion", "missing_digit"),
    "octal:dec_to_oct": ("direct_conversion", "method_selection"),
    "octal:oct_to_dec": ("direct_conversion", "positional_expansion"),
    "hexadecimal:digits": ("base_identification", "missing_digit"),
    "hexadecimal:four_bit_mapping": ("explanation_selection", "method_selection"),
    "hexadecimal:bin_to_hex": ("direct_conversion", "error_detection"),
    "hexadecimal:hex_to_bin": ("direct_conversion", "construct_representation"),
    "hexadecimal:dec_to_hex": ("direct_conversion", "method_selection"),
    "hexadecimal:hex_to_dec": ("direct_conversion", "positional_expansion"),
    "cross_base:oct_to_hex": ("cross_conversion", "mixed_transformation"),
    "cross_base:hex_to_oct": ("cross_conversion", "mixed_transformation"),
    "cross_base:equivalent": ("equivalent_representation", "comparison"),
    "cross_base:compare": ("comparison", "equivalent_representation"),
    "cross_base:efficient_route": ("method_selection", "error_detection"),
    "data_units:bit": ("bit_count", "explanation_selection"),
    "data_units:nibble": ("byte_decomposition", "explanation_selection"),
    "data_units:byte": ("byte_decomposition", "bit_count"),
    "data_units:patterns": ("bit_count", "byte_range"),
    "data_units:byte_range": ("byte_range", "error_detection"),
    "data_units:leading_zeroes": ("construct_representation", "error_detection"),
    "rgb:channels": ("colour_recognition", "rgb_channel"),
    "rgb:dec_to_hex": ("rgb_channel", "direct_conversion"),
    "rgb:hex_to_dec": ("direct_conversion", "colour_recognition"),
    "rgb:complete_code": ("rgb_channel", "colour_recognition"),
    "rgb:visual": ("colour_recognition", "rgb_channel"),
    "rgb:binary": ("rgb_binary", "rgb_channel"),
    "characters:assigned_code": ("character_code", "interpretation"),
    "characters:decimal": ("character_code", "interpretation"),
    "characters:hex": ("character_code", "mixed_transformation"),
    "characters:binary": ("character_code", "construct_representation"),
    "characters:code_to_char": ("character_code", "interpretation"),
    "characters:decode": ("character_code", "interpretation"),
    "characters:numeric_vs_char": ("interpretation", "same_bits_different_meanings"),
    "metaconcept:bits_interpretation": ("interpretation", "same_bits_different_meanings"),
    "metaconcept:hex_compact": ("explanation_selection", "method_selection"),
    "metaconcept:same_value": ("equivalent_representation", "comparison"),
    "metaconcept:same_bits": ("same_bits_different_meanings", "interpretation"),
}


MODE_GROUPS: dict[str, tuple[str, ...]] = {
    "binary_decimal": ("foundation", "binary_decimal"),
    "binary_octal": ("octal",),
    "binary_hex": ("hexadecimal",),
    "four_systems": ("foundation", "binary_decimal", "octal", "hexadecimal", "cross_base"),
    "bits_bytes": ("data_units", "metaconcept"),
    "colours": ("rgb",),
    "characters": ("characters", "metaconcept"),
}

TIER_ONE_BLUEPRINT: tuple[tuple[str, str], ...] = (
    ("foundation:valid_digits", "base_identification"),
    ("foundation:meaning_ten", "meaning_ten"),
    ("octal:three_bit_mapping", "explanation_selection"),
    ("hexadecimal:four_bit_mapping", "explanation_selection"),
    ("data_units:nibble", "byte_decomposition"),
    ("data_units:byte", "bit_count_easy"),
    ("data_units:byte_range", "byte_range"),
    ("metaconcept:hex_compact", "explanation_selection"),
)

TIER_TWO_BLUEPRINT: tuple[tuple[str, str], ...] = (
    ("octal:three_bit_mapping", "explanation_selection"),
    ("hexadecimal:four_bit_mapping", "explanation_selection"),
    ("octal:bin_to_oct", "guided_conversion"),
    ("octal:oct_to_bin", "guided_conversion"),
    ("hexadecimal:bin_to_hex", "guided_conversion"),
    ("hexadecimal:hex_to_bin", "guided_conversion"),
    ("data_units:nibble", "byte_decomposition"),
    ("metaconcept:hex_compact", "explanation_selection"),
)


class NumeralSystemsModule:
    metadata = TopicMetadata(
        topic_id="numeral_systems",
        version="1.0.0",
        title_key="topic.title",
        short_title_key="topic.short_title",
        description_key="topic.description",
        icon="🔢",
        daily_extended_actions=True,
    )

    def __init__(self) -> None:
        self.catalog = ContentCatalog(CONTENT_PATH)
        self._skills = skill_catalogue()
        self._skill_map = {item.skill_key: item for item in self._skills}

    def skills(self) -> tuple[SkillDefinition, ...]:
        return self._skills

    def practice_modes(self) -> tuple[PracticeModeDefinition, ...]:
        return (
            PracticeModeDefinition("quick", "mode.quick", "mode.quick.description", 5),
            PracticeModeDefinition("guided", "mode.guided", "mode.guided.description", 6),
            PracticeModeDefinition("deep", "mode.deep", "mode.deep.description", 8),
            PracticeModeDefinition(
                "binary_decimal", "mode.binary_decimal", "mode.binary_decimal.description", 8
            ),
            PracticeModeDefinition(
                "binary_octal", "mode.binary_octal", "mode.binary_octal.description", 8
            ),
            PracticeModeDefinition(
                "binary_hex", "mode.binary_hex", "mode.binary_hex.description", 8
            ),
            PracticeModeDefinition(
                "four_systems", "mode.four_systems", "mode.four_systems.description", 8
            ),
            PracticeModeDefinition(
                "bits_bytes", "mode.bits_bytes", "mode.bits_bytes.description", 8
            ),
            PracticeModeDefinition("colours", "mode.colours", "mode.colours.description", 8),
            PracticeModeDefinition(
                "characters", "mode.characters", "mode.characters.description", 8
            ),
            PracticeModeDefinition("weak", "mode.weak", "mode.weak.description", 8),
        )

    def test_definitions(self) -> tuple[TestDefinition, ...]:
        return (
            TestDefinition("foundations", "challenge.foundations", 10, "numeral_systems"),
            TestDefinition("binary_octal", "challenge.binary_octal", 10, "numeral_systems"),
            TestDefinition("binary_hex", "challenge.binary_hex", 12, "numeral_systems"),
            TestDefinition("four_systems", "challenge.four_systems", 15, "numeral_systems"),
            TestDefinition("bits_bytes", "challenge.bits_bytes", 10, "numeral_systems"),
            TestDefinition("rgb", "challenge.rgb", 12, "numeral_systems"),
            TestDefinition("characters", "challenge.characters", 10, "numeral_systems"),
            TestDefinition("final", "challenge.final", 20, "numeral_systems"),
        )

    def learning_units(self) -> tuple[LearningUnit, ...]:
        return (
            LearningUnit(
                "bases",
                "learn.bases.title",
                "learn.bases.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "foundation"),
                "place_values",
                "binary_decimal",
            ),
            LearningUnit(
                "binary",
                "learn.binary.title",
                "learn.binary.body",
                tuple(
                    item.skill_key for item in self._skills if item.group_key == "binary_decimal"
                ),
                "byte",
                "binary_decimal",
            ),
            LearningUnit(
                "octal",
                "learn.octal.title",
                "learn.octal.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "octal"),
                "grouping",
                "binary_octal",
            ),
            LearningUnit(
                "hex",
                "learn.hex.title",
                "learn.hex.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "hexadecimal"),
                "grouping",
                "binary_hex",
            ),
            LearningUnit(
                "decimal",
                "learn.decimal.title",
                "learn.decimal.body",
                (
                    "binary_decimal:dec_to_bin",
                    "octal:dec_to_oct",
                    "octal:oct_to_dec",
                    "hexadecimal:dec_to_hex",
                    "hexadecimal:hex_to_dec",
                ),
                related_practice_mode_id="four_systems",
            ),
            LearningUnit(
                "cross",
                "learn.cross.title",
                "learn.cross.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "cross_base"),
                "grouping",
                "four_systems",
            ),
            LearningUnit(
                "bytes",
                "learn.bytes.title",
                "learn.bytes.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "data_units"),
                "byte",
                "bits_bytes",
            ),
            LearningUnit(
                "rgb",
                "learn.rgb.title",
                "learn.rgb.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "rgb"),
                "rgb_channels",
                "colours",
            ),
            LearningUnit(
                "characters",
                "learn.characters.title",
                "learn.characters.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "characters"),
                "ascii_card",
                "characters",
            ),
            LearningUnit(
                "interpretation",
                "learn.interpretation.title",
                "learn.interpretation.body",
                tuple(item.skill_key for item in self._skills if item.group_key == "metaconcept"),
                "ascii_card",
                "deep",
            ),
            LearningUnit(
                "reference",
                "learn.reference.title",
                "learn.reference.body",
                (),
            ),
        )

    def render_learning_unit(self, unit_id: str) -> LearningView:
        unit = next((item for item in self.learning_units() if item.unit_id == unit_id), None)
        if unit is None:
            raise ValueError("unknown numeral-systems learning unit")
        payloads: dict[str, dict[str, Any]] = {
            "bases": {"digits": "2F", "base": 16},
            "binary": {"bits": "10110110"},
            "octal": {"bits": "1011011", "size": 3},
            "hex": {"bits": "10101111", "size": 4},
            "cross": {"bits": "111011", "size": 4},
            "bytes": {"bits": "11001010"},
            "rgb": {"red": 128, "green": 64, "blue": 255},
            "characters": {"bits": "01000001", "character": "A"},
            "interpretation": {"bits": "00110000", "character": "0"},
        }
        return LearningView(
            title=self.content(unit.title_key),
            body=self.content(unit.body_key),
            image_renderer_id=unit.image_renderer_id,
            image_payload=payloads.get(unit_id, {}),
        )

    def content(self, key: str, **values: object) -> str:
        return self.catalog.get(key, **values)

    def _eligible(
        self, mode_id: str, mastery: dict[str, MasteryState]
    ) -> tuple[SkillDefinition, ...]:
        if mode_id in {"quick", "guided", "deep"}:
            return self._skills
        if mode_id == "weak":
            attempted = tuple(
                item
                for item in self._skills
                if mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count > 0
                and mastery.get(item.skill_key, MasteryState(item.skill_key)).box < 4
            )
            return attempted or self._skills
        try:
            groups = MODE_GROUPS[mode_id]
        except KeyError as exc:
            raise ValueError(f"unknown numeral-systems practice mode: {mode_id}") from exc
        return tuple(item for item in self._skills if item.group_key in groups)

    def _select_skills(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> list[str]:
        eligible = self._eligible(mode_id, mastery)
        focus = str(configuration.get("focus_skill", ""))
        if focus in self._skill_map:
            related = [
                item.skill_key
                for item in eligible
                if item.group_key == self._skill_map[focus].group_key and item.skill_key != focus
            ]
            rng.shuffle(related)
            return [focus, *related, focus, *related][:question_count]
        keys = tuple(item.skill_key for item in eligible)
        ready = tuple(
            item.skill_key
            for item in eligible
            if not item.prerequisites
            or all(
                mastery.get(prerequisite, MasteryState(prerequisite)).box >= 2
                for prerequisite in item.prerequisites
            )
        )
        preview = tuple(key for key in keys if key not in ready)
        now = datetime.now(UTC)
        ordered = weighted_skill_order(ready, mastery, now, rng)
        ordered.extend(weighted_skill_order(preview, mastery, now, rng) if preview else [])

        if mode_id == "quick":
            quick_categories = (
                ("foundation", "binary_decimal"),
                ("octal", "hexadecimal", "cross_base"),
                ("foundation", "data_units", "metaconcept"),
                ("rgb", "characters"),
                ("rgb", "characters", "metaconcept"),
            )
            selected: list[str] = []
            for groups in quick_categories[:question_count]:
                candidates = [item.skill_key for item in eligible if item.group_key in groups]
                weighted = [item for item in ordered if item in candidates]
                selected.append(
                    next(
                        (item for item in weighted if item not in selected), rng.choice(candidates)
                    )
                )
            return selected
        if mode_id == "deep":
            deep_groups = (
                "foundation",
                "metaconcept",
                "binary_decimal",
                "octal",
                "hexadecimal",
                "cross_base",
                "rgb",
                "characters",
            )
            selected = []
            for group in deep_groups[:question_count]:
                candidates = [item.skill_key for item in eligible if item.group_key == group]
                weighted = [item for item in ordered if item in candidates]
                selected.append(
                    next(
                        (item for item in weighted if item not in selected), rng.choice(candidates)
                    )
                )
            return selected

        selected = []
        for key in ordered:
            if key not in selected:
                selected.append(key)
            if len(selected) == question_count:
                break
        while len(selected) < question_count:
            selected.append(rng.choice(list(keys)))
        return selected

    def session_blueprint(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> tuple[tuple[str, str], ...]:
        if not configuration.get("focus_skill") and mode_id in {"quick", "guided"}:
            source = list(TIER_ONE_BLUEPRINT if mode_id == "quick" else TIER_TWO_BLUEPRINT)
            rng.shuffle(source)
            return tuple(source[index % len(source)] for index in range(question_count))
        selected = self._select_skills(mode_id, question_count, mastery, configuration, rng)
        blueprint: list[tuple[str, str]] = []
        previous_type = ""
        conversion_run = 0
        for index, skill_key in enumerate(selected):
            choices = list(QUESTION_TYPES[skill_key])
            rng.shuffle(choices)
            question_type = choices[index % len(choices)]
            if question_type == previous_type and len(choices) > 1:
                question_type = choices[1]
            is_conversion = question_type in {
                "direct_conversion",
                "cross_conversion",
                "mixed_transformation",
                "construct_representation",
            }
            conversion_run = conversion_run + 1 if is_conversion else 0
            if conversion_run >= 4 and len(choices) > 1:
                conceptual = next(
                    (
                        item
                        for item in choices
                        if item not in {"direct_conversion", "cross_conversion"}
                    ),
                    question_type,
                )
                question_type = conceptual
                conversion_run = 0
            blueprint.append((skill_key, question_type))
            previous_type = question_type
        return tuple(blueprint)

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]:
        del configuration
        blueprints: dict[str, list[tuple[str, str]]] = {
            "foundations": [
                ("foundation:representation_value", "equivalent_representation"),
                ("foundation:positional_value", "positional_expansion"),
                ("foundation:powers", "positional_expansion"),
                ("foundation:valid_digits", "base_identification"),
                ("foundation:meaning_ten", "meaning_ten"),
                ("binary_decimal:bin_to_dec", "direct_conversion"),
                ("binary_decimal:dec_to_bin", "direct_conversion"),
                ("binary_decimal:binary_addition", "binary_addition"),
                ("cross_base:compare", "comparison"),
                ("metaconcept:same_value", "interpretation"),
            ],
            "binary_octal": [
                *([("octal:bin_to_oct", "direct_conversion")] * 3),
                *([("octal:oct_to_bin", "direct_conversion")] * 3),
                ("octal:three_bit_mapping", "explanation_selection"),
                ("octal:three_bit_mapping", "method_selection"),
                ("octal:dec_to_oct", "direct_conversion"),
                ("octal:bin_to_oct", "error_detection"),
            ],
            "binary_hex": [
                *([("hexadecimal:bin_to_hex", "direct_conversion")] * 4),
                *([("hexadecimal:hex_to_bin", "direct_conversion")] * 3),
                ("hexadecimal:dec_to_hex", "direct_conversion"),
                ("hexadecimal:hex_to_dec", "direct_conversion"),
                ("data_units:nibble", "byte_decomposition"),
                ("data_units:byte", "bit_count"),
                ("hexadecimal:four_bit_mapping", "explanation_selection"),
            ],
            "four_systems": [
                ("binary_decimal:bin_to_dec", "direct_conversion"),
                ("binary_decimal:dec_to_bin", "direct_conversion"),
                ("octal:bin_to_oct", "direct_conversion"),
                ("octal:oct_to_bin", "direct_conversion"),
                ("hexadecimal:bin_to_hex", "direct_conversion"),
                ("hexadecimal:hex_to_bin", "direct_conversion"),
                ("octal:dec_to_oct", "direct_conversion"),
                ("hexadecimal:dec_to_hex", "direct_conversion"),
                ("cross_base:oct_to_hex", "cross_conversion"),
                ("cross_base:hex_to_oct", "cross_conversion"),
                ("cross_base:equivalent", "equivalent_representation"),
                ("cross_base:compare", "comparison"),
                ("cross_base:efficient_route", "method_selection"),
                ("foundation:positional_value", "missing_digit"),
                ("cross_base:efficient_route", "error_detection"),
            ],
            "bits_bytes": [
                ("data_units:bit", "bit_count"),
                ("data_units:nibble", "byte_decomposition"),
                ("data_units:byte", "byte_decomposition"),
                ("data_units:patterns", "bit_count"),
                ("data_units:patterns", "bit_count"),
                ("data_units:byte_range", "byte_range"),
                ("data_units:byte_range", "error_detection"),
                ("data_units:leading_zeroes", "construct_representation"),
                ("hexadecimal:bin_to_hex", "direct_conversion"),
                ("metaconcept:hex_compact", "explanation_selection"),
            ],
            "rgb": [
                ("rgb:channels", "colour_recognition"),
                ("rgb:dec_to_hex", "direct_conversion"),
                ("rgb:dec_to_hex", "direct_conversion"),
                ("rgb:hex_to_dec", "direct_conversion"),
                ("rgb:hex_to_dec", "direct_conversion"),
                ("rgb:complete_code", "rgb_channel"),
                ("rgb:complete_code", "rgb_channel"),
                ("rgb:visual", "colour_recognition"),
                ("rgb:visual", "colour_recognition"),
                ("rgb:binary", "rgb_binary"),
                ("rgb:channels", "error_detection"),
                ("rgb:binary", "rgb_binary"),
            ],
            "characters": [
                ("characters:assigned_code", "interpretation"),
                ("characters:decimal", "character_code"),
                ("characters:hex", "character_code"),
                ("characters:binary", "character_code"),
                ("characters:code_to_char", "character_code"),
                ("characters:decode", "character_code"),
                ("characters:numeric_vs_char", "interpretation"),
                ("characters:numeric_vs_char", "same_bits_different_meanings"),
                ("metaconcept:bits_interpretation", "interpretation"),
                ("metaconcept:same_bits", "same_bits_different_meanings"),
            ],
        }
        final = [
            ("foundation:representation_value", "equivalent_representation"),
            ("foundation:valid_digits", "base_identification"),
            ("metaconcept:hex_compact", "explanation_selection"),
            ("binary_decimal:bin_to_dec", "direct_conversion"),
            ("binary_decimal:dec_to_bin", "direct_conversion"),
            ("octal:bin_to_oct", "direct_conversion"),
            ("octal:oct_to_bin", "direct_conversion"),
            ("hexadecimal:bin_to_hex", "direct_conversion"),
            ("hexadecimal:hex_to_bin", "direct_conversion"),
            ("cross_base:oct_to_hex", "cross_conversion"),
            ("cross_base:hex_to_oct", "cross_conversion"),
            ("data_units:patterns", "bit_count"),
            ("data_units:byte_range", "byte_range"),
            ("rgb:complete_code", "rgb_channel"),
            ("rgb:visual", "colour_recognition"),
            ("rgb:binary", "rgb_binary"),
            ("characters:hex", "character_code"),
            ("characters:binary", "character_code"),
            ("characters:code_to_char", "character_code"),
            ("metaconcept:same_bits", "same_bits_different_meanings"),
        ]
        blueprints["final"] = final
        try:
            result = blueprints[test_id]
        except KeyError as exc:
            raise ValueError(f"unknown numeral-systems challenge: {test_id}") from exc
        rng.shuffle(result)
        return tuple(result)

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion:
        if skill_key not in self._skill_map:
            raise ValueError(f"unknown numeral-systems skill: {skill_key}")
        return generate(skill_key, question_type, rng)

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult:
        correct = question_payload["correct_answer"]
        actual = str(selected_answer.get("value", "")).upper()
        expected = str(correct.get("value", "")).upper()
        metadata = question_payload.get("metadata", {})
        if not metadata.get("fixed_width") and metadata.get("target_base"):
            actual = actual.lstrip("0") or "0"
            expected = expected.lstrip("0") or "0"
        is_correct = actual == expected
        explanation = question_payload["explanation_payload"]
        return EvaluationResult(
            is_correct=is_correct,
            canonical_answer=correct,
            feedback_key="feedback.correct" if is_correct else "feedback.incorrect",
            feedback_payload={
                "equation": explanation["equation"],
                "misconception": explanation.get("misconception", ""),
            },
        )

    def retry_question_type(self, skill_key: str, question_type: str, rng: Random) -> str:
        if question_type == "guided_conversion":
            return "guided_conversion_pad"
        if question_type == "guided_conversion_pad":
            return "guided_conversion"
        try:
            choices = QUESTION_TYPES[skill_key]
        except KeyError as exc:
            raise ValueError(f"unknown numeral-systems skill: {skill_key}") from exc
        alternatives = [item for item in choices if item != question_type]
        return rng.choice(alternatives or list(choices))

    def progress_view(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> TopicProgressView:
        groups: list[ProgressGroup] = []
        for group_key, label in GROUP_LABELS.items():
            keys = [item.skill_key for item in self._skills if item.group_key == group_key]
            percentage = round(
                sum(mastery.get(key, MasteryState(key)).box for key in keys) / (len(keys) * 5) * 100
            )
            groups.append(ProgressGroup(label, percentage))
        mastered = [
            item
            for item in self._skills
            if self._is_mastered(mastery.get(item.skill_key, MasteryState(item.skill_key)))
        ]
        ranked_targets = sorted(
            self._skills,
            key=lambda item: (
                mastery.get(item.skill_key, MasteryState(item.skill_key)).box,
                -mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count,
                item.difficulty,
            ),
        )
        targets = tuple(
            ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
            for item in ranked_targets[:3]
        )
        strengths = tuple(
            ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
            for item in mastered[:3]
        )
        stage = next((group.label for group in groups if group.percentage < 60), groups[-1].label)
        return TopicProgressView(
            headline_metrics=(
                Metric("Total tasks", str(int(metrics.get("total", 0)))),
                Metric("Active days", str(int(metrics.get("active_days", 0)))),
                Metric("Recent accuracy", f"{int(metrics.get('accuracy', 0))}%"),
                Metric("Concepts mastered", str(len(mastered))),
                Metric("Current learning stage", stage),
            ),
            progress_groups=tuple(groups),
            strengths=strengths,
            current_targets=targets,
            suggested_action=SuggestedAction("Practise developing concepts", "practice:weak"),
        )

    @staticmethod
    def _is_mastered(state: MasteryState) -> bool:
        formats = {str(item) for item in state.state.get("correct_formats", [])}
        return is_mastered(state) and len(formats) >= 2

    def test_result_metrics(self, attempts: tuple[dict[str, Any], ...]) -> tuple[Metric, ...]:
        result: list[Metric] = []
        for group_key, label in GROUP_LABELS.items():
            relevant = [
                item
                for item in attempts
                if self._skill_map[str(item["skill_key"])].group_key == group_key
            ]
            if relevant:
                accuracy = round(
                    sum(bool(item["is_correct"]) for item in relevant) / len(relevant) * 100
                )
                result.append(Metric(label, f"{accuracy}%"))
        return tuple(result)

    def teacher_insights(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> tuple[ProgressItem, ...]:
        misconceptions: dict[str, int] = {}
        for state in mastery.values():
            for label, count in dict(state.state.get("misconceptions", {})).items():
                misconceptions[str(label)] = misconceptions.get(str(label), 0) + int(count)
        ranked = sorted(misconceptions.items(), key=lambda item: (-item[1], item[0]))[:3]
        notes = [
            ProgressItem("Hints used", str(int(metrics.get("hints", 0)))),
            ProgressItem("Daily tasks in 7 days", str(int(metrics.get("daily", 0)))),
        ]
        notes.extend(ProgressItem(label, f"{count} observed") for label, count in ranked)
        if ranked:
            procedural_words = ("groups", "digit", "width", "route", "channel")
            procedural = sum(
                count for label, count in ranked if any(word in label for word in procedural_words)
            )
            kind = (
                "mostly procedural"
                if procedural >= sum(count for _, count in ranked) / 2
                else "mostly conceptual"
            )
            notes.append(ProgressItem("Recent mistake pattern", kind))
        return tuple(notes)

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]:
        pools: tuple[dict[str, str], ...] = (
            {
                "foundation:meaning_ten": "meaning_ten",
                "foundation:valid_digits": "base_identification",
                "hexadecimal:four_bit_mapping": "explanation_selection",
                "cross_base:equivalent": "equivalent_representation",
            },
            {
                "octal:bin_to_oct": "guided_conversion",
                "octal:oct_to_bin": "guided_conversion",
                "hexadecimal:bin_to_hex": "guided_conversion",
                "hexadecimal:hex_to_bin": "guided_conversion",
            },
            {
                "data_units:patterns": "bit_count_easy",
                "data_units:byte_range": "byte_range",
                "data_units:nibble": "byte_decomposition",
                "rgb:visual": "colour_recognition",
            },
            {
                "characters:numeric_vs_char": "interpretation",
                "metaconcept:bits_interpretation": "interpretation",
                "metaconcept:same_bits": "same_bits_different_meanings",
                "characters:code_to_char": "character_code",
            },
        )
        pool = pools[now.date().toordinal() % len(pools)]
        ordered = weighted_skill_order(tuple(pool), mastery, now, rng)
        skill = ordered[0]
        return skill, pool[skill]

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes:
        return images.render(renderer_id, payload)

    def validate(self) -> list[str]:
        errors = validate_topic_contract(self)
        if len(self.practice_modes()) != 11:
            errors.append("all eleven numeral-systems practice modes are required")
        if len(self.test_definitions()) != 8:
            errors.append("all eight numeral-systems challenges are required")
        required_types = {
            "positional_expansion": "foundation:positional_value",
            "base_identification": "foundation:valid_digits",
            "direct_conversion": "binary_decimal:bin_to_dec",
            "guided_conversion": "octal:bin_to_oct",
            "guided_conversion_pad": "hexadecimal:hex_to_bin",
            "cross_conversion": "cross_base:oct_to_hex",
            "equivalent_representation": "cross_base:equivalent",
            "comparison": "cross_base:compare",
            "missing_digit": "foundation:positional_value",
            "error_detection": "foundation:valid_digits",
            "method_selection": "cross_base:efficient_route",
            "explanation_selection": "hexadecimal:four_bit_mapping",
            "bit_count": "data_units:patterns",
            "bit_count_easy": "data_units:bit",
            "byte_range": "data_units:byte_range",
            "byte_decomposition": "data_units:nibble",
            "rgb_channel": "rgb:complete_code",
            "colour_recognition": "rgb:visual",
            "rgb_binary": "rgb:binary",
            "character_code": "characters:hex",
            "interpretation": "characters:numeric_vs_char",
            "same_bits_different_meanings": "metaconcept:same_bits",
            "mixed_transformation": "cross_base:oct_to_hex",
            "construct_representation": "data_units:leading_zeroes",
        }
        for index, (question_type, skill_key) in enumerate(required_types.items()):
            try:
                question = self.generate_question(skill_key, question_type, Random(index + 1))
                validate_options(question.answer_mode, question.answer_options)
            except Exception as exc:
                errors.append(f"{question_type} generation failed: {exc}")
        for definition in self.test_definitions():
            try:
                if (
                    len(self.test_blueprint(definition.test_id, {}, Random(1)))
                    != definition.question_count
                ):
                    errors.append(f"{definition.test_id} challenge has the wrong length")
            except Exception as exc:
                errors.append(f"{definition.test_id} challenge failed: {exc}")
        media_samples: dict[str, dict[str, Any]] = {
            "grouping": {"bits": "1011011", "size": 3},
            "place_values": {"digits": "2F", "base": 16},
            "byte": {"bits": "11001010"},
            "rgb_swatch": {"hex": "8040FF"},
            "rgb_channels": {"red": 128, "green": 64, "blue": 255},
            "ascii_card": {"bits": "01000001", "character": "A"},
        }
        for renderer_id, payload in media_samples.items():
            try:
                self.render_media(renderer_id, payload)
            except Exception as exc:
                errors.append(f"{renderer_id} renderer failed: {exc}")
        return errors
