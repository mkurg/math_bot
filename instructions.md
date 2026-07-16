# Modular Mathematics Practice Telegram Bot  
## Version 1.0: Times Tables  
### Product Design, Technical Specification, and Instructions for an AI Coding Agent

**Specification version:** 1.1  
**Initial product:** Times-table learning bot  
**Primary users:** One teacher and the teacher’s students  
**Initial mathematical scope:** Multiplication and division using factors from 1 through 10  
**Architectural requirement:** Mathematical topics must be replaceable and extendable without rebuilding the Telegram application

---

# 1. Product objective

Build a friendly Telegram bot that initially helps students learn and retain the multiplication table from 1 to 10 and the corresponding division facts during the summer.

The first version must:

- teach multiplication tables;
- provide short multiplication and division practice sessions;
- provide tests;
- provide visual and text-based problems;
- remember each student’s strengths and weaknesses;
- adapt future questions to the student’s performance;
- send one optional scheduled question on selected days;
- show useful progress statistics to the student and teacher;
- require almost no typed input;
- remain friendly, calm, and non-invasive.

The underlying application must be reusable for other mathematics topics.

A future developer or AI coding agent must be able to add or replace the times-table topic with topics such as:

- the distributive property;
- order of operations;
- fractions;
- divisibility;
- factors and multiples;
- addition and subtraction;
- equations;
- percentages;
- another structured school-mathematics topic.

Adding a new topic must not require rebuilding:

- Telegram onboarding;
- menus;
- answer-button handling;
- practice-session infrastructure;
- test-session infrastructure;
- daily scheduling;
- statistics storage;
- teacher administration;
- invitations;
- privacy functions;
- deployment infrastructure.

Version 1.0 still exposes only the times-table topic to users.

---

# 2. Fixed scope of version 1.0

Version 1.0 supports:

- one teacher;
- one class;
- one student profile per Telegram account;
- private chats with the bot only;
- one enabled mathematics topic: `times_tables`;
- factors from 1 to 10;
- multiplication and exact integer division;
- button-based answers;
- scheduled daily questions;
- student and teacher statistics;
- deterministic educational content;
- simple generated educational images;
- one configured interface language.

All visible strings must be stored outside the business logic so they can be translated later.

Version 1.0 must not include a language-selection interface.

The internal platform may support registering more than one topic, but only the times-table module is enabled and visible in version 1.0.

---

# 3. Architectural modularity requirement

The mathematical content must be implemented as a module plugged into a topic-independent bot platform.

The application must be divided into two conceptual layers.

## 3.1 Core platform

The core platform handles:

- Telegram communication;
- users and roles;
- invitations;
- onboarding;
- menus;
- sessions;
- question delivery;
- button callbacks;
- answer idempotency;
- scheduling;
- daily tasks;
- generic mastery storage;
- generic statistics aggregation;
- teacher administration;
- privacy;
- deletion;
- database access;
- logging;
- deployment.

The core platform must not contain times-table formulas, factor-family logic, multiplication-specific menu labels, or multiplication-specific test composition.

## 3.2 Mathematics topic modules

A topic module handles:

- the topic’s skill catalogue;
- learning materials;
- question generation;
- answer evaluation;
- answer distractors;
- feedback;
- hints;
- topic-specific mastery interpretation;
- practice-mode definitions;
- test definitions;
- visual-question generation;
- progress presentation;
- topic-specific validation.

Version 1.0 contains one topic module:

```text
times_tables
```

The times-table module implements every multiplication- and division-specific requirement in this document.

---

# 4. Topic module contract

Every mathematics topic must implement the same core contract.

The exact Python names may vary, but the separation of responsibilities is mandatory.

## 4.1 Topic metadata

Each topic must provide:

```python
class TopicMetadata:
    topic_id: str
    version: str
    title_key: str
    short_title_key: str
    description_key: str
    icon: str
```

For version 1.0:

```text
topic_id = "times_tables"
```

Topic IDs must be stable machine-readable identifiers.

They must not be renamed after student data has been created.

## 4.2 Skill catalogue

Each topic must expose a catalogue of skills.

Conceptual interface:

```python
class SkillDefinition:
    skill_key: str
    group_key: str
    title_key: str
    description_key: str
    prerequisites: list[str]
    difficulty: int
    tags: list[str]
```

The core platform treats `skill_key` as an opaque identifier.

Only the topic module interprets its mathematical meaning.

Examples for times tables:

```text
mul:1:7
mul:6:7
div:6:7
table:7
```

The module may choose another stable format.

The format must be documented and tested.

## 4.3 Practice modes

Each topic must expose its available practice modes through data rather than hard-coded Telegram handlers.

Conceptual interface:

```python
class PracticeModeDefinition:
    mode_id: str
    title_key: str
    description_key: str
    default_question_count: int
    supports_custom_length: bool
```

The core platform renders buttons from these definitions.

For the times-table module, the practice modes are:

- quick;
- normal;
- choose table;
- multiplication;
- division;
- mixed.

## 4.4 Test definitions

Each topic must expose its test types.

Conceptual interface:

```python
class TestDefinition:
    test_id: str
    title_key: str
    question_count: int
    result_renderer_id: str
```

The topic module determines the exact question composition.

The core platform handles:

- starting the test;
- storing the session;
- delivering questions;
- withholding feedback;
- finishing;
- retrieving the result.

## 4.5 Question generation

Each topic module must generate complete question specifications.

Conceptual structure:

```python
class GeneratedQuestion:
    topic_id: str
    skill_key: str
    question_type: str
    prompt_key: str | None
    rendered_prompt: str
    media: GeneratedMedia | None
    answer_mode: str
    answer_options: list[AnswerOption]
    correct_answer: dict
    explanation_payload: dict
    metadata: dict
```

The core platform must not calculate the correct mathematical answer.

It receives a completed, validated question from the topic module.

## 4.6 Answer evaluation

Each topic must implement answer evaluation:

```python
def evaluate_answer(
    question_payload: dict,
    selected_answer: dict,
) -> EvaluationResult:
    ...
```

Conceptual result:

```python
class EvaluationResult:
    is_correct: bool
    canonical_answer: dict
    feedback_key: str
    feedback_payload: dict
    hint_key: str | None
    hint_payload: dict | None
```

The core platform records the result but does not interpret the mathematics.

## 4.7 Mastery policy

The core platform provides a generic spaced-repetition mechanism.

Each topic module must map its skills to this mechanism and may provide topic-specific rules for:

- selecting the affected skill;
- selecting related skills;
- defining prerequisites;
- determining whether a skill is mastered;
- rendering progress groups;
- deciding which skills are eligible for practice.

The generic platform stores mastery by:

```text
user + topic_id + skill_key
```

It must not require factor columns or multiplication-specific database fields.

## 4.8 Learning materials

Each topic must provide learning units.

Conceptual interface:

```python
class LearningUnit:
    unit_id: str
    title_key: str
    body_key: str
    skill_keys: list[str]
    image_renderer_id: str | None
    related_practice_mode_id: str | None
    child_unit_ids: list[str]
```

The core platform renders the unit and generic navigation buttons.

For times tables, learning units include:

- tables ×1 through ×10;
- the full table;
- related division;
- patterns;
- difficult-fact cards.

## 4.9 Progress rendering

Every topic must expose a progress-view model.

Conceptual interface:

```python
class TopicProgressView:
    headline_metrics: list[Metric]
    progress_groups: list[ProgressGroup]
    strengths: list[ProgressItem]
    current_targets: list[ProgressItem]
    suggested_action: SuggestedAction | None
```

The core platform renders this structure.

It must not assume that every topic contains numbered multiplication tables.

---

# 5. Topic registry

Create a central topic registry.

Conceptual interface:

```python
class TopicRegistry:
    def register(self, module: TopicModule) -> None: ...
    def get(self, topic_id: str) -> TopicModule: ...
    def enabled_topics(self) -> list[TopicModule]: ...
```

