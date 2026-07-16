import re

ANSWER_CALLBACK = re.compile(r"^a:([A-Za-z0-9_-]{4,16}):([0-3])$")
PAD_CALLBACK = re.compile(r"^p:([A-Za-z0-9_-]{4,16}):(-|[0-9A-F]{1,16}):([0-9A-Fxcsn])$")
HINT_CALLBACK = re.compile(r"^h:([A-Za-z0-9_-]{4,16})$")


def answer_callback(public_id: str, option_index: int) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{4,16}", public_id):
        raise ValueError("invalid public question ID")
    if option_index not in range(4):
        raise ValueError("invalid option index")
    return f"a:{public_id}:{option_index}"


def parse_answer_callback(value: str) -> tuple[str, int]:
    match = ANSWER_CALLBACK.fullmatch(value)
    if not match:
        raise ValueError("invalid answer callback")
    return match.group(1), int(match.group(2))


def pad_callback(public_id: str, current: str, action: str) -> str:
    value = f"p:{public_id}:{current or '-'}:{action}"
    if not PAD_CALLBACK.fullmatch(value):
        raise ValueError("invalid numeral-pad callback")
    return value


def parse_pad_callback(value: str) -> tuple[str, str, str]:
    match = PAD_CALLBACK.fullmatch(value)
    if not match:
        raise ValueError("invalid numeral-pad callback")
    return match.group(1), "" if match.group(2) == "-" else match.group(2), match.group(3)


def hint_callback(public_id: str) -> str:
    value = f"h:{public_id}"
    if not HINT_CALLBACK.fullmatch(value):
        raise ValueError("invalid hint callback")
    return value


def parse_hint_callback(value: str) -> str:
    match = HINT_CALLBACK.fullmatch(value)
    if not match:
        raise ValueError("invalid hint callback")
    return match.group(1)
