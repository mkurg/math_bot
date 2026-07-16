from pathlib import Path

from app.content.loader import ContentCatalog
from app.topics.numeral_systems import NumeralSystemsModule
from app.topics.times_tables import TimesTablesModule


def main() -> None:
    root = Path(__file__).parents[1]
    ContentCatalog(root / "app" / "content" / "core" / "strings.yaml")
    modules = (TimesTablesModule(), NumeralSystemsModule())
    errors = [error for module in modules for error in module.validate()]
    searchable = "\n".join(
        path.read_text(encoding="utf-8") for path in (root / "app").rglob("*.yaml")
    ).lower()
    forbidden = ("text-to-speech", "voice message", "microphone")
    errors.extend(f"forbidden audio content: {term}" for term in forbidden if term in searchable)
    if errors:
        raise SystemExit("Content validation failed: " + "; ".join(errors))
    print("Content validation passed: core, times_tables, and numeral_systems")


if __name__ == "__main__":
    main()