The registry must:

- reject duplicate topic IDs;
- validate every module at startup;
- expose enabled modules;
- fail startup if an enabled module is missing or invalid.

Version 1.0 registers and enables:

```text
times_tables
```

No Telegram handler may import the times-table module directly.

Handlers access topics through the registry.

---

# 6. Topic activation

Configuration must support:

```text
ENABLED_TOPIC_IDS=times_tables
DEFAULT_TOPIC_ID=times_tables
```

Version 1.0 has one enabled topic.

When exactly one topic is enabled:

- do not show a topic-selection screen;
- open that topic automatically;
- preserve the main menu specified in this document.

The core must nevertheless support the following future behavior:

- when multiple topics are enabled, display a generic topic-selection menu;
- save the student’s currently selected topic;
- allow daily questions and practice sessions to use the selected topic;
- show teacher statistics filtered by topic.

This future behavior may remain hidden in version 1.0, but the data model and core interfaces must not prevent it.

---

# 7. Adding or replacing a topic

A future developer must be able to add a topic by:

1. creating a new directory under `app/topics/`;
2. implementing the topic contract;
3. adding content files;
4. registering the topic;
5. adding the topic ID to configuration;
6. running topic contract tests.

Adding a topic must not require changes to:

- database tables;
- generic Telegram handlers;
- answer callback format;
- session engine;
- scheduling worker;
- invitation system;
- privacy system;
- generic administration;
- deployment configuration.

A topic may require new reusable media renderers or answer modes. Such additions must extend generic interfaces rather than insert topic-specific conditions into handlers.

## 7.1 Replacing the times-table topic

A future version must be able to run only another topic:

```text
ENABLED_TOPIC_IDS=distributive_property
DEFAULT_TOPIC_ID=distributive_property
```

The bot must then retain:

- onboarding;
- student profiles;
- reminders;
- sessions;
- teacher tools;
- privacy;
- generic statistics;
- deployment.

Times-table-specific progress remains stored under its topic ID and must not be confused with the new topic.

---

# 8. Explicit exclusions

The agent must **not** implement any of the following:

- audio files;
- voice messages;
- text-to-speech;
- speech recognition;
- microphone access;
- video;
- live calls;
- AI-generated questions at runtime;
- integration with ChatGPT or another LLM;
- a Telegram Mini App;
- a web dashboard;
- payments;
- advertisements;
- public rankings;
- student-to-student messaging;
- group-chat operation;
- public profiles;
- competitive leaderboards;
- multiple teachers;
- multiple classes;
- parent accounts as a separate role;
- custom avatars;
- an inventory, shop, virtual currency, or complex game economy;
- manually editable question content through Telegram;
- unrestricted free-text answers;
- cloud-vendor-specific infrastructure;
- unnecessary microservices;
- Redis unless a demonstrated technical requirement emerges;
- machine-learning-based performance prediction.

Version 1.0 must also not implement:

- a second mathematics topic;
- visible topic switching;
- addition, subtraction, fractions, geometry, or other topics;
- factors greater than 10;
- multiplication by zero.

Modularity is an architectural requirement, not permission to expand version-one functionality.

Do not implement “helpful extras” beyond this specification.

---

# 9. Product personality

The bot should feel like a friendly summer study companion rather than an examiner.

## 9.1 Tone

Messages must be:

- short;
- encouraging;
- concrete;
- easy to read;
- free of sarcasm;
- free of shame or pressure;
- limited to approximately two emojis per message.

Use language such as:

> ✅ Correct! 6 × 7 = 42.

> 🌱 Not quite. 6 × 7 = 42. We’ll practise it again later.

Do not use language such as:

> Incorrect response.

> You failed.

> This is easy.

> You should know this already.

## 9.2 Mistakes

A mistake must:

1. be recorded;
2. produce a short correction;
3. optionally show one concise hint;
4. cause the relevant skill to return later;
5. never subtract points or remove a reward.

## 9.3 Missed days

The bot must not guilt students for inactivity.

Do not send:

- “You lost your streak”;
- “You missed yesterday”;
- repeated reminders;
- escalating notifications.

There is only one scheduled question on an enabled day.

There is no follow-up notification if it is ignored.

---

# 10. Interface principles

## 10.1 Button-first interaction

Ordinary use must require no typing.

Use Telegram inline keyboards for:

- menu navigation;
- selecting practice modes;
- selecting tables;
- answering questions;
- starting the next question;
- changing reminder settings;
- navigating statistics;
- teacher administration.

Callback payloads must be short and opaque.

The bot must acknowledge every callback promptly so Telegram does not leave the user seeing a loading indicator.

## 10.2 Free text

When a student sends an unexpected text message, respond with:

> Please use the buttons below 🙂

Then display the main menu.

Do not attempt to interpret typed mathematical answers.

## 10.3 One task per message

During practice, show one question at a time.

Do not send worksheets containing many unanswered questions in one message.

## 10.4 Answer layout

For four-option questions, use a two-by-two inline keyboard.

Example:

> **6 × 7 = ?**

| 36 | 42 |
|---|---|
| 48 | 54 |

The order of options must be randomized.

## 10.5 Answer protection

After the first answer:

- count only the first valid click;
- immediately disable or replace the answer keyboard;
- reject later clicks as already answered;
- prevent one user from answering another user’s question;
- prevent an expired question from changing statistics.

---

# 11. Main student menu

With only the times-table topic enabled, the main menu contains exactly:

- **▶️ Practice**
- **📚 Learn tables**
- **🎯 Tests**
- **☀️ Daily task**
- **📊 My progress**
- **⚙️ Settings**

Use a reply keyboard for the persistent main menu or an inline menu that is easily restored.

The interaction must remain consistent throughout the bot.

The following commands must also exist:

- `/start`
- `/menu`
- `/practice`
- `/learn`
- `/test`
- `/progress`
- `/settings`
- `/help`
- `/privacy`
- `/delete_me`

Commands are secondary entry points.

Students should normally use buttons.

The command handlers must delegate to the active topic rather than contain times-table-specific logic.

---

# 12. Onboarding

Students must join through a teacher-generated Telegram deep link.

They must not type a class code.

Conceptual form:

```text
https://t.me/BOT_USERNAME?start=join_TOKEN
```

## 12.1 First valid start

When a new student opens a valid invite:

1. create the student profile;
2. assign the configured default topic;
3. use the Telegram first name as the display name;
4. show a short welcome message;
5. explain that answers are selected with buttons;
6. offer:
   - **Start 5 questions**
   - **Choose reminders**
   - **Open menu**

Do not require a placement test.

## 12.2 Invalid invite

An unregistered user opening the bot without a valid invitation sees:

> This bot is available to invited students only. Please ask your teacher for an invitation link.

## 12.3 Returning student

A returning student using `/start` sees the main menu.

Do not repeat onboarding.

---

# 13. Times-table learning section

The requirements in this section belong to the `times_tables` topic module, not the core application.

Selecting **📚 Learn tables** displays buttons for:

- ×1
- ×2
- ×3
- ×4
- ×5
- ×6
- ×7
- ×8
- ×9
- ×10
- Full table

## 13.1 Individual table page

Selecting a table shows:

- all ten facts for that table;
- a short pattern or tip;
- buttons:
  - **Practise this table**
  - **Show picture**
  - **Related division**
  - **Back**

Example:

> **Table of 7**
>
> 7 × 1 = 7  
> 7 × 2 = 14  
> …  
> 7 × 10 = 70
>
> 💡 Break difficult facts into ×5 and ×2.  
> For example: 7 × 8 = 7 × 5 + 7 × 3.

## 13.2 Related division

For the table of 7, show examples such as:

> 42 ÷ 7 = 6  
> 56 ÷ 7 = 8  
> 63 ÷ 7 = 9

Do not show division with remainders.

## 13.3 Full table

The full table page provides:

