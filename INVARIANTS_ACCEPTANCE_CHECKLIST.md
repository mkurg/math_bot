# Invariants module acceptance checklist

The `invariants` topic implements the attached lesson plan “Invariants — What Refuses to
Change?” as an isolated third learning module.

## Curriculum and theory

- [x] Eight ordered learning units preserve the lesson arc: the ±2 coin game, the role of
  the starting state, two-card flips, remainders, the four-step method, the logical warning
  about matching invariants, experiments versus proof, and deeper invariants.
- [x] Theory distinguishes the changing state from a preserved property.
- [x] Theory requires checking every type of legal move.
- [x] Theory explicitly states that different invariant values prove impossibility, while
  matching values do not by themselves prove reachability.
- [x] Worked constructions are included for reachable targets.
- [x] The optional odd-part example and the programming assertion distinction are included.
- [x] Every learning unit links directly to focused practice.

## Practice and assessment

- [x] Seven button-first practice modes are available: quick, guided, parity/cards,
  remainders, proof/possibility, advanced, and adaptive developing-ideas review.
- [x] Three challenges contain 10, 12, and 16 questions.
- [x] Eleven stable skills cover discovery, preservation, proof, evidence, and extensions.
- [x] Every skill has two distinct question formats so mastery requires varied evidence.
- [x] Questions include concise feedback, a hint, and a recorded misconception category.
- [x] Wrong answers return later through the generic retry pipeline.
- [x] Daily questions rotate through the central conceptual skills.

## Isolation, progress, and administration

- [x] Storage uses the generic `user + topic_id + skill_key` model; no migration is needed.
- [x] Practice, challenges, daily questions, mastery, progress, and misconceptions remain
  isolated from `times_tables` and `numeral_systems`.
- [x] The teacher can assign the module from the existing student detail screen.
- [x] Existing students keep their current topic assignment and historical progress.
- [x] Teacher student details show progress, recent challenges, hints, daily activity, and
  the most frequent invariant misconceptions.
- [x] Group statistics include a separate Invariants row.

## Validation evidence

- [x] Topic validation passes for all three production modules.
- [x] Content validation passes for core and all three production modules.
- [x] `ruff check .` passes.
- [x] `ruff format --check .` passes.
- [x] Strict `mypy app tests` passes.
- [x] The full PostgreSQL suite passes: **357 passed**, no skips.
- [x] Overall coverage is **86.70%**; the invariants module is **96%** covered.
- [x] Randomized mathematical soundness tests cover parity, remainders, card flips, and the
  odd-part invariant across hundreds of seeds.
