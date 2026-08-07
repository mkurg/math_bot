from __future__ import annotations

from app.core.topics.contracts import SkillDefinition

GROUP_LABELS = {
    "terms": "Части выражения",
    "parentheses": "Знаки и скобки",
    "distribution": "Распределительный закон",
    "like_terms": "Подобные слагаемые",
    "simplification": "Раскрытие и упрощение",
    "reasoning": "Объяснение и поиск ошибок",
}

SKILL_LABELS = {
    "terms:identify": "Находить слагаемые",
    "terms:sign": "Относить знак к слагаемому",
    "terms:coefficient": "Находить коэффициент",
    "parentheses:group": "Видеть в скобках единую группу",
    "parentheses:plus": "Убирать скобки после плюса",
    "parentheses:minus_sum": "Раскрывать минус перед суммой",
    "parentheses:minus_difference": "Раскрывать минус перед разностью",
    "distribution:numeric": "Объяснять распределение на числах",
    "distribution:positive_sum": "Распределять множитель по сумме",
    "distribution:positive_difference": "Распределять множитель по разности",
    "distribution:coefficient": "Умножать коэффициенты при раскрытии",
    "distribution:negative": "Раскрывать скобки с отрицательным множителем",
    "like:identify": "Находить подобные слагаемые",
    "like:unlike": "Не объединять неподобные слагаемые",
    "collect:positive": "Складывать положительные коэффициенты",
    "collect:negative": "Работать с отрицательными коэффициентами",
    "collect:constants": "Объединять постоянные слагаемые",
    "collect:two_variables": "Группировать слагаемые с x и y",
    "simplify:one_group": "Раскрывать одни скобки и упрощать",
    "simplify:subtract_group": "Вычитать выражение в скобках",
    "simplify:two_groups": "Упрощать выражение с двумя группами",
    "reasoning:errors": "Объяснять типичные ошибки",
}


def skill_catalogue() -> tuple[SkillDefinition, ...]:
    definitions = (
        ("terms:identify", "terms", (), 1, ("terms",)),
        ("terms:sign", "terms", ("terms:identify",), 1, ("terms", "sign")),
        (
            "terms:coefficient",
            "terms",
            ("terms:identify",),
            2,
            ("coefficient",),
        ),
        (
            "parentheses:group",
            "parentheses",
            ("terms:identify",),
            1,
            ("group",),
        ),
        (
            "parentheses:plus",
            "parentheses",
            ("parentheses:group",),
            1,
            ("plus",),
        ),
        (
            "parentheses:minus_sum",
            "parentheses",
            ("parentheses:plus", "terms:sign"),
            2,
            ("minus", "distribution"),
        ),
        (
            "parentheses:minus_difference",
            "parentheses",
            ("parentheses:minus_sum",),
            3,
            ("minus", "double_negative"),
        ),
        (
            "distribution:numeric",
            "distribution",
            ("parentheses:group",),
            2,
            ("numeric", "distribution"),
        ),
        (
            "distribution:positive_sum",
            "distribution",
            ("distribution:numeric",),
            3,
            ("positive", "sum"),
        ),
        (
            "distribution:positive_difference",
            "distribution",
            ("distribution:positive_sum",),
            3,
            ("positive", "difference"),
        ),
        (
            "distribution:coefficient",
            "distribution",
            ("distribution:positive_sum", "terms:coefficient"),
            4,
            ("coefficient", "distribution"),
        ),
        (
            "distribution:negative",
            "distribution",
            ("distribution:positive_difference", "parentheses:minus_difference"),
            4,
            ("negative", "distribution"),
        ),
        (
            "like:identify",
            "like_terms",
            ("terms:identify",),
            2,
            ("like_terms",),
        ),
        (
            "like:unlike",
            "like_terms",
            ("like:identify",),
            2,
            ("unlike_terms",),
        ),
        (
            "collect:positive",
            "like_terms",
            ("like:identify", "terms:coefficient"),
            3,
            ("collect", "positive"),
        ),
        (
            "collect:negative",
            "like_terms",
            ("collect:positive", "terms:sign"),
            4,
            ("collect", "negative"),
        ),
        (
            "collect:constants",
            "like_terms",
            ("like:identify",),
            3,
            ("constants",),
        ),
        (
            "collect:two_variables",
            "like_terms",
            ("collect:negative", "like:unlike"),
            5,
            ("two_variables",),
        ),
        (
            "simplify:one_group",
            "simplification",
            ("distribution:positive_difference", "collect:positive"),
            5,
            ("expand", "collect"),
        ),
        (
            "simplify:subtract_group",
            "simplification",
            ("parentheses:minus_difference", "collect:negative"),
            6,
            ("subtract_group",),
        ),
        (
            "simplify:two_groups",
            "simplification",
            ("simplify:one_group", "distribution:negative"),
            7,
            ("two_groups", "multi_step"),
        ),
        (
            "reasoning:errors",
            "reasoning",
            ("parentheses:minus_sum", "distribution:positive_sum", "like:unlike"),
            4,
            ("explanation", "misconception"),
        ),
    )
    return tuple(
        SkillDefinition(
            skill_key=key,
            group_key=group,
            title_key=f"skill.{key.replace(':', '.')}.title",
            description_key=f"skill.{key.replace(':', '.')}.description",
            prerequisites=prerequisites,
            difficulty=difficulty,
            tags=tags,
        )
        for key, group, prerequisites, difficulty, tags in definitions
    )


def skill_label(skill_key: str) -> str:
    try:
        return SKILL_LABELS[skill_key]
    except KeyError as exc:
        raise ValueError(f"неизвестный навык алгебраических выражений: {skill_key}") from exc
