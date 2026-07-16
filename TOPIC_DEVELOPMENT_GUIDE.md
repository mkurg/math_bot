# Topic development guide

The Telegram application treats mathematics as a plugin-like domain module. A new topic is added under `app/topics/<topic_id>/`; generic handlers, callbacks, sessions, reminders, privacy, invitations, and database tables remain unchanged.

## Contract

Implement `TopicModule` from `app/core/topics/contracts.py`. A module supplies:

- stable `TopicMetadata`;
- unique `SkillDefinition` records and valid prerequisite keys;
- data-defined practice modes and tests;
- learning units and rendered learning views;
- deterministic session and test blueprints;
- complete generated questions, answer options, correct payloads, hints, and media metadata;
- answer evaluation;
- topic-specific progress and test metrics;
- daily-skill selection;
- deterministic media rendering;
- startup validation.

Skill keys are permanent data identifiers. Prefer a namespaced form that describes the smallest mastery unit without leaking fields into the generic schema. Times tables use `mul:6:7` and `div:6:7`. A future distributive-property module might use:

```text
distributive:expand:a_times_b_plus_c
distributive:factor:common_factor
distributive:equivalent_expression
```

## Minimal shape

```python
class ExampleTopic:
    metadata = TopicMetadata(
        topic_id="example",
        version="1.0.0",
        title_key="topic.title",
        short_title_key="topic.short",
        description_key="topic.description",
        icon="🧮",
    )

    def skills(self) -> tuple[SkillDefinition, ...]:
        return (SkillDefinition("example:first", "example", "skill.first", "skill.first.body"),)

    def practice_modes(self) -> tuple[PracticeModeDefinition, ...]:
        return (PracticeModeDefinition("quick", "mode.quick", "mode.quick.body", 5),)

    # Implement every remaining TopicModule method.
```

The complete small example used by contract and modularity tests is in `tests/sample_topic.py`.

## Questions and answer modes

`GeneratedQuestion` must contain a rendered prompt, opaque skill key, registered answer mode, unique options, canonical correct answer, serializable explanation payload, and optional `GeneratedMedia`. The core supports `single_choice` and `true_false`. Extend `app/core/questions/answer_modes.py` only when a genuinely reusable new answer interaction is needed; never add `if topic_id == ...` to a callback handler.

Evaluation receives the persisted question payload and selected answer payload. It returns correctness and feedback data; the core does not calculate mathematics.

## Mastery and progress

Map each question to one stable skill. The generic engine owns boxes 0–5, due timestamps, answer counts, and the minimum mastered rule. Topic code owns prerequisites, related skills, eligibility, group percentages, labels, strengths, targets, and test breakdowns.

Keep `topic_state` small, bounded, and JSON-serializable. New topics fitting these generic payloads require no database migration.

## Learning content and media

Place visible topic strings and reviewed educational material under `app/topics/<topic_id>/content/`. Learning views may attach a registered deterministic renderer. Provide phone-readable output and text fallback. Do not download assets or call an AI service at runtime.

## Registration and configuration

Register the module in the composition root, then add its ID to `ENABLED_TOPIC_IDS`. `DEFAULT_TOPIC_ID` must be enabled. With one topic, no topic selector is shown. Removing `times_tables` from configuration must not cause an import from a core module.

For a future distributive-property topic, implement its directory and register it in the composition root. Do not modify Telegram handlers, the session engine, the mastery engine, reminders, privacy, invitations, or database tables.

## Validation and tests

Every topic must pass the generic contract expectations demonstrated by `SampleTopic`, plus domain tests for all formulas, distractors, blueprints, content, serialization, deterministic seeds, progress, and media.

```bash
python scripts/validate_topics.py
python scripts/validate_content.py
pytest
```

If a topic needs new durable data beyond bounded JSON payloads, design an explicit migration. Never reinterpret or rename an existing skill key after student data exists.

