from __future__ import annotations

from collections.abc import Callable
from random import Random
from typing import Any

from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import AnswerOption, GeneratedMedia, GeneratedQuestion
from app.topics.times_tables.distractors import numeric_options
from app.topics.times_tables.skills import parse_skill_key

ContentGetter = Callable[..., str]
RawContentGetter = Callable[[str], Any]


def _answers(correct: int, group_size: int, rng: Random) -> tuple[AnswerOption, ...]:
    return tuple(
        AnswerOption(label=str(value), value={"value": value})
        for value in numeric_options(correct, group_size, rng)
    )


def _question(
    *,
    skill_key: str,
    kind: str,
    prompt: str,
    correct: int | bool,
    equation: str,
    hint: str,
    options: tuple[AnswerOption, ...],
    payload: dict[str, Any],
    media: GeneratedMedia | None = None,
    answer_mode: str = "single_choice",
) -> GeneratedQuestion:
    validate_options(answer_mode, options)
    return GeneratedQuestion(
        topic_id="times_tables",
        skill_key=skill_key,
        question_type=kind,
        rendered_prompt=prompt,
        answer_mode=answer_mode,
        answer_options=options,
        correct_answer={"value": correct},
        explanation_payload={"equation": equation, "hint": hint},
        metadata=payload,
        media=media,
    )


def _factor_order(low: int, high: int, rng: Random) -> tuple[int, int]:
    if low != high and rng.choice((True, False)):
        return high, low
    return low, high


def generate(
    skill_key: str,
    question_type: str,
    rng: Random,
    content: ContentGetter,
    raw_content: RawContentGetter,
) -> GeneratedQuestion:
    operation, low, high = parse_skill_key(skill_key)
    first, second = _factor_order(low, high, rng)
    product = first * second
    hint = content("hint.generic", first=first, second=second, product=product)

    if question_type == "direct_multiplication":
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=content("prompt.direct_mul", first=first, second=second),
            correct=product,
            equation=f"{first} × {second} = {product}",
            hint=hint,
            options=_answers(product, first, rng),
            payload={"operation": "mul", "first": first, "second": second},
        )

    divisor = rng.choice((low, high))
    quotient = product // divisor
    division_equation = f"{product} ÷ {divisor} = {quotient}"
    if question_type == "direct_division":
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=content("prompt.direct_div", product=product, divisor=divisor),
            correct=quotient,
            equation=division_equation,
            hint=content("hint.division", product=product, divisor=divisor, quotient=quotient),
            options=_answers(quotient, 1, rng),
            payload={"operation": "div", "product": product, "divisor": divisor},
        )
    if question_type == "missing_factor":
        missing_first = rng.choice((True, False))
        prompt = (
            content("prompt.missing_factor_first", first=first, product=product)
            if missing_first
            else content("prompt.missing_factor_second", second=second, product=product)
        )
        correct = second if missing_first else first
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=prompt,
            correct=correct,
            equation=f"{first} × {second} = {product}",
            hint=hint,
            options=_answers(correct, 1, rng),
            payload={"operation": "mul", "first": first, "second": second},
        )
    if question_type == "missing_divisor":
        if rng.choice((True, False)):
            prompt = content("prompt.missing_divisor", product=product, quotient=quotient)
            correct = divisor
        else:
            prompt = content("prompt.direct_div", product=product, divisor=divisor)
            correct = quotient
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=prompt,
            correct=correct,
            equation=division_equation,
            hint=content("hint.division", product=product, divisor=divisor, quotient=quotient),
            options=_answers(correct, 1, rng),
            payload={"operation": "div", "product": product, "divisor": divisor},
        )
    if question_type == "true_false":
        is_true = rng.choice((True, False))
        shown = product if is_true else numeric_options(product, first, rng)[0]
        if shown == product and not is_true:
            shown = product + first if product + first <= 100 else product - first
        options = (
            AnswerOption(label=content("answer.true"), value={"value": True}),
            AnswerOption(label=content("answer.false"), value={"value": False}),
        )
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=content("prompt.true_false", first=first, second=second, shown=shown),
            correct=is_true,
            equation=f"{first} × {second} = {product}",
            hint=hint,
            options=options,
            payload={"operation": "mul", "first": first, "second": second},
            answer_mode="true_false",
        )
    if question_type == "visual":
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=content("prompt.visual", rows=first, columns=second),
            correct=product,
            equation=f"{first} groups of {second} = {product}",
            hint=content("hint.visual", rows=first, columns=second),
            options=_answers(product, second, rng),
            payload={"operation": "mul", "first": first, "second": second},
            media=GeneratedMedia(
                renderer_id="array",
                payload={"rows": first, "columns": second},
                fallback_text=content("fallback.visual", rows=first, columns=second),
            ),
        )
    if question_type == "story":
        story_operation = operation
        templates = raw_content(f"story.{story_operation}")
        if not isinstance(templates, list) or not templates:
            raise ValueError(f"missing story templates for {story_operation}")
        template = str(rng.choice(templates))
        if story_operation == "mul":
            prompt = template.format(groups=first, size=second, total=product)
            correct = product
            group_size = first
            equation = f"{first} × {second} = {product}"
        else:
            prompt = template.format(groups=divisor, size=quotient, total=product)
            correct = quotient
            group_size = 1
            equation = division_equation
        return _question(
            skill_key=skill_key,
            kind=question_type,
            prompt=prompt,
            correct=correct,
            equation=equation,
            hint=content("hint.story"),
            options=_answers(correct, group_size, rng),
            payload={"operation": story_operation, "first": first, "second": second},
        )
    raise ValueError(f"unknown times-table question type: {question_type}")
