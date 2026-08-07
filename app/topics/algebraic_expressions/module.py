from __future__ import annotations

from dataclasses import dataclass
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
from app.topics.algebraic_expressions.skills import (
    GROUP_LABELS,
    skill_catalogue,
    skill_label,
)

CONTENT_PATH = Path(__file__).with_name("content") / "strings.yaml"


QUESTION_TYPES: dict[str, tuple[str, ...]] = {
    "terms:identify": ("term_count", "identify_terms"),
    "terms:sign": ("signed_term", "sign_belongs"),
    "terms:coefficient": ("coefficient", "implicit_coefficient"),
    "parentheses:group": ("group_contents", "group_role"),
    "parentheses:plus": ("remove_plus", "plus_reason"),
    "parentheses:minus_sum": ("minus_sum", "minus_sum_reason"),
    "parentheses:minus_difference": ("minus_difference", "double_negative_reason"),
    "distribution:numeric": ("numeric_distribution", "three_copies"),
    "distribution:positive_sum": ("expand_positive_sum", "missing_product"),
    "distribution:positive_difference": ("expand_positive_difference", "next_step"),
    "distribution:coefficient": ("coefficient_product", "missing_coefficient"),
    "distribution:negative": ("expand_negative", "compare_solutions"),
    "like:identify": ("find_like", "like_reason"),
    "like:unlike": ("unlike_error", "true_false_like"),
    "collect:positive": ("collect_positive", "reverse_distribution"),
    "collect:negative": ("collect_negative", "implicit_one"),
    "collect:constants": ("collect_constants", "sort_terms"),
    "collect:two_variables": ("two_variables", "group_two_variables"),
    "simplify:one_group": ("simplify_one_group", "stop_after_expansion"),
    "simplify:subtract_group": ("subtract_group", "sign_error"),
    "simplify:two_groups": ("two_groups", "final_target"),
    "reasoning:errors": ("distribution_error", "like_terms_error"),
}


MODE_SKILLS: dict[str, tuple[str, ...]] = {
    "quick": tuple(QUESTION_TYPES),
    "signs": (
        "terms:identify",
        "terms:sign",
        "parentheses:group",
        "parentheses:plus",
        "parentheses:minus_sum",
        "parentheses:minus_difference",
    ),
    "distribute": (
        "distribution:numeric",
        "distribution:positive_sum",
        "distribution:positive_difference",
        "distribution:coefficient",
        "distribution:negative",
    ),
    "find_like": (
        "terms:coefficient",
        "like:identify",
        "like:unlike",
    ),
    "collect": (
        "like:identify",
        "collect:positive",
        "collect:negative",
        "collect:constants",
        "collect:two_variables",
    ),
    "expand": (
        "distribution:positive_sum",
        "distribution:positive_difference",
        "distribution:negative",
        "simplify:one_group",
        "simplify:subtract_group",
        "simplify:two_groups",
    ),
    "mixed": tuple(QUESTION_TYPES),
    "mistakes": (
        "parentheses:minus_sum",
        "parentheses:minus_difference",
        "distribution:positive_sum",
        "distribution:negative",
        "like:unlike",
        "simplify:subtract_group",
        "reasoning:errors",
    ),
}


LEARNING_SPECS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("terms", ("terms:identify", "terms:sign"), "signs"),
    ("groups", ("parentheses:group",), "signs"),
    ("plus", ("parentheses:plus",), "signs"),
    ("minus", ("parentheses:minus_sum", "parentheses:minus_difference"), "signs"),
    ("numeric", ("distribution:numeric",), "distribute"),
    (
        "positive",
        ("distribution:positive_sum", "distribution:positive_difference"),
        "distribute",
    ),
    ("negative", ("distribution:negative",), "distribute"),
    ("like", ("like:identify", "like:unlike"), "find_like"),
    ("coefficients", ("terms:coefficient", "collect:positive"), "collect"),
    ("collect", ("collect:negative", "collect:constants"), "collect"),
    ("two_variables", ("collect:two_variables",), "collect"),
    ("expand_collect", ("simplify:one_group",), "expand"),
    ("subtract", ("simplify:subtract_group",), "expand"),
    ("full", ("simplify:two_groups",), "expand"),
    ("reference", ("reasoning:errors",), "mistakes"),
)


@dataclass(frozen=True, slots=True)
class _QuestionParts:
    prompt: str
    answers: tuple[str, str, str, str]
    explanation: str
    hint: str
    misconception: str


def _x_term(coefficient: int) -> str:
    if coefficient == 1:
        return "x"
    if coefficient == -1:
        return "−x"
    return f"{coefficient}x" if coefficient >= 0 else f"−{abs(coefficient)}x"


