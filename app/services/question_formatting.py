from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any


def render_question_prompt(prompt_payload: Mapping[str, Any]) -> str:
    """Return Telegram-safe HTML for a stored question prompt."""
    prompt = str(prompt_payload["rendered_prompt"])
    metadata = prompt_payload.get("metadata", {})
    if isinstance(metadata, Mapping) and metadata.get("prompt_format") == "html":
        return prompt
    return escape(prompt)
