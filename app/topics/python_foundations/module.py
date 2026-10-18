from __future__ import annotations

import builtins
import io
from contextlib import redirect_stdout
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from random import Random
from typing import Any

from app.content.loader import ContentCatalog
from app.core.mastery.engine import is_mastered
from app.core.mastery.selection import weighted_skill_order
from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import (
    AnswerOption,
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
from app.topics.python_foundations.questions import (
    CONCEPTS,
    QUESTION_TYPES,
    STDOUT_SKILLS,
    question_parts,
)
from app.topics.python_foundations.skills import (
    GROUP_LABELS,
    skill_catalogue,
    skill_label,
)

CONTENT_PATH = Path(__file__).with_name("content") / "strings.yaml"


LEARNING_SPECS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("diagnostic", ("PY.EXEC.ORDER", "PY.EXEC.DEF_VS_CALL", "PY.INDENTATION"), "diagnostic"),
    (
        "values",
        (
            "PY.VAR.ASSIGN",
            "PY.VAR.UPDATE",
            "PY.TYPE.INT",
            "PY.TYPE.FLOAT",
            "PY.TYPE.STRING",
            "PY.TYPE.BOOL",
            "PY.TYPE.COLLECTIONS",
        ),
        "quick",
    ),
    ("io", ("PY.IO.PRINT", "PY.IO.FSTRING", "PY.IO.INPUT", "PY.IO.CONVERSION"), "predict_output"),
    (
        "conditions",
        (
            "PY.OP.ARITHMETIC",
            "PY.OP.COMPARISON",
            "PY.OP.BOOLEAN",
            "PY.IF.BASIC",
            "PY.IF.ELIF",
            "PY.IF.NESTED",
        ),
        "trace_program",
    ),
    (
        "loops",
        ("PY.LOOP.WHILE", "PY.LOOP.UPDATE", "PY.LOOP.BREAK", "PY.LOOP.FOR_RANGE"),
        "trace_program",
    ),
    ("modulo", ("PY.OP.MODULO",), "mini_script"),
    (
        "functions",
        (
            "PY.FUNC.DEFINE",
            "PY.FUNC.CALL",
            "PY.FUNC.PARAMETER",
            "PY.FUNC.RETURN",
            "PY.FUNC.PRINT_VS_RETURN",
        ),
        "predict_output",
    ),
    (
        "randomness",
        ("PY.IMPORT.BASIC", "PY.RANDOM.RANDINT", "PY.RANDOM.CHOICE"),
        "quick",
    ),
    (
        "collections",
        ("PY.DICT.BASIC", "PY.DICT.ITEMS", "PY.TUPLE.BASIC", "PY.UNPACKING"),
        "trace_program",
    ),
    (
        "classes",
        ("PY.CLASS.CLASS_VS_OBJECT", "PY.CLASS.INIT", "PY.CLASS.SELF"),
        "quick",
    ),
    (
        "methods",
        (
            "PY.CLASS.ATTRIBUTE",
            "PY.CLASS.METHOD",
            "PY.CLASS.MULTIPLE_OBJECTS",
            "PY.CLASS.STATE_CHANGE",
            "PY.CLASS.SELF_OTHER",
        ),
        "trace_program",
    ),
    ("terminology", ("PY.IMPORT.BASIC", "PY.CLASS.SELF"), "quick"),
    ("lab1_init", ("GAME.PLAYER_STATE",), "fighting_lab"),
    ("lab2_weapons", ("GAME.WEAPON_SELECTION",), "fighting_lab"),
    ("lab3_attack", ("PY.CLASS.SELF_OTHER", "PY.CLASS.STATE_CHANGE"), "fighting_lab"),
    ("lab4_armor", ("GAME.ARMOR_DAMAGE",), "fighting_lab"),
    ("lab5_objects", ("GAME.PLAYER_STATE", "PY.CLASS.MULTIPLE_OBJECTS"), "fighting_lab"),
    ("lab6_loop", ("GAME.STRUCTURE", "GAME.MAIN_LOOP"), "fighting_lab"),
    ("lab7_initiative", ("GAME.INITIATIVE",), "fighting_lab"),
    ("lab8_refactor", ("GAME.DEBUG_INITIATIVE",), "fix_bug"),
    ("lab9_critical", ("GAME.CRITICAL_COUNTER",), "mini_script"),
    ("d20", ("PY.FUNC.RETURN", "PY.RANDOM.RANDINT"), "mini_script"),
)


