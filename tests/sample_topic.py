from __future__ import annotations

from datetime import datetime
from random import Random
from typing import Any

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
    TestDefinition,
    TopicMetadata,
    TopicProgressView,
)
from app.core.topics.validation import validate_topic_contract


class SampleTopic:
    metadata = TopicMetadata(
        "sample_topic", "1", "sample.title", "sample.short", "sample.desc", "🧪"
    )

    def skills(self) -> tuple[SkillDefinition, ...]:
        return (
            SkillDefinition("sample:one", "sample", "one", "one"),
            SkillDefinition("sample:two", "sample", "two", "two", ("sample:one",)),
        )

    def practice_modes(self) -> tuple[PracticeModeDefinition, ...]:
        return (PracticeModeDefinition("sample", "sample.mode", "sample.mode.desc", 1),)

    def test_definitions(self) -> tuple[TestDefinition, ...]:
        return (TestDefinition("sample", "sample.test", 1),)

    def learning_units(self) -> tuple[LearningUnit, ...]:
        return (LearningUnit("sample", "sample", "sample", ("sample:one",)),)

    def render_learning_unit(self, unit_id: str) -> LearningView:
        if unit_id != "sample":
            raise ValueError
        return LearningView("Sample", "A sample learning unit")

    def content(self, key: str, **values: object) -> str:
        del values
        return key

    def session_blueprint(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> tuple[tuple[str, str], ...]:
        del mode_id, mastery, configuration, rng
        return tuple(("sample:one", "choice") for _ in range(question_count))

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]:
        del test_id, configuration, rng
        return (("sample:two", "choice"),)

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion:
        del question_type, rng
        return GeneratedQuestion(
            "sample_topic",
            skill_key,
            "choice",
            "Choose one",
            "single_choice",
            tuple(AnswerOption(str(value), {"value": value}) for value in (1, 2, 3, 4)),
            {"value": 1},
            {"equation": "one", "hint": "one"},
        )

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult:
        correct = question_payload["correct_answer"]
        return EvaluationResult(
            selected_answer == correct,
            correct,
            "correct",
            {"equation": "one"},
        )

    def retry_question_type(self, skill_key: str, question_type: str, rng: Random) -> str:
        del skill_key, question_type, rng
        return "choice"

    def progress_view(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> TopicProgressView:
        return TopicProgressView(
            (),
            (ProgressGroup("Sample", int(metrics.get("accuracy", 0))),),
            (),
            (ProgressItem("Sample one", skill_key="sample:one"),) if mastery else (),
        )

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]:
        del mastery, now, rng
        return "sample:one", "choice"

    def test_result_metrics(self, attempts: tuple[dict[str, Any], ...]) -> tuple[Metric, ...]:
        correct = sum(bool(attempt["is_correct"]) for attempt in attempts)
        accuracy = round(correct / len(attempts) * 100) if attempts else 0
        return (Metric("Sample accuracy", f"{accuracy}%"),)

    def teacher_insights(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> tuple[ProgressItem, ...]:
        del mastery, metrics
        return ()

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes:
        del renderer_id, payload
        return b"sample"

    def validate(self) -> list[str]:
        return validate_topic_contract(self)
