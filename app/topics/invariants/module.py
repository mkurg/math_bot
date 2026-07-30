from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from random import Random
from typing import Any

from app.content.loader import ContentCatalog
from app.core.mastery.engine import is_mastered
from app.core.mastery.selection import weighted_skill_order
from app.core.questions.answer_modes import validate_options
from app.core.topics.contracts import (
    AnswerOption,
    EvaluationResult,
    GeneratedQuestion,
    LearningUnit,
    LearningView,
    MasteryState,
    Metric,
    PracticeModeDefinition,
    ProgressGroup,
    ProgressItem,
    SkillDefinition,
    SuggestedAction,
    TestDefinition,
    TopicMetadata,
    TopicProgressView,
)
from app.core.topics.validation import validate_topic_contract
from app.topics.invariants.skills import GROUP_LABELS, skill_catalogue, skill_label

CONTENT_PATH = Path(__file__).with_name("content") / "strings.yaml"


QUESTION_TYPES: dict[str, tuple[str, ...]] = {
    "discover:state_property": ("state_vs_property", "identify_invariant"),
    "discover:parity": ("parity_reachable", "starting_parity"),
    "preserve:all_moves": ("check_all_moves", "breaker_move"),
    "preserve:card_flips": ("card_flip_reachable", "card_move_changes"),
    "preserve:remainders": ("identify_remainder", "remainder_reachable"),
    "prove:impossible": ("choose_proof", "exit_problem"),
    "prove:construct": ("construct_route", "count_moves"),
    "prove:same_not_sufficient": ("same_not_sufficient", "conclusion_strength"),
    "reason:evidence_vs_proof": ("evidence_vs_proof", "definition"),
    "extend:stronger_invariant": ("stronger_invariant", "mixed_moves"),
    "extend:odd_part": ("odd_part_reachable", "odd_part_value"),
}


MODE_SKILLS: dict[str, tuple[str, ...]] = {
    "quick": (
        "discover:state_property",
        "discover:parity",
        "preserve:all_moves",
        "preserve:card_flips",
        "preserve:remainders",
        "prove:impossible",
        "prove:construct",
        "prove:same_not_sufficient",
        "reason:evidence_vs_proof",
    ),
    "parity": (
        "discover:state_property",
        "discover:parity",
        "preserve:all_moves",
        "preserve:card_flips",
        "prove:impossible",
        "prove:construct",
        "prove:same_not_sufficient",
    ),
    "remainders": (
        "preserve:remainders",
        "preserve:all_moves",
        "prove:impossible",
        "prove:construct",
        "prove:same_not_sufficient",
        "extend:stronger_invariant",
    ),
    "proof": (
        "preserve:all_moves",
        "prove:impossible",
        "prove:construct",
        "prove:same_not_sufficient",
        "reason:evidence_vs_proof",
    ),
    "advanced": (
        "preserve:remainders",
        "prove:impossible",
        "prove:same_not_sufficient",
        "extend:stronger_invariant",
        "extend:odd_part",
        "reason:evidence_vs_proof",
    ),
}


GUIDED_BLUEPRINT: tuple[tuple[str, str], ...] = (
    ("discover:state_property", "state_vs_property"),
    ("discover:parity", "parity_reachable"),
    ("preserve:card_flips", "card_move_changes"),
    ("preserve:remainders", "identify_remainder"),
    ("preserve:all_moves", "check_all_moves"),
    ("prove:impossible", "choose_proof"),
    ("prove:construct", "construct_route"),
    ("prove:same_not_sufficient", "same_not_sufficient"),
)


LEARNING_SPECS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("coins", ("discover:state_property", "discover:parity"), "parity"),
    ("start", ("discover:parity",), "parity"),
    ("cards", ("preserve:card_flips", "preserve:all_moves"), "parity"),
    ("remainders", ("preserve:remainders",), "remainders"),
    ("method", ("preserve:all_moves", "prove:impossible"), "proof"),
    (
        "warning",
        ("prove:construct", "prove:same_not_sufficient"),
        "proof",
    ),
    ("evidence", ("reason:evidence_vs_proof",), "proof"),
    (
        "advanced",
        ("extend:stronger_invariant", "extend:odd_part"),
        "advanced",
    ),
)


def _odd_part(value: int) -> int:
    while value % 2 == 0:
        value //= 2
    return value