def _linear(coefficient: int, constant: int = 0) -> str:
    if coefficient == 0:
        return str(constant).replace("-", "−")
    result = _x_term(coefficient)
    if constant > 0:
        return f"{result} + {constant}"
    if constant < 0:
        return f"{result} − {abs(constant)}"
    return result


def _signed(value: int) -> str:
    return f"+ {value}" if value >= 0 else f"− {abs(value)}"


def _unique_answers(correct: str, *wrong: str) -> tuple[str, str, str, str]:
    values: list[str] = []
    for value in (correct, *wrong):
        if value not in values:
            values.append(value)
    candidate = 1
    while len(values) < 4:
        filler = f"Другой ответ: {candidate}"
        if filler not in values:
            values.append(filler)
        candidate += 1
    return values[0], values[1], values[2], values[3]


class AlgebraicExpressionsModule:
    metadata = TopicMetadata(
        topic_id="algebraic_expressions",
        version="1.0.0",
        title_key="topic.title",
        short_title_key="topic.short_title",
        description_key="topic.description",
        icon="🧮",
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
            PracticeModeDefinition("signs", "mode.signs", "mode.signs.description", 8),
            PracticeModeDefinition(
                "distribute", "mode.distribute", "mode.distribute.description", 8
            ),
            PracticeModeDefinition("find_like", "mode.find_like", "mode.find_like.description", 8),
            PracticeModeDefinition("collect", "mode.collect", "mode.collect.description", 8),
            PracticeModeDefinition("expand", "mode.expand", "mode.expand.description", 10),
            PracticeModeDefinition("mixed", "mode.mixed", "mode.mixed.description", 10),
            PracticeModeDefinition("mistakes", "mode.mistakes", "mode.mistakes.description", 8),
            PracticeModeDefinition("weak", "mode.weak", "mode.weak.description", 8),
        )

    def test_definitions(self) -> tuple[TestDefinition, ...]:
        return (
            TestDefinition("signs", "challenge.signs", 10, "algebraic_expressions"),
            TestDefinition("distribution", "challenge.distribution", 12, "algebraic_expressions"),
            TestDefinition("like_terms", "challenge.like_terms", 12, "algebraic_expressions"),
            TestDefinition("final", "challenge.final", 15, "algebraic_expressions"),
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
        return self.catalog.get(key, **values)

    def render_learning_unit(self, unit_id: str) -> LearningView:
        unit = next((item for item in self.learning_units() if item.unit_id == unit_id), None)
        if unit is None:
            raise ValueError("неизвестный раздел теории по выражениям")
        return LearningView(
            title=self.content(unit.title_key),
            body=self.content(unit.body_key),
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
        if mode_id == "weak":
            eligible = tuple(
                item.skill_key
                for item in self._skills
                if mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count > 0
                and not self._is_mastered(mastery.get(item.skill_key, MasteryState(item.skill_key)))
            )
            if not eligible:
                eligible = MODE_SKILLS["quick"]
        else:
            try:
                eligible = MODE_SKILLS[mode_id]
            except KeyError as exc:
                raise ValueError(f"неизвестный режим выражений: {mode_id}") from exc
        focus = configuration.get("focus_skill")
        if focus is not None and str(focus) not in self._skill_map:
            raise ValueError("неизвестный навык для тренировки")
        ordered = weighted_skill_order(eligible, mastery, datetime.now(UTC), rng)
        chosen: list[str] = []
        if focus is not None:
            chosen.append(str(focus))
        for skill_key in ordered:
            if skill_key not in chosen:
                chosen.append(skill_key)
            if len(chosen) >= question_count:
                break
        while len(chosen) < question_count:
            chosen.append(rng.choice(eligible))
        return tuple(
            (skill_key, rng.choice(QUESTION_TYPES[skill_key]))
            for skill_key in chosen[:question_count]
        )

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]:
        del configuration
        blueprints: dict[str, tuple[tuple[str, str], ...]] = {
            "signs": (
                ("terms:identify", "term_count"),
                ("terms:sign", "signed_term"),
                ("parentheses:group", "group_contents"),
                ("parentheses:plus", "remove_plus"),
                ("parentheses:minus_sum", "minus_sum"),
                ("parentheses:minus_difference", "minus_difference"),
                ("parentheses:minus_sum", "minus_sum_reason"),
                ("parentheses:minus_difference", "double_negative_reason"),
                ("terms:coefficient", "implicit_coefficient"),
                ("reasoning:errors", "distribution_error"),
            ),
            "distribution": (
                ("distribution:numeric", "numeric_distribution"),
                ("distribution:numeric", "three_copies"),
                ("distribution:positive_sum", "expand_positive_sum"),
                ("distribution:positive_sum", "missing_product"),
                ("distribution:positive_difference", "expand_positive_difference"),
                ("distribution:positive_difference", "next_step"),
                ("distribution:coefficient", "coefficient_product"),
                ("distribution:coefficient", "missing_coefficient"),
                ("distribution:negative", "expand_negative"),
                ("distribution:negative", "compare_solutions"),
                ("parentheses:minus_difference", "minus_difference"),
                ("reasoning:errors", "distribution_error"),
            ),
            "like_terms": (
                ("like:identify", "find_like"),
                ("like:identify", "like_reason"),
                ("like:unlike", "unlike_error"),
                ("like:unlike", "true_false_like"),
                ("collect:positive", "collect_positive"),
                ("collect:positive", "reverse_distribution"),
                ("collect:negative", "collect_negative"),
                ("collect:negative", "implicit_one"),
                ("collect:constants", "collect_constants"),
                ("collect:constants", "sort_terms"),
                ("collect:two_variables", "two_variables"),
                ("reasoning:errors", "like_terms_error"),
            ),
            "final": (
                ("parentheses:minus_difference", "minus_difference"),
                ("distribution:positive_sum", "expand_positive_sum"),
                ("distribution:positive_difference", "expand_positive_difference"),
                ("distribution:coefficient", "coefficient_product"),
                ("distribution:negative", "expand_negative"),
                ("like:identify", "find_like"),
                ("like:unlike", "unlike_error"),
                ("collect:positive", "collect_positive"),
                ("collect:negative", "collect_negative"),
                ("collect:constants", "collect_constants"),
                ("collect:two_variables", "two_variables"),
                ("simplify:one_group", "simplify_one_group"),
                ("simplify:subtract_group", "subtract_group"),
                ("simplify:two_groups", "two_groups"),
                ("simplify:two_groups", "final_target"),
            ),
        }
        try:
            result = list(blueprints[test_id])
        except KeyError as exc:
            raise ValueError(f"неизвестная проверочная: {test_id}") from exc
        rng.shuffle(result)
        return tuple(result)

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion:
        if skill_key not in self._skill_map:
            raise ValueError(f"неизвестный навык выражений: {skill_key}")
        if question_type not in QUESTION_TYPES[skill_key]:
            raise ValueError(f"тип {question_type} не подходит навыку {skill_key}")
        parts = self._question_parts(question_type, rng)
        indexed = list(enumerate(parts.answers))
        rng.shuffle(indexed)
        options = tuple(
            AnswerOption(label=label, value={"value": f"answer_{index}"})
            for index, label in indexed
        )
        validate_options("single_choice", options)
        return GeneratedQuestion(
            topic_id=self.metadata.topic_id,
            skill_key=skill_key,
            question_type=question_type,
            rendered_prompt=parts.prompt,
            answer_mode="single_choice",
            answer_options=options,
            correct_answer={"value": "answer_0"},
            explanation_payload={"equation": parts.explanation},
            metadata={
                "hints": [parts.hint],
                "misconception": parts.misconception,
            },
        )

    def _question_parts(self, question_type: str, rng: Random) -> _QuestionParts:
        m1 = "M1: действие перед скобками применено не ко всей группе"
        m2 = "M2: плюс перед скобками ошибочно меняет знаки"
        m3 = "M3: потерян знак слагаемого"
        m4 = "M4: перепутаны подобные и неподобные слагаемые"
        m5 = "M5: сложены сами буквы вместо коэффициентов"
        m6 = "M6: раскрытие скобок остановлено или выполнено не полностью"
        m7 = "M7: неверно обработано произведение двух отрицательных чисел"
        m8 = "M8: нарушен порядок «раскрыть, затем привести подобные»"

        if question_type == "term_count":
            expression, count = rng.choice(
                (("4x − 2 + 7y", 3), ("3a + 5", 2), ("x − 3 + y − 8", 4))
            )
            return _QuestionParts(
                f"Сколько слагаемых в выражении {expression}?",
                _unique_answers(str(count), str(count - 1), str(count + 1), str(count + 2)),
                f"Слагаемые разделяются знаками + и −. Здесь их {count}.",
                "Прочитай каждую часть вместе со знаком перед ней.",
                m3,
            )
        if question_type == "identify_terms":
            return _QuestionParts(
                "Какая строка верно перечисляет слагаемые выражения 4x − 2 + 7y?",
                ("4x; −2; +7y", "4x; 2; 7y", "4; x; −2; 7; y", "4x − 2; 7y; +"),
                "Знак относится к следующему слагаемому: 4x, −2 и +7y.",
                "Не отделяй минус от числа 2.",
                m3,
            )
        if question_type == "signed_term":
            return _QuestionParts(
                "Каково второе слагаемое в выражении x − 3?",
                ("−3", "3", "−x", "x − 3"),
                "x − 3 можно записать как x + (−3), поэтому второе слагаемое равно −3.",
                "Замени вычитание сложением отрицательного числа.",
                m3,
            )
        if question_type == "sign_belongs":
            return _QuestionParts(
                "К какой части относится минус в записи 5x − 2 + y?",
                ("К слагаемому −2", "К слагаемому 5x", "Ко всему выражению", "Только к букве y"),
                "Минус перед 2 входит в слагаемое −2.",
                "Читай выражение слева направо по слагаемым.",
                m3,
            )
        if question_type == "coefficient":
            coefficient = rng.choice((3, 5, 7, -2))
            term = _x_term(coefficient)
            wrong = (str(abs(coefficient)), "x", str(coefficient + 1))
            return _QuestionParts(
                f"Каков коэффициент в слагаемом {term}?",
                _unique_answers(str(coefficient).replace("-", "−"), *wrong),
                f"{term} — это {coefficient}·x, значит коэффициент равен {coefficient}.",
                "Коэффициент — число, на которое умножается буква.",
                m5,
            )
        if question_type == "implicit_coefficient":
            return _QuestionParts(
                "Каков коэффициент у слагаемого −x?",
                ("−1", "1", "0", "−x"),
                "−x = (−1)·x, поэтому коэффициент равен −1.",
                "Какое число, умноженное на x, даёт −x?",
                m5,
            )
        if question_type == "group_contents":
            return _QuestionParts(
                "Что именно образует одну группу в выражении 7 + (x − 3)?",
                ("x − 3", "Только x", "Только −3", "7 + x"),
                "Скобки объединяют x и −3 в одну группу x − 3.",
                "Найди открывающую и закрывающую скобки.",
                m1,
            )
        if question_type == "group_role":
            return _QuestionParts(
                "Что означает число 2 в записи 2(x + 4)?",
                (
                    "Оно умножает всю группу x + 4",
                    "Оно умножает только x",
                    "Оно прибавляется к 4",
                    "Оно показывает число слагаемых",
                ),
                "Множитель перед скобками относится ко всей группе.",
                "Представь две одинаковые копии пакета (x + 4).",
                m1,
            )
        if question_type == "remove_plus":
            return _QuestionParts(
                "Убери скобки: +(x − 4)",
                ("x − 4", "x + 4", "−x + 4", "−x − 4"),
                "Плюс перед группой сохраняет каждое слагаемое: +(x − 4) = x − 4.",
                "Прибавляемая группа не меняется.",
                m2,
            )
        if question_type == "plus_reason":
            return _QuestionParts(
                "Почему 5 + (x − 2) можно записать как 5 + x − 2?",
                (
                    "Плюс перед скобками сохраняет всю группу",
                    "Плюс меняет все знаки",
                    "Скобки всегда можно игнорировать",
                    "Число 5 умножает группу",
                ),
                "Мы прибавляем группу x − 2, поэтому оба её слагаемых сохраняют знаки.",
                "Определи внешнее действие перед скобками.",
                m2,
            )
        if question_type == "minus_sum":
            return _QuestionParts(
                "Раскрой скобки: −(x + 4)",
                ("−x − 4", "−x + 4", "x − 4", "x + 4"),
                "Внешний минус — это множитель −1: (−1)x + (−1)4 = −x − 4.",
                "Умножь на −1 каждое слагаемое группы.",
                m1,
            )
        if question_type == "minus_sum_reason":
            return _QuestionParts(
                "Ученик написал −(x + 5) = −x + 5. Где ошибка?",
                (
                    "Минус не применён к числу +5",
                    "Минус не применён к x",
                    "Нужно получить x + 5",
                    "Ошибки нет",
                ),
                "Множитель −1 действует и на x, и на +5. Верно: −x − 5.",
                "Проверь отдельно (−1)·x и (−1)·5.",
                m1,
            )
        if question_type == "minus_difference":
            return _QuestionParts(
                "Раскрой скобки: −(x − 4)",
                ("−x + 4", "−x − 4", "x − 4", "x + 4"),
                "(−1)·x = −x, а (−1)·(−4) = +4. Получаем −x + 4.",
                "Второе слагаемое внутри группы равно −4.",
                m7,
            )
        if question_type == "double_negative_reason":
            return _QuestionParts(
                "Почему в −(x − 4) число 4 после раскрытия становится положительным?",
                (
                    "Потому что (−1)·(−4) = +4",
                    "Потому что скобки удаляют минусы",
                    "Потому что 4 всегда положительно",
                    "Потому что x меняет знак дважды",
                ),
                (
                    "Внешний множитель −1 умножается на внутреннее слагаемое −4; "
                    "произведение двух отрицательных чисел положительно."
                ),
                "Запиши внешний минус как множитель −1.",
                m7,
            )
        if question_type == "numeric_distribution":
            a, b, c = rng.choice(((3, 4, 2), (2, 5, 3), (4, 2, 6)))
            return _QuestionParts(
                f"Какая запись верно раскрывает {a}({b} + {c})?",
                (f"{a}·{b} + {a}·{c}", f"{a}·{b} + {c}", f"{a} + {b}·{c}", f"{a}·({b}·{c})"),
                f"Есть {a} копии всей суммы, поэтому множитель {a} действует на {b} и на {c}.",
                "Покажи отдельно произведение с каждым слагаемым.",
                m1,
            )
        if question_type == "three_copies":
            return _QuestionParts(
                "Какая сумма буквально показывает три копии группы (x + 2)?",
                ("(x + 2) + (x + 2) + (x + 2)", "3x + 2", "x + 2 + 3", "x + 2 + x"),
                "Три копии содержат три раза и x, и число 2; после упрощения это 3x + 6.",
                "Повтори весь пакет три раза.",
                m6,
            )
        if question_type == "expand_positive_sum":
            a, b = rng.choice(((2, 3), (3, 4), (5, 2)))
            return _QuestionParts(
                f"Раскрой скобки: {a}(x + {b})",
                (f"{a}x + {a * b}", f"{a}x + {b}", f"{a + 1}x + {b}", f"x + {a * b}"),
                f"{a}·x + {a}·{b} = {a}x + {a * b}.",
                "Умножь внешний множитель на оба слагаемых.",
                m6,
            )
        if question_type == "missing_product":
            return _QuestionParts(
                "Заполни пропуск: 3(2x + 5) = 6x + …",
                ("15", "5", "8", "10"),
                "Второе произведение равно 3·5 = 15.",
                "После 3·2x вычисли 3·5.",
                m6,
            )
        if question_type == "expand_positive_difference":
            a, b = rng.choice(((4, 2), (3, 5), (2, 6)))
            return _QuestionParts(
                f"Раскрой скобки: {a}(x − {b})",
                (f"{a}x − {a * b}", f"{a}x − {b}", f"{a}x + {a * b}", f"x − {a * b}"),
                f"{a}·x + {a}·(−{b}) = {a}x − {a * b}.",
                "Считай второе слагаемое внутри равным отрицательному числу.",
                m3,
            )
        if question_type == "next_step":
            return _QuestionParts(
                "Какой следующий шаг верен для 5(2x − 3)?",
                ("5·2x + 5·(−3)", "5·2x − 3", "5 + 2x − 3", "10x + 3"),
                "Множитель 5 действует на 2x и на слагаемое −3.",
                "Пока не считай: сначала запиши два произведения.",
                m1,
            )
        if question_type == "coefficient_product":
            a, b, c = rng.choice(((3, 2, 5), (2, 4, 3), (4, 3, 2)))
            return _QuestionParts(
                f"Раскрой скобки: {a}({b}x + {c})",
                (
                    f"{a * b}x + {a * c}",
                    f"{a + b}x + {a * c}",
                    f"{a * b}x + {c}",
                    f"{a}x + {a * c}",
                ),
                f"Коэффициенты перемножаются: {a}·{b} = {a * b}; также {a}·{c} = {a * c}.",
                "В слагаемом bx число b тоже участвует в умножении.",
                m5,
            )
        if question_type == "missing_coefficient":
            return _QuestionParts(
                "Заполни пропуск: 4(3x − 2) = …x − 8",
                ("12", "7", "4", "3"),
                "4·3x = 12x, поэтому пропущенный коэффициент равен 12.",
                "Перемножь внешний множитель и коэффициент у x.",
                m5,
            )
        if question_type == "expand_negative":
            return _QuestionParts(
                "Раскрой скобки: −2(x − 3)",
                ("−2x + 6", "−2x − 6", "2x + 6", "−2x − 3"),
                "(−2)·x = −2x, а (−2)·(−3) = +6. Ответ: −2x + 6.",
                "Умножь −2 отдельно на x и на −3.",
                m7,
            )
        if question_type == "compare_solutions":
            return _QuestionParts(
                "Кто верно раскрыл −3(2x + 4)?",
                ("Лена: −6x − 12", "Миша: −6x + 12", "Олег: −3x − 4", "Все ответы верны"),
                "−3·2x = −6x и −3·4 = −12.",
                "Проверь оба произведения и их знаки.",
                m1,
            )
        if question_type == "find_like":
            return _QuestionParts(
                "Какая пара состоит из подобных слагаемых?",
                ("3x и −5x", "3x и 5y", "x и x²", "2x и 2"),
                "У 3x и −5x одинаковая буквенная часть x; различаются только коэффициенты.",
                "Сравни буквенную часть каждого слагаемого.",
                m4,
            )
        if question_type == "like_reason":
            return _QuestionParts(
                "Почему 7x и −2x являются подобными?",
                (
                    "У них одинаковая буквенная часть x",
                    "У них одинаковые коэффициенты",
                    "Оба слагаемых положительные",
                    "Потому что 7 − 2 = 5",
                ),
                "Подобие определяет одинаковая буквенная часть; коэффициенты могут различаться.",
                "Спрячь числа 7 и −2 и сравни оставшееся.",
                m4,
            )
        if question_type == "unlike_error":
            return _QuestionParts(
                "Ученик написал 3x + 2y = 5xy. Почему это неверно?",
                (
                    "x-слагаемые и y-слагаемые не подобны",
                    "Нужно только поменять плюс на минус",
                    "Коэффициенты нельзя складывать никогда",
                    "Равенство верно",
                ),
                "У слагаемых разные буквенные части x и y, поэтому объединить их в одно нельзя.",
                "Сравни не числа, а буквенные части.",
                m4,
            )
        if question_type == "true_false_like":
            return _QuestionParts(
                "Какое утверждение верно?",
                (
                    "x и x² не являются подобными",
                    "x и y являются подобными",
                    "3x и 3 являются подобными",
                    "Любые слагаемые с числами подобны",
                ),
                "Степень входит в буквенную часть, поэтому x и x² различаются.",
                "Буквенная часть должна совпасть полностью.",
                m4,
            )
        if question_type == "collect_positive":
            a, b = rng.choice(((3, 4), (2, 5), (6, 3)))
            return _QuestionParts(
                f"Приведи подобные: {a}x + {b}x",
                (f"{a + b}x", f"{a * b}x", f"{a + b}x²", f"{a + b}"),
                f"({a} + {b})x = {a + b}x: складываются коэффициенты, буква x сохраняется.",
                "Вынеси общий множитель x за скобки.",
                m5,
            )
        if question_type == "reverse_distribution":
            return _QuestionParts(
                "Какая запись показывает приведение 5x + 2x через распределительный закон?",
                ("(5 + 2)x = 7x", "(5·2)x = 10x", "5 + 2 + x = 7 + x", "5x² + 2x²"),
                "Общий множитель x выносится: 5x + 2x = (5 + 2)x.",
                "Распределительный закон можно читать справа налево.",
                m5,
            )
        if question_type == "collect_negative":
            return _QuestionParts(
                "Приведи подобные: 3x − 5x",
                ("−2x", "2x", "−8x", "8x"),
                "(3 − 5)x = −2x.",
                "Вычисли разность коэффициентов 3 − 5.",
                m3,
            )
        if question_type == "implicit_one":
            return _QuestionParts(
                "Упрости: 4x − x",
                ("3x", "4", "5x", "3"),
                "У x коэффициент 1: 4x − 1x = 3x.",
                "Замени x на 1x.",
                m5,
            )
        if question_type == "collect_constants":
            return _QuestionParts(
                "Упрости: 3x + 2 + 4x + 5",
                ("7x + 7", "14x", "7x + 5", "12x"),
                "3x + 4x = 7x, а 2 + 5 = 7. Получаем 7x + 7.",
                "Собери отдельно x-слагаемые и отдельно числа.",
                m8,
            )
        if question_type == "sort_terms":
            return _QuestionParts(
                "Как лучше сгруппировать 5 + 2x − 3 + 4x перед вычислением?",
                (
                    "(2x + 4x) + (5 − 3)",
                    "(5 + 2x) − (3 + 4x)",
                    "(2x − 3) + (4x − 5)",
                    "Все слагаемые сразу перемножить",
                ),
                "Подобные буквенные слагаемые собираем вместе, постоянные — отдельно.",
                "Найди две группы с одинаковым типом слагаемых.",
                m8,
            )
        if question_type == "two_variables":
            return _QuestionParts(
                "Упрости: 3x + 2y + 4x − y",
                ("7x + y", "9xy", "7x + 3y", "6x + y"),
                "3x + 4x = 7x, а 2y − y = y. Буквы x и y не смешиваются. Ответ: 7x + y.",
                "Собери отдельно коэффициенты при x и при y.",
                m4,
            )
        if question_type == "group_two_variables":
            return _QuestionParts(
                "Какой промежуточный шаг верен для 5x − 2y − 3x + 4y?",
                (
                    "(5x − 3x) + (−2y + 4y)",
                    "(5x − 2y) − (3x + 4y)",
                    "(5 − 2 − 3 + 4)xy",
                    "(5x + 4y) − (2y − 3x)",
                ),
                "Группируем одинаковые буквенные части: x с x, y с y, сохраняя знаки.",
                "Перепиши каждое слагаемое вместе с его знаком.",
                m3,
            )
        if question_type == "simplify_one_group":
            a, b, c = rng.choice(((2, 3, 1), (3, 2, 2), (4, 2, 3)))
            answer = _linear(a + c, a * b)
            return _QuestionParts(
                f"Раскрой скобки и упрости: {a}(x + {b}) + {c}x",
                _unique_answers(
                    answer, f"{a}x + {a * b} + {c}x", _linear(a + c, b), _linear(a * c, a * b)
                ),
                (
                    f"Сначала {a}(x + {b}) = {a}x + {a * b}; затем {a}x + {c}x "
                    f"= {a + c}x. Ответ: {answer}."
                ),
                "Сначала раскрой скобки, потом найди подобные x-слагаемые.",
                m8,
            )
        if question_type == "stop_after_expansion":
            return _QuestionParts(
                "Ученик получил 2x + 6 + x из 2(x + 3) + x. Что делать дальше?",
                (
                    "Привести 2x и x: получить 3x + 6",
                    "Остановиться: выражение уже полностью упрощено",
                    "Сложить все числа и получить 9x",
                    "Умножить 6 на x",
                ),
                "Скобки раскрыты верно, но подобные 2x и x ещё нужно объединить.",
                "Проверь, остались ли слагаемые с одинаковой буквенной частью.",
                m8,
            )
        if question_type == "subtract_group":
            return _QuestionParts(
                "Раскрой скобки и упрости: 3x − (x − 4)",
                ("2x + 4", "2x − 4", "4x − 4", "4x + 4"),
                "−(x − 4) = −x + 4, затем 3x − x = 2x. Ответ: 2x + 4.",
                "Сначала перепиши внешний минус как умножение всей группы на −1.",
                m7,
            )
        if question_type == "sign_error":
            return _QuestionParts(
                "В преобразовании 3x − (x − 4) → 3x − x − 4 какой знак неверен?",
                (
                    "Перед 4: должно быть +4",
                    "Перед x: должно быть +x",
                    "Перед 3x: должен быть минус",
                    "Все знаки верны",
                ),
                "Внешний −1 умножается на −4, поэтому появляется +4.",
                "Проверь произведение (−1)·(−4).",
                m7,
            )
        if question_type == "two_groups":
            return _QuestionParts(
                "Раскрой скобки и упрости: 2(x + 3) − 3(x − 1)",
                ("−x + 9", "−x + 3", "5x + 9", "x + 9"),
                "2x + 6 − 3x + 3 = −x + 9.",
                "Распредели 2 по первой группе и −3 по второй, затем собери подобные.",
                m8,
            )
        if question_type == "final_target":
            return _QuestionParts(
                "Раскрой скобки и упрости: 3(2x − 1) − 2(x + 4)",
                ("4x − 11", "4x + 5", "8x − 11", "4x − 5"),
                (
                    "3(2x − 1) = 6x − 3; −2(x + 4) = −2x − 8. "
                    "Затем 6x − 2x = 4x и −3 − 8 = −11. Ответ: 4x − 11."
                ),
                "Сначала получи четыре слагаемых: два из каждой группы.",
                m8,
            )
        if question_type == "distribution_error":
            return _QuestionParts(
                "Ученик написал 4(x + 2) = 4x + 2. Как точнее объяснить ошибку?",
                (
                    "Множитель 4 не применён ко второму слагаемому группы",
                    "Коэффициент при x должен остаться 1",
                    "Плюс нужно заменить минусом",
                    "Слагаемые x и 2 надо перемножить",
                ),
                "Число 4 умножает всю группу: 4·x + 4·2 = 4x + 8.",
                "Покажи стрелками два произведения от внешнего множителя.",
                m1,
            )
        if question_type == "like_terms_error":
            return _QuestionParts(
                "Ученик написал 2x + 3 = 5x. Как точнее объяснить ошибку?",
                (
                    "2x и 3 не подобны: у числа 3 нет буквенной части x",
                    "Нужно получить 6x",
                    "Складывать коэффициенты вообще нельзя",
                    "Нужно получить 5x²",
                ),
                "Объединять можно только подобные слагаемые. Выражение 2x + 3 уже упрощено.",
                "Сравни буквенную часть 2x и постоянного числа 3.",
                m4,
            )
        raise ValueError(f"неподдерживаемый тип вопроса: {question_type}")

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult:
        correct_answer = dict(question_payload["correct_answer"])
        is_correct = selected_answer.get("value") == correct_answer.get("value")
        explanation = str(question_payload["explanation_payload"]["equation"])
        metadata = dict(question_payload.get("metadata", {}))
        hints = list(metadata.get("hints", []))
        return EvaluationResult(
            is_correct=is_correct,
            canonical_answer=correct_answer,
            feedback_key="feedback.correct" if is_correct else "feedback.incorrect",
            feedback_payload={
                "equation": explanation,
                "misconception": "" if is_correct else str(metadata.get("misconception", "")),
            },
            hint_key=None if is_correct else "feedback.hint",
            hint_payload=None
            if is_correct
            else {"hint": str(hints[0]) if hints else "Проверь каждый шаг преобразования."},
        )

    def retry_question_type(self, skill_key: str, question_type: str, rng: Random) -> str:
        try:
            choices = QUESTION_TYPES[skill_key]
        except KeyError as exc:
            raise ValueError(f"неизвестный навык выражений: {skill_key}") from exc
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
        ranked = sorted(
            self._skills,
            key=lambda item: (
                mastery.get(item.skill_key, MasteryState(item.skill_key)).box,
                -mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count,
                item.difficulty,
            ),
        )
        return TopicProgressView(
            headline_metrics=(
                Metric("Всего ответов", str(int(metrics.get("total", 0)))),
                Metric("Ответов за 7 дней", str(int(metrics.get("recent", 0)))),
                Metric("Точность за последнее время", f"{int(metrics.get('accuracy', 0))}%"),
                Metric("Освоено навыков", str(len(mastered))),
                Metric("Дней занятий", str(int(metrics.get("active_days", 0)))),
            ),
            progress_groups=tuple(groups),
            strengths=tuple(
                ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
                for item in mastered[:3]
            ),
            current_targets=tuple(
                ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
                for item in ranked[:3]
            ),
            suggested_action=SuggestedAction("Потренировать трудные места", "practice:weak"),
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
                correct = sum(bool(item["is_correct"]) for item in relevant)
                result.append(Metric(label, f"{round(correct / len(relevant) * 100)}%"))
        return tuple(result)

    def teacher_insights(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> tuple[ProgressItem, ...]:
        misconceptions: dict[str, int] = {}
        for state in mastery.values():
            for label, count in dict(state.state.get("misconceptions", {})).items():
                misconceptions[str(label)] = misconceptions.get(str(label), 0) + int(count)
        ranked = sorted(misconceptions.items(), key=lambda item: (-item[1], item[0]))[:3]
        return (
            ProgressItem("Использовано подсказок", str(int(metrics.get("hints", 0)))),
            ProgressItem("Заданий дня за 7 дней", str(int(metrics.get("daily", 0)))),
            *(ProgressItem(label, f"замечено: {count}") for label, count in ranked),
        )

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]:
        del rng
        rotations = (
            ("terms:sign", "signed_term"),
            ("parentheses:plus", "remove_plus"),
            ("parentheses:minus_difference", "minus_difference"),
            ("distribution:numeric", "numeric_distribution"),
            ("distribution:positive_sum", "expand_positive_sum"),
            ("like:identify", "find_like"),
            ("collect:positive", "collect_positive"),
            ("collect:constants", "collect_constants"),
            ("simplify:one_group", "simplify_one_group"),
        )
        offset = now.date().toordinal() % len(rotations)
        shifted = rotations[offset:] + rotations[:offset]
        score = min(
            (
                mastery.get(skill, MasteryState(skill)).box,
                mastery.get(skill, MasteryState(skill)).attempt_count,
            )
            for skill, _ in shifted
        )
        skill_key = next(
            skill
            for skill, _ in shifted
            if (
                mastery.get(skill, MasteryState(skill)).box,
                mastery.get(skill, MasteryState(skill)).attempt_count,
            )
            == score
        )
        return skill_key, dict(shifted)[skill_key]

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes:
        del renderer_id, payload
        raise ValueError("для темы выражений изображения не используются")

    def validate(self) -> list[str]:
        errors = validate_topic_contract(self)
        if len(self.learning_units()) != 15:
            errors.append("нужна полная последовательность из 15 разделов теории")
        if len(self.practice_modes()) != 9:
            errors.append("нужны все 9 режимов тренировки")
        if len(self.test_definitions()) != 4:
            errors.append("нужны все 4 проверочные работы")
        for skill_key, question_types in QUESTION_TYPES.items():
            if len(question_types) < 2:
                errors.append(f"для навыка мало форматов: {skill_key}")
            for question_type in question_types:
                try:
                    for seed in range(4):
                        question = self.generate_question(skill_key, question_type, Random(seed))
                        validate_options(question.answer_mode, question.answer_options)
                        if not self.evaluate_answer(
                            {
                                "correct_answer": question.correct_answer,
                                "explanation_payload": question.explanation_payload,
                                "metadata": question.metadata,
                            },
                            question.correct_answer,
                        ).is_correct:
                            errors.append(f"правильный ответ отклонён: {skill_key}/{question_type}")
                except Exception as exc:
                    errors.append(f"ошибка вопроса {skill_key}/{question_type}: {exc}")
        for unit in self.learning_units():
            try:
                view = self.render_learning_unit(unit.unit_id)
                if not view.title or not view.body:
                    errors.append(f"пустой раздел теории: {unit.unit_id}")
            except Exception as exc:
                errors.append(f"ошибка раздела теории {unit.unit_id}: {exc}")
        return errors
