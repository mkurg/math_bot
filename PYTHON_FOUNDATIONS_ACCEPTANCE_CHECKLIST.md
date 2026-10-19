# Python Foundations & Fighting Game acceptance checklist

The `python_foundations` topic implements the attached execution-first curriculum as an
isolated production module. It uses the existing generic session, mastery, daily-question,
progress, and teacher-insight infrastructure and requires no database migration.

## Curriculum

- [x] The stable catalogue contains all 53 specified `PY.*` and `GAME.*` skill IDs.
- [x] Adaptive practice uses prerequisites; choosing a lesson or catalog task opens that exact material directly.
- [x] Twenty-two ordered learning units cover the diagnostic, foundations, terminology,
  all nine Fighting labs, and the optional small `d20()` bridge.
- [x] Content consistently uses Predict → Run → Explain → Modify.
- [x] The full AI-generated RPG, persistence, decorators, dataclasses, inheritance,
  exceptions, async code, and external packages are outside the required curriculum.
- [x] All student-facing module instructions and answers are in Russian; Python code remains Python.

## Practice and assessment

- [x] Diagnostic, quick, exact-output, tracing, debugging, mini-script construction,
  Fighting Lab, mixed review, challenge, and weak-prerequisite modes are available.
- [x] Every skill has recognition, prediction, and construction/debugging levels.
- [x] The optional in-bot catalog exposes all 53 skills and all three levels in curriculum order.
- [x] Lesson practice uses the selected lesson's skills, and short diagnostics rotate through their full pool.
- [x] Exact-output code is compiled and executed during startup validation; simulated input
  is declared, loops terminate, and random questions never claim an uncontrolled output.
- [x] Three progressive hints are the maximum for every question.
- [x] Wrong answers store an explicit misconception flag and retry in another format.
- [x] Four challenges cover foundations, functions/data, objects/state, and Fighting.
- [x] The acceptance path tests definition versus call, `self`/`other`, armor overflow,
  initiative timing, and the every-third-hit counter.

## Adaptation and reporting

- [x] Adaptive practice prioritizes prerequisite-sized gaps, attempted weak skills, due
  review, the current curriculum target, and varied question formats.
- [x] Mastery requires generic multi-day evidence plus at least two formats; functions,
  classes, and Fighting also require a construction/debugging success.
- [x] Student progress is grouped by execution, values, I/O and operators, control flow,
  functions, collections, classes, and Fighting.
- [x] Teacher insights expose attempts, recent accuracy, hint use, prediction evidence,
  construction/debug evidence, Fighting mastery, and persistent misconceptions.

## Local validation evidence — 2026-10-18

- [x] `python scripts/validate_topics.py` passes for all five registered modules.
- [x] `python scripts/validate_content.py` passes for all five registered modules.
- [x] Ruff passes for the new topic, its tests, and modified registration scripts.
- [x] Strict mypy passes for all new and modified Python files.
- [x] The 60 dedicated Python Foundations tests pass.
- [x] The complete test collection passes without coverage enforcement: **433 passed,
  16 skipped**. The skipped PostgreSQL/handler integration tests require the external test
  database configured by `TEST_DATABASE_URL`.