- a clean 10 × 10 multiplication-table image;
- a text fallback;
- buttons for selecting an individual table.

---

# 14. Times-table learning tips and mnemonics

All tips are static reviewed content.

They must not be generated dynamically by an AI service.

Include at least one tip for each table:

- **×1:** the number stays the same;
- **×2:** double the number;
- **×3:** double the number and add it once more;
- **×4:** double twice;
- **×5:** answers end in 0 or 5;
- **×6:** use ×5 and add one more group;
- **×7:** split difficult facts into ×5 and ×2;
- **×8:** double three times;
- **×9:** tens rise while units fall; the digits of products from 9 × 1 through 9 × 10 add to 9;
- **×10:** add a zero.

Include individual cards for these commonly difficult facts:

- 6 × 6 = 36
- 6 × 7 = 42
- 6 × 8 = 48
- 7 × 7 = 49
- 7 × 8 = 56
- 8 × 8 = 64

For 7 × 8 = 56, the sequence “5, 6, 7, 8” may be used as a memory cue.

Tips must remain optional and concise.

Do not show a long explanation after every answer.

---

# 15. Times-table practice modes

The topic module exposes these practice modes to the core menu renderer:

- **Quick practice — 5 questions**
- **Normal practice — 10 questions**
- **Choose a table**
- **Multiplication**
- **Division**
- **Mixed**
- **Back**

## 15.1 Quick practice

Five adaptive questions.

Target duration: approximately two to four minutes.

## 15.2 Normal practice

Ten adaptive questions.

Target duration: approximately four to eight minutes.

## 15.3 Choose a table

The student chooses ×1 through ×10.

In a table-specific session:

- approximately 70% of questions concern the selected table;
- approximately 20% revisit due weak facts;
- approximately 10% are easy confidence questions.

## 15.4 Multiplication

Only multiplication and missing-factor questions.

## 15.5 Division

Only division and missing-divisor questions.

## 15.6 Mixed

A mixture of multiplication, division, missing-number, visual, and story questions.

---

# 16. Required times-table question types

The times-table module must implement all seven types below.

## 16.1 Direct multiplication

> 7 × 8 = ?

## 16.2 Direct division

> 56 ÷ 7 = ?

## 16.3 Missing factor

> 7 × ? = 56

The missing number may appear in either factor position.

## 16.4 Missing divisor or quotient

Examples:

> 56 ÷ ? = 8

> 56 ÷ 7 = ?

## 16.5 True or false

> 9 × 6 = 56

Buttons:

- True
- False

The false equation must use a plausible nearby value.

## 16.6 Visual grouping problem

Show a generated image containing groups or an array.

Examples:

- four rows with six stars in each row;
- five groups containing three circles each;
- eight boxes represented by simple shapes, with two objects per box.

Question:

> How many stars are there altogether?

The student answers with buttons.

## 16.7 Short text problem

Examples:

> Lena has 5 packets. Each packet contains 6 stickers. How many stickers does she have?

> There are 32 children. They form teams of 4. How many teams are there?

Every story problem must:

- be one or two short sentences;
- contain only information required for the answer;
- use multiplication or exact division;
- use factors from 1 to 10;
- have four button answers;
- avoid money values, cultural assumptions, violence, dieting, and sensitive personal topics.

Provide at least:

- 15 multiplication story templates;
- 15 division story templates.

Templates may be parameterized but must produce grammatically correct output.

---

# 17. Generic answer modes

The core platform must support answer modes through registered renderers.

Version 1.0 requires:

```text
single_choice
true_false
```

The times-table module uses these modes.

A future topic may register another generic mode, such as:

```text
multiple_choice
ordered_steps
expression_choice
```

New answer modes must be added as reusable platform components.

Do not put mathematics-topic conditions into callback handlers.

---

# 18. Image design

The core platform provides a generic media-sending service.

The topic module provides media renderers.

Images must be produced without generative AI.

Use Pillow, SVG, or another deterministic drawing method.

Required times-table images:

- one full multiplication-table image;
- ten individual table images;
- dynamically generated array or grouping images;
- one simple bot identity image or mascot icon.

Visual-question images should use:

- simple geometric objects;
- high contrast;
- large objects;
- uncluttered backgrounds;
- no copyrighted characters;
- no external image downloads at runtime.

Images must remain understandable on a phone screen.

Image generation must have a text-only fallback if image sending fails.

The core media service must not assume that every image is a multiplication array.

---

# 19. Times-table distractor generation

Distractor generation belongs to the times-table module.

Four-answer questions must contain:

- exactly one correct answer;
- three unique incorrect answers;
- no negative numbers;
- no duplicate buttons;
- no value above 100;
- plausible alternatives.

Preferred distractors include:

- one neighboring multiple;
- the result of adding or subtracting one group;
- a nearby arithmetic value;
- a commonly confused product.

Example for 6 × 7 = 42:

- 36
- 42
- 48
- 49

Do not generate obviously absurd options such as 2, 97, or 100 unless they are mathematically plausible in the specific problem.

If the distractor generator cannot create three valid unique options, it must use a validated fallback pool.

It must never send a malformed question.

A future topic must provide its own distractor strategy or use a reusable generic strategy suitable for that topic.

---

# 20. Answer feedback

The core controls the interaction sequence.

The topic module supplies topic-specific feedback content.

## 20.1 Correct answer

Show:

- confirmation;
- complete equation or solution;
- current position in the session;
- **Next** button.

Example:

> ✅ Correct!  
> 6 × 7 = 42  
> Question 4 of 10

## 20.2 Incorrect answer

Show:

- calm correction;
- complete equation or solution;
- one short hint when available;
- **Next** button.

Example:

> 🌱 Not quite.  
> 6 × 7 = 42  
> Tip: 6 × 5 is 30, then add two more sixes.

## 20.3 Session ending

Show:

- correct answers out of total;
- number of skills reviewed;
- up to three skills that will return later;
- one positive sentence;
- buttons:
  - **Practise again**
  - **Main menu**

Do not display a school-style grade during ordinary practice.

The core must render these summaries from a generic session-result structure.

---

# 21. Generic adaptive learning model

Use a transparent rule-based spaced-repetition model.

Do not use machine learning.

## 21.1 Generic mastery boxes

Every student-topic-skill combination has a box from 0 through 5.

Initial value: 0.

After a correct answer:

- increase the box by 1;
- maximum 5.

After an incorrect answer:

- decrease the box by 2;
- minimum 0.

Suggested review intervals:

- box 0: later in the same session or next session;
- box 1: after approximately 10 minutes;
- box 2: after 1 day;
- box 3: after 3 days;
- box 4: after 7 days;
- box 5: after 14 days.

Exact due timestamps must be stored.

Response speed must be recorded but must not reduce mastery.

A slow correct answer is still correct.

## 21.2 Generic skill mastery

A skill is considered mastered only when:

- its box is 5;
- its last three answers were correct;
- those answers occurred on at least two separate calendar dates.

A topic module may add stricter requirements.

It may not weaken the minimum generic rule without an explicit future specification change.

## 21.3 Generic question selection

For a general adaptive session:

- 50% due or weak skills;
- 25% unseen or low-box skills;
- 15% previously mastered review skills;
- 10% easy confidence skills.

When too few skills exist in a category, redistribute the unused share among the other categories.

Generic rules:

- do not ask the identical prompt twice consecutively;
- do not repeat a skill indefinitely in one session;
- after an incorrect answer, the same skill may return once after at least two intervening questions;
- vary question form when the topic supports more than one form;
- observe topic prerequisites;
- ask only skills eligible for the selected practice mode.

The topic module defines:

- what counts as the same skill;
- what counts as a related skill;
- how prompt equivalence is determined;
- which skills are easy-confidence skills;
- which skills satisfy a practice mode.

---

# 22. Times-table mastery mapping

This section belongs only to the times-table module.

## 22.1 Fact families

Multiplication is commutative.

Store multiplication mastery using a canonical fact family:

