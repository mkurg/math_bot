from collections.abc import Iterable

from app.core.topics.contracts import AnswerOption


def validate_options(answer_mode: str, options: Iterable[AnswerOption]) -> None:
    values = list(options)
    pad_modes = {"binary_pad", "octal_pad", "decimal_pad", "hexadecimal_pad"}
    if answer_mode not in {"single_choice", "true_false", *pad_modes}:
        raise ValueError(f"unregistered answer mode: {answer_mode}")
    if answer_mode in pad_modes:
        if values:
            raise ValueError(f"{answer_mode} does not use answer options")
        return
    expected = 2 if answer_mode == "true_false" else 4
    if len(values) != expected:
        raise ValueError(f"{answer_mode} requires {expected} options")
    serialized = [repr(option.value) for option in values]
    if len(serialized) != len(set(serialized)):
        raise ValueError("answer options must be unique")