ALL_SKILLS = tuple(CONCEPTS)
GAME_SKILLS = tuple(key for key in ALL_SKILLS if key.startswith("GAME."))
TRACE_SKILLS = tuple(
    key
    for key in ALL_SKILLS
    if key.startswith("GAME.")
    or key.startswith("PY.EXEC")
    or ".LOOP." in key
    or key
    in {
        "PY.VAR.UPDATE",
        "PY.IF.BASIC",
        "PY.IF.ELIF",
        "PY.IF.NESTED",
        "PY.FUNC.CALL",
        "PY.FUNC.PARAMETER",
        "PY.FUNC.RETURN",
        "PY.CLASS.ATTRIBUTE",
        "PY.CLASS.STATE_CHANGE",
        "PY.CLASS.SELF_OTHER",
        "PY.UNPACKING",
    }
)
BUG_SKILLS = (
    "PY.EXEC.DEF_VS_CALL",
    "PY.INDENTATION",
    "PY.IO.CONVERSION",
    "PY.OP.COMPARISON",
    "PY.LOOP.UPDATE",
    "PY.FUNC.PRINT_VS_RETURN",
    "PY.CLASS.SELF",
    "PY.CLASS.MULTIPLE_OBJECTS",
    "PY.CLASS.SELF_OTHER",
    "GAME.ARMOR_DAMAGE",
    "GAME.DEBUG_INITIATIVE",
    "GAME.CRITICAL_COUNTER",
)
MINI_SCRIPT_SKILLS = (
    "PY.IO.PRINT",
    "PY.IO.FSTRING",
    "PY.IO.INPUT",
    "PY.IO.CONVERSION",
    "PY.IF.BASIC",
    "PY.LOOP.WHILE",
    "PY.LOOP.FOR_RANGE",
    "PY.FUNC.DEFINE",
    "PY.FUNC.CALL",
    "PY.FUNC.PARAMETER",
    "PY.FUNC.RETURN",
    "PY.RANDOM.RANDINT",
    "PY.DICT.BASIC",
    "PY.CLASS.INIT",
    "PY.CLASS.METHOD",
    "PY.CLASS.STATE_CHANGE",
    "GAME.CRITICAL_COUNTER",
)
FIGHTING_LAB_SKILLS = (
    "PY.DICT.BASIC",
    "PY.DICT.ITEMS",
    "PY.TUPLE.BASIC",
    "PY.UNPACKING",
    "PY.CLASS.SELF",
    "PY.CLASS.ATTRIBUTE",
    "PY.CLASS.METHOD",
    "PY.CLASS.MULTIPLE_OBJECTS",
    "PY.CLASS.STATE_CHANGE",
    "PY.CLASS.SELF_OTHER",
    *GAME_SKILLS,
)
DIAGNOSTIC_SKILLS = (
    "PY.EXEC.ORDER",
    "PY.EXEC.DEF_VS_CALL",
    "PY.VAR.UPDATE",
    "PY.IO.PRINT",
    "PY.OP.COMPARISON",
    "PY.IF.BASIC",
    "PY.LOOP.WHILE",
    "PY.FUNC.CALL",
    "PY.FUNC.PRINT_VS_RETURN",
    "PY.DICT.BASIC",
    "PY.UNPACKING",
    "PY.CLASS.CLASS_VS_OBJECT",
    "PY.CLASS.SELF",
    "PY.CLASS.SELF_OTHER",
    "GAME.STRUCTURE",
    "GAME.ARMOR_DAMAGE",
)


MODE_SKILLS: dict[str, tuple[str, ...]] = {
    "diagnostic": DIAGNOSTIC_SKILLS,
    "quick": ALL_SKILLS,
    "predict_output": STDOUT_SKILLS,
    "trace_program": TRACE_SKILLS,
    "fix_bug": BUG_SKILLS,
    "mini_script": MINI_SCRIPT_SKILLS,
    "fighting_lab": FIGHTING_LAB_SKILLS,
    "mixed_review": ALL_SKILLS,
    "challenge": tuple(
        key for key in ALL_SKILLS if skill_catalogue()[ALL_SKILLS.index(key)].difficulty >= 4
    ),
    "weak": ALL_SKILLS,
}


