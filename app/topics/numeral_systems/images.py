from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BACKGROUND = "#F5F8FF"
INK = "#14213D"
ACCENT = "#4C6FFF"
PALE = "#E5EAFF"


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
    image = Image.new("RGB", (760, 320), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (380, 45), f"Groups of {size} from the right", fill=INK, font=_font(30, True), anchor="mm"
    )
    cell = min(72, 620 // len(padded))
    start = 380 - len(padded) * cell / 2
    for index, bit in enumerate(padded):
        x = start + index * cell
        group = index // size
        fill = ("#DDE7FF", "#DDF7E7", "#FFE8D9", "#F1E1FF")[group % 4]
        draw.rounded_rectangle((x + 3, 110, x + cell - 3, 190), 10, fill=fill, outline=INK, width=2)
        draw.text((x + cell / 2, 150), bit, fill=INK, font=_font(34, True), anchor="mm")
    grouped = " ".join(padded[index : index + size] for index in range(0, len(padded), size))
    draw.text((380, 245), grouped, fill=ACCENT, font=_font(32, True), anchor="mm")
    return _png(image)


def render_place_values(payload: dict[str, Any]) -> bytes:
    representation = str(payload["digits"])
    base = int(payload["base"])
    image = Image.new("RGB", (760, 330), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (380, 42), f"Place values in base {base}", fill=INK, font=_font(30, True), anchor="mm"
    )
    cell = min(150, 620 // len(representation))
    start = 380 - len(representation) * cell / 2
    for index, character in enumerate(representation):
        power = len(representation) - index - 1
        x = start + index * cell
        draw.rounded_rectangle(
            (x + 5, 100, x + cell - 5, 235), 12, fill="white", outline=ACCENT, width=3
        )
        draw.text((x + cell / 2, 145), character, fill=INK, font=_font(42, True), anchor="mm")
        draw.text(
            (x + cell / 2, 200), f"x {base}^{power}", fill=ACCENT, font=_font(22), anchor="mm"
        )
    return _png(image)


def render_byte(payload: dict[str, Any]) -> bytes:
    bits = str(payload["bits"]).zfill(8)[-8:]
    image = Image.new("RGB", (760, 300), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((380, 45), "One byte = two nibbles", fill=INK, font=_font(30, True), anchor="mm")
    cell = 70
    start = 380 - 4 * cell
    for index, bit in enumerate(bits):
        x = start + index * cell
        fill = "#DDE7FF" if index < 4 else "#DDF7E7"
        draw.rounded_rectangle((x + 4, 105, x + cell - 4, 185), 9, fill=fill, outline=INK, width=2)
        draw.text((x + cell / 2, 145), bit, fill=INK, font=_font(34, True), anchor="mm")
    draw.line((380, 90, 380, 210), fill=ACCENT, width=5)
    draw.text((240, 235), "nibble", fill=INK, font=_font(22), anchor="mm")
    draw.text((520, 235), "nibble", fill=INK, font=_font(22), anchor="mm")
    return _png(image)


def render_rgb_swatch(payload: dict[str, Any]) -> bytes:
    code = str(payload["hex"]).removeprefix("#").upper()
    if len(code) != 6 or any(character not in "0123456789ABCDEF" for character in code):
        raise ValueError("invalid RGB hexadecimal code")
    image = Image.new("RGB", (640, 420), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((95, 55, 545, 325), 30, fill=f"#{code}", outline=INK, width=5)
    draw.text((320, 375), "Which RGB code matches?", fill=INK, font=_font(28, True), anchor="mm")
    return _png(image)


def render_rgb_channels(payload: dict[str, Any]) -> bytes:
    values = (int(payload["red"]), int(payload["green"]), int(payload["blue"]))
    if any(not 0 <= value <= 255 for value in values):
        raise ValueError("RGB channels must be in 0 through 255")
    image = Image.new("RGB", (760, 400), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text((380, 42), "Three one-byte RGB channels", fill=INK, font=_font(30, True), anchor="mm")
    colours = ("#E5484D", "#30A46C", "#3E63DD")
    for index, (label, value, colour) in enumerate(
        zip(("Red", "Green", "Blue"), values, colours, strict=True)
    ):
        y = 110 + index * 90
        draw.text((75, y), label, fill=INK, font=_font(24, True), anchor="lm")
        draw.rounded_rectangle((180, y - 22, 620, y + 22), 12, fill="#E6E8EC")
        width = round(440 * value / 255)
        if width:
            draw.rounded_rectangle((180, y - 22, 180 + width, y + 22), 12, fill=colour)
        draw.text((680, y), f"{value} / {value:02X}", fill=INK, font=_font(22), anchor="mm")
    return _png(image)


def render_ascii_card(payload: dict[str, Any]) -> bytes:
    bits = str(payload["bits"])
    character = str(payload["character"])
    image = Image.new("RGB", (760, 360), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (380, 46),
        "One bit pattern, different interpretations",
        fill=INK,
        font=_font(28, True),
        anchor="mm",
    )
    draw.rounded_rectangle((80, 100, 680, 180), 16, fill=PALE, outline=ACCENT, width=3)
    draw.text((380, 140), bits, fill=INK, font=_font(42, True), anchor="mm")
    value = int(bits, 2)
    draw.text(
        (220, 260),
        f"unsigned number\n{value}",
        fill=INK,
        font=_font(26, True),
        anchor="mm",
        align="center",
    )
    draw.text(
        (540, 260),
        f"ASCII character\n{character}",
        fill=INK,
        font=_font(26, True),
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
