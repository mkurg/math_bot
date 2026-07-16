from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.content.loader import ContentCatalog
from app.core.topics.contracts import Metric, ProgressGroup, ProgressItem, TopicProgressView
from app.handlers.progress import render_progress
from app.keyboards.common import main_menu, table_grid
from app.topics.times_tables import TimesTablesModule


def valid_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "bot_token": "1234567890:abcdefghijklmnopqrstuvwxyz123456",
        "bot_username": "@TimesBot",
        "admin_telegram_id": 123,
        "database_url": "postgresql+asyncpg://user:pass@db/database",
        "default_timezone": "Europe/Zurich",
        "enabled_topic_ids": "times_tables",
        "default_topic_id": "times_tables",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_settings_normalize_and_validate() -> None:
    settings = valid_settings(enabled_topic_ids="times_tables, sample_topic")
    assert settings.bot_username == "TimesBot"
    assert settings.enabled_topics == ("times_tables", "sample_topic")
    with pytest.raises(ValueError, match="timezone"):
        valid_settings(default_timezone="Mars/Olympus")
    with pytest.raises(ValueError, match="enabled"):
        valid_settings(default_topic_id="sample")
    with pytest.raises(ValueError):
        valid_settings(default_reminder_days="SOMETIMES")


def test_content_catalog_and_keyboards() -> None:
    root = Path(__file__).parents[1]
    catalog = ContentCatalog(root / "app" / "content" / "core" / "strings.yaml")
    assert catalog.get("welcome", name="Mira").startswith("👋 Welcome, Mira")
    with pytest.raises(KeyError):
        catalog.get("missing")
    menu = main_menu(TimesTablesModule())
    assert len(menu.keyboard) == 3
    assert menu.keyboard[0][0].text == "▶️ Тренировка"
    grid = table_grid("table")
    assert len(grid.inline_keyboard) == 3
    assert grid.inline_keyboard[0][0].callback_data == "table:1"


def test_generic_progress_rendering() -> None:
    view = TopicProgressView(
        (Metric("Total", "10"),),
        (
            ProgressGroup("Overview", 60),
            ProgressGroup(
                "Details",
                0,
                (ProgressItem("First", "80%"), ProgressItem("Second", "new")),
            ),
        ),
        (ProgressItem("Strong"),),
        (ProgressItem("Target"),),
    )
    rendered = render_progress(view, "Progress")
    assert "██████░░░░ 60%" in rendered
    assert "First: ████████░░ 80%" in rendered
    assert "Strong" in rendered and "Target" in rendered


def test_all_content_counts_and_learning_units() -> None:
    module = TimesTablesModule()
    assert len(module.catalog.raw("story.mul")) == 15
    assert len(module.catalog.raw("story.div")) == 15
    assert len(module.catalog.raw("tips")) == 10
    assert len(module.catalog.raw("hard_facts")) == 6
    assert len(module.learning_units()) == 11
