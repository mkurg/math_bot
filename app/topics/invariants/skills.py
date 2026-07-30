from __future__ import annotations

from app.core.topics.contracts import SkillDefinition

GROUP_LABELS = {
    "discover": "Spotting what stays the same",
    "preserve": "Checking every allowed move",
    "prove": "Proving possible and impossible",
    "reason": "Evidence and mathematical proof",
    "extend": "Deeper invariants",
}


SKILL_LABELS = {
    "discover:state_property": "Separate the changing state from a fixed property",
    "discover:parity": "Notice parity as an invariant",
    "preserve:all_moves": "Check every allowed move",
    "preserve:card_flips": "Track parity in the two-card flip game",
    "preserve:remainders": "Track a remainder through additive moves",
    "prove:impossible": "Prove that a target is impossible",
    "prove:construct": "Construct a route to a reachable target",
    "prove:same_not_sufficient": "Know what a matching invariant does not prove",
    "reason:evidence_vs_proof": "Distinguish experiments from proof",
    "extend:stronger_invariant": "Choose the most informative invariant",
    "extend:odd_part": "Use the odd part under doubling and halving",
}


def skill_catalogue() -> tuple[SkillDefinition, ...]:
    return (
        SkillDefinition(
            "discover:state_property",
            "discover",
            "skill.discover.state",
            "skill.discover.state.description",
            difficulty=1,
            tags=("state", "property"),
        ),
        SkillDefinition(
            "discover:parity",
            "discover",
            "skill.discover.parity",
            "skill.discover.parity.description",
            prerequisites=("discover:state_property",),
            difficulty=1,
            tags=("parity", "modulo:2"),
        ),
        SkillDefinition(
            "preserve:all_moves",
            "preserve",
            "skill.preserve.moves",
            "skill.preserve.moves.description",
            prerequisites=("discover:parity",),
            difficulty=2,
            tags=("preservation", "proof"),
        ),
        SkillDefinition(
            "preserve:card_flips",
            "preserve",
            "skill.preserve.cards",
            "skill.preserve.cards.description",
            prerequisites=("discover:parity",),
            difficulty=2,
            tags=("parity", "cards"),
        ),
        SkillDefinition(
            "preserve:remainders",
            "preserve",
            "skill.preserve.remainders",
            "skill.preserve.remainders.description",
            prerequisites=("discover:parity",),
            difficulty=2,
            tags=("remainders", "modular_arithmetic"),
        ),
        SkillDefinition(
            "prove:impossible",
            "prove",
            "skill.prove.impossible",
            "skill.prove.impossible.description",
            prerequisites=("preserve:all_moves", "preserve:remainders"),
            difficulty=3,
            tags=("impossibility", "proof"),
        ),
        SkillDefinition(
            "prove:construct",
            "prove",
            "skill.prove.construct",
            "skill.prove.construct.description",
            prerequisites=("prove:impossible",),
            difficulty=3,
            tags=("reachability", "construction"),
        ),
        SkillDefinition(
            "prove:same_not_sufficient",
            "prove",
            "skill.prove.warning",
            "skill.prove.warning.description",
            prerequisites=("prove:impossible",),
            difficulty=3,
            tags=("logic", "reachability"),
        ),
        SkillDefinition(
            "reason:evidence_vs_proof",
            "reason",
            "skill.reason.proof",
            "skill.reason.proof.description",
            prerequisites=("preserve:all_moves",),
            difficulty=3,
            tags=("experiments", "proof"),
        ),
        SkillDefinition(
            "extend:stronger_invariant",
            "extend",
            "skill.extend.stronger",
            "skill.extend.stronger.description",
            prerequisites=("preserve:remainders",),
            difficulty=4,
            tags=("remainders", "comparison"),
        ),
        SkillDefinition(
            "extend:odd_part",
            "extend",
            "skill.extend.odd_part",
            "skill.extend.odd_part.description",
            prerequisites=("prove:same_not_sufficient",),
            difficulty=5,
            tags=("factorisation", "odd_part"),
        ),
    )


def skill_label(skill_key: str) -> str:
    try:
        return SKILL_LABELS[skill_key]
    except KeyError as exc:
        raise ValueError(f"unknown invariants skill: {skill_key}") from exc
