from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from random import Random
from typing import Any

from app.content.loader import ContentCatalog
from app.core.mastery.engine import is_mastered
from app.core.mastery.selection import weighted_skill_order
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
from app.topics.times_tables import images
from app.topics.times_tables.question_generator import generate
from app.topics.times_tables.skills import fact_key, parse_skill_key, skill_catalogue

CONTENT_PATH = Path(__file__).with_name("content") / "strings.yaml"


class TimesTablesModule:
    metadata = TopicMetadata(
        topic_id="times_tables",
        version="1.0.0",
        title_key="topic.title",
        short_title_key="topic.short_title",
        description_key="topic.description",
        icon="✖️",
    )

    def __init__(self) -> None:
        self.catalog = ContentCatalog(CONTENT_PATH)
        self._skills = skill_catalogue()

    def skills(self) -> tuple[SkillDefinition, ...]:
        return self._skills

    def practice_modes(self) -> tuple[PracticeModeDefinition, ...]:
        return (
            PracticeModeDefinition("quick", "mode.quick", "mode.quick.description", 5),
            PracticeModeDefinition("normal", "mode.normal", "mode.normal.description", 10),
            PracticeModeDefinition("table", "mode.table", "mode.table.description", 10),
            PracticeModeDefinition("multiplication", "mode.mul", "mode.mul.description", 10),
            PracticeModeDefinition("division", "mode.div", "mode.div.description", 10),
            PracticeModeDefinition("mixed", "mode.mixed", "mode.mixed.description", 10),
        )

    def test_definitions(self) -> tuple[TestDefinition, ...]:
        return (
            TestDefinition("table", "test.table", 10, "times_tables"),
            TestDefinition("division", "test.division", 10, "times_tables"),
            TestDefinition("mixed", "test.mixed", 20, "times_tables"),
        )

    def learning_units(self) -> tuple[LearningUnit, ...]:
        units = [
            LearningUnit(
                unit_id=f"table:{table}",
                title_key=f"table.{table}.title",
                body_key=f"table.{table}.body",
                skill_keys=tuple(fact_key("mul", table, factor) for factor in range(1, 11)),
                image_renderer_id="individual_table",
                related_practice_mode_id="table",
            )
            for table in range(1, 11)
        ]
        units.append(
            LearningUnit(
                "full_table",
                "learn.full.title",
                "learn.full.body",
                tuple(
                    skill.skill_key for skill in self._skills if skill.skill_key.startswith("mul:")
                ),
                "full_table",
            )
        )
        return tuple(units)

    def content(self, key: str, **values: object) -> str:
        return self.catalog.get(key, **values)

    def render_learning_unit(self, unit_id: str) -> LearningView:
        if unit_id == "full_table":
            body = "\n".join(
                " · ".join(str(row * column) for column in range(1, 11)) for row in range(1, 11)
            )
            return LearningView(
                title=self.content("learn.full.title"),
                body=f"{self.content('learn.full.body')}\n\n{body}",
                image_renderer_id="full_table",
            )
        if not unit_id.startswith("table:"):
            raise ValueError("unknown learning unit")
        table = int(unit_id.split(":", 1)[1])
        if not 1 <= table <= 10:
            raise ValueError("unknown multiplication table")
        facts = "\n".join(f"{table} × {factor} = {table * factor}" for factor in range(1, 11))
        tips = self.catalog.raw("tips")
        related = "\n".join(f"{table * quotient} ÷ {table} = {quotient}" for quotient in (6, 8, 9))
        return LearningView(
            title=f"Table of {table}",
            body=f"{facts}\n\n💡 {tips[str(table)]}",
            image_renderer_id="individual_table",
            image_payload={"table": table},
            related_text=related,
            practice_configuration={"table": table},
        )

    def _eligible(
        self, mode_id: str, mastery: dict[str, MasteryState], configuration: dict[str, Any]
    ) -> tuple[str, ...]:
        all_keys = tuple(skill.skill_key for skill in self._skills)
        if mode_id == "multiplication":
            return tuple(key for key in all_keys if key.startswith("mul:"))
        if mode_id == "division":
            return tuple(key for key in all_keys if key.startswith("div:"))
        if mode_id == "table":
            table = int(configuration["table"])
            return tuple(fact_key("mul", table, factor) for factor in range(1, 11))
        if mode_id in {"quick", "normal", "mixed"}:
            eligible: list[str] = []
            for key in all_keys:
                operation, low, high = parse_skill_key(key)
                if operation == "div":
                    mul_state = mastery.get(fact_key("mul", low, high), MasteryState(key))
                    if mul_state.box < 2:
                        continue
                eligible.append(key)
            return tuple(eligible)
        raise ValueError(f"unknown practice mode: {mode_id}")

    def session_blueprint(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> tuple[tuple[str, str], ...]:
        eligible = self._eligible(mode_id, mastery, configuration)
        now = datetime.now(UTC)
        chosen: list[str]
        if mode_id == "table":
            table_keys = list(eligible)
            rng.shuffle(table_keys)
            table_count = max(1, round(question_count * 0.7))
            weak_count = round(question_count * 0.2)
            chosen = table_keys[:table_count]
            all_multiplication = tuple(
                skill.skill_key
                for skill in self._skills
                if skill.skill_key.startswith("mul:") and skill.skill_key not in chosen
            )
            weak_order = weighted_skill_order(all_multiplication, mastery, now, rng)
            for key in weak_order:
                if key not in chosen:
                    chosen.append(key)
                if len(chosen) == table_count + weak_count:
                    break
            confidence = [
                key
                for key in all_multiplication
                if 1 in parse_skill_key(key)[1:] and key not in chosen
            ]
            rng.shuffle(confidence)
            chosen.extend(confidence[: question_count - len(chosen)])
            rng.shuffle(chosen)
        else:
            weighted = weighted_skill_order(eligible, mastery, now, rng)
            chosen = []
            for key in weighted:
                if key not in chosen:
                    chosen.append(key)
                if len(chosen) == question_count:
                    break
        while len(chosen) < question_count:
            candidates = [key for key in eligible if chosen.count(key) < 2]
            chosen.append(rng.choice(candidates or list(eligible)))

        mul_types = ("direct_multiplication", "missing_factor", "true_false", "visual", "story")
        div_types = ("direct_division", "missing_divisor", "story")
        blueprint: list[tuple[str, str]] = []
        for index, key in enumerate(chosen):
            operation, _, _ = parse_skill_key(key)
            if mode_id == "multiplication":
                question_type = rng.choice(("direct_multiplication", "missing_factor"))
            elif mode_id == "division":
                question_type = rng.choice(("direct_division", "missing_divisor"))
            elif mode_id != "mixed":
                question_type = "direct_multiplication" if operation == "mul" else "direct_division"
                if index and rng.random() < 0.3:
                    question_type = rng.choice(mul_types if operation == "mul" else div_types)
            else:
                question_type = rng.choice(mul_types if operation == "mul" else div_types)
            blueprint.append((key, question_type))
        return tuple(blueprint)

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]:
        if test_id == "table":
            table = int(configuration["table"])
            table_result = [
                (fact_key("mul", table, factor), "direct_multiplication") for factor in range(1, 11)
            ]
            rng.shuffle(table_result)
            return tuple(table_result)
        if test_id == "division":
            pairs = [(factor, ((factor + 3) % 10) + 1) for factor in range(1, 11)]
            division_result = [
                (fact_key("div", first, second), "direct_division") for first, second in pairs
            ]
            rng.shuffle(division_result)
            return tuple(division_result)
        if test_id == "mixed":
            tables = list(range(1, 11))
            rng.shuffle(tables)
            mixed_result: list[tuple[str, str]] = []
            mixed_result.extend(
                (fact_key("mul", table, ((table + 4) % 10) + 1), "direct_multiplication")
                for table in tables
            )
            mixed_result.extend(
                (fact_key("div", table, ((table + 2) % 10) + 1), "direct_division")
                for table in tables[:5]
            )
            mixed_result.extend(
                (fact_key("mul", table, ((table + 6) % 10) + 1), "missing_factor")
                for table in tables[:3]
            )
            mixed_result.append((fact_key("mul", tables[0], tables[-1]), "visual"))
            mixed_result.append((fact_key("div", tables[1], tables[-2]), "story"))
            rng.shuffle(mixed_result)
            return tuple(mixed_result)
        raise ValueError(f"unknown test: {test_id}")

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion:
        return generate(skill_key, question_type, rng, self.content, self.catalog.raw)

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult:
        correct = question_payload["correct_answer"]
        explanation = question_payload["explanation_payload"]
        is_correct = selected_answer == correct
        return EvaluationResult(
            is_correct=is_correct,
            canonical_answer=correct,
            feedback_key="feedback.correct" if is_correct else "feedback.incorrect",
            feedback_payload={"equation": explanation["equation"]},
            hint_key=None if is_correct else "feedback.hint",
            hint_payload=None if is_correct else {"hint": explanation.get("hint", "")},
        )

    def retry_question_type(self, skill_key: str, question_type: str, rng: Random) -> str:
        operation, _, _ = parse_skill_key(skill_key)
        choices = (
            ("missing_factor", "direct_multiplication", "true_false")
            if operation == "mul"
            else ("missing_divisor", "direct_division", "story")
        )
        alternatives = [item for item in choices if item != question_type]
        return rng.choice(alternatives)

    def progress_view(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> TopicProgressView:
        operation_progress: list[ProgressGroup] = []
        for operation, label in (("mul", "Multiplication"), ("div", "Division")):
            keys = [
                skill.skill_key for skill in self._skills if skill.skill_key.startswith(operation)
            ]
            percentage = round(
                sum(mastery.get(key, MasteryState(key)).box for key in keys) / (len(keys) * 5) * 100
            )
            operation_progress.append(ProgressGroup(label, percentage))
        table_items: list[ProgressItem] = []
        for table in range(1, 11):
            keys = [fact_key("mul", table, factor) for factor in range(1, 11)]
            percent = round(sum(mastery.get(key, MasteryState(key)).box for key in keys) / 50 * 100)
            table_items.append(ProgressItem(f"×{table}", f"{percent}%"))
        ranked = sorted(
            self._skills,
            key=lambda skill: mastery.get(skill.skill_key, MasteryState(skill.skill_key)).box,
            reverse=True,
        )
        strengths = tuple(
            ProgressItem(self._skill_label(skill.skill_key), skill_key=skill.skill_key)
            for skill in ranked
            if is_mastered(mastery.get(skill.skill_key, MasteryState(skill.skill_key)))
        )[:3]
        attempted = [
            skill
            for skill in reversed(ranked)
            if mastery.get(skill.skill_key, MasteryState(skill.skill_key)).attempt_count > 0
        ]
        targets = tuple(
            ProgressItem(self._skill_label(skill.skill_key), skill_key=skill.skill_key)
            for skill in attempted[:3]
        )
        return TopicProgressView(
            headline_metrics=(
                Metric("Total questions", str(int(metrics.get("total", 0)))),
                Metric("Last 7 days", str(int(metrics.get("recent", 0)))),
                Metric("7-day accuracy", f"{int(metrics.get('accuracy', 0))}%"),
                Metric("Active days", str(int(metrics.get("active_days", 0)))),
            ),
            progress_groups=(*operation_progress, ProgressGroup("Tables", 0, tuple(table_items))),
            strengths=strengths,
            current_targets=targets,
            suggested_action=SuggestedAction("Practise weak facts", "practice:weak"),
        )

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]:
        keys = tuple(
            skill.skill_key for skill in self._skills if skill.skill_key.startswith("mul:")
        )
        ordered = weighted_skill_order(keys, mastery, now, rng)
        return ordered[0], "direct_multiplication"

    def test_result_metrics(self, attempts: tuple[dict[str, Any], ...]) -> tuple[Metric, ...]:
        metrics: list[Metric] = []
        for operation, label in (("mul", "Multiplication accuracy"), ("div", "Division accuracy")):
            relevant = [
                attempt
                for attempt in attempts
                if parse_skill_key(str(attempt["skill_key"]))[0] == operation
            ]
            if relevant:
                correct = sum(bool(attempt["is_correct"]) for attempt in relevant)
                metrics.append(Metric(label, f"{round(correct / len(relevant) * 100)}%"))
        return tuple(metrics)

    def teacher_insights(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> tuple[ProgressItem, ...]:
        del mastery
        return (ProgressItem("Hints used", str(int(metrics.get("hints", 0)))),)

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes:
        return images.render(renderer_id, payload)

    def validate(self) -> list[str]:
        errors = validate_topic_contract(self)
        tips = self.catalog.raw("tips")
        hard_facts = self.catalog.raw("hard_facts")
        if not isinstance(tips, dict) or set(map(str, range(1, 11))).difference(tips):
            errors.append("tips must exist for tables 1 through 10")
        required = {"6x6", "6x7", "6x8", "7x7", "7x8", "8x8"}
        if not isinstance(hard_facts, dict) or required.difference(hard_facts):
            errors.append("required hard-fact cards are missing")
        for operation in ("mul", "div"):
            templates = self.catalog.raw(f"story.{operation}")
            if not isinstance(templates, list) or len(templates) < 15:
                errors.append(f"at least 15 {operation} story templates are required")
        try:
            for table in range(1, 11):
                self.render_media("individual_table", {"table": table})
            self.render_media("full_table", {})
        except Exception as exc:
            errors.append(f"media renderer failed: {exc}")
        return errors

    @staticmethod
    def _skill_label(skill_key: str) -> str:
        operation, low, high = parse_skill_key(skill_key)
        if operation == "mul":
            return f"{low} × {high}"
        return f"{low * high} ÷ {low}/{high}"
