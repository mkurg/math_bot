# Numeral systems acceptance checklist

Automated evidence recorded on 2026-07-16 with Python 3.14.5 and PostgreSQL 17.9: `304 passed`, no skips, 85.17% overall coverage, Ruff clean, formatting clean, and strict mypy clean.

## Assignment and isolation

- [x] `numeral_systems` is a registered, validated topic and can be assigned per student.
- [x] One assigned topic opens directly without a topic-selection screen.
- [x] Menus, sessions, daily questions, attempts, mastery, progress, and challenge history use the student’s assigned topic.
- [x] Times-table and numeral-systems students are covered together by a PostgreSQL isolation test.
- [x] The teacher can change an individual student’s module or active/paused state.
- [x] Teacher lists, detail views, group breakdowns, difficult skills, and recent results identify both topics.

## Curriculum and mathematical accuracy

- [x] Diagnostic binary recap, general positional notation, binary/decimal, binary/octal, binary/hexadecimal, decimal conversion, and octal/hexadecimal bridging are present.
- [x] Bits, nibbles, bytes, 256 patterns versus maximum 255, RGB, selected ASCII, and interpretation are present.
- [x] All generated values use canonical integer conversions for bases 2, 8, 10, and 16; every byte value round-trips in every supported base in tests.
- [x] Structural grouping uses three bits for octal and four for hexadecimal, from the right with left padding.
- [x] Hexadecimal is described as compact human notation for stored bits, never as the computer’s storage format.
- [x] RGB channels stay in 0–255 with exactly two hexadecimal digits per channel; ASCII characters remain distinct from their assigned codes.

## Practice, questions, and interaction

- [x] The ten original practice modes and all eight specified challenges remain; an eleventh guided mode creates a three-tier progression without reducing the full-curriculum tier.
- [x] All required conceptual, conversion, comparison, missing-digit, error, method, bit/byte, RGB, character, interpretation, and transformation question families are generated and tested.
- [x] Multiple choice and binary/octal/decimal/hexadecimal numeral pads require no Telegram keyboard typing; long options are printed in full and selected with compact A/B/C/D buttons.
- [x] Tier 1 contains foundational recognition with no decimal-conversion drills; Tier 2 uses single 3-bit/4-bit groups and no decimal conversions; Tier 3 preserves the original full difficulty.
- [x] Constructed answers show the current value and provide digit, backspace, clear, and submit controls.
- [x] Ownership, expiry, validation, and first-submission-only behavior use the generic answer service.
- [x] Three-level progressive hints are bounded, separately recorded, and do not count as failure.
- [x] Incorrect answers receive a worked explanation and return later in a different format.

## Adaptation, progress, and teacher view

- [x] Forty-eight stable skills cover foundation, conversions, cross-base reasoning, data units, RGB, characters, and interpretation.
- [x] Prerequisites affect selection priority while occasional exploratory applications remain available.
- [x] Mastery requires correct work across multiple days and at least two question formats.
- [x] Daily questions rotate among concept, guided bit-group conversion, application, and interpretation without hard decimal-conversion drills.
- [x] Student progress shows topic-specific metrics, conceptual groups, strengths, current targets, stage, and recent challenges.
- [x] Teacher detail shows module, reminder, challenge history, hint use, daily activity, misconceptions, and procedural/conceptual pattern.
- [x] No speed penalty, public leaderboard, runtime AI content, or excluded advanced topic is included.

## Delivery

- [x] Production image with both topics is deployed on Hetzner; Python 3.14.5, topic validation, live polling, and zero restarts were verified on 2026-07-16.
- [ ] Telegram acceptance is completed from the assigned numeral-systems student account.