```text
factor_low = min(a, b)
factor_high = max(a, b)
```

Therefore, 4 × 7 and 7 × 4 belong to the same multiplication fact family, although both prompt orders may be shown.

Track multiplication and division separately.

For the family 6 and 7:

- multiplication prompts may be 6 × 7 or 7 × 6;
- division prompts may be 42 ÷ 6 or 42 ÷ 7.

Stable skill keys may be:

```text
mul:6:7
div:6:7
```

## 22.2 Table progress

For each table, calculate multiplication and division progress separately.

Progress percentage:

```text
sum(box values for the ten relevant skills) / 50 × 100
```

A table is displayed as mastered when at least nine of its ten relevant skills satisfy the mastered-skill rule.

## 22.3 Times-table repetition rules

Additional rules:

- do not ask more than two prompts from the same fact family in a ten-question session;
- vary factor order;
- vary direct and missing-number forms;
- use division only when permitted by the selected mode.

## 22.4 Introducing division

In mixed practice, prefer division skills whose related multiplication skill has reached at least box 2.

The dedicated division mode may include all division skills regardless of multiplication mastery.

---

# 23. Tests

The core platform handles generic test sessions.

The times-table module supplies the following test definitions:

- **Test one table**
- **Division test**
- **Mixed test**
- **Back**

Tests differ from practice:

- no hints during the test;
- do not reveal whether an answer is correct until the end;
- answer buttons are still used;
- results are stored;
- test answers also update mastery;
- tests can be abandoned through a confirmation button.

## 23.1 One-table test

- student selects a table;
- exactly ten multiplication questions;
- one question for each multiplier from 1 through 10;
- randomized order;
- no repeated fact.

## 23.2 Division test

- exactly ten direct division questions;
- factors from 1 through 10;
- balanced selection;
- no remainder;
- no duplicate prompt.

## 23.3 Mixed test

Exactly twenty questions:

- 10 direct multiplication;
- 5 direct division;
- 3 missing-number questions;
- 1 visual question;
- 1 story problem.

It must cover at least eight different tables.

## 23.4 Test result

Show:

- score;
- percentage;
- multiplication accuracy;
- division accuracy where applicable;
- up to three strong areas;
- up to three skills to practise;
- **Practise weak skills** button;
- **Main menu** button.

Do not use labels such as “fail,” “bad,” or “poor.”

The core result screen must consume a generic topic result object.

---

# 24. Daily task and notifications

The daily task is one question, not an entire practice session.

Example:

> ☀️ Today’s tiny challenge:
>
> 7 × 6 = ?

The answer buttons are attached directly to the notification.

After answering, show:

- feedback;
- **One more**
- **Practise for 5 questions**
- **Done for today**

## 24.1 Schedule choices

Students and the teacher can configure reminders entirely through buttons.

Frequency options:

- Every day
- Weekdays
- Monday, Wednesday, Friday
- Off

Time options:

- every whole hour from 07:00 through 20:00;
- shown through paginated buttons if necessary.

Version 1.0 uses one class timezone configured by the teacher.

Per-student timezones are out of scope.

## 24.2 Precedence

Each student has an individual setting.

- New students inherit the teacher’s current default.
- Students may change their own setting.
- The teacher may change an individual student’s setting.
- The teacher may apply the default to all students after confirmation.
- There is no permanent teacher lock; a student may later change the setting again.

## 24.3 Topic selection for daily questions

Version 1.0 always uses:

```text
times_tables
```

The database must nevertheless store the daily question’s `topic_id`.

In a future multi-topic version, daily-task selection may use:

- the student’s selected topic;
- a teacher-assigned topic;
- a configured rotation.

This future policy is not implemented in version 1.0.

## 24.4 Scheduling behavior

The scheduling system must:

- evaluate due reminders at least once per minute;
- send no more than one scheduled task per student per local calendar date;
- survive application restarts;
- avoid duplicates after failures or restarts;
- store whether delivery succeeded;
- skip students who blocked the bot;
- disable future delivery after repeated permanent Telegram delivery failures;
- never send a second reminder because the first question was ignored.

The daily question should select:

1. the highest-priority due weak skill;
2. otherwise, a low-mastery skill;
3. otherwise, a mastered review skill.

The topic module generates the actual question.

---

# 25. Student progress screen

Selecting **📊 My progress** displays:

- questions answered in total;
- questions answered in the last seven days;
- accuracy in the last seven days;
- active practice days in the last seven days;
- topic-specific progress;
- three strongest skills or groups;
- up to three skills currently being learned.

For the times-table module, topic-specific progress contains:

- multiplication progress;
- division progress;
- progress by table.

Do not present a public rank.

Suggested times-table display:

> ×2: ██████████ 100%  
> ×5: ████████░░ 80%  
> ×7: ████░░░░░░ 40%

Telegram-safe Unicode blocks may be used, but the result must remain readable without monospace alignment.

The times-table module exposes these detail actions:

- **Multiplication details**
- **Division details**
- **Practise weak facts**
- **Back**

A future topic supplies its own topic-specific detail actions through the generic progress interface.

---

# 26. Teacher administration

Only the Telegram user ID configured as `ADMIN_TELEGRAM_ID` may access `/admin`.

The admin menu contains exactly:

- **Students**
- **Group progress**
- **Reminder defaults**
- **Invite link**
- **Back**

## 26.1 Students

Show a paginated student list, eight students per page.

For each student, show:

- display name;
- last active date;
- seven-day accuracy;
- total questions;
- reminder status.

Selecting a student shows:

- progress for the active topic;
- difficult skills;
- recent test results;
- reminder setting;
- buttons:
  - **Change reminder**
  - **Back**

For version 1.0, progress means:

- multiplication progress by table;
- division progress by table;
- difficult multiplication and division facts.

Do not implement teacher editing of scores or mastery.

## 26.2 Group progress

Show:

- total active students;
- students active during the last seven days;
- questions answered during the last seven days;
- group accuracy during the last seven days;
- most commonly difficult five skills or skill groups;
- number of enabled reminders.

For version 1.0, difficult skills are times-table fact families.

Do not sort or describe students as winners and losers.

## 26.3 Reminder defaults

The teacher can set:

- default frequency;
- default hour;
- class timezone through configuration, not conversational text entry;
- whether to apply the current default to all students.

Applying settings to all students must require a confirmation button.

## 26.4 Invite link

The teacher can:

- display the current invitation link;
- invalidate the current token;
- generate a new token.

Old invalidated links must immediately stop admitting new students.

Existing students remain registered.

---

# 27. Privacy and data handling

Store only data necessary to operate the bot:

- Telegram user ID;
- Telegram chat ID;
- Telegram first name;
- optional Telegram username;
- role;
- selected topic;
- settings;
- question history;
- answer correctness;
- response time;
- mastery state;
- activity timestamps.

Do not collect:

- date of birth;
- home address;
- phone number;
- school name;
- email address;
- legal name;
- location;
- contacts;
- photographs;
- audio;
- arbitrary chat history.

## 27.1 Private chats only

If the bot is added to a group, respond only with a short instruction that it works in private chat.

Do not process group messages or create student records from groups.

## 27.2 Privacy command

`/privacy` explains:

- what is stored;
- why it is stored;
- that the teacher can view learning statistics;
- how to request deletion.

## 27.3 Data deletion

`/delete_me` must:

1. explain that progress will be permanently deleted;
2. require explicit button confirmation;
3. delete or anonymize all student-linked learning data across every topic;
4. preserve only non-identifying aggregate values if technically needed;
5. remove the user’s access until they rejoin through a valid invitation.

## 27.4 Logging

Application logs must not include:

- bot tokens;
- full callback payload contents when they contain identifiers;
- database URLs with passwords;
- unnecessary student names;
- complete Telegram update objects.

Use internal user IDs in operational logs wherever possible.

---

# 28. Technical architecture

## 28.1 Required stack

Use:

