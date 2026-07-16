from app.core.topics.contracts import SkillDefinition


def fact_key(operation: str, first: int, second: int) -> str:
    if operation not in {"mul", "div"}:
        raise ValueError("operation must be mul or div")
    if not 1 <= first <= 10 or not 1 <= second <= 10:
        raise ValueError("factors must be from 1 through 10")
    low, high = sorted((first, second))
    return f"{operation}:{low}:{high}"


def parse_skill_key(skill_key: str) -> tuple[str, int, int]:
    try:
        operation, low_text, high_text = skill_key.split(":")
        low, high = int(low_text), int(high_text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid times-table skill key: {skill_key}") from exc
    if skill_key != fact_key(operation, low, high):
        raise ValueError(f"noncanonical times-table skill key: {skill_key}")
    return operation, low, high


def skill_catalogue() -> tuple[SkillDefinition, ...]:
    skills: list[SkillDefinition] = []
    for operation in ("mul", "div"):
        for low in range(1, 11):
            for high in range(low, 11):
                prerequisites: tuple[str, ...] = ()
                if operation == "div":
                    prerequisites = (fact_key("mul", low, high),)
                skills.append(
                    SkillDefinition(
                        skill_key=fact_key(operation, low, high),
                        group_key=f"{operation}:table:{high}",
                        title_key=f"skill.{operation}",
                        description_key=f"skill.{operation}.description",
                        prerequisites=prerequisites,
                        difficulty=max(low, high),
                        tags=(operation, f"table:{low}", f"table:{high}"),
                    )
                )
    return tuple(skills)
