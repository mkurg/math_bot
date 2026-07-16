import re

ANSWER_CALLBACK = re.compile(r"^a:([A-Za-z0-9_-]{4,16}):([0-3])$")


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