- Python 3.12;
- aiogram 3.x;
- PostgreSQL;
- SQLAlchemy 2.x async ORM;
- Alembic migrations;
- Pydantic Settings;
- Pillow or SVG generation for images;
- pytest;
- pytest-asyncio;
- Ruff;
- mypy;
- Docker;
- Docker Compose.

Pin exact dependency versions in the lockfile.

## 28.2 Telegram update mode

Use long polling for version 1.0.

Do not implement both polling and webhook modes.

## 28.3 Processes

Use:

- one bot application process;
- one PostgreSQL database.

The bot process runs:

- Telegram polling;
- a background daily-delivery loop;
- startup validation.

Do not split the application into microservices.

## 28.4 Restart safety

Do not store active learning state only in process memory.

The following must survive restart:

- current topic;
- current session;
- already answered questions;
- student settings;
- mastery state;
- daily-delivery status;
- invite-token validity.

FSM storage may be used for temporary navigation, but authoritative state belongs in PostgreSQL.

---

# 29. Required module boundaries

The following boundaries are mandatory.

## 29.1 Telegram handlers

Handlers may:

- identify the user;
- load the active topic through the registry;
- call platform services;
- render returned view models;
- acknowledge callbacks.

Handlers must not:

- multiply or divide numbers;
- generate distractors;
- decide what a skill means;
- calculate topic mastery;
- hard-code test composition;
- import `app.topics.times_tables` directly.

## 29.2 Session engine

The session engine may:

- create and resume sessions;
- request a session blueprint from a topic;
- store question order;
- track answered count;
- complete or abandon a session.

It must not:

- know what a multiplication table is;
- assume every session uses numerical answers;
- assume every topic has the same practice modes.

## 29.3 Mastery engine

The mastery engine handles:

- boxes;
- due times;
- answer history;
- generic selection categories;
- generic mastered-skill minimums.

The topic adapter handles:

- skill identity;
- prerequisites;
- related skills;
- topic-specific group progress;
- topic-specific eligibility.

## 29.4 Statistics service

The generic statistics service calculates:

- total attempts;
- accuracy;
- recent activity;
- session counts;
- test counts;
- per-skill aggregates;
- per-topic aggregates.

The topic module transforms these aggregates into:

- table progress;
- named strengths;
- difficult facts;
- topic-specific progress groups.

## 29.5 Content

Core interface strings belong under:

```text
app/content/core/
```

Topic strings and educational content belong under:

```text
app/topics/<topic_id>/content/
```

Do not place multiplication tips in global content files.

---

# 30. Suggested project structure

```text
math-practice-bot/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── logging.py
│   ├── bot.py
│   │
│   ├── core/
│   │   ├── topics/
│   │   │   ├── contracts.py
│   │   │   ├── registry.py
│   │   │   ├── validation.py
│   │   │   └── view_models.py
│   │   │
│   │   ├── sessions/
│   │   │   ├── engine.py
│   │   │   ├── models.py
│   │   │   └── results.py
│   │   │
│   │   ├── mastery/
│   │   │   ├── engine.py
│   │   │   ├── intervals.py
│   │   │   └── selection.py
│   │   │
│   │   ├── questions/
│   │   │   ├── models.py
│   │   │   ├── answer_modes.py
│   │   │   └── callbacks.py
│   │   │
│   │   ├── statistics/
│   │   │   ├── aggregates.py
│   │   │   └── service.py
│   │   │
│   │   └── media/
│   │       ├── models.py
│   │       └── service.py
│   │
│   ├── topics/
│   │   └── times_tables/
│   │       ├── __init__.py
│   │       ├── module.py
│   │       ├── metadata.py
│   │       ├── skills.py
│   │       ├── learning.py
│   │       ├── practice_modes.py
│   │       ├── test_definitions.py
│   │       ├── question_generator.py
│   │       ├── question_types.py
│   │       ├── evaluator.py
│   │       ├── distractors.py
│   │       ├── mastery_adapter.py
│   │       ├── progress_renderer.py
│   │       ├── images.py
│   │       ├── validators.py
│   │       ├── content/
│   │       │   ├── strings.yaml
│   │       │   ├── tips.yaml
│   │       │   ├── hard_facts.yaml
│   │       │   └── story_templates.yaml
│   │       └── assets/
│   │           └── mascot.png
│   │
│   ├── handlers/
│   │   ├── start.py
│   │   ├── menu.py
│   │   ├── practice.py
│   │   ├── learning.py
│   │   ├── tests.py
│   │   ├── progress.py
│   │   ├── settings.py
│   │   ├── privacy.py
│   │   └── admin.py
│   │
│   ├── keyboards/
│   │   ├── common.py
│   │   ├── questions.py
│   │   ├── settings.py
│   │   └── admin.py
│   │
│   ├── services/
│   │   ├── users.py
│   │   ├── sessions.py
│   │   ├── answers.py
│   │   ├── reminders.py
│   │   ├── invitations.py
│   │   └── privacy.py
│   │
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── models.py
│   │   └── repositories/
│   │
│   ├── content/
│   │   └── core/
│   │       └── strings.yaml
│   │
│   └── workers/
│       └── daily_questions.py
│
├── migrations/
├── scripts/
│   ├── validate_topics.py
│   ├── validate_content.py
│   └── generate_times_table_images.py
├── tests/
│   ├── contracts/
│   ├── unit/
│   │   ├── core/
│   │   └── topics/
│   │       └── times_tables/
│   ├── integration/
│   └── fixtures/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
├── README.md
├── SPEC.md
├── TOPIC_DEVELOPMENT_GUIDE.md
└── ACCEPTANCE_CHECKLIST.md
```

The exact division into files may vary.

The separation between core platform and topic modules may not be removed.

---

# 31. Generic database model

Use UTC timestamps internally.

## 31.1 `users`

Fields:

- `id`
- `telegram_user_id`, unique
- `telegram_chat_id`
- `role`: `student` or `admin`
- `display_name`
- `telegram_username`, nullable
- `selected_topic_id`
- `is_active`
- `created_at`
- `last_seen_at`
- `delivery_failure_count`

## 31.2 `student_settings`

Fields:

- `user_id`, unique foreign key
- `reminders_enabled`
- `days_mask`
- `local_hour`
- `timezone`
- `updated_at`
- `updated_by_user_id`

## 31.3 `class_settings`

One active row containing:

- `timezone`
- `default_topic_id`
- `default_reminders_enabled`
- `default_days_mask`
- `default_local_hour`
- `updated_at`

## 31.4 `invite_tokens`

Fields:

- `id`
- `token_hash`
- `is_active`
- `created_at`
- `invalidated_at`
- `created_by_user_id`

Store a hash rather than the raw token where practical.

## 31.5 `skill_mastery`

Fields:

- `id`
- `user_id`
- `topic_id`
- `skill_key`
- `box`
- `due_at`
- `attempt_count`
- `correct_count`
- `consecutive_correct`
- `last_answered_at`
- `last_correct_at`
- `topic_state`, JSONB, default empty object

Unique constraint:

```text
user_id + topic_id + skill_key
```

`topic_state` may store a small amount of topic-specific mastery metadata.

Do not use it to duplicate general fields or store arbitrary unbounded data.

## 31.6 `practice_sessions`

Fields:

- `id`
- `user_id`
- `topic_id`
- `mode_id`
- `session_kind`: practice or test
- `status`: active, completed, abandoned, expired
- `configuration`, JSONB
- `planned_question_count`
- `answered_count`
- `correct_count`
- `started_at`
- `completed_at`

A student may have only one active ordinary session per topic at a time.

Version 1.0 may restrict the student to one active session overall for simplicity.

## 31.7 `questions`

Fields:

- `id`
- `public_id`, short unique opaque identifier
- `session_id`, nullable for independent daily questions
- `user_id`
- `topic_id`
- `skill_key`
- `position`
- `question_type`
- `answer_mode`
- `prompt_payload`, JSONB
- `media_payload`, JSONB, nullable
- `options`, JSONB
- `correct_answer`, JSONB
- `evaluation_payload`, JSONB
- `status`
- `created_at`
- `expires_at`

