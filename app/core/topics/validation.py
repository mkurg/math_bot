from app.core.topics.contracts import TopicModule

REGISTERED_ANSWER_MODES = {
    "single_choice",
    "true_false",
    "binary_pad",
    "octal_pad",
    "decimal_pad",
    "hexadecimal_pad",
}


def validate_topic_contract(module: TopicModule) -> list[str]:
    errors: list[str] = []
    skills = module.skills()
    modes = module.practice_modes()
    tests = module.test_definitions()
    units = module.learning_units()
    if not module.metadata.topic_id:
        errors.append("empty topic_id")
    if not skills:
        errors.append("empty skill catalogue")
    identifier_groups = {
        "skill": [item.skill_key for item in skills],
        "mode": [item.mode_id for item in modes],
        "test": [item.test_id for item in tests],
        "unit": [item.unit_id for item in units],
    }
    for label, identifiers in identifier_groups.items():
        if len(identifiers) != len(set(identifiers)):
            errors.append(f"duplicate {label} identifier")
    skill_keys = {skill.skill_key for skill in skills}
    for skill in skills:
        missing = set(skill.prerequisites).difference(skill_keys)
        if missing:
            errors.append(f"{skill.skill_key} has missing prerequisites: {sorted(missing)}")
    return errors
