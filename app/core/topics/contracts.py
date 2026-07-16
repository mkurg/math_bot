from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from random import Random
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TopicMetadata:
    topic_id: str
    version: str
    title_key: str
    short_title_key: str
    description_key: str
    icon: str


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    skill_key: str
    group_key: str
    title_key: str
    description_key: str
    prerequisites: tuple[str, ...] = ()
    difficulty: int = 1
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PracticeModeDefinition:
    mode_id: str
    title_key: str
    description_key: str
    default_question_count: int
    supports_custom_length: bool = False


@dataclass(frozen=True, slots=True)
class TestDefinition:
    test_id: str
    title_key: str
    question_count: int
    result_renderer_id: str = "generic"


@dataclass(frozen=True, slots=True)
class LearningUnit:
    unit_id: str
    title_key: str
    body_key: str
    skill_keys: tuple[str, ...]
    image_renderer_id: str | None = None
    related_practice_mode_id: str | None = None
    child_unit_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LearningView:
    title: str
    body: str
    image_renderer_id: str | None = None
    image_payload: dict[str, Any] = field(default_factory=dict)
    related_text: str | None = None
    practice_configuration: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnswerOption:
    label: str
    value: dict[str, Any]


@dataclass(frozen=True, slots=True)
class GeneratedMedia:
    renderer_id: str
    payload: dict[str, Any]
    fallback_text: str


@dataclass(frozen=True, slots=True)
class GeneratedQuestion:
    topic_id: str
    skill_key: str
    question_type: str
    rendered_prompt: str
    answer_mode: str
    answer_options: tuple[AnswerOption, ...]
    correct_answer: dict[str, Any]
    explanation_payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    prompt_key: str | None = None
    media: GeneratedMedia | None = None


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    is_correct: bool
    canonical_answer: dict[str, Any]
    feedback_key: str
    feedback_payload: dict[str, Any]
    hint_key: str | None = None
    hint_payload: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MasteryState:
    skill_key: str
    box: int = 0
    due_at: datetime | None = None
    attempt_count: int = 0
    correct_count: int = 0
    consecutive_correct: int = 0
    correct_dates: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Metric:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ProgressItem:
    label: str
    value: str = ""
    skill_key: str | None = None


@dataclass(frozen=True, slots=True)
class ProgressGroup:
    label: str
    percentage: int
    items: tuple[ProgressItem, ...] = ()


@dataclass(frozen=True, slots=True)
class SuggestedAction:
    label: str
    action_id: str


@dataclass(frozen=True, slots=True)
class TopicProgressView:
    headline_metrics: tuple[Metric, ...]
    progress_groups: tuple[ProgressGroup, ...]
    strengths: tuple[ProgressItem, ...]
    current_targets: tuple[ProgressItem, ...]
    suggested_action: SuggestedAction | None = None


class TopicModule(Protocol):
    metadata: TopicMetadata

    def skills(self) -> tuple[SkillDefinition, ...]: ...

    def practice_modes(self) -> tuple[PracticeModeDefinition, ...]: ...

    def test_definitions(self) -> tuple[TestDefinition, ...]: ...

    def learning_units(self) -> tuple[LearningUnit, ...]: ...

    def render_learning_unit(self, unit_id: str) -> LearningView: ...

    def content(self, key: str, **values: object) -> str: ...

    def session_blueprint(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> tuple[tuple[str, str], ...]: ...

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]: ...

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion: ...

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult: ...

    def progress_view(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> TopicProgressView: ...

    def test_result_metrics(self, attempts: tuple[dict[str, Any], ...]) -> tuple[Metric, ...]: ...

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]: ...

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes: ...

    def validate(self) -> list[str]: ...
