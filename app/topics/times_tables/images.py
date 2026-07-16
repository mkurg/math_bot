from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BACKGROUND = "#FFF9E8"
INK = "#183153"
ACCENT = "#5B8DEF"
COLORS = ("#5B8DEF", "#FF9F6E", "#6BCB77", "#B983FF")


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


def render_full_table(_: dict[str, Any] | None = None) -> bytes:
    cell = 62
    margin = 42
    image = Image.new("RGB", (margin * 2 + cell * 11, margin * 2 + cell * 11), BACKGROUND)
    draw = ImageDraw.Draw(image)
    font = _font(23)
    bold = _font(24, bold=True)
    for row in range(11):
        for column in range(11):
            x = margin + column * cell
            y = margin + row * cell
            header = row == 0 or column == 0
            fill = ACCENT if header else ("#FFFFFF" if (row + column) % 2 else "#EDF3FF")
            draw.rounded_rectangle((x + 2, y + 2, x + cell - 2, y + cell - 2), 8, fill=fill)
            if row == 0 and column == 0:
                text = "×"
            elif row == 0:
                text = str(column)
            elif column == 0:
                text = str(row)
            else:
                text = str(row * column)
            color = "white" if header else INK
            draw.text(
                (x + cell / 2, y + cell / 2),
                text,
                fill=color,
                font=bold if header else font,
                anchor="mm",
            )
    return _png(image)


def render_individual_table(payload: dict[str, Any]) -> bytes:
    table = int(payload["table"])
    image = Image.new("RGB", (720, 860), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.text(
        (360, 60),
        f"Таблица на {table}",
        fill=INK,
        font=_font(42, bold=True),
        anchor="mm",
    )
    for index in range(1, 11):
        y = 125 + index * 65
        fill = "#FFFFFF" if index % 2 else "#EDF3FF"
        draw.rounded_rectangle((115, y - 28, 605, y + 28), 12, fill=fill)
        draw.text(
            (360, y),
            f"{table} × {index} = {table * index}",
            fill=INK,
            font=_font(30, bold=True),
            anchor="mm",
        )
    return _png(image)


def render_array(payload: dict[str, Any]) -> bytes:
    rows = int(payload["rows"])
    columns = int(payload["columns"])
    image = Image.new("RGB", (720, 520), BACKGROUND)
    draw = ImageDraw.Draw(image)
    gap = min(65, 420 // max(rows, columns))
    start_x = 360 - (columns - 1) * gap / 2
    start_y = 260 - (rows - 1) * gap / 2
    radius = max(12, min(25, gap // 3))
    for row in range(rows):
        for column in range(columns):
            x = start_x + column * gap
            y = start_y + row * gap
            fill = COLORS[row % len(COLORS)]
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius), fill=fill, outline=INK, width=2
            )
    return _png(image)


def render_mascot(_: dict[str, Any] | None = None) -> bytes:
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((82, 96, 430, 420), 80, fill=ACCENT, outline=INK, width=12)
    draw.ellipse((155, 185, 205, 235), fill="white")
    draw.ellipse((307, 185, 357, 235), fill="white")
    draw.ellipse((173, 202, 191, 220), fill=INK)
    draw.ellipse((325, 202, 343, 220), fill=INK)
    draw.arc((170, 210, 342, 340), 20, 160, fill="white", width=12)
    draw.text((256, 70), "×", fill="#FF9F6E", font=_font(100, bold=True), anchor="mm")
    return _png(image)


RENDERERS: dict[str, Callable[[dict[str, Any]], bytes]] = {
    "full_table": render_full_table,
    "individual_table": render_individual_table,
    "array": render_array,
    "mascot": render_mascot,
}


def render(renderer_id: str, payload: dict[str, Any]) -> bytes:
    try:
        renderer = RENDERERS[renderer_id]
    except KeyError as exc:
        raise ValueError(f"unknown media renderer: {renderer_id}") from exc
    return renderer(payload)
