from __future__ import annotations

from collections.abc import Callable, Iterable
from random import Random

from app.core.topics.contracts import (
    AnswerOption,
    GeneratedMedia,
    GeneratedQuestion,
)

BASE_NAMES = {2: "binary", 8: "octal", 10: "decimal", 16: "hexadecimal"}
BASE_SUFFIXES = {2: "₂", 8: "₈", 10: "₁₀", 16: "₁₆"}
PAD_MODES = {2: "binary_pad", 8: "octal_pad", 10: "decimal_pad", 16: "hexadecimal_pad"}
MAX_LENGTHS = {2: 8, 8: 3, 10: 3, 16: 2}

CONVERSIONS: dict[str, tuple[int, int]] = {
    "binary_decimal:bin_to_dec": (2, 10),
    "binary_decimal:dec_to_bin": (10, 2),
    "octal:bin_to_oct": (2, 8),
    "octal:oct_to_bin": (8, 2),
    "octal:dec_to_oct": (10, 8),
    "octal:oct_to_dec": (8, 10),
    "hexadecimal:bin_to_hex": (2, 16),
    "hexadecimal:hex_to_bin": (16, 2),
    "hexadecimal:dec_to_hex": (10, 16),
    "hexadecimal:hex_to_dec": (16, 10),
    "cross_base:oct_to_hex": (8, 16),
    "cross_base:hex_to_oct": (16, 8),
    "rgb:dec_to_hex": (10, 16),
    "rgb:hex_to_dec": (16, 10),
}

ASCII_CHARACTERS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 !?.")


def digits(value: int, base: int, width: int | None = None) -> str:
    if not 0 <= value <= 255:
        raise ValueError("generated values must fit one unsigned byte")
    if base == 2:
        result = format(value, "b")
    elif base == 8:
        result = format(value, "o")
    elif base == 10:
        result = str(value)
    elif base == 16:
        result = format(value, "X")
    else:
        raise ValueError("only bases 2, 8, 10, and 16 are supported")
    return result.zfill(width) if width is not None else result


def labelled(value: int, base: int, width: int | None = None) -> str:
    return f"{digits(value, base, width)}{BASE_SUFFIXES[base]}"


def _group_from_right(value: str, size: int) -> str:
    padding = (-len(value)) % size
    padded = "0" * padding + value
    return " ".join(padded[index : index + size] for index in range(0, len(padded), size))


def _options(
    correct_label: str,
    correct_value: str,
    distractors: Iterable[tuple[str, str]],
    rng: Random,
) -> tuple[AnswerOption, ...]:
    unique: list[tuple[str, str]] = [(correct_label, correct_value)]
    for label, value in distractors:
        if value not in {item[1] for item in unique}:
            unique.append((label, value))
        if len(unique) == 4:
            break
    if len(unique) != 4:
        raise ValueError("four unique answer options are required")
    rng.shuffle(unique)
    return tuple(AnswerOption(label, {"value": value}) for label, value in unique)