Do not add multiplication-specific columns such as:

- `factor_a`;
- `factor_b`;
- `operation`;
- `product`.

Such information belongs inside the times-table module’s validated payload.

## 31.8 `attempts`

Fields:

- `id`
- `question_id`
- `user_id`
- `topic_id`
- `skill_key`
- `selected_answer`, JSONB
- `is_correct`
- `response_time_ms`
- `source`: practice, test, daily
- `created_at`

Unique constraint:

```text
question_id + user_id
```

This enforces one counted answer.

## 31.9 `daily_deliveries`

Fields:

- `id`
- `user_id`
- `topic_id`
- `local_date`
- `question_id`
- `status`: pending, sent, answered, failed, skipped
- `sent_at`
- `answered_at`
- `error_code`, nullable

Unique constraint:

```text
user_id + local_date
```

Version 1.0 sends at most one daily question across all topics.

If a future version allows one daily question per topic, that requires an explicit migration and specification change.

---

# 32. Callback design

Use opaque callback formats such as:

```text
a:q7F3:2
m:practice
p:next:q7F3
s:time:17
```

Do not place the complete equation, correct answer, Telegram user ID, topic payload, or JSON object in callback data.

For an answer callback:

1. acknowledge the callback immediately;
2. load the question by public ID;
3. validate ownership;
4. validate expiration;
5. obtain the module from `question.topic_id`;
6. ask the module to evaluate the selected answer;
7. attempt an atomic insert into `attempts`;
8. treat unique-constraint failure as already answered;
9. update question status;
10. update generic mastery using the module’s mastery adapter;
11. update session statistics;
12. replace the keyboard with feedback controls.

Database writes associated with one answer must occur in one transaction.

---

# 33. Daily-delivery worker

Implement a background loop that runs approximately once per minute.

For each iteration:

1. calculate the current local time for the configured class timezone;
2. find students whose enabled schedule matches the local date and hour;
3. exclude students with an existing `daily_deliveries` row for that date;
4. resolve the student’s topic;
5. obtain that topic through the registry;
6. ask the topic for a daily-question skill and generated question;
7. create the daily-delivery row and question transactionally;
8. send the question;
9. mark it sent;
10. record failure safely if Telegram rejects delivery.

Use locking or uniqueness constraints so two overlapping iterations cannot send duplicates.

Do not depend on an in-memory scheduler job for each student.

---

# 34. Error handling

The bot must handle:

- database temporarily unavailable;
- Telegram timeout;
- Telegram rate limiting;
- student blocking the bot;
- invalid or stale callback;
- already answered question;
- expired session;
- missing image asset;
- malformed core content;
- malformed topic content;
- missing topic module;
- disabled topic containing existing student data;
- restart during an active session.

User-facing errors must be brief:

> Something went wrong. Your progress is safe. Please try again from the menu.

Do not expose stack traces or internal identifiers.

Retry transient Telegram errors with bounded exponential backoff.

Do not retry permanent errors indefinitely.

If a configured topic cannot be loaded or validated, the application must refuse to start.

---

# 35. Configuration

Provide `.env.example` containing at least:

```text
BOT_TOKEN=
BOT_USERNAME=
ADMIN_TELEGRAM_ID=
DATABASE_URL=postgresql+asyncpg://...
DEFAULT_TIMEZONE=Europe/Zurich
DEFAULT_REMINDER_HOUR=17
DEFAULT_REMINDER_DAYS=DAILY
ENABLED_TOPIC_IDS=times_tables
DEFAULT_TOPIC_ID=times_tables
APP_ENV=development
LOG_LEVEL=INFO
```

Validate all required settings at startup.

The application must refuse to start with:

- missing bot token;
- invalid admin ID;
- invalid timezone;
- unreachable or unmigrated database;
- missing enabled topic;
- invalid default topic;
- default topic not included among enabled topics;
- invalid core content;
- invalid topic content.

Do not silently invent production defaults for secrets or identifiers.

---

# 36. Content validation

Create:

```text
scripts/validate_content.py
scripts/validate_topics.py
```

## 36.1 Core validation

Verify:

- every visible core string key used by handlers exists;
- every answer mode referenced by a topic is registered;
- every enabled topic is registered;
- every topic implements the required contract;
- every topic ID is unique;
- every practice-mode ID is unique within its topic;
- every test ID is unique within its topic;
- every skill key is unique within its topic;
- every referenced prerequisite exists;
- every referenced renderer exists;
- no audio-related feature or text is present.

## 36.2 Times-table validation

Verify:

- tips exist for all tables 1–10;
- hard-fact cards exist for all required facts;
- at least 15 multiplication story templates exist;
- at least 15 division story templates exist;
- all templates render with representative values;
- every rendered answer is an integer from 1 through 100;
- all questions can generate three unique distractors;
- table images can be generated successfully;
- all required practice modes exist;
- all required test definitions exist;
- all times-table skills have stable unique keys.

Run validation:

- in tests;
- during application startup;
- before declaring completion.

---

# 37. Topic contract tests

Create a generic test suite that can be run against every topic module.

Every module must pass tests for:

- valid metadata;
- unique topic ID;
- nonempty skill catalogue;
- unique skill keys;
- valid prerequisite references;
- valid practice modes;
- valid test definitions;
- successful learning-unit rendering;
- successful practice-question generation;
- successful test-question generation;
- valid answer modes;
- exactly one correct answer where required;
- successful answer evaluation;
- mastery-skill resolution;
- progress-view generation;
- deterministic behavior when provided with a fixed random seed;
- serialization of all question payloads;
- no unbounded or unserializable topic state.

The contract tests must make adding another topic straightforward.

Document how to run them against a newly created topic.

---

# 38. Testing requirements

## 38.1 Core unit tests

Core unit tests must cover:

- topic registration;
- duplicate-topic rejection;
- missing-topic handling;
- enabled-topic validation;
- default-topic validation;
- generic mastery increases and decreases;
- due-date interval calculation;
- generic mastered-skill rules;
- generic adaptive selection percentages within reasonable statistical tolerance;
- no immediate duplicate prompts;
- reminder day matching;
- timezone calculations;
- daily duplicate prevention;
- callback ownership;
- callback expiration;
- answer idempotency;
- generic statistics calculations;
- cross-topic data isolation;
- deletion across all topics;
- serialization of question payloads.

## 38.2 Times-table unit tests

Times-table tests must cover:

- all multiplication results for factors 1–10;
- all corresponding exact division results;
- canonical fact-family creation;
- stable skill-key creation;
- distractor uniqueness;
- distractor range;
- question generation for every required question type;
- story-template rendering;
- table-progress calculation;
- times-table adaptive eligibility;
- division introduction rules;
- table-test blueprint;
- division-test blueprint;
- mixed-test blueprint;
- progress-view generation.

## 38.3 Integration tests

Use a temporary PostgreSQL database and mocked Telegram Bot API.

Integration tests must verify:

- valid invitation onboarding;
- invalid invitation rejection;
- assignment of the default topic;
- five-question session completion;
- incorrect-answer feedback;
- session recovery after restart;
- test completion and result generation;
- reminder-setting changes;
- daily-question delivery;
- no duplicate daily question;
- teacher access;
- non-teacher admin rejection;
- student deletion;
- database migrations from an empty database;
- topic resolution through the registry;
- no direct dependency from handlers to times-table implementation.

## 38.4 Modularity test

Add an intentionally minimal test-only topic module, for example:

```text
sample_topic
```

This module exists only in tests.

It should contain:

- two test skills;
- one practice mode;
- one test definition;
- one simple single-choice question;
- one progress group.

The complete generic flow must work with this module:

