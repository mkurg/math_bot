# Implementation notes

- The user explicitly changed the specified runtime from Python 3.12 to Python 3.14. The project, container, lint target, type-check target, lockfile, tests, and documentation consistently use Python 3.14.
- Generic database records identify mathematics only by stable `topic_id`, opaque `skill_key`, and validated JSON payloads. No factor or operation columns exist in the core schema.
- Multiplication skill keys are canonical commutative families such as `mul:6:7`; division is tracked separately as `div:6:7`.
- Answer recording locks the question, inserts through the `(question_id, user_id)` uniqueness boundary, updates mastery, and advances the session in one transaction.
- Daily deliveries use `(user_id, local_date)` uniqueness. The worker creates the delivery and question before sending and never creates a second row for an ignored question.
- Invitations store only a SHA-256 hash. The displayed token is an HMAC-derived value that can be reconstructed for the active record and invalidated immediately by rotation.
- Images are deterministic Pillow output. Committed assets improve responsiveness; runtime renderers remain available for visual questions and fallbacks.
- The core handler layer imports only topic contracts and the registry. Production topic registration occurs only in `app/main.py`.