class PythonFoundationsModule:
    metadata = TopicMetadata(
        topic_id="python_foundations",
        version="1.0.0",
        title_key="topic.title",
        short_title_key="topic.short_title",
        description_key="topic.description",
        icon="🐍",
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
            PracticeModeDefinition(
                "diagnostic", "mode.diagnostic", "mode.diagnostic.description", 12
            ),
            PracticeModeDefinition("quick", "mode.quick", "mode.quick.description", 6),
            PracticeModeDefinition(
                "predict_output", "mode.predict_output", "mode.predict_output.description", 8
            ),
            PracticeModeDefinition(
                "trace_program", "mode.trace_program", "mode.trace_program.description", 8
            ),
            PracticeModeDefinition("fix_bug", "mode.fix_bug", "mode.fix_bug.description", 8),
            PracticeModeDefinition(
                "mini_script", "mode.mini_script", "mode.mini_script.description", 6
            ),
            PracticeModeDefinition(
                "fighting_lab", "mode.fighting_lab", "mode.fighting_lab.description", 8
            ),
            PracticeModeDefinition(
                "mixed_review", "mode.mixed_review", "mode.mixed_review.description", 8
            ),
            PracticeModeDefinition("challenge", "mode.challenge", "mode.challenge.description", 12),
            PracticeModeDefinition("weak", "mode.weak", "mode.weak.description", 8),
        )

    def test_definitions(self) -> tuple[TestDefinition, ...]:
        return (
            TestDefinition("foundations", "challenge.foundations", 15, "python_foundations"),
            TestDefinition("functions_data", "challenge.functions_data", 15, "python_foundations"),
            TestDefinition("objects", "challenge.objects", 14, "python_foundations"),
            TestDefinition("fighting", "challenge.fighting", 15, "python_foundations"),
        )

    def learning_units(self) -> tuple[LearningUnit, ...]:
        return tuple(
            LearningUnit(
                unit_id=unit_id,
                title_key=f"learn.{unit_id}.title",
                body_key=f"learn.{unit_id}.body",
                skill_keys=skills,
                related_practice_mode_id=mode_id,
            )
            for unit_id, skills, mode_id in LEARNING_SPECS
        )

    def content(self, key: str, **values: object) -> str:
        try:
            return self.catalog.get(key, **values)
        except KeyError:
            for skill in self._skills:
                if key == skill.title_key:
                    return skill_label(skill.skill_key)
                if key == skill.description_key:
                    return f"Practise how to {skill_label(skill.skill_key).lower()}."
            raise

    def render_learning_unit(self, unit_id: str) -> LearningView:
        unit = next((item for item in self.learning_units() if item.unit_id == unit_id), None)
        if unit is None:
            raise ValueError("unknown Python Foundations learning unit")
        return LearningView(
            title=self.content(unit.title_key),
            body=self.content(unit.body_key),
            related_text=self.content("learn.cycle"),
            practice_configuration={"focus_skill": unit.skill_keys[0]},
        )

    def session_blueprint(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> tuple[tuple[str, str], ...]:
        try:
            mode_candidates = MODE_SKILLS[mode_id]
        except KeyError as exc:
            raise ValueError(f"unknown Python Foundations mode: {mode_id}") from exc
        if question_count < 1:
            raise ValueError("question_count must be positive")
        focus_value = configuration.get("focus_skill")
        focus = str(focus_value) if focus_value is not None else None
        if focus is not None and focus not in self._skill_map:
            raise ValueError("unknown focus skill")

        if mode_id == "diagnostic":
            candidates = mode_candidates
        else:
            unlocked = set(self._unlocked_skills(mastery))
            if mode_id == "weak":
                candidates = tuple(
                    key
                    for key in mode_candidates
                    if key in unlocked
                    and mastery.get(key, MasteryState(key)).attempt_count > 0
                    and not self._is_mastered_key(key, mastery.get(key, MasteryState(key)))
                )
            else:
                candidates = tuple(key for key in mode_candidates if key in unlocked)
            if not candidates:
                candidates = tuple(key for key in mode_candidates if key in unlocked)
            if not candidates:
                candidates = mode_candidates[:1]

        ordered = self._adaptive_order(candidates, mastery, rng)
        chosen: list[str] = []
        if focus is not None and focus in mode_candidates:
            target = self._nearest_ready_target(focus, mastery)
            if target in mode_candidates:
                chosen.append(target)
        for key in ordered:
            if key not in chosen:
                chosen.append(key)
        while len(chosen) < question_count:
            chosen.append(candidates[len(chosen) % len(candidates)])

        forced_type = {
            "predict_output": "predict",
            "fix_bug": "apply",
            "mini_script": "apply",
        }.get(mode_id)
        result: list[tuple[str, str]] = []
        format_counts: dict[str, int] = {}
        for index, skill_key in enumerate(chosen[:question_count]):
            if forced_type is not None:
                question_type = forced_type
            elif mode_id == "diagnostic":
                question_type = QUESTION_TYPES[index % len(QUESTION_TYPES)]
            elif mode_id == "challenge":
                question_type = ("predict", "apply")[index % 2]
            else:
                seen = {
                    str(value)
                    for value in mastery.get(skill_key, MasteryState(skill_key)).state.get(
                        "correct_formats", []
                    )
                }
                untried = [kind for kind in QUESTION_TYPES if kind not in seen]
                if untried:
                    question_type = untried[format_counts.get(skill_key, 0) % len(untried)]
                else:
                    question_type = rng.choice(QUESTION_TYPES)
            format_counts[skill_key] = format_counts.get(skill_key, 0) + 1
            result.append((skill_key, question_type))
        return tuple(result)

    def _unlocked_skills(self, mastery: dict[str, MasteryState]) -> tuple[str, ...]:
        if not any(state.attempt_count for state in mastery.values()):
            return tuple(item.skill_key for item in self._skills[:10])
        return tuple(
            item.skill_key
            for item in self._skills
            if all(mastery.get(key, MasteryState(key)).box >= 2 for key in item.prerequisites)
        )

    def _nearest_ready_target(self, skill_key: str, mastery: dict[str, MasteryState]) -> str:
        target = skill_key
        visited: set[str] = set()
        while target not in visited:
            visited.add(target)
            missing = [
                key
                for key in self._skill_map[target].prerequisites
                if mastery.get(key, MasteryState(key)).box < 2
            ]
            if not missing:
                return target
            target = missing[0]
        return skill_key

    def _adaptive_order(
        self,
        candidates: tuple[str, ...],
        mastery: dict[str, MasteryState],
        rng: Random,
    ) -> list[str]:
        weighted = weighted_skill_order(candidates, mastery, datetime.now(UTC), rng)
        unique: list[str] = []
        for key in weighted:
            if key not in unique:
                unique.append(key)
        curriculum_target = next(
            (
                key
                for key in candidates
                if not self._is_mastered_key(key, mastery.get(key, MasteryState(key)))
            ),
            None,
        )
        if curriculum_target is not None:
            unique.remove(curriculum_target)
            unique.insert(0, curriculum_target)
        return unique

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]:
        del configuration
        blueprints: dict[str, tuple[tuple[str, str], ...]] = {
            "foundations": tuple(
                (key, QUESTION_TYPES[index % 3]) for index, key in enumerate(ALL_SKILLS[:15])
            ),
            "functions_data": tuple(
                (key, ("predict", "apply")[index % 2])
                for index, key in enumerate(ALL_SKILLS[18:33])
            ),
            "objects": tuple(
                (key, ("recognize", "predict", "apply")[index % 3])
                for index, key in enumerate(ALL_SKILLS[33:45])
            )
            + (("PY.CLASS.SELF_OTHER", "predict"), ("PY.CLASS.STATE_CHANGE", "apply")),
            "fighting": tuple(
                (
                    GAME_SKILLS[index % len(GAME_SKILLS)],
                    ("recognize", "predict", "apply")[index % 3],
                )
                for index in range(15)
            ),
        }
        try:
            result = list(blueprints[test_id])
        except KeyError as exc:
            raise ValueError(f"unknown Python Foundations challenge: {test_id}") from exc
        rng.shuffle(result)
        return tuple(result)

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion:
        if skill_key not in self._skill_map:
            raise ValueError(f"unknown Python Foundations skill: {skill_key}")
        if question_type not in QUESTION_TYPES:
            raise ValueError(f"question type {question_type} does not fit {skill_key}")
        parts = question_parts(skill_key, question_type)
        indexed = list(enumerate(parts.answers))
        rng.shuffle(indexed)
        options = tuple(
            AnswerOption(label=label, value={"value": f"answer_{index}"})
            for index, label in indexed
        )
        validate_options("single_choice", options)
        metadata: dict[str, Any] = {
            "hints": list(parts.hints),
            "misconception": parts.misconception,
            "difficulty_level": parts.difficulty_level,
            "question_format": (
                "stdout"
                if parts.stdout_code
                else "debug"
                if question_type == "apply" and skill_key in BUG_SKILLS
                else "construction"
                if question_type == "apply"
                else question_type
            ),
        }
        if '<pre><code class="language-python">' in parts.prompt:
            metadata["prompt_format"] = "html"
        if parts.stdout_code is not None:
            metadata.update(
                {
                    "validated_stdout": True,
                    "stdout_code": parts.stdout_code,
                    "stdout_inputs": list(parts.stdout_inputs),
                    "stdout_expected": parts.stdout_expected,
                }
            )
        return GeneratedQuestion(
            topic_id=self.metadata.topic_id,
            skill_key=skill_key,
            question_type=question_type,
            rendered_prompt=parts.prompt,
            answer_mode="single_choice",
            answer_options=options,
            correct_answer={"value": "answer_0"},
            explanation_payload={
                "explanation": parts.explanation,
                "equation": parts.explanation,
            },
            metadata=metadata,
        )

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult:
        correct_answer = dict(question_payload["correct_answer"])
        is_correct = selected_answer.get("value") == correct_answer.get("value")
        explanation = str(question_payload["explanation_payload"]["explanation"])
        metadata = dict(question_payload.get("metadata", {}))
        hints = [str(value) for value in metadata.get("hints", [])][:3]
        return EvaluationResult(
            is_correct=is_correct,
            canonical_answer=correct_answer,
            feedback_key="feedback.correct" if is_correct else "feedback.incorrect",
            feedback_payload={
                "equation": explanation
                if is_correct
                else "That choice does not match the value flow or rule in this example.",
                "misconception": "" if is_correct else str(metadata.get("misconception", "")),
            },
            hint_key=None if is_correct else "feedback.hint",
            hint_payload=None
            if is_correct
            else {"hint": hints[0] if hints else "Trace one executed step at a time."},
        )

    def retry_question_type(self, skill_key: str, question_type: str, rng: Random) -> str:
        if skill_key not in self._skill_map:
            raise ValueError(f"unknown Python Foundations skill: {skill_key}")
        alternatives = [kind for kind in QUESTION_TYPES if kind != question_type]
        return rng.choice(alternatives)

    def progress_view(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> TopicProgressView:
        groups: list[ProgressGroup] = []
        for group_key, label in GROUP_LABELS.items():
            keys = [item.skill_key for item in self._skills if item.group_key == group_key]
            percentage = round(
                sum(mastery.get(key, MasteryState(key)).box for key in keys) / (len(keys) * 5) * 100
            )
            groups.append(
                ProgressGroup(
                    label,
                    percentage,
                    tuple(
                        ProgressItem(
                            skill_label(key),
                            f"{mastery.get(key, MasteryState(key)).box}/5",
                            key,
                        )
                        for key in keys
                    ),
                )
            )
        mastered = [
            item
            for item in self._skills
            if self._is_mastered_key(
                item.skill_key, mastery.get(item.skill_key, MasteryState(item.skill_key))
            )
        ]
        targets = sorted(
            self._skills,
            key=lambda item: (
                0 if item.skill_key in self._unlocked_skills(mastery) else 1,
                mastery.get(item.skill_key, MasteryState(item.skill_key)).box,
                -mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count,
                item.difficulty,
            ),
        )[:3]
        return TopicProgressView(
            headline_metrics=(
                Metric("Answers", str(int(metrics.get("total", 0)))),
                Metric("Answers in 7 days", str(int(metrics.get("recent", 0)))),
                Metric("Recent accuracy", f"{int(metrics.get('accuracy', 0))}%"),
                Metric("Mastered skills", str(len(mastered))),
                Metric("Practice days", str(int(metrics.get("active_days", 0)))),
            ),
            progress_groups=tuple(groups),
            strengths=tuple(
                ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
                for item in mastered[:4]
            ),
            current_targets=tuple(
                ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
                for item in targets
            ),
            suggested_action=SuggestedAction("Continue adaptive practice", "practice:quick"),
        )

    @staticmethod
    def _important_skill(skill_key: str) -> bool:
        return skill_key.startswith(("PY.FUNC.", "PY.CLASS.", "GAME."))

    def _is_mastered_key(self, skill_key: str, state: MasteryState) -> bool:
        formats = {str(item) for item in state.state.get("correct_formats", [])}
        if not is_mastered(state) or len(formats) < 2:
            return False
        return not self._important_skill(skill_key) or (
            "apply" in formats and bool({"recognize", "predict"}.intersection(formats))
        )

    def test_result_metrics(self, attempts: tuple[dict[str, Any], ...]) -> tuple[Metric, ...]:
        result: list[Metric] = []
        for group_key, label in GROUP_LABELS.items():
            relevant = [
                attempt
                for attempt in attempts
                if self._skill_map[str(attempt["skill_key"])].group_key == group_key
            ]
            if relevant:
                correct = sum(bool(item["is_correct"]) for item in relevant)
                result.append(Metric(label, f"{round(correct / len(relevant) * 100)}%"))
        return tuple(result)

    def teacher_insights(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> tuple[ProgressItem, ...]:
        misconceptions: dict[str, int] = {}
        format_results: dict[str, dict[str, int]] = {}
        for state in mastery.values():
            for label, count in dict(state.state.get("misconceptions", {})).items():
                misconceptions[str(label)] = misconceptions.get(str(label), 0) + int(count)
            for label, result in dict(state.state.get("format_results", {})).items():
                totals = format_results.setdefault(str(label), {"attempts": 0, "correct": 0})
                values = dict(result)
                totals["attempts"] += int(values.get("attempts", 0))
                totals["correct"] += int(values.get("correct", 0))
        ranked = sorted(misconceptions.items(), key=lambda item: (-item[1], item[0]))[:6]
        prediction_skills = sum(
            "predict" in state.state.get("correct_formats", []) for state in mastery.values()
        )
        construction_skills = sum(
            "apply" in state.state.get("correct_formats", []) for state in mastery.values()
        )
        fighting_mastered = sum(
            self._is_mastered_key(key, mastery.get(key, MasteryState(key))) for key in GAME_SKILLS
        )
        stdout = format_results.get("stdout", {"attempts": 0, "correct": 0})
        construction_attempts = sum(
            format_results.get(label, {}).get("attempts", 0) for label in ("construction", "debug")
        )
        construction_correct = sum(
            format_results.get(label, {}).get("correct", 0) for label in ("construction", "debug")
        )
        return (
            ProgressItem("Attempts", str(int(metrics.get("total", 0)))),
            ProgressItem("Recent accuracy", f"{int(metrics.get('accuracy', 0))}%"),
            ProgressItem("Hints used", str(int(metrics.get("hints", 0)))),
            ProgressItem("Prediction skills demonstrated", str(prediction_skills)),
            ProgressItem("Construction/debug skills demonstrated", str(construction_skills)),
            ProgressItem("Exact-output performance", f"{stdout['correct']}/{stdout['attempts']}"),
            ProgressItem(
                "Construction/debug performance",
                f"{construction_correct}/{construction_attempts}",
            ),
            ProgressItem("Fighting skills mastered", f"{fighting_mastered}/{len(GAME_SKILLS)}"),
            *(ProgressItem(label, f"seen {count} times") for label, count in ranked),
        )

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]:
        eligible = self._unlocked_skills(mastery)
        review = tuple(key for key in STDOUT_SKILLS if key in eligible)
        candidates = review or eligible
        ordered = self._adaptive_order(candidates, mastery, rng)
        offset = now.date().toordinal() % len(ordered)
        skill_key = ordered[offset]
        # Daily work alternates prediction with a small debugging/construction check.
        question_type = "predict" if now.date().toordinal() % 3 else "apply"
        return skill_key, question_type

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes:
        del renderer_id, payload
        raise ValueError("Python Foundations uses text and code blocks, not generated media")

    @staticmethod
    def _execute_stdout(code: str, inputs: tuple[str, ...]) -> str:
        supplied = iter(inputs)

        def simulated_input(prompt: str = "") -> str:
            try:
                value = next(supplied)
            except StopIteration as exc:
                raise ValueError("stdout snippet requested undeclared input") from exc
            print(f"{prompt}{value}")
            return value

        safe_builtins = dict(vars(builtins))
        safe_builtins["input"] = simulated_input
        stream = io.StringIO()
        compiled = compile(code, "<python-foundations-question>", "exec")
        with redirect_stdout(stream):
            exec(compiled, {"__builtins__": safe_builtins}, {})
        return stream.getvalue().removesuffix("\n")

    def validate(self) -> list[str]:
        errors = validate_topic_contract(self)
        if tuple(self._skill_map) != ALL_SKILLS:
            errors.append("skill catalogue and question bank are not aligned")
        if len(self._skills) != 53:
            errors.append("the complete 53-skill catalogue is required")
        if len(self.practice_modes()) != 10:
            errors.append("all student practice and weak-review modes are required")
        if len(self.learning_units()) != 22:
            errors.append("the full foundation and nine-lab learning sequence is required")
        for mode_id, keys in MODE_SKILLS.items():
            missing = set(keys).difference(self._skill_map)
            if missing:
                errors.append(f"mode {mode_id} has unknown skills: {sorted(missing)}")
        for skill_key in ALL_SKILLS:
            for question_type in QUESTION_TYPES:
                try:
                    for seed in range(3):
                        question = self.generate_question(skill_key, question_type, Random(seed))
                        validate_options(question.answer_mode, question.answer_options)
                        if len(question.metadata.get("hints", [])) > 3:
                            errors.append(f"too many hints: {skill_key}/{question_type}")
                        if question.metadata.get("difficulty_level") not in {1, 2, 3}:
                            errors.append(f"missing difficulty level: {skill_key}/{question_type}")
                        payload = asdict(question)
                        if not self.evaluate_answer(payload, question.correct_answer).is_correct:
                            errors.append(f"correct answer rejected: {skill_key}/{question_type}")
                except Exception as exc:
                    errors.append(f"question error {skill_key}/{question_type}: {exc}")
            concept = CONCEPTS[skill_key]
            if concept.stdout_code is not None:
                try:
                    actual = self._execute_stdout(concept.stdout_code, concept.stdout_inputs)
                    if actual != concept.stdout_expected:
                        mismatch = (
                            f"stdout mismatch for {skill_key}: "
                            f"{actual!r} != {concept.stdout_expected!r}"
                        )
                        errors.append(mismatch)
                except Exception as exc:
                    errors.append(f"stdout validation failed for {skill_key}: {exc}")
        for unit in self.learning_units():
            try:
                view = self.render_learning_unit(unit.unit_id)
                if not view.title or not view.body:
                    errors.append(f"empty learning unit: {unit.unit_id}")
            except Exception as exc:
                errors.append(f"learning unit error {unit.unit_id}: {exc}")
        errors.extend(self._prerequisite_cycle_errors())
        return errors

    def _prerequisite_cycle_errors(self) -> list[str]:
        errors: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(key: str) -> None:
            if key in visiting:
                errors.append(f"prerequisite cycle includes {key}")
                return
            if key in visited:
                return
            visiting.add(key)
            for prerequisite in self._skill_map[key].prerequisites:
                visit(prerequisite)
            visiting.remove(key)
            visited.add(key)

        for skill_key in self._skill_map:
            visit(skill_key)
        return errors