1. register the module;
2. create a student session;
3. generate a question;
4. submit an answer;
5. update mastery;
6. produce progress;
7. create a daily question.

This proves that the core is not secretly dependent on times-table logic.

The test-only topic must not be enabled in production.

## 38.5 Code quality

The following commands must pass:

```bash
ruff check .
ruff format --check .
mypy app
pytest
python scripts/validate_topics.py
python scripts/validate_content.py
```

Minimum coverage:

- 85% for `app/core`, `app/services`, and topic domain logic;
- 75% overall.

Coverage must not be increased by excluding important modules without justification.

---

# 39. Topic development guide

Provide `TOPIC_DEVELOPMENT_GUIDE.md`.

It must explain:

- the topic contract;
- required metadata;
- skill-key design;
- learning-unit design;
- practice-mode definitions;
- test definitions;
- question payloads;
- answer evaluation;
- mastery integration;
- progress rendering;
- media generation;
- content validation;
- contract tests;
- registration;
- configuration;
- data migration expectations.

It must include a small example topic.

It must explicitly explain how to create a future distributive-property module without modifying Telegram handlers.

Example future skill keys might be:

```text
distributive:expand:a_times_b_plus_c
distributive:factor:common_factor
distributive:equivalent_expression
```

These examples are documentation only.

Do not implement the future topic in version 1.0.

---

# 40. Deployment and documentation

Provide:

- production-ready Dockerfile;
- Docker Compose setup for bot and PostgreSQL;
- persistent PostgreSQL volume;
- migration instructions;
- startup command;
- graceful shutdown;
- `.env.example`;
- README;
- backup and restore instructions;
- teacher setup instructions;
- BotFather setup instructions;
- instructions for obtaining the teacher’s Telegram ID;
- instructions for generating the first invitation link;
- topic-development guide.

Required local startup flow:

```bash
cp .env.example .env
# Fill in required values
docker compose up --build
```

The README must explain how to run migrations before normal startup.

Do not require a public domain, TLS certificate, or webhook endpoint.

---

# 41. Instructions to the AI coding agent

You are implementing the modular mathematics-practice Telegram bot described in this specification.

Version 1.0 is a times-table bot.

The modular architecture is mandatory, but additional mathematics topics are not part of version 1.0.

## 41.1 General operating rules

1. Treat this document as the authoritative scope.
2. Implement all required version-one behavior.
3. Do not add excluded features.
4. Keep the visible product focused on times tables.
5. Implement mathematical functionality through the topic contract.
6. Do not put multiplication-specific logic into the core.
7. When something is ambiguous, choose the simplest implementation consistent with the specification.
8. Do not replace required functionality with placeholders.
9. Do not leave production-path `TODO` comments.
10. Do not claim completion while tests, migrations, assets, content, documentation, or contract validation are missing.
11. Do not introduce runtime AI services.
12. Do not introduce audio functionality.
13. Store authoritative user and session state in PostgreSQL.
14. Use atomic database operations for answers and deliveries.
15. Maintain an implementation checklist mapped to the acceptance criteria.
16. Run the full quality suite before declaring completion.
17. Do not implement a general educational framework beyond the interfaces required here.
18. Do not implement a second production topic merely to demonstrate modularity.
19. Use the test-only sample topic to prove modularity.
20. Ensure the times-table module can be removed from configuration without breaking imports in the core.

## 41.2 Forbidden shortcuts

The agent must not:

- create a `topic_id` column while leaving all formulas in handlers;
- rename times-table classes to generic names without making them generic;
- store factors in generic database columns;
- use large `if topic_id == "times_tables"` blocks in core services;
- place multiplication-specific test logic in the generic test engine;
- make progress rendering assume tables ×1 through ×10;
- make the scheduling worker call a times-table generator directly;
- make callback handlers calculate the correct answer;
- claim modularity only because files are in separate folders.

## 41.3 Acceptable topic-specific dependencies

Code inside:

```text
app/topics/times_tables/
```

may contain:

- multiplication;
- division;
- factor families;
- tables;
- times-table tips;
- times-table images;
- times-table test composition.

Core code may know only:

- topic IDs;
- skill keys;
- topic contracts;
- generic question structures;
- generic session structures;
- generic mastery records.

## 41.4 Implementation order

Implement in this order.

### Phase 1: Foundation

- project structure;
- dependency configuration;
- settings;
- logging;
- PostgreSQL;
- generic SQLAlchemy models;
- Alembic;
- Docker;
- basic bot startup.

### Phase 2: Topic framework

- topic contracts;
- topic registry;
- topic validation;
- generic question models;
- generic answer modes;
- generic session engine;
- generic mastery engine;
- generic progress view models;
- test-only sample topic;
- topic contract tests.

Do not begin the production times-table module until the sample topic can complete a generic session in tests.

### Phase 3: Times-table domain

- skill catalogue;
- fact-family model;
- multiplication and division generation;
- distractors;
- required question types;
- content files;
- mastery adapter;
- progress renderer;
- test definitions;
- times-table unit tests.

### Phase 4: Student experience

- invitations;
- onboarding;
- main menu;
- learning tables;
- practice sessions;
- answer processing;
- feedback;
- progress screens.

Handlers must use the topic registry.

### Phase 5: Tests and images

- table test;
- division test;
- mixed test;
- table images;
- visual problems;
- image fallbacks.

### Phase 6: Scheduling

- reminder settings;
- daily-delivery worker;
- topic-based daily-question generation;
- duplicate protection;
- delivery failures;
- restart tests.

### Phase 7: Teacher administration

- admin authorization;
- student list;
- individual statistics;
- group statistics;
- reminder defaults;
- invite rotation.

### Phase 8: Privacy and completion

- `/privacy`;
- `/delete_me`;
- logging review;
- documentation;
- topic-development guide;
- content validation;
- modularity validation;
- full acceptance run.

## 41.5 Progress files

Maintain:

- `SPEC.md`: this specification;
- `ACCEPTANCE_CHECKLIST.md`: every criterion with pass/fail status;
- `IMPLEMENTATION_NOTES.md`: important technical decisions only;
- `TOPIC_DEVELOPMENT_GUIDE.md`: instructions for adding another topic.

Do not use implementation notes to change product scope.

## 41.6 Final delivery report

The coding agent’s final response must include:

- what was implemented;
- how core and topic code are separated;
- how to add a future topic;
- exact startup commands;
- migration command;
- test commands;
- actual test results;
- actual coverage results;
- topic-validation result;
- content-validation result;
- list of environment variables;
- any acceptance criterion that did not pass.

The agent must not describe the project as complete if any mandatory criterion failed.

---

# 42. Definition of done

The project is complete only when **every mandatory criterion below passes**.

## A. Version-one scope

- [ ] Factors 1 through 10 are supported.
- [ ] Multiplication by zero is not included.
- [ ] Exact related division is supported.
- [ ] The bot supports one teacher and one class.
- [ ] The bot works in private chats.
- [ ] Only the times-table topic is enabled in production.
- [ ] No audio-related functionality or dependency exists.
- [ ] No runtime AI service exists.
- [ ] No web dashboard or Mini App exists.
- [ ] No leaderboard exists.
- [ ] No additional mathematics topic is visible.

## B. Modular architecture

- [ ] A documented topic contract exists.
- [ ] A topic registry exists.
- [ ] Enabled topics are loaded through configuration.
- [ ] The default topic is loaded through configuration.
- [ ] Telegram handlers do not import the times-table module directly.
- [ ] The session engine contains no multiplication-specific logic.
- [ ] The generic mastery engine contains no factor-specific fields.
- [ ] The generic database schema stores `topic_id` and `skill_key`.
- [ ] Questions use generic JSON payloads rather than multiplication columns.
- [ ] Progress rendering uses a generic topic view model.
- [ ] Test composition is supplied by the topic module.
- [ ] Daily questions are generated through the topic module.
- [ ] Topic validation runs at startup.
- [ ] A test-only sample topic completes the generic learning flow.
- [ ] The sample topic requires no changes to core handlers.
- [ ] `TOPIC_DEVELOPMENT_GUIDE.md` explains how to add a topic.
- [ ] Removing `times_tables` from enabled configuration does not produce a core import error.
- [ ] A future topic can be added without a database migration, assuming it fits existing generic answer modes and payload limits.

