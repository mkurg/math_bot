from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BACKGROUND = "#F5F8FF"
INK = "#14213D"
ACCENT = "#4C6FFF"
PALE = "#E5EAFF"
GROUP_COLOURS = ("#DDE7FF", "#DDF7E7", "#FFE8D9", "#F1E1FF")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    )
    for name in names:
        if not name:
            continue
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def render_grouping(payload: dict[str, Any]) -> bytes:
    bits = str(payload["bits"])
    size = int(payload["size"])
    padding = (-len(bits)) % size
    padded = "0" * padding + bits
    groups = [padded[index : index + size] for index in range(0, len(padded), size)]
    base = 8 if size == 3 else 16
    target_digits = [format(int(group, 2), "X") for group in groups]
    image = Image.new("RGB", (1080, 720), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (540, 68),
        f"Group bits from the RIGHT in sets of {size}",
        fill=INK,
        font=_font(52, True),
        anchor="mm",
    )
    draw.text(
        (540, 132),
        "If needed, add zeroes only at the far left",
        fill=ACCENT,
        font=_font(34),
        anchor="mm",
    )
    gap = 28
    card_width = min(300, (920 - gap * (len(groups) - 1)) // len(groups))
    total_width = card_width * len(groups) + gap * (len(groups) - 1)
    start_x = (1080 - total_width) // 2
    for index, (group, digit) in enumerate(zip(groups, target_digits, strict=True)):
        left = start_x + index * (card_width + gap)
        right = left + card_width
        draw.rounded_rectangle(
            (left, 195, right, 500),
            28,
            fill=GROUP_COLOURS[index % len(GROUP_COLOURS)],
            outline=INK,
            width=4,
        )
        draw.text(
            ((left + right) / 2, 245),
            f"group {index + 1}",
            fill=INK,
            font=_font(30, True),
            anchor="mm",
        )
        draw.text(
            ((left + right) / 2, 335),
            group,
            fill=INK,
            font=_font(68, True),
            anchor="mm",
        )
        draw.text(((left + right) / 2, 405), "↓", fill=ACCENT, font=_font(48, True), anchor="mm")
        draw.text(
            ((left + right) / 2, 465),
            digit,
            fill=INK,
            font=_font(64, True),
            anchor="mm",
        )
    draw.text(
        (540, 575),
        "  |  ".join(groups) + "   →   " + "  |  ".join(target_digits),
        fill=INK,
        font=_font(42, True),
        anchor="mm",
    )
    draw.text(
        (540, 655),
        f"Result: {''.join(target_digits)} in base {base}",
        fill=ACCENT,
        font=_font(48, True),
        anchor="mm",
    )
    return _png(image)


def render_place_values(payload: dict[str, Any]) -> bytes:
    representation = str(payload["digits"])
    base = int(payload["base"])
    powers = tuple(range(len(representation) - 1, -1, -1))
    terms = tuple(
        int(character, base) * base**power
        for character, power in zip(representation, powers, strict=True)
    )
    value = sum(terms)
    image = Image.new("RGB", (1080, 760), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (540, 68),
        f"{representation} in base {base}",
        fill=INK,
        font=_font(58, True),
        anchor="mm",
    )
    draw.text(
        (540, 140),
        f"The RIGHTMOST digit is the units place ({base}^0)",
        fill=ACCENT,
        font=_font(38, True),
        anchor="mm",
    )
    gap = 50
    card_width = min(410, (900 - gap * (len(representation) - 1)) // len(representation))
    total_width = card_width * len(representation) + gap * (len(representation) - 1)
    start = (1080 - total_width) // 2
    for index, (character, power, term) in enumerate(
        zip(representation, powers, terms, strict=True)
    ):
        x = start + index * (card_width + gap)
        draw.rounded_rectangle(
            (x, 200, x + card_width, 520),
            30,
            fill=GROUP_COLOURS[index % len(GROUP_COLOURS)],
            outline=INK,
            width=4,
        )
        draw.text(
            (x + card_width / 2, 260),
            "RIGHTMOST DIGIT" if power == 0 else f"{power} PLACE LEFT",
            fill=INK,
            font=_font(28, True),
            anchor="mm",
        )
        draw.text(
            (x + card_width / 2, 355),
            character,
            fill=INK,
            font=_font(96, True),
            anchor="mm",
        )
        draw.text(
            (x + card_width / 2, 440),
            f"{character} × {base}^{power}",
            fill=INK,
            font=_font(46, True),
            anchor="mm",
        )
        draw.text(
            (x + card_width / 2, 495),
            f"= {term}",
            fill=ACCENT,
            font=_font(44, True),
            anchor="mm",
        )
    expression = " + ".join(str(term) for term in terms)
    draw.text(
        (540, 615),
        f"{expression} = {value}",
        fill=INK,
        font=_font(64, True),
        anchor="mm",
    )
    draw.text(
        (540, 690),
        "Write the terms in the same LEFT-to-RIGHT order as the digits",
        fill=ACCENT,
        font=_font(35, True),
        anchor="mm",
    )
    return _png(image)


def render_byte(payload: dict[str, Any]) -> bytes:
    bits = str(payload["bits"]).zfill(8)[-8:]
    image = Image.new("RGB", (1080, 600), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((540, 70), "1 byte = 8 bits = 2 nibbles", fill=INK, font=_font(54, True), anchor="mm")
    cell = 108
    start = 540 - 4 * cell
    for index, bit in enumerate(bits):
        x = start + index * cell
        fill = GROUP_COLOURS[0] if index < 4 else GROUP_COLOURS[1]
        draw.rounded_rectangle((x + 5, 180, x + cell - 5, 315), 18, fill=fill, outline=INK, width=3)
        draw.text((x + cell / 2, 247), bit, fill=INK, font=_font(64, True), anchor="mm")
    draw.line((540, 155, 540, 355), fill=ACCENT, width=8)
    draw.text((324, 390), "first nibble", fill=INK, font=_font(38, True), anchor="mm")
    draw.text((756, 390), "second nibble", fill=INK, font=_font(38, True), anchor="mm")
    draw.text((324, 445), "4 bits", fill=ACCENT, font=_font(36, True), anchor="mm")
    draw.text((756, 445), "4 bits", fill=ACCENT, font=_font(36, True), anchor="mm")
    draw.text(
        (540, 535),
        "Keep all 8 positions when a complete byte is required",
        fill=INK,
        font=_font(38, True),
        anchor="mm",
    )
    return _png(image)


def render_rgb_swatch(payload: dict[str, Any]) -> bytes:
    code = str(payload["hex"]).removeprefix("#").upper()
    if len(code) != 6 or any(character not in "0123456789ABCDEF" for character in code):
        raise ValueError("invalid RGB hexadecimal code")
    image = Image.new("RGB", (900, 700), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((450, 65), "Match the RGB colour", fill=INK, font=_font(54, True), anchor="mm")
    draw.rounded_rectangle((100, 135, 800, 570), 45, fill=f"#{code}", outline=INK, width=7)
    draw.text(
        (450, 635),
        "Read channels in the order  Red → Green → Blue",
        fill=INK,
        font=_font(36, True),
        anchor="mm",
    )
    return _png(image)


def render_rgb_channels(payload: dict[str, Any]) -> bytes:
    values = (int(payload["red"]), int(payload["green"]), int(payload["blue"]))
    if any(not 0 <= value <= 255 for value in values):
        raise ValueError("RGB channels must be in 0 through 255")
    image = Image.new("RGB", (1080, 720), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (540, 68), "Three RGB channels — one byte each", fill=INK, font=_font(52, True), anchor="mm"
    )
    draw.text(
        (540, 125),
        "Each decimal value is between 0 and 255",
        fill=ACCENT,
        font=_font(34, True),
        anchor="mm",
    )
    colours = ("#E5484D", "#30A46C", "#3E63DD")
    for index, (label, value, colour) in enumerate(
        zip(("Red", "Green", "Blue"), values, colours, strict=True)
    ):
        y = 235 + index * 145
        draw.text((80, y), label, fill=INK, font=_font(42, True), anchor="lm")
        draw.rounded_rectangle((250, y - 38, 860, y + 38), 20, fill="#E6E8EC")
        width = round(610 * value / 255)
        if width:
            draw.rounded_rectangle((250, y - 38, 250 + width, y + 38), 20, fill=colour)
        draw.text((955, y), str(value), fill=INK, font=_font(44, True), anchor="mm")
    return _png(image)


def render_ascii_card(payload: dict[str, Any]) -> bytes:
    bits = str(payload["bits"])
    character = str(payload["character"])
    image = Image.new("RGB", (1080, 720), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (540, 68),
        "One bit pattern, different interpretations",
        fill=INK,
        font=_font(50, True),
        anchor="mm",
    )
    draw.rounded_rectangle((120, 145, 960, 290), 28, fill=PALE, outline=ACCENT, width=5)
    draw.text((540, 217), bits, fill=INK, font=_font(72, True), anchor="mm")
    value = int(bits, 2)
    draw.line((540, 290, 540, 365), fill=ACCENT, width=7)
    draw.line((300, 365, 780, 365), fill=ACCENT, width=7)
    draw.line((300, 365, 300, 405), fill=ACCENT, width=7)
    draw.line((780, 365, 780, 405), fill=ACCENT, width=7)
    draw.rounded_rectangle((100, 405, 500, 630), 28, fill=GROUP_COLOURS[0], outline=INK, width=4)
    draw.rounded_rectangle((580, 405, 980, 630), 28, fill=GROUP_COLOURS[1], outline=INK, width=4)
    draw.text(
        (300, 515),
        f"Unsigned number\n{value}",
        fill=INK,
        font=_font(44, True),
        anchor="mm",
        align="center",
    )
    draw.text(
        (780, 515),
        f"ASCII character\n{character}",
        fill=INK,
        font=_font(44, True),
        anchor="mm",
        align="center",
    )
    return _png(image)


RENDERERS: dict[str, Callable[[dict[str, Any]], bytes]] = {
    "grouping": render_grouping,
    "place_values": render_place_values,
    "byte": render_byte,
    "rgb_swatch": render_rgb_swatch,
    "rgb_channels": render_rgb_channels,
    "ascii_card": render_ascii_card,
}


def render(renderer_id: str, payload: dict[str, Any]) -> bytes:
    try:
        renderer = RENDERERS[renderer_id]
    except KeyError as exc:
        raise ValueError(f"unknown numeral-systems media renderer: {renderer_id}") from exc
    return renderer(payload)