def _number_distractors(value: int, base: int) -> list[tuple[str, str]]:
    candidates = (value + 1, value - 1, value + 2, value ^ 3, value + 8, value // 2)
    result: list[tuple[str, str]] = []
    for candidate in candidates:
        if 0 <= candidate <= 255 and candidate != value:
            rendered = digits(candidate, base)
            result.append((f"{rendered}{BASE_SUFFIXES[base]}", rendered))
    return result


def _choice(
    skill_key: str,
    question_type: str,
    prompt: str,
    correct_label: str,
    correct_value: str,
    distractors: Iterable[tuple[str, str]],
    explanation: str,
    hints: tuple[str, ...],
    misconception: str,
    rng: Random,
    media: GeneratedMedia | None = None,
) -> GeneratedQuestion:
    options = _options(correct_label, correct_value, distractors, rng)
    return GeneratedQuestion(
        topic_id="numeral_systems",
        skill_key=skill_key,
        question_type=question_type,
        rendered_prompt=prompt,
        answer_mode="single_choice",
        answer_options=options,
        correct_answer={"value": correct_value},
        explanation_payload={
            "equation": explanation,
            "hint": hints[0],
            "misconception": misconception,
        },
        metadata={"hints": list(hints[:3])},
        media=media,
    )


def _pad(
    skill_key: str,
    question_type: str,
    prompt: str,
    correct: str,
    target_base: int,
    explanation: str,
    hints: tuple[str, ...],
    misconception: str,
    *,
    fixed_width: bool = False,
    max_length: int | None = None,
    media: GeneratedMedia | None = None,
) -> GeneratedQuestion:
    return GeneratedQuestion(
        topic_id="numeral_systems",
        skill_key=skill_key,
        question_type=question_type,
        rendered_prompt=prompt,
        answer_mode=PAD_MODES[target_base],
        answer_options=(),
        correct_answer={"value": correct},
        explanation_payload={
            "equation": explanation,
            "hint": hints[0],
            "misconception": misconception,
        },
        metadata={
            "hints": list(hints[:3]),
            "fixed_width": fixed_width,
            "max_length": max_length or MAX_LENGTHS[target_base],
            "target_base": target_base,
        },
        media=media,
    )


def _conversion_explanation(value: int, source: int, target: int) -> tuple[str, tuple[str, ...]]:
    source_text = labelled(value, source)
    target_text = labelled(value, target)
    if source == 2 and target in {8, 16}:
        size = 3 if target == 8 else 4
        grouped = _group_from_right(digits(value, 2), size)
        word = "three" if size == 3 else "four"
        return (
            f"Group from the right in sets of {word}: {grouped}. "
            f"The groups give {target_text}, so {source_text} = {target_text}.",
            (
                f"Use groups of {word} bits, starting at the right.",
                f"Pad the leftmost group with zeroes if it is short: {grouped}.",
                f"Convert each group to one base-{target} digit.",
            ),
        )
    if source in {8, 16} and target == 2:
        size = 3 if source == 8 else 4
        grouped = " ".join(
            digits(int(character, source), 2, size) for character in digits(value, source)
        )
        return (
            f"Replace each base-{source} digit with exactly {size} bits: {grouped}. "
            f"Therefore {source_text} = {target_text}.",
            (
                f"Each base-{source} digit maps to exactly {size} bits.",
                "Convert the digits separately, then join the bit groups.",
                f"The complete value is {target_text}.",
            ),
        )
    if {source, target} == {8, 16}:
        binary = digits(value, 2)
        return (
            f"Use binary as the structural bridge: {source_text} = {binary}₂ = {target_text}.",
            (
                "Convert the source digits into bit groups first.",
                f"The shared binary value is {binary}₂.",
                "Regroup those bits for the target base.",
            ),
        )
    return (
        f"Both representations have value {value}: {source_text} = {value}₁₀ = {target_text}.",
        (
            f"Use place values or repeated division by {target}.",
            f"The value being represented is {value}.",
            f"Write {value} using the digits of base {target}.",
        ),
    )


def _direct_conversion(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    try:
        source, target = CONVERSIONS[skill_key]
    except KeyError as exc:
        raise ValueError(f"skill does not define a direct conversion: {skill_key}") from exc
    value = rng.randint(5, 254)
    source_value = digits(value, source)
    target_value = digits(value, target)
    explanation, hints = _conversion_explanation(value, source, target)
    media = None
    if source == 2 and target in {8, 16}:
        media = GeneratedMedia(
            "grouping",
            {"bits": source_value, "size": 3 if target == 8 else 4},
            f"Group {source_value} from the right.",
        )
    return _pad(
        skill_key,
        question_type,
        f"Convert {labelled(value, source)} to {BASE_NAMES[target]}. "
        f"Build only the base-{target} digits.",
        target_value,
        target,
        explanation,
        hints,
        "uses the wrong conversion structure",
        media=media,
    )


def _positional_expansion(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    base = rng.choice((2, 8, 16))
    value = rng.randint(base + 1, min(255, base * base - 1))
    representation = digits(value, base)
    terms = [
        int(character, base) * base**power
        for power, character in enumerate(reversed(representation))
    ]
    correct_label = " + ".join(str(term) for term in terms)
    distractors = [
        (" + ".join(str(int(character, base)) for character in representation), "digits-only"),
        (" + ".join(str(term + base) for term in terms), "shifted"),
        (" + ".join(str(term) for term in reversed(terms)), "reversed"),
    ]
    return _choice(
        skill_key,
        question_type,
        f"Which place-value expansion represents {representation}{BASE_SUFFIXES[base]}?",
        correct_label,
        "correct",
        distractors,
        f"In base {base}, positions from the right are {base}⁰, {base}¹, and so on. "
        f"The value is {correct_label} = {value}.",
        (
            "Start at the right with the units place.",
            f"Each step left multiplies the place value by {base}.",
            correct_label,
        ),
        "confuses positional place values",
        rng,
        GeneratedMedia(
            "place_values", {"digits": representation, "base": base}, "Place-value columns"
        ),
    )


def _base_identification(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    base = rng.choice((2, 8, 10, 16))
    correct = {2: "0 and 1", 8: "0 through 7", 10: "0 through 9", 16: "0–9 and A–F"}[base]
    alternatives = [
        ("0 and 1", "2"),
        ("0 through 7", "8"),
        ("0 through 9", "10"),
        ("0–9 and A–F", "16"),
    ]
    return _choice(
        skill_key,
        question_type,
        f"Which digit set is valid in base {base}?",
        correct,
        str(base),
        (item for item in alternatives if item[1] != str(base)),
        f"Base {base} needs exactly {base} digit symbols, "
        f"representing values 0 through {base - 1}.",
        (
            "A base uses digits from zero up to one less than the base.",
            f"The largest digit value is {base - 1}.",
            correct,
        ),
        "uses a digit that is not valid in the base",
        rng,
    )


def _equivalent(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    value = rng.randint(9, 240)
    target = rng.choice((2, 8, 10, 16))
    source = rng.choice(tuple(base for base in (2, 8, 10, 16) if base != target))
    correct = labelled(value, target)
    return _choice(
        skill_key,
        question_type,
        f"Which representation has the same value as {labelled(value, source)}?",
        correct,
        digits(value, target),
        _number_distractors(value, target),
        f"The number is the value {value}; {labelled(value, source)} and {correct} "
        "are two representations of that same value.",
        (
            "Find the value, not a similar-looking digit string.",
            f"The shared value is {value}₁₀.",
            correct,
        ),
        "confuses value with visible digits",
        rng,
    )


def _comparison(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    left_value = rng.randint(5, 240)
    right_value = max(0, min(255, left_value + rng.choice((-9, -3, 0, 4, 11))))
    left_base, right_base = rng.sample((2, 8, 10, 16), 2)
    relation = "=" if left_value == right_value else ">" if left_value > right_value else "<"
    return _choice(
        skill_key,
        question_type,
        f"Choose the correct comparison: {labelled(left_value, left_base)} "
        f"? {labelled(right_value, right_base)}",
        relation,
        relation,
        ((symbol, symbol) for symbol in ("<", ">", "=", "cannot compare") if symbol != relation),
        f"Their values are {left_value} and {right_value}, so "
        f"{labelled(left_value, left_base)} {relation} "
        f"{labelled(right_value, right_base)}.",
        (
            "Convert both representations to values before comparing.",
            f"Left: {left_value}; right: {right_value}.",
            f"The correct sign is {relation}.",
        ),
        "compares visible digits instead of values",
        rng,
    )


def _missing_digit(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    base = rng.choice((8, 16))
    value = rng.randint(base, min(255, base * base - 1))
    representation = digits(value, base)
    position = rng.randrange(len(representation))
    missing = representation[position]
    shown = representation[:position] + "?" + representation[position + 1 :]
    candidates = [missing]
    for character in "0123456789ABCDEF"[:base]:
        if character != missing:
            candidates.append(character)
        if len(candidates) == 4:
            break
    return _choice(
        skill_key,
        question_type,
        f"Which digit completes {shown}{BASE_SUFFIXES[base]} = {value}₁₀?",
        missing,
        missing,
        ((item, item) for item in candidates if item != missing),
        f"{representation}{BASE_SUFFIXES[base]} has value {value}, "
        f"so the missing digit is {missing}.",
        (
            "Use the place value of the missing position.",
            f"Only digits below {base} are valid here.",
            f"The complete representation is {representation}{BASE_SUFFIXES[base]}.",
        ),
        "misplaces a digit in positional notation",
        rng,
    )


def _error_detection(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    cases = (
        (
            "A student groups 1011011₂ as 101 101 1 to convert it to octal.",
            "The groups must start from the right.",
            "groups bits from the wrong side",
        ),
        (
            "A student writes 128₈.",
            "Digit 8 is not valid in octal.",
            "uses an invalid digit for the base",
        ),
        (
            "A student says one byte has a maximum value of 256.",
            "There are 256 patterns, but values run from 0 through 255.",
            "confuses number of patterns with maximum value",
        ),
        (
            "A student says hexadecimal is what computers store instead of binary.",
            "Computers store bits; hexadecimal is compact notation for humans.",
            "interprets hexadecimal as native storage",
        ),
    )
    prompt, correct, misconception = rng.choice(cases)
    alternatives = (
        ("Nothing is wrong.", "none"),
        ("Every conversion must go through decimal.", "decimal"),
        ("Leading zeroes always change a value.", "zeroes"),
        (correct, "correct"),
    )
    return _choice(
        skill_key,
        question_type,
        f"Find the error. {prompt}",
        correct,
        "correct",
        (item for item in alternatives if item[1] != "correct"),
        correct,
        (
            "Check the structure, not only the final digits.",
            "Which base rule is being broken?",
            correct,
        ),
        misconception,
        rng,
    )


def _method_selection(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    prompts = (
        ("binary to hexadecimal", "Group bits into fours from the right."),
        ("binary to octal", "Group bits into threes from the right."),
        ("octal to hexadecimal", "Map octal to bits, then regroup those bits into fours."),
        ("decimal to hexadecimal", "Use place values or repeated division by sixteen."),
    )
    route, correct = rng.choice(prompts)
    alternatives = (
        ("Group bits into pairs from the left.", "pairs"),
        ("Always convert every digit separately into decimal.", "always-decimal"),
        ("Remove zeroes before choosing a method.", "remove-zeroes"),
        (correct, "correct"),
    )
    return _choice(
        skill_key,
        question_type,
        f"Which is the most useful first step for converting {route}?",
        correct,
        "correct",
        (item for item in alternatives if item[1] != "correct"),
        correct,
        (
            "Look for a structural relationship between the bases.",
            "Powers of two allow direct bit grouping.",
            correct,
        ),
        "chooses an inefficient conversion route",
        rng,
    )


def _explanation_selection(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    hexadecimal = rng.choice((True, False))
    bits = 4 if hexadecimal else 3
    base = 16 if hexadecimal else 8
    correct = (
        f"{bits} bits make 2^{bits} = {base} patterns, matching the {base} base-{base} digits."
    )
    return _choice(
        skill_key,
        question_type,
        f"Why does one base-{base} digit correspond to exactly {bits} bits?",
        correct,
        "correct",
        (
            ("Because decimal says so.", "decimal"),
            (f"Because {bits} is the largest base-{base} digit.", "largest"),
            ("Because computers store hexadecimal letters.", "native"),
        ),
        correct,
        (
            "Count how many patterns the bits can form.",
            f"{bits} bits form 2^{bits} patterns.",
            correct,
        ),
        "does not connect bit patterns to base digits",
        rng,
    )


def _bit_count(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    count = rng.randint(2, 8)
    patterns = 2**count
    return _choice(
        skill_key,
        question_type,
        f"How many different patterns can {count} bits form?",
        str(patterns),
        str(patterns),
        (
            (str(item), str(item))
            for item in (patterns - 1, patterns + 1, count, patterns * 2, count * 2)
        ),
        f"Each bit has two possibilities, so {count} bits form 2^{count} = {patterns} patterns.",
        ("Each added bit doubles the pattern count.", f"Calculate 2^{count}.", str(patterns)),
        "confuses bit count with pattern count",
        rng,
    )


def _range_question(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    del rng
    return _choice(
        skill_key,
        question_type,
        "A byte has 256 possible patterns. Why is its largest unsigned value 255?",
        "The values start at 0, so 256 values end at 255.",
        "correct",
        (
            ("One pattern is always unused.", "unused"),
            ("The last bit cannot be 1.", "last-bit"),
            ("Hexadecimal stops at FE.", "hex"),
        ),
        "Counting 256 values from zero gives 0 through 255. FF₁₆ and 11111111₂ both represent 255.",
        (
            "List the first few values starting at zero.",
            "The first value is 0, not 1.",
            "The range is 0–255.",
        ),
        "confuses number of patterns with maximum value",
        Random(0),
    )


def _byte_decomposition(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    value = rng.randint(16, 254)
    byte = digits(value, 2, 8)
    correct = f"{byte[:4]} | {byte[4:]}"
    return _choice(
        skill_key,
        question_type,
        f"Split the byte {byte}₂ into two nibbles.",
        correct,
        "correct",
        (
            (f"{byte[:3]} | {byte[3:]}", "three-five"),
            (f"{byte[:2]} | {byte[2:]}", "two-six"),
            (f"{byte[:-1]} | {byte[-1:]}", "seven-one"),
        ),
        f"A nibble is four bits, so the byte splits as {correct}.",
        ("A byte has eight bits and a nibble has four.", "Count four bits from the left.", correct),
        "uses the wrong nibble size",
        rng,
        GeneratedMedia("byte", {"bits": byte}, f"Byte: {byte}"),
    )


def _rgb_channel(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    red, green, blue = (rng.randint(16, 239) for _ in range(3))
    code = f"{red:02X}{green:02X}{blue:02X}"
    return _pad(
        skill_key,
        question_type,
        f"Build the six hexadecimal digits for Red = {red}, Green = {green}, "
        f"Blue = {blue}. The # is already supplied.",
        code,
        16,
        f"Convert each one-byte channel separately: {red} = {red:02X}, "
        f"{green} = {green:02X}, {blue} = {blue:02X}. Together: #{code}.",
        (
            "Convert each channel to exactly two hexadecimal digits.",
            f"Red becomes {red:02X}; now do green and blue.",
            f"Keep the order red, green, blue: {code}.",
        ),
        "confuses RGB channel order",
        fixed_width=True,
        max_length=6,
        media=GeneratedMedia(
            "rgb_channels",
            {"red": red, "green": green, "blue": blue},
            f"RGB channels {red}, {green}, {blue}",
        ),
    )


def _colour_recognition(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    colours = (
        ("FF0000", "red"),
        ("00FF00", "green"),
        ("0000FF", "blue"),
        ("FFFF00", "yellow"),
        ("00FFFF", "cyan"),
        ("FF00FF", "magenta"),
        ("8040FF", "violet with some red"),
        ("2080A0", "blue-green"),
        ("808080", "mid grey"),
    )
    code, description = rng.choice(colours)
    other_codes = [item[0] for item in colours if item[0] != code]
    rng.shuffle(other_codes)
    media = GeneratedMedia(
        "rgb_swatch",
        {"hex": code},
        f"Colour swatch #{code} ({description})",
    )
    return _choice(
        skill_key,
        question_type,
        "Which hexadecimal RGB code matches this colour swatch?",
        f"#{code}",
        code,
        ((f"#{item}", item) for item in other_codes),
        f"The swatch uses RGB #{code}: its channel strengths make it {description}.",
        (
            "Read the swatch as red, green, then blue channel strength.",
            "00 means absent and FF means maximum.",
            f"The matching code is #{code}.",
        ),
        "confuses RGB channel order",
        rng,
        media,
    )


def _rgb_binary(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    red, green, blue = (rng.randint(16, 239) for _ in range(3))
    code = f"{red:02X}{green:02X}{blue:02X}"
    bits = f"{red:08b} {green:08b} {blue:08b}"
    distractors = (
        (f"#{blue:02X}{green:02X}{red:02X}", "reverse"),
        (f"#{red:02X}{blue:02X}{green:02X}", "swap"),
        (f"#{255 - red:02X}{255 - green:02X}{255 - blue:02X}", "inverse"),
    )
    return _choice(
        skill_key,
        question_type,
        f"These three bytes are Red, Green, Blue in that order: {bits}. "
        "Which colour code do they form?",
        f"#{code}",
        "correct",
        distractors,
        f"Group each byte into two nibbles: {red:08b} = {red:02X}, "
        f"{green:08b} = {green:02X}, {blue:08b} = {blue:02X}. "
        f"Therefore the colour is #{code}.",
        (
            "Treat each eight-bit channel separately.",
            "Convert each byte into two hexadecimal digits.",
            f"Keep red, green, blue order: #{code}.",
        ),
        "confuses RGB channel order",
        rng,
        GeneratedMedia(
            "rgb_channels",
            {"red": red, "green": green, "blue": blue},
            f"RGB bytes {bits}",
        ),
    )


def _character_question(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    character = rng.choice(ASCII_CHARACTERS)
    value = ord(character)
    shown = "space" if character == " " else character
    if skill_key == "characters:decimal":
        return _pad(
            skill_key,
            question_type,
            f"ASCII assigns '{shown}' a numerical code. Build that code in decimal.",
            str(value),
            10,
            f"ASCII assigns '{shown}' the value {value}₁₀.",
            (
                "Use the supplied ASCII reference idea.",
                "The code lies between 32 and 122.",
                f"The decimal code is {value}.",
            ),
            "confuses a character with its numerical code",
        )
    if skill_key == "characters:hex":
        return _pad(
            skill_key,
            question_type,
            f"ASCII assigns '{shown}' the decimal code {value}. Build its two hexadecimal digits.",
            f"{value:02X}",
            16,
            f"{shown} = {value}₁₀ = {value:02X}₁₆.",
            (
                "Convert the assigned number, not the character shape.",
                f"Divide {value} by 16.",
                f"The code is {value:02X}₁₆.",
            ),
            "confuses a character with its numerical code",
            fixed_width=True,
            max_length=2,
        )
    if skill_key == "characters:binary":
        return _pad(
            skill_key,
            question_type,
            f"ASCII assigns '{shown}' the decimal code {value}. Build its complete eight-bit byte.",
            f"{value:08b}",
            2,
            f"{shown} = {value}₁₀ = {value:02X}₁₆ = {value:08b}₂ as one byte.",
            (
                "A byte must show eight bit positions.",
                f"First convert {value} to binary.",
                f"Pad on the left to eight bits: {value:08b}.",
            ),
            "drops significant fixed-width information",
            fixed_width=True,
            max_length=8,
        )
    if skill_key == "characters:decode":
        second = rng.choice(ASCII_CHARACTERS[:52])
        text = character + second
        encoded = " ".join(f"{ord(item):02X}" for item in text)
        distractors = ((text[::-1], "reverse"), (text.swapcase(), "case"), (text + "?", "extra"))
        return _choice(
            skill_key,
            question_type,
            f"Using ASCII, decode the hexadecimal bytes {encoded}.",
            text,
            "correct",
            distractors,
            f"Decode each byte separately: {encoded} represents {text!r}.",
            (
                "Each pair of hexadecimal digits is one byte.",
                "Decode the bytes one at a time.",
                text,
            ),
            "decodes byte boundaries incorrectly",
            rng,
        )
    if skill_key == "characters:code_to_char":
        choices = [character]
        while len(choices) < 4:
            item = rng.choice(ASCII_CHARACTERS)
            if item not in choices:
                choices.append(item)
        return _choice(
            skill_key,
            question_type,
            f"Under ASCII, which character is assigned code {value:02X}₁₆?",
            shown,
            character,
            (("space" if item == " " else item, item) for item in choices if item != character),
            f"{value:02X}₁₆ = {value}₁₀, and ASCII assigns that code to '{shown}'.",
            (
                "Convert the hexadecimal code to its value.",
                f"The decimal code is {value}.",
                f"ASCII maps it to '{shown}'.",
            ),
            "confuses code value with character",
            rng,
        )
    return _interpretation(skill_key, question_type, rng, value=value, character=character)


def _interpretation(
    skill_key: str,
    question_type: str,
    rng: Random,
    *,
    value: int | None = None,
    character: str | None = None,
) -> GeneratedQuestion:
    if character is None:
        character = rng.choice(ASCII_CHARACTERS)
    if value is None:
        value = ord(character)
    shown = "space" if character == " " else character
    bits = f"{value:08b}"
    correct = f"As an unsigned number it is {value}; under ASCII it represents '{shown}'."
    return _choice(
        skill_key,
        question_type,
        f"How can the byte {bits}₂ be interpreted?",
        correct,
        "correct",
        (
            (f"It can only mean the number {value}.", "number-only"),
            (f"It is literally the character '{shown}' without an encoding.", "literal"),
            ("It is hexadecimal storage rather than bits.", "hex-storage"),
        ),
        f"The bits have value {value}. ASCII is an interpretation that assigns code "
        f"{value} to '{shown}'. The bits alone do not choose their meaning.",
        (
            "Separate the bit pattern from its interpretation.",
            f"Its unsigned numerical value is {value}.",
            f"ASCII assigns that code to '{shown}'.",
        ),
        "confuses representation with interpretation",
        rng,
        GeneratedMedia(
            "ascii_card", {"bits": bits, "character": shown}, f"{bits} can mean {value} or {shown}"
        ),
    )


def _mixed_chain(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    value = rng.randint(16, 254)
    hexadecimal = digits(value, 16)
    binary = digits(value, 2)
    return _pad(
        skill_key,
        question_type,
        f"Convert {hexadecimal}₁₆ to binary, then give the final decimal value.",
        str(value),
        10,
        f"{hexadecimal}₁₆ maps to {binary}₂, and that bit pattern has decimal value {value}.",
        (
            "Map each hexadecimal digit to four bits.",
            f"The binary form is {_group_from_right(binary, 4)}.",
            f"Add its powers of two to get {value}.",
        ),
        "loses the shared value during a transformation chain",
    )


def _construct_representation(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    value = rng.randint(16, 254)
    hexadecimal = digits(value, 16, 2)
    binary = digits(value, 2, 8)
    return _pad(
        skill_key,
        question_type,
        f"Build the complete eight-bit binary representation of {hexadecimal}₁₆.",
        binary,
        2,
        f"{hexadecimal[0]} maps to {binary[:4]} and {hexadecimal[1]} maps to "
        f"{binary[4:]}; together they form {binary}₂.",
        (
            "Each hexadecimal digit becomes four bits.",
            f"Convert {hexadecimal[0]} and {hexadecimal[1]} separately.",
            f"Keep all eight bit positions: {binary}.",
        ),
        "drops significant fixed-width information",
        fixed_width=True,
        max_length=8,
        media=GeneratedMedia("byte", {"bits": binary}, f"One byte for {hexadecimal} hexadecimal"),
    )


def _binary_addition(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    left, right = rng.randint(2, 31), rng.randint(2, 31)
    total = left + right
    return _pad(
        skill_key,
        question_type,
        f"Add {digits(left, 2)}₂ + {digits(right, 2)}₂. Build the binary result.",
        digits(total, 2),
        2,
        f"The values are {left} and {right}; their sum is {total}, which is "
        f"{digits(total, 2)}₂. In binary, 1 + 1 writes 0 and carries 1.",
        (
            "Work from the right and carry whenever a column totals two.",
            "Remember: 1 + 1 = 10₂.",
            f"The result has value {total}.",
        ),
        "forgets binary carrying",
    )


def _meaning_ten(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    base = rng.choice((2, 8, 10, 16))
    return _choice(
        skill_key,
        question_type,
        f"What value does 10{BASE_SUFFIXES[base]} represent?",
        str(base),
        str(base),
        ((str(item), str(item)) for item in (2, 8, 10, 16) if item != base),
        "In any positional base, 10 means one group of the base and zero units, "
        f"so 10{BASE_SUFFIXES[base]} = {base}₁₀.",
        ("10 does not always mean decimal ten.", "It means one group of the base.", str(base)),
        "confuses value with visible digits",
        rng,
    )


def generate(skill_key: str, question_type: str, rng: Random) -> GeneratedQuestion:
    if question_type in {"direct_conversion", "cross_conversion"}:
        return _direct_conversion(skill_key, question_type, rng)
    if question_type == "positional_expansion":
        return _positional_expansion(skill_key, question_type, rng)
    if question_type == "base_identification":
        return _base_identification(skill_key, question_type, rng)
    if question_type == "equivalent_representation":
        return _equivalent(skill_key, question_type, rng)
    if question_type == "comparison":
        return _comparison(skill_key, question_type, rng)
    if question_type == "missing_digit":
        return _missing_digit(skill_key, question_type, rng)
    if question_type == "error_detection":
        return _error_detection(skill_key, question_type, rng)
    if question_type == "method_selection":
        return _method_selection(skill_key, question_type, rng)
    if question_type == "explanation_selection":
        return _explanation_selection(skill_key, question_type, rng)
    if question_type == "bit_count":
        return _bit_count(skill_key, question_type, rng)
    if question_type == "byte_range":
        return _range_question(skill_key, question_type, rng)
    if question_type == "byte_decomposition":
        return _byte_decomposition(skill_key, question_type, rng)
    if question_type == "rgb_channel":
        return _rgb_channel(skill_key, question_type, rng)
    if question_type == "colour_recognition":
        return _colour_recognition(skill_key, question_type, rng)
    if question_type == "rgb_binary":
        return _rgb_binary(skill_key, question_type, rng)
    if question_type == "character_code":
        return _character_question(skill_key, question_type, rng)
    if question_type in {"interpretation", "same_bits_different_meanings"}:
        return _interpretation(skill_key, question_type, rng)
    if question_type == "mixed_transformation":
        return _mixed_chain(skill_key, question_type, rng)
    if question_type == "construct_representation":
        return _construct_representation(skill_key, question_type, rng)
    if question_type == "binary_addition":
        return _binary_addition(skill_key, question_type, rng)
    if question_type == "meaning_ten":
        return _meaning_ten(skill_key, question_type, rng)
    raise ValueError(f"unknown numeral-systems question type: {question_type}")


ContentGetter = Callable[..., str]