## C. Onboarding and access

- [ ] A valid deep-link invitation creates a student.
- [ ] The configured default topic is assigned.
- [ ] No class-code typing is required.
- [ ] An invalid invitation does not create a student.
- [ ] Returning students retain their progress.
- [ ] Unauthorized users cannot access teacher functions.
- [ ] Group messages do not create learning records.

## D. Learning content

- [ ] All ten multiplication tables are viewable as text.
- [ ] A full multiplication-table image exists.
- [ ] Ten individual table images exist.
- [ ] Every table has at least one reviewed tip.
- [ ] All required hard-fact cards exist.
- [ ] Related division examples are available.
- [ ] Image failure produces a usable text fallback.
- [ ] Learning units are supplied by the times-table topic module.

## E. Practice

- [ ] Five-question practice works.
- [ ] Ten-question practice works.
- [ ] Table-specific practice works.
- [ ] Multiplication-only practice works.
- [ ] Division-only practice works.
- [ ] Mixed practice works.
- [ ] Every required question type appears.
- [ ] Each ordinary answer is selected through buttons.
- [ ] Every four-option question has one correct answer.
- [ ] Incorrect options are unique and plausible.
- [ ] The first answer is counted exactly once.
- [ ] Old buttons cannot change the result.
- [ ] One student cannot answer another student’s question.
- [ ] Incorrect answers receive calm corrective feedback.
- [ ] A session can be recovered after application restart.
- [ ] The session summary is displayed.
- [ ] Practice modes are returned by the topic module rather than hard-coded in the generic session engine.

## F. Adaptive behavior

- [ ] Generic mastery is stored by user, topic, and skill.
- [ ] Multiplication fact families are canonicalized inside the times-table module.
- [ ] Multiplication and division mastery are tracked separately.
- [ ] Correct answers increase the mastery box.
- [ ] Incorrect answers reduce the mastery box.
- [ ] Review due dates are stored.
- [ ] Weak and due skills receive greater selection priority.
- [ ] Mastered skills still return for review.
- [ ] The same prompt is not repeated consecutively.
- [ ] Incorrect skills may return later without looping indefinitely.
- [ ] Response times are recorded without punishing slow correct answers.
- [ ] Topic-specific prerequisites and eligibility are resolved through the topic adapter.

## G. Tests

- [ ] One-table test contains exactly ten balanced questions.
- [ ] Division test contains exactly ten questions.
- [ ] Mixed test contains exactly twenty questions with the required composition.
- [ ] Test feedback is withheld until completion.
- [ ] Test results include useful strengths and practice targets.
- [ ] Test answers update statistics and mastery.
- [ ] Test definitions come from the times-table module.

## H. Daily tasks

- [ ] Students can enable or disable reminders with buttons.
- [ ] Students can select each required frequency.
- [ ] Students can choose an hour from 07:00 through 20:00.
- [ ] The teacher can set defaults.
- [ ] The teacher can change one student’s schedule.
- [ ] The teacher can apply defaults to all after confirmation.
- [ ] Exactly one scheduled question is sent per enabled local day.
- [ ] Ignoring the question produces no second reminder.
- [ ] Restarting the application does not duplicate delivery.
- [ ] A daily answer is counted only once.
- [ ] Blocked users do not crash the worker.
- [ ] The worker resolves question generation through the topic registry.

## I. Statistics

- [ ] Students can see total activity.
- [ ] Students can see seven-day activity and accuracy.
- [ ] Students can see times-table multiplication progress.
- [ ] Students can see times-table division progress.
- [ ] Students can see facts needing practice.
- [ ] The teacher can see all registered students.
- [ ] The teacher can inspect individual progress.
- [ ] The teacher can see group-level statistics.
- [ ] No public ranking is shown.
- [ ] Core statistics remain generic.
- [ ] Times-table grouping and labels are produced by the times-table progress renderer.

## J. Privacy

- [ ] The bot stores only specified data.
- [ ] `/privacy` accurately explains stored data.
- [ ] `/delete_me` requires confirmation.
- [ ] Confirmed deletion removes student-linked progress across all topics.
- [ ] Logs contain no token or database password.
- [ ] Logs do not dump complete Telegram updates.
- [ ] The bot does not request age, phone number, address, or school.

## K. Reliability

- [ ] An empty database can be migrated successfully.
- [ ] Database uniqueness prevents duplicate answers.
- [ ] Database uniqueness prevents duplicate daily deliveries.
- [ ] Temporary Telegram failures are handled.
- [ ] Permanent Telegram failures do not retry forever.
- [ ] Missing or invalid core content causes a clear startup failure.
- [ ] Missing or invalid topic content causes a clear startup failure.
- [ ] Missing enabled topics cause a clear startup failure.
- [ ] Graceful shutdown works.
- [ ] Restart does not erase active sessions or progress.
- [ ] Topic-specific payloads survive database serialization and restart.

## L. Quality and delivery

- [ ] `ruff check .` passes.
- [ ] `ruff format --check .` passes.
- [ ] `mypy app` passes.
- [ ] `pytest` passes.
- [ ] Topic contract tests pass.
- [ ] The sample-topic integration test passes.
- [ ] Core, services, and topic-domain coverage is at least 85%.
- [ ] Overall coverage is at least 75%.
- [ ] Topic validation passes.
- [ ] Content validation passes.
- [ ] Docker image builds.
- [ ] Docker Compose starts the bot and database.
- [ ] README setup instructions work from a clean checkout.
- [ ] `.env.example` contains every required variable.
- [ ] `TOPIC_DEVELOPMENT_GUIDE.md` exists and is usable.
- [ ] No production-path placeholder or unfinished `TODO` remains.
- [ ] Every item in this definition of done is marked with evidence in `ACCEPTANCE_CHECKLIST.md`.

---

# 43. Modularity acceptance scenario

Before delivery, perform this automated or controlled integration scenario using the test-only sample topic:

1. register `sample_topic`;
2. enable it in the test configuration;
3. create a test student assigned to `sample_topic`;
4. load the main practice action through a generic handler;
5. retrieve the sample topic’s practice modes;
6. start a session;
7. generate a question;
8. answer through the normal callback path;
9. evaluate through the sample topic;
10. update generic mastery;
11. complete the session;
12. render generic progress using the sample topic’s view model;
13. generate a daily question through the normal worker;
14. confirm no times-table class or function was imported by the generic path.

The modularity requirement fails if this scenario requires editing production core code.

---

# 44. Final product acceptance scenario

Before delivery, perform this manual scenario from a clean database:

1. Start PostgreSQL and the bot through Docker Compose.
2. Run all migrations.
3. Verify that `times_tables` is loaded through the topic registry.
4. Open the bot as the configured teacher.
5. Generate an invitation link.
6. Join as a new student through that link.
7. Confirm that the student is assigned to `times_tables`.
8. Complete a five-question practice session containing at least one mistake.
9. Verify that the mistake returns later.
10. Open one table and its picture.
11. Complete a division practice session.
12. Complete a table test.
13. View student progress.
14. Enable a scheduled question.
15. Trigger the scheduling worker using a controlled test clock.
16. Verify one delivery.
17. Run the worker again and verify no duplicate.
18. Restart the bot.
19. Confirm that progress remains.
20. Inspect the student from the teacher menu.
21. Inspect group progress.
22. Delete the student through `/delete_me`.
23. Confirm that the deleted account cannot continue without a new valid invitation.
24. Run the topic contract test with the sample topic.
25. Run the complete test and quality suite.

The application is not done until both the modularity scenario and the complete times-table scenario succeed without manually modifying the database.