from pathlib import Path

from app.topics.times_tables.images import render_full_table, render_individual_table, render_mascot


def main() -> None:
    target = Path(__file__).parents[1] / "app" / "topics" / "times_tables" / "assets"
    target.mkdir(parents=True, exist_ok=True)
    (target / "full_table.png").write_bytes(render_full_table({}))
    (target / "mascot.png").write_bytes(render_mascot({}))
    for table in range(1, 11):
        (target / f"table_{table}.png").write_bytes(render_individual_table({"table": table}))
    print(f"Generated 12 deterministic images in {target}")


if __name__ == "__main__":
    main()
