# Acceptance checklist

Evidence recorded on 2026-07-16 with Python 3.14.5, PostgreSQL 17.9, and Docker. Current combined automated evidence: `304 passed`, no skips, 85.17% overall coverage, Ruff clean, formatting clean, strict mypy clean, topic/content validation passed, clean Alembic upgrade passed, and `alembic check` reported no model drift.

## A. Version-one scope

- [x] Factors 1–10, no multiplication by zero, and exact related division are domain-tested.
- [x] One teacher/one class, private chats, and invitation-only students are enforced.
- [x] Times-table students remain assigned only to `times_tables`; the separately specified `numeral_systems` module is isolated by student assignment.
- [x] No audio, runtime AI, web dashboard, Mini App, leaderboard, or unrelated visible topic exists.

## B. Modular architecture

- [x] The documented topic contract, validated registry, enabled/default configuration, and generic view models exist.
- [x] Handlers resolve modules through the registry and do not import `times_tables`.
- [x] Sessions, mastery, statistics, callbacks, daily delivery, and JSON database payloads are topic-independent.
- [x] Test composition, learning content, media, progress grouping, and daily generation come from the topic.
- [x] `SampleTopic` completes session, answer, mastery, progress, and daily flows without core edits.
- [x] A future compatible topic requires no schema or generic-handler change.

## C. Onboarding and access

- [x] Hashed, rotatable deep-link invitations create students and assign the configured default topic.
- [x] Invalid invitations create no student; returning students retain progress.
- [x] Admin access is restricted to the configured Telegram ID.
- [x] Group messages create no learning records and direct users to private chat.

## D. Learning content

- [x] Ten text tables, related division, a full table, all reviewed tips, and all hard-fact cards exist.
- [x] Ten individual images, one full image, mascot, and deterministic visual renderers are generated and committed.
- [x] Media sending has a text fallback; learning units belong to the topic module.

## E. Practice

- [x] Five-, ten-, table-, multiplication-, division-, and mixed-practice blueprints are tested.
- [x] Table practice uses approximately 70% selected table, 20% weak review, and 10% confidence material.
- [x] All seven required question types, unique plausible options, button answers, calm feedback, delayed retry, recovery, and summaries exist.
- [x] The entire times-table student journey is Russian-localized, including menus, prompts, stories, feedback, progress, reminders, privacy text, and learning-image titles.
- [x] Ownership, expiry, first-answer-only behavior, and database idempotency are enforced.

## F. Adaptive behavior

- [x] Mastery is keyed by user/topic/skill; multiplication and division families are separate.
- [x] Correct/wrong box movement, due timestamps, response times, mastered review, prerequisites, and adaptive priority are tested.
- [x] Consecutive prompt/family controls and delayed mistake return are implemented without loops.

## G. Tests

- [x] Table (10), division (10), and mixed (20 with exact composition) tests are domain-tested.
- [x] Feedback is withheld until completion; answers update mastery and statistics.
- [x] Results show score, percentage, operation accuracy, strengths/targets, and weak-practice action.
- [x] Test abandonment requires confirmation.

## H. Daily tasks

- [x] All frequencies and hours 07:00–20:00 are button-configurable by student and teacher.
- [x] Defaults and confirmed apply-to-all are implemented without a permanent lock.
- [x] One local-date delivery, ignored-question silence, restart persistence, answer idempotency, and registry-based generation are database-tested.
- [x] Telegram failure handling is bounded and repeated permanent failures deactivate delivery.

## I. Statistics

- [x] Student totals, seven-day questions/accuracy/days, multiplication/division, table progress, strengths, and targets exist.
- [x] Teacher student list, individual detail/recent tests, group activity/accuracy/difficult skills, and reminder count exist.
- [x] No public ranking exists; generic aggregates and topic labels remain separated.

## J. Privacy

- [x] Only specified operational and learning data is modeled.
- [x] `/privacy` explains storage, teacher access, and deletion.
- [x] `/delete_me` confirms and cascade-deletes all student-linked topic data.
- [x] Secret-bearing files are ignored; logs do not dump tokens, passwords, names, callbacks, or updates.

## K. Reliability

- [x] Empty-database migration and model-drift checks pass.
- [x] Uniqueness blocks duplicate answers and daily deliveries.
- [x] Startup validates settings, database, topics, content, and migrations.
- [x] Transient/permanent Telegram failures and missing images are handled.
- [x] Graceful shutdown, persisted sessions, and serializable topic payloads are tested.

## L. Quality and delivery

- [x] `ruff check .` and `ruff format --check .` pass.
- [x] `mypy app tests` passes in strict mode.
- [x] `pytest` passes: 304 tests, no skips, 85.17% overall coverage.
- [x] Core/services/topic-domain coverage meets or exceeds 85%; overall exceeds 75%.
- [x] Topic and content validators pass.
- [x] Dependency lock, Dockerfile, Compose, persistent database volume, migration, environment example, README, backup/restore, and topic guide exist.
- [x] Production Python 3.14.5 Docker image and live polling deployment verified on Hetzner; PostgreSQL is healthy, migration `20260716_0001` is applied, and the bot is running with zero restarts.
- [ ] Final manual Telegram acceptance flow completed. Requires one invited student Telegram account to exercise the live student journey.
