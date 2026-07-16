from collections.abc import Iterable

from app.core.topics.contracts import AnswerOption


def validate_options(answer_mode: str, options: Iterable[AnswerOption]) -> None:
    values = list(options)
    if answer_mode not in {"single_choice", "true_false"}:
        raise ValueError(f"unregistered answer mode: {answer_mode}")
    expected = 2 if answer_mode == "true_false" else 4
    if len(values) != expected:
        raise ValueError(f"{answer_mode} requires {expected} options")
    serialized = [repr(option.value) for option in values]
    if len(serialized) != len(set(serialized)):
        raise ValueError("answer options must be unique")
