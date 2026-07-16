from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ContentCatalog:
    def __init__(self, path: Path) -> None:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not all(isinstance(k, str) for k in data):
            raise ValueError(f"invalid content file: {path}")
        self._values: dict[str, Any] = data

    def get(self, key: str, **values: object) -> str:
        try:
            template = self._values[key]
        except KeyError as exc:
            raise KeyError(f"missing content key: {key}") from exc
        if not isinstance(template, str):
            raise TypeError(f"content key is not text: {key}")
        return template.format(**values)

    def raw(self, key: str) -> Any:
        if key not in self._values:
            raise KeyError(f"missing content key: {key}")
        return self._values[key]