class InvariantsModule:
    metadata = TopicMetadata(
        topic_id="invariants",
        version="1.0.0",
        title_key="topic.title",
        short_title_key="topic.short_title",
        description_key="topic.description",
        icon="♾️",
        daily_extended_actions=True,
    )

    def __init__(self) -> None:
        self.catalog = ContentCatalog(CONTENT_PATH)
        self._skills = skill_catalogue()
        self._skill_map = {item.skill_key: item for item in self._skills}

    def skills(self) -> tuple[SkillDefinition, ...]:
        return self._skills

    def practice_modes(self) -> tuple[PracticeModeDefinition, ...]:
        return (
            PracticeModeDefinition("quick", "mode.quick", "mode.quick.description", 5),
            PracticeModeDefinition("guided", "mode.guided", "mode.guided.description", 8),
            PracticeModeDefinition("parity", "mode.parity", "mode.parity.description", 8),
            PracticeModeDefinition(
                "remainders", "mode.remainders", "mode.remainders.description", 8
            ),
            PracticeModeDefinition("proof", "mode.proof", "mode.proof.description", 8),
            PracticeModeDefinition("advanced", "mode.advanced", "mode.advanced.description", 8),
            PracticeModeDefinition("weak", "mode.weak", "mode.weak.description", 8),
        )

    def test_definitions(self) -> tuple[TestDefinition, ...]:
        return (
            TestDefinition("foundations", "challenge.foundations", 10, "invariants"),
            TestDefinition("method", "challenge.method", 12, "invariants"),
            TestDefinition("final", "challenge.final", 16, "invariants"),
        )

    def learning_units(self) -> tuple[LearningUnit, ...]:
        return tuple(
            LearningUnit(
                unit_id=unit_id,
                title_key=f"learn.{unit_id}.title",
                body_key=f"learn.{unit_id}.body",
                skill_keys=skills,
                related_practice_mode_id=mode_id,
            )
            for unit_id, skills, mode_id in LEARNING_SPECS
        )

    def content(self, key: str, **values: object) -> str:
        return self.catalog.get(key, **values)

    def render_learning_unit(self, unit_id: str) -> LearningView:
        unit = next((item for item in self.learning_units() if item.unit_id == unit_id), None)
        if unit is None:
            raise ValueError("unknown invariants learning unit")
        return LearningView(
            title=self.content(unit.title_key),
            body=self.content(unit.body_key),
            practice_configuration={"focus_skill": unit.skill_keys[0]},
        )

    def session_blueprint(
        self,
        mode_id: str,
        question_count: int,
        mastery: dict[str, MasteryState],
        configuration: dict[str, Any],
        rng: Random,
    ) -> tuple[tuple[str, str], ...]:
        if mode_id == "guided":
            blueprint = list(GUIDED_BLUEPRINT)
            while len(blueprint) < question_count:
                blueprint.extend(GUIDED_BLUEPRINT)
            return tuple(blueprint[:question_count])
        if mode_id == "weak":
            eligible = tuple(
                item.skill_key
                for item in self._skills
                if mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count > 0
                and not self._is_mastered(mastery.get(item.skill_key, MasteryState(item.skill_key)))
            )
            if not eligible:
                eligible = MODE_SKILLS["quick"]
        else:
            try:
                eligible = MODE_SKILLS[mode_id]
            except KeyError as exc:
                raise ValueError(f"unknown invariants practice mode: {mode_id}") from exc
        focus = configuration.get("focus_skill")
        if focus is not None and str(focus) not in self._skill_map:
            raise ValueError("unknown invariants focus skill")
        ordered = weighted_skill_order(eligible, mastery, datetime.now(UTC), rng)
        chosen: list[str] = []
        if focus is not None:
            chosen.append(str(focus))
        for skill_key in ordered:
            if skill_key not in chosen:
                chosen.append(skill_key)
            if len(chosen) >= question_count:
                break
        while len(chosen) < question_count:
            chosen.append(rng.choice(eligible))
        return tuple(
            (skill_key, rng.choice(QUESTION_TYPES[skill_key]))
            for skill_key in chosen[:question_count]
        )

    def test_blueprint(
        self, test_id: str, configuration: dict[str, Any], rng: Random
    ) -> tuple[tuple[str, str], ...]:
        del configuration
        foundations = (
            *GUIDED_BLUEPRINT,
            ("discover:parity", "starting_parity"),
            ("preserve:remainders", "remainder_reachable"),
        )
        method = (
            *foundations,
            ("reason:evidence_vs_proof", "evidence_vs_proof"),
            ("extend:stronger_invariant", "stronger_invariant"),
        )
        final = (
            *method,
            ("preserve:all_moves", "breaker_move"),
            ("prove:same_not_sufficient", "conclusion_strength"),
            ("extend:odd_part", "odd_part_reachable"),
            ("extend:odd_part", "odd_part_value"),
        )
        blueprints = {
            "foundations": foundations,
            "method": method,
            "final": final,
        }
        try:
            blueprint = list(blueprints[test_id])
        except KeyError as exc:
            raise ValueError(f"unknown invariants challenge: {test_id}") from exc
        rng.shuffle(blueprint)
        return tuple(blueprint)

    def generate_question(
        self, skill_key: str, question_type: str, rng: Random
    ) -> GeneratedQuestion:
        if skill_key not in self._skill_map:
            raise ValueError(f"unknown invariants skill: {skill_key}")
        if question_type not in QUESTION_TYPES[skill_key]:
            raise ValueError(f"{question_type} is not valid for {skill_key}")

        prompt: str
        options: tuple[tuple[str, str], ...]
        correct: str
        explanation: str
        hint: str
        misconception: str

        if question_type == "state_vs_property":
            prompt = (
                "Start with 10 coins and repeatedly add or remove exactly 2. "
                "Which statement correctly separates the state from the preserved property?"
            )
            options = (
                ("The exact coin count changes; its parity stays even.", "correct"),
                ("The exact coin count stays 10; only parity changes.", "reversed"),
                ("Nothing changes after a legal move.", "nothing"),
                ("The number of moves is always even.", "moves"),
            )
            correct = "correct"
            explanation = (
                "Values such as 8, 10, and 12 differ, but each is even. "
                "The changing state is the count; the preserved property is its parity."
            )
            hint = "List 10 → 8 and 10 → 12. Compare the values and their parity."
            misconception = "confuses the state with a property of the state"
        elif question_type == "identify_invariant":
            start, step = rng.choice(((10, 2), (11, 2), (23, 10)))
            prompt = f"Start at {start}. Every move is +{step} or −{step}. What stays fixed?"
            options = (
                ("The exact number", "exact"),
                (f"The remainder after division by {step}", "remainder"),
                ("The number always increases", "increase"),
                ("The number of moves", "moves"),
            )
            correct = "remainder"
            explanation = (
                f"Adding or subtracting {step} changes the value by a whole multiple of {step}, "
                f"so the remainder modulo {step} stays {start % step}."
            )
            hint = f"Compare {start}, {start + step}, and {start - step} modulo {step}."
            misconception = "tracks the exact value instead of a preserved property"
        elif question_type == "parity_reachable":
            start = rng.choice((7, 10, 11, 14))
            reachable = rng.choice((True, False))
            distance = 2 * rng.randint(1, 5)
            target = start + distance if reachable else start + distance + 1
            prompt = f"Start at {start}. Moves are +2 or −2. Can you reach {target}?"
            options = (
                ("Yes — the difference is a multiple of 2.", "yes_multiple"),
                ("No — the start and target have different parity.", "no_parity"),
                ("Yes — enough moves can reach every number.", "yes_any"),
                ("No — the exact starting number can never change.", "no_change"),
            )
            correct = "yes_multiple" if reachable else "no_parity"
            explanation = f"{target} − {start} = {target - start}. " + (
                "This is a multiple of 2, so repeated +2 moves give a route."
                if reachable
                else "This is odd, so the target has different parity and is impossible."
            )
            hint = "Compare whether the start and target are both even or both odd."
            misconception = "does not compare the parity of start and target"
        elif question_type == "starting_parity":
            start = rng.choice((8, 11, 15, 20))
            parity = "even" if start % 2 == 0 else "odd"
            other = "odd" if parity == "even" else "even"
            prompt = f"Start at {start} and use only ±2 moves. Which description is correct?"
            options = (
                (f"Every reachable number is {parity}.", "start_parity"),
                (f"Every reachable number is {other}.", "other_parity"),
                ("The moves decide a new parity each time.", "random"),
                ("Only the starting number is reachable.", "fixed"),
            )
            correct = "start_parity"
            explanation = f"{start} is {parity}, and adding or subtracting 2 preserves that parity."
            hint = "The starting state chooses the parity; ±2 preserves it."
            misconception = "treats even as the invariant regardless of the starting state"
        elif question_type == "check_all_moves":
            preserved = rng.choice((True, False))
            allowed_moves = (4, -6) if preserved else (4, -5)
            prompt = (
                f"Allowed changes are {allowed_moves[0]:+d} and {allowed_moves[1]:+d}. "
                "Is parity an invariant?"
            )
            breaker = next((move for move in allowed_moves if move % 2), None)
            options = (
                ("Yes — every allowed change is even.", "yes_all"),
                (
                    f"No — the {breaker:+d} move changes parity."
                    if breaker is not None
                    else "No — one move changes parity.",
                    "no_breaker",
                ),
                ("Yes — the first few examples happened to match.", "yes_examples"),
                ("No — an invariant must be the exact numerical value.", "no_exact"),
            )
            correct = "yes_all" if preserved else "no_breaker"
            explanation = (
                "Both move types are even, so each preserves parity."
                if preserved
                else (
                    f"The {breaker:+d} move is odd and switches parity, so parity is not invariant."
                )
            )
            hint = "Check each allowed change separately. An odd change switches parity."
            misconception = "fails to check every type of legal move"
        elif question_type == "breaker_move":
            divisor = rng.choice((2, 3, 5))
            breaker = divisor + 1
            move_values = (divisor, -2 * divisor, 3 * divisor, breaker)
            prompt = (
                f"We want the remainder modulo {divisor} to stay fixed. "
                "Which added move would break that invariant?"
            )
            options = tuple((f"Change by {move:+d}", str(move)) for move in move_values)
            correct = str(breaker)
            explanation = (
                f"The change {breaker:+d} is not divisible by {divisor}; "
                f"the other changes are whole multiples of {divisor}."
            )
            hint = f"Which change leaves a non-zero remainder when divided by {divisor}?"
            misconception = "checks examples instead of divisibility of every move"
        elif question_type == "card_flip_reachable":
            card_cases = (
                (
                    4,
                    1,
                    "no",
                    "No — an even black-card count cannot become odd.",
                    "The black count changes only by −2, 0, or +2, so 4 cannot become 1.",
                ),
                (
                    5,
                    0,
                    "no",
                    "No — an odd black-card count cannot become even.",
                    "Every move preserves parity, so 5 cannot become 0.",
                ),
                (
                    5,
                    1,
                    "yes",
                    "Yes — flip two black cards twice: 5 → 3 → 1.",
                    "The target has matching parity, and this explicit legal route "
                    "proves it reachable.",
                ),
                (
                    4,
                    2,
                    "yes",
                    "Yes — flip two black cards once: 4 → 2.",
                    "One BB → WW move reduces the black count by 2.",
                ),
            )
            start, target, correct, correct_label, explanation = rng.choice(card_cases)
            prompt = (
                f"There are 8 two-sided cards, initially {start} black. "
                f"Each move flips exactly two cards. Can exactly {target} be black?"
            )
            options = (
                (correct_label, correct),
                ("Yes — matching parity always proves a route without showing one.", "unsupported"),
                ("No — the number of black cards can never change.", "fixed"),
                ("It depends on which card is called first.", "order"),
            )
            hint = "A move changes the black-card count by −2, 0, or +2."
            misconception = "does not track parity through every two-card flip"
        elif question_type == "card_move_changes":
            prompt = (
                "When exactly two black/white cards are flipped, what are all possible changes "
                "in the number of black cards?"
            )
            options = (
                ("−2, 0, or +2", "even_changes"),
                ("Only +2", "plus_only"),
                ("−1 or +1", "odd_changes"),
                ("Any whole number", "anything"),
            )
            correct = "even_changes"
            explanation = (
                "BB → WW gives −2, WW → BB gives +2, and BW → WB gives 0. "
                "All possible changes are even."
            )
            hint = "Check BB, WW, and one card of each colour."
            misconception = "does not enumerate every card-flip move type"
        elif question_type == "identify_remainder":
            start, divisor = rng.choice(((20, 3), (14, 5), (23, 10)))
            remainder = start % divisor
            prompt = (
                f"Start at {start}; moves are +{divisor} or −{divisor}. "
                "Which invariant is most precise?"
            )
            options = (
                (f"Remainder {remainder} modulo {divisor}", "correct_remainder"),
                ("The exact number", "exact"),
                ("The quotient after division", "quotient"),
                ("The number always stays positive", "positive"),
            )
            correct = "correct_remainder"
            explanation = (
                f"{start} leaves remainder {remainder} modulo {divisor}. "
                f"Changing by ±{divisor} cannot change that remainder."
            )
            hint = f"Divide {start} and {start + divisor} by {divisor} and compare remainders."
            misconception = "confuses a fixed remainder with a changing quotient"
        elif question_type == "remainder_reachable":
            start, divisor = rng.choice(((20, 3), (14, 5), (23, 10)))
            reachable = rng.choice((True, False))
            multiplier = rng.randint(2, 7)
            target = start + divisor * multiplier + (0 if reachable else 1)
            prompt = f"Start at {start}; moves are ±{divisor}. Can you reach {target}?"
            options = (
                (
                    f"Yes — {target - start} is divisible by {divisor}.",
                    "yes_divisible",
                ),
                (
                    f"No — start and target have different remainders modulo {divisor}.",
                    "no_remainder",
                ),
                ("Yes — any large enough target is reachable.", "yes_large"),
                ("No — only one move is allowed.", "one_move"),
            )
            correct = "yes_divisible" if reachable else "no_remainder"
            explanation = f"The difference is {target - start}. " + (
                f"It equals {multiplier} × {divisor}, giving a legal route."
                if reachable
                else f"It is not divisible by {divisor}, so the invariant values differ."
            )
            hint = f"Check whether {target} − {start} is divisible by {divisor}."
            misconception = "does not compare the start and target remainders"
        elif question_type == "choose_proof":
            prompt = "Start at 15. Allowed moves are +4 and −6. Why is 16 impossible?"
            options = (
                (
                    "15 is odd and both legal changes are even, so every reachable value is odd.",
                    "parity_proof",
                ),
                ("I tried several moves and did not see 16.", "examples"),
                ("All targets larger than 15 are impossible.", "larger"),
                ("Because +4 is the only move that matters.", "one_move"),
            )
            correct = "parity_proof"
            explanation = (
                "Every legal change is even, so parity is preserved. "
                "The odd start 15 cannot reach the even target 16."
            )
            hint = "Check the parity of the start, both move sizes, and the target."
            misconception = "uses examples instead of a proof covering every move"
        elif question_type == "exit_problem":
            prompt = "Start at 7. Allowed moves are +6 and −9. Can you reach 20?"
            options = (
                (
                    "No — every change is divisible by 3, but 7 and 20 have different "
                    "remainders modulo 3.",
                    "no_mod3",
                ),
                ("Yes — 20 is larger than 7.", "yes_larger"),
                ("Yes — matching parity is enough.", "yes_parity"),
                ("No — subtraction is never allowed in invariant problems.", "no_subtraction"),
            )
            correct = "no_mod3"
            explanation = (
                "Both +6 and −9 change the value by a multiple of 3. "
                "But 7 ≡ 1 and 20 ≡ 2 modulo 3, so 20 is impossible."
            )
            hint = "Find a number that divides both 6 and 9, then compare remainders."
            misconception = "misses the common remainder preserved by all moves"
        elif question_type == "construct_route":
            route_cases = (
                (
                    "Start at 11 with ±2 moves. Which route reaches 19?",
                    "11 → 13 → 15 → 17 → 19",
                    (
                        "11 → 13 → 15 → 17 → 19",
                        "11 → 12 → 14 → 19",
                        "11 → 9 → 14 → 19",
                        "11 → 20 → 19",
                    ),
                ),
                (
                    "Start at 7 with +6 or −9 moves. Which route reaches 25?",
                    "7 → 13 → 19 → 25",
                    (
                        "7 → 13 → 19 → 25",
                        "7 → 16 → 25",
                        "7 → 14 → 20 → 25",
                        "7 → 1 → 10 → 25",
                    ),
                ),
                (
                    "Start at 20 with ±3 moves. Which route reaches 29?",
                    "20 → 23 → 26 → 29",
                    (
                        "20 → 23 → 26 → 29",
                        "20 → 22 → 25 → 29",
                        "20 → 17 → 24 → 29",
                        "20 → 30 → 29",
                    ),
                ),
            )
            prompt, correct_label, routes = rng.choice(route_cases)
            options = tuple((route, route) for route in routes)
            correct = correct_label
            explanation = (
                f"{correct_label} uses only allowed moves and ends at the requested target."
            )
            hint = "Check every arrow, not only the start and end."
            misconception = "accepts a route containing an illegal move"
        elif question_type == "count_moves":
            start, step, move_count = rng.choice(((11, 2, 4), (20, 3, 6), (14, 5, 3)))
            target = start + step * move_count
            prompt = (
                f"Start at {start} and use ±{step}. What is the fewest number of moves "
                f"needed to reach {target}?"
            )
            values = {
                move_count,
                max(1, move_count - 1),
                move_count + 1,
                move_count + 2,
            }
            while len(values) < 4:
                values.add(max(values) + 1)
            options = tuple((str(value), str(value)) for value in sorted(values))
            correct = str(move_count)
            explanation = (
                f"{target} − {start} = {target - start} = {move_count} × {step}, "
                f"so {move_count} forward moves are sufficient and minimal."
            )
            hint = "Divide the required change by the size of one move."
            misconception = "finds reachability but not the number of legal moves"
        elif question_type == "same_not_sufficient":
            prompt = (
                "A start and target have the same value of a known invariant. "
                "What may we conclude immediately?"
            )
            options = (
                (
                    "The invariant does not rule the target out; a route or another argument "
                    "is still needed.",
                    "maybe",
                ),
                ("The target is definitely reachable.", "definitely"),
                ("The target is definitely impossible.", "impossible"),
                ("Every sequence of moves reaches the target.", "every"),
            )
            correct = "maybe"
            explanation = (
                "Different invariant values prove impossibility. Matching values remove that "
                "particular obstruction, but they do not construct a route."
            )
            hint = "An invariant is a one-way obstruction: different means no."
            misconception = "treats a necessary condition as sufficient"
        elif question_type == "conclusion_strength":
            prompt = (
                "Start with 5 black cards and flip exactly two cards each move. "
                "The target of 1 black card has matching odd parity. Which is the strongest "
                "justified statement before constructing moves?"
            )
            options = (
                ("Parity does not forbid 1, but reachability is not proved yet.", "not_forbidden"),
                ("Exactly 1 black card is automatically reachable.", "automatic"),
                ("Exactly 1 black card is impossible.", "impossible"),
                ("The black-card count never changes.", "fixed"),
            )
            correct = "not_forbidden"
            explanation = (
                "Both counts are odd, so parity cannot rule the target out. "
                "A construction such as 5 → 3 → 1 supplies the separate proof of possibility."
            )
            hint = "Separate what parity says from what an explicit route says."
            misconception = "overstates what a matching invariant proves"
        elif question_type == "evidence_vs_proof":
            prompt = (
                "A program tries 10,000 sequences of ±2 moves from 10 and never reaches an odd "
                "number. What turns the observation into a proof?"
            )
            options = (
                (
                    "Show that the start is even and that both +2 and −2 preserve evenness.",
                    "all_moves_proof",
                ),
                ("Run the program for another 10,000 sequences.", "more_trials"),
                ("Choose only sequences that increase.", "increasing"),
                ("Assume the program has tested every possible future.", "assume"),
            )
            correct = "all_moves_proof"
            explanation = (
                "Experiments suggest the pattern. Checking the start and every legal move "
                "proves it for all sequences, including those never simulated."
            )
            hint = "A proof must cover infinitely many possible sequences at once."
            misconception = "confuses computational evidence with mathematical proof"
        elif question_type == "definition":
            prompt = "Which definition best describes an invariant?"
            options = (
                (
                    "A property preserved by every allowed move while the state may change.",
                    "definition",
                ),
                ("A numerical value that must never change at all.", "exact_value"),
                ("A pattern seen in several experiments.", "examples"),
                ("The final target of a process.", "target"),
            )
            correct = "definition"
            explanation = (
                "An invariant is a preserved property of the state. "
                "It need not be the exact value, and every legal move must preserve it."
            )
            hint = "Focus on a property and on every allowed move."
            misconception = "defines an invariant as an unchanging exact quantity"
        elif question_type == "stronger_invariant":
            prompt = (
                "Start at 23 with moves +10 or −10. Both parity and remainder modulo 10 are "
                "preserved. Which invariant gives more information?"
            )
            options = (
                (
                    "Remainder modulo 10, because it says every reachable number ends in 3.",
                    "mod10",
                ),
                ("Parity, because it identifies every reachable number exactly.", "parity_exact"),
                ("The exact number 23, because it never changes.", "exact"),
                ("Neither property is preserved.", "neither"),
            )
            correct = "mod10"
            explanation = (
                "Parity says only that states stay odd. Remainder 3 modulo 10 gives the "
                "stronger restriction that every reachable state ends in 3."
            )
            hint = "Which property splits whole numbers into more precise classes?"
            misconception = "chooses a weaker invariant when a stronger one is available"
        elif question_type == "mixed_moves":
            mixed_cases = (
                (
                    15,
                    "+4 and −6",
                    "Parity",
                    "Both changes are even, so parity stays fixed.",
                ),
                (
                    7,
                    "+6 and −9",
                    "Remainder modulo 3",
                    "Both changes are multiples of 3.",
                ),
                (
                    14,
                    "+5 and −5",
                    "Remainder modulo 5",
                    "Both changes are multiples of 5; parity can change.",
                ),
            )
            start, moves_text, correct_label, explanation = rng.choice(mixed_cases)
            prompt = f"Start at {start} with moves {moves_text}. Which is a useful invariant?"
            labels = (
                "Parity",
                "Remainder modulo 3",
                "Remainder modulo 5",
                "The exact number",
            )
            options = tuple((label, label) for label in labels)
            correct = correct_label
            hint = "Find a divisor shared by every allowed change."
            misconception = "uses parity automatically without checking the moves"
        elif question_type == "odd_part_reachable":
            target = rng.choice((3, 48, 18))
            reachable = target in {3, 48}
            prompt = (
                "Start at 12. You may multiply by 2 or divide by 2 when the result is whole. "
                f"Can you reach {target}?"
            )
            options = (
                (
                    f"Yes — 12 and {target} have the same odd part, 3.",
                    "yes_same",
                ),
                (
                    f"No — 12 has odd part 3 but {target} has odd part {_odd_part(target)}.",
                    "no_different",
                ),
                ("Yes — doubling and halving eventually reach every number.", "yes_any"),
                ("No — the starting value itself is invariant.", "no_fixed"),
            )
            correct = "yes_same" if reachable else "no_different"
            route = (
                "12 → 6 → 3"
                if target == 3
                else "12 → 24 → 48"
                if target == 48
                else "18 = 9 × 2 has odd part 9, unlike 12 = 3 × 4."
            )
            explanation = f"Doubling or halving changes only the power of 2. {route}"
            hint = "Remove all factors of 2 from the start and target."
            misconception = "does not separate the odd part from the power of two"
        elif question_type == "odd_part_value":
            value = rng.choice((12, 24, 40, 56, 72))
            part = _odd_part(value)
            prompt = f"What is the odd part of {value}?"
            distractors = {part, value // 2, 1, value}
            candidate = 3
            while len(distractors) < 4:
                distractors.add(candidate)
                candidate += 2
            options = tuple((str(item), str(item)) for item in sorted(distractors)[:4])
            if str(part) not in {value for _, value in options}:
                options = (*options[:3], (str(part), str(part)))
            correct = str(part)
            explanation = (
                f"Repeatedly divide {value} by 2 while possible. "
                f"The remaining odd factor is {part}."
            )
            hint = "Keep removing factors of 2 until the result is odd."
            misconception = "removes only one factor of two instead of all of them"
        else:  # pragma: no cover - guarded by QUESTION_TYPES
            raise ValueError(f"unsupported invariants question type: {question_type}")

        shuffled = list(options)
        rng.shuffle(shuffled)
        answer_options = tuple(
            AnswerOption(label=label, value={"value": value}) for label, value in shuffled
        )
        validate_options("single_choice", answer_options)
        return GeneratedQuestion(
            topic_id=self.metadata.topic_id,
            skill_key=skill_key,
            question_type=question_type,
            rendered_prompt=prompt,
            answer_mode="single_choice",
            answer_options=answer_options,
            correct_answer={"value": correct},
            explanation_payload={"equation": explanation},
            metadata={
                "hints": [hint],
                "misconception": misconception,
            },
        )

    def evaluate_answer(
        self, question_payload: dict[str, Any], selected_answer: dict[str, Any]
    ) -> EvaluationResult:
        correct_answer = dict(question_payload["correct_answer"])
        is_correct = selected_answer.get("value") == correct_answer.get("value")
        explanation = str(question_payload["explanation_payload"]["equation"])
        metadata = dict(question_payload.get("metadata", {}))
        hints = list(metadata.get("hints", []))
        return EvaluationResult(
            is_correct=is_correct,
            canonical_answer=correct_answer,
            feedback_key="feedback.correct" if is_correct else "feedback.incorrect",
            feedback_payload={
                "equation": explanation,
                "misconception": "" if is_correct else str(metadata.get("misconception", "")),
            },
            hint_key=None if is_correct else "feedback.hint",
            hint_payload=None
            if is_correct
            else {"hint": str(hints[0]) if hints else "Check every allowed move."},
        )

    def retry_question_type(self, skill_key: str, question_type: str, rng: Random) -> str:
        try:
            choices = QUESTION_TYPES[skill_key]
        except KeyError as exc:
            raise ValueError(f"unknown invariants skill: {skill_key}") from exc
        alternatives = [item for item in choices if item != question_type]
        return rng.choice(alternatives or list(choices))

    def progress_view(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> TopicProgressView:
        groups: list[ProgressGroup] = []
        for group_key, label in GROUP_LABELS.items():
            keys = [item.skill_key for item in self._skills if item.group_key == group_key]
            percentage = round(
                sum(mastery.get(key, MasteryState(key)).box for key in keys) / (len(keys) * 5) * 100
            )
            groups.append(ProgressGroup(label, percentage))
        mastered = [
            item
            for item in self._skills
            if self._is_mastered(mastery.get(item.skill_key, MasteryState(item.skill_key)))
        ]
        ranked = sorted(
            self._skills,
            key=lambda item: (
                mastery.get(item.skill_key, MasteryState(item.skill_key)).box,
                -mastery.get(item.skill_key, MasteryState(item.skill_key)).attempt_count,
                item.difficulty,
            ),
        )
        return TopicProgressView(
            headline_metrics=(
                Metric("Total questions", str(int(metrics.get("total", 0)))),
                Metric("Questions in 7 days", str(int(metrics.get("recent", 0)))),
                Metric("Recent accuracy", f"{int(metrics.get('accuracy', 0))}%"),
                Metric("Ideas mastered", str(len(mastered))),
                Metric("Active days", str(int(metrics.get("active_days", 0)))),
            ),
            progress_groups=tuple(groups),
            strengths=tuple(
                ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
                for item in mastered[:3]
            ),
            current_targets=tuple(
                ProgressItem(skill_label(item.skill_key), skill_key=item.skill_key)
                for item in ranked[:3]
            ),
            suggested_action=SuggestedAction(
                "Practise developing invariant ideas", "practice:weak"
            ),
        )

    @staticmethod
    def _is_mastered(state: MasteryState) -> bool:
        formats = {str(item) for item in state.state.get("correct_formats", [])}
        return is_mastered(state) and len(formats) >= 2

    def test_result_metrics(self, attempts: tuple[dict[str, Any], ...]) -> tuple[Metric, ...]:
        result: list[Metric] = []
        for group_key, label in GROUP_LABELS.items():
            relevant = [
                item
                for item in attempts
                if self._skill_map[str(item["skill_key"])].group_key == group_key
            ]
            if relevant:
                correct = sum(bool(item["is_correct"]) for item in relevant)
                result.append(Metric(label, f"{round(correct / len(relevant) * 100)}%"))
        return tuple(result)

    def teacher_insights(
        self, mastery: dict[str, MasteryState], metrics: dict[str, int | float]
    ) -> tuple[ProgressItem, ...]:
        misconceptions: dict[str, int] = {}
        for state in mastery.values():
            for label, count in dict(state.state.get("misconceptions", {})).items():
                misconceptions[str(label)] = misconceptions.get(str(label), 0) + int(count)
        ranked = sorted(misconceptions.items(), key=lambda item: (-item[1], item[0]))[:3]
        return (
            ProgressItem("Hints used", str(int(metrics.get("hints", 0)))),
            ProgressItem("Daily questions in 7 days", str(int(metrics.get("daily", 0)))),
            *(ProgressItem(label, f"{count} observed") for label, count in ranked),
        )

    def daily_skill(
        self, mastery: dict[str, MasteryState], now: datetime, rng: Random
    ) -> tuple[str, str]:
        rotations = (
            ("discover:parity", "parity_reachable"),
            ("preserve:card_flips", "card_flip_reachable"),
            ("preserve:remainders", "remainder_reachable"),
            ("preserve:all_moves", "check_all_moves"),
            ("prove:impossible", "exit_problem"),
            ("prove:same_not_sufficient", "same_not_sufficient"),
            ("reason:evidence_vs_proof", "evidence_vs_proof"),
        )
        shifted = (
            rotations[now.date().toordinal() % len(rotations) :]
            + rotations[: now.date().toordinal() % len(rotations)]
        )
        ordered = weighted_skill_order(tuple(skill for skill, _ in shifted), mastery, now, rng)
        skill_key = ordered[0]
        return skill_key, dict(shifted)[skill_key]

    def render_media(self, renderer_id: str, payload: dict[str, Any]) -> bytes:
        del renderer_id, payload
        raise ValueError("the invariants topic has no media renderer")

    def validate(self) -> list[str]:
        errors = validate_topic_contract(self)
        if len(self.learning_units()) != 8:
            errors.append("the complete eight-part invariants theory sequence is required")
        if len(self.practice_modes()) != 7:
            errors.append("all seven invariants practice modes are required")
        if len(self.test_definitions()) != 3:
            errors.append("all three invariants challenges are required")
        for skill_key, question_types in QUESTION_TYPES.items():
            for question_type in question_types:
                try:
                    for seed in range(3):
                        question = self.generate_question(skill_key, question_type, Random(seed))
                        validate_options(question.answer_mode, question.answer_options)
                        if not self.evaluate_answer(
                            {
                                "correct_answer": question.correct_answer,
                                "explanation_payload": question.explanation_payload,
                                "metadata": question.metadata,
                            },
                            question.correct_answer,
                        ).is_correct:
                            errors.append(f"correct answer rejected: {skill_key}/{question_type}")
                except Exception as exc:
                    errors.append(f"question failed: {skill_key}/{question_type}: {exc}")
        for unit in self.learning_units():
            try:
                view = self.render_learning_unit(unit.unit_id)
                if not view.title or not view.body:
                    errors.append(f"empty learning unit: {unit.unit_id}")
            except Exception as exc:
                errors.append(f"learning unit failed: {unit.unit_id}: {exc}")
        return errors
