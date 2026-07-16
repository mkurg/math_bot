# Numeral Systems and Computer Representation Module

## Student-Specific Learning Plan and Functional Specification

**Module name:** Numeral Systems and Data Representation
**Suggested internal topic name:** `numeral_systems`
**Target student:** Approximately Grade 4, with programming experience and strong abstract reasoning
**Starting level:** Already understands the foundations of binary positional notation and has encountered hexadecimal conceptually
**Primary educational direction:** Mathematics as systems, representations, transformations, and interpretation

---

# 1. Purpose of the module

This module continues the student’s existing work with numeral systems and gradually connects positional notation to real computer representations.

The module must help the student understand:

* that a number and its written representation are different things;
* how positional numeral systems work in any base;
* why binary, octal, decimal, and hexadecimal follow the same underlying rules;
* why binary can be converted directly into octal or hexadecimal by grouping digits;
* how decimal fits into the same system without becoming the only “real” representation;
* what bits, nibbles, and bytes are;
* how one byte represents values from 0 through 255;
* how RGB colours are represented using three numerical channels;
* why hexadecimal colour notation is a compact representation of binary data;
* how characters can be associated with numerical codes;
* how the same character code can be written in decimal, binary, or hexadecimal.

The module should develop conceptual flexibility rather than only conversion speed.

The desired final understanding is:

> Computers store patterns of bits.
> Numbers, colours, and characters are different interpretations of those patterns.

---

# 2. Student assignment and module visibility

The bot contains at least two separate educational modules:

1. **Times Tables**
2. **Numeral Systems and Data Representation**

Students must receive tasks according to the module assigned to their Telegram account.

For the student described in this specification:

* the default module is **Numeral Systems and Data Representation**;
* the student must not automatically receive elementary times-table tasks;
* daily questions must come from the numeral-systems module;
* statistics must be calculated separately from times-table statistics;
* the learning menu must display numeral-systems content rather than multiplication tables.

For the other student:

* the default module remains **Times Tables**;
* numeral-systems tasks must not appear unless the teacher deliberately assigns that module.

## 2.1 One assigned module

When a student has only one assigned module:

* do not show a module-selection screen;
* open the assigned module directly;
* keep the interface simple.

## 2.2 Several assigned modules

The design may later allow a student to have several modules.

In that case, the student may choose:

* Times Tables
* Numeral Systems
* another future topic

This is not necessary for the current student.

## 2.3 Teacher control

The teacher must be able to determine, for each registered Telegram account:

* which module the student uses;
* which module supplies daily tasks;
* whether the student may access more than one module;
* whether a module is active or paused.

Changing one student’s assignment must not affect other students.

---

# 3. Existing knowledge that the module must assume

The student has already worked with the following concepts.

## 3.1 Positional notation

The student understands that a digit’s value depends on its position.

Examples already familiar:

> 347 = 3 × 100 + 4 × 10 + 7 × 1

> 1101₂ = 1 × 8 + 1 × 4 + 0 × 2 + 1 × 1

The module must not restart from the assumption that binary is completely unfamiliar.

## 3.2 Binary as selecting powers of two

The student understands that binary digits indicate whether a power of two is present.

Example:

```text
8 4 2 1
1 1 0 1
```

Therefore:

> 1101₂ = 8 + 4 + 1 = 13₁₀

## 3.3 Binary-to-decimal conversion

The student knows how to:

* write the powers of two;
* select positions containing `1`;
* add their values.

## 3.4 Decimal-to-binary conversion

The student has encountered both:

* decomposition into powers of two;
* repeated division by two.

The student has also received the conceptual explanation:

> n = 2q + r

where the remainder is either `0` or `1`.

## 3.5 Binary addition

The student knows the basic rules:

* `0 + 0 = 0`
* `0 + 1 = 1`
* `1 + 0 = 1`
* `1 + 1 = 10`

The student understands that carrying occurs because two units of one binary position equal one unit of the next position.

## 3.6 Hexadecimal motivation

The student has already seen that:

* four binary digits correspond to one hexadecimal digit;
* hexadecimal is a shorter human-readable representation of binary;
* digits `A` through `F` represent values 10 through 15.

The module should therefore begin with a short recap and diagnostic activity, not a long introductory course.

---

# 4. Pedagogical principles

## 4.1 Representation is not value

The central distinction must appear repeatedly:

> The number is the value.
> Binary, decimal, octal, and hexadecimal are ways of writing that value.

The bot must avoid language suggesting that:

* `1010₂` and `10₁₀` are the same number because the visible digits look similar;
* hexadecimal creates different numbers;
* computers “understand hexadecimal” instead of binary;
* decimal is the original or natural form of every number.

## 4.2 General rule before isolated algorithm

When introducing a conversion method, the bot should first explain why it works.

For example, before practising binary-to-hexadecimal grouping:

> One hexadecimal digit represents 16 possible values.
> Four binary digits also represent 16 possible patterns.
> That is why one hexadecimal digit matches exactly four binary digits.

For octal:

> One octal digit represents 8 possible values.
> Three binary digits also represent 8 possible patterns.
> That is why one octal digit matches exactly three binary digits.

## 4.3 Discovery before explanation

Whenever possible, the bot should first ask the student to notice a pattern.

Example:

> How many different patterns can three bits make?

Possible answers:

* 3
* 6
* 8
* 9

After the student answers:

> Exactly: 2³ = 8 patterns.
> That matches the eight digits of the octal system.

## 4.4 Fewer tasks, deeper variation

The module should avoid sessions consisting of twenty nearly identical conversions.

A good five-question session may contain:

1. one conceptual question;
2. one direct conversion;
3. one explanation or error-detection task;
4. one computer-representation problem;
5. one transfer task using a colour or character.

## 4.5 Explanations must remain concise

The student enjoys conceptual depth, but the bot must not send textbook-length lectures during ordinary practice.

Use:

* one central idea;
* one worked step;
* one follow-up question.

Longer reference materials belong in the learning section.

---

# 5. Scope of the first numeral-systems module

The module must include:

* positional numeral systems;
* binary, octal, decimal, and hexadecimal;
* conversion between all four systems;
* direct binary-to-octal conversion;
* direct binary-to-hexadecimal conversion;
* octal-to-binary conversion;
* hexadecimal-to-binary conversion;
* decimal as a bridge where appropriate;
* conversion between octal and hexadecimal, normally through binary;
* comparison of values written in different systems;
* missing-digit and place-value tasks;
* bit, nibble, and byte concepts;
* the number of possible bit patterns;
* unsigned byte range 0–255;
* RGB channels;
* hexadecimal colour notation;
* simple character coding using ASCII;
* the same numerical code written in several numeral systems;
* short mixed interpretation problems.

The module may briefly mention that larger and more complex character systems exist, but full Unicode and UTF-8 instruction are outside the first version.

---

# 6. Explicit exclusions

The module must not include:

* floating-point representation;
* negative-number binary representation;
* two’s complement;
* signed integer overflow;
* floating-point precision;
* IEEE 754;
* full Unicode encoding;
* detailed UTF-8 byte construction;
* character normalization;
* binary fractions;
* base conversions involving fractional parts;
* bases other than 2, 8, 10, and 16;
* advanced Boolean algebra;
* bitwise programming syntax;
* networking protocols;
* machine code;
* assembly language;
* hexadecimal memory addresses;
* cryptography;
* arbitrary long arithmetic;
* timed speed competitions;
* public rankings;
* runtime AI-generated educational explanations.

The first module should establish a coherent foundation before these topics are added.

---

# 7. Learning progression

The curriculum is mastery-based rather than tied to a fixed number of weeks.

---

## Stage 1: Diagnostic recap

### Goal

Check that the previous binary knowledge remains active without making the student repeat an entire introductory course.

### Concepts

* positional notation;
* powers of two;
* binary-to-decimal conversion;
* decimal-to-binary conversion;
* simple binary addition;
* meaning of a bit.

### Example tasks

> Which expansion represents `10110₂`?

> Which binary number represents `19₁₀`?

> Why does `1 + 1` become `10` in binary?

> Which statement is correct?
>
> * Binary numbers are different kinds of quantities.
> * Binary and decimal can represent the same value.
> * Binary digits have no positional value.
> * Computers store decimal digits directly.

### Completion rule

The student does not need perfect performance.

The recap is complete when the student shows reliable understanding of:

* positional value;
* binary-to-decimal;
* decimal-to-binary;
* carrying in binary.

Weak points should be included later rather than blocking the entire module.

---

## Stage 2: General positional systems

### Goal

Move from “binary and decimal” to the general idea of base.

### Main idea

In a positional system with base `b`, the positions represent:

```text
..., b³, b², b¹, b⁰
```

The available digits are:

```text
0 through b − 1
```

### Examples

Base 10:

```text
10³, 10², 10¹, 10⁰
```

Base 2:

```text
2³, 2², 2¹, 2⁰
```

Base 8:

```text
8³, 8², 8¹, 8⁰
```

Base 16:

```text
16³, 16², 16¹, 16⁰
```

### Important insights

* Base 8 uses digits `0–7`.
* Base 16 needs sixteen digit symbols.
* `A–F` are digit symbols, not variables.
* `10` in any base means “one group of the base and zero units.”

Examples:

* `10₂ = 2₁₀`
* `10₈ = 8₁₀`
* `10₁₀ = 10₁₀`
* `10₁₆ = 16₁₀`

### Discovery tasks

> What does `10` mean in base 7?

> Why can the digit `8` not appear in an octal number?

> Which is larger: `10₁₆` or `10₈`?

> What is the largest single digit in base 16?

---

## Stage 3: Binary and octal

### Goal

Understand direct conversion through groups of three bits.

### Conceptual foundation

Three bits can form:

```text
2³ = 8
```

different patterns.

Octal has exactly eight digits:

```text
0, 1, 2, 3, 4, 5, 6, 7
```

Therefore:

> Three binary digits correspond exactly to one octal digit.

### Required mapping

```text
000₂ = 0₈
001₂ = 1₈
010₂ = 2₈
011₂ = 3₈
100₂ = 4₈
101₂ = 5₈
110₂ = 6₈
111₂ = 7₈
```

### Binary-to-octal method

1. Start from the right.
2. Divide the binary number into groups of three.
3. Add leading zeroes when necessary.
4. Convert each group into one octal digit.

Example:

```text
1011011₂
```

Group:

```text
001 011 011
```

Convert:

```text
1 3 3
```

Therefore:

```text
1011011₂ = 133₈
```

### Octal-to-binary method

Replace every octal digit with exactly three binary digits.

Example:

```text
57₈
```

```text
5 → 101
7 → 111
```

Therefore:

```text
57₈ = 101111₂
```

### Common misconceptions to test

* grouping from the left instead of from the right;
* forgetting leading zeroes;
* treating `10₈` as decimal ten;
* using four-bit groups for octal;
* using octal digit `8` or `9`.

---

## Stage 4: Binary and hexadecimal

### Goal

Develop fluent conversion using groups of four bits.

### Conceptual foundation

Four bits can form:

```text
2⁴ = 16
```

different patterns.

Hexadecimal has sixteen digits:

```text
0–9 and A–F
```

Therefore:

> Four binary digits correspond exactly to one hexadecimal digit.

### Required mapping

```text
0000 = 0
0001 = 1
0010 = 2
0011 = 3
0100 = 4
0101 = 5
0110 = 6
0111 = 7
1000 = 8
1001 = 9
1010 = A
1011 = B
1100 = C
1101 = D
1110 = E
1111 = F
```

### Binary-to-hexadecimal method

1. Start from the right.
2. Divide the binary number into groups of four.
3. Add leading zeroes when necessary.
4. Replace each group with a hexadecimal digit.

Example:

```text
10101111₂
```

```text
1010 1111
```

```text
A F
```

Therefore:

```text
10101111₂ = AF₁₆
```

### Hexadecimal-to-binary method

Replace every hexadecimal digit with exactly four bits.

Example:

```text
3D₁₆
```

```text
3 → 0011
D → 1101
```

Therefore:

```text
3D₁₆ = 00111101₂
```

Leading zeroes may be removed when the number is viewed only as a value:

```text
00111101₂ = 111101₂
```

However, when discussing bytes, the leading zeroes may be meaningful for displaying the complete eight-bit representation.

### Important language

Do not say:

> Hexadecimal is how computers store numbers.

Say:

> Computers store bits. Hexadecimal is a compact way for humans to write groups of bits.

---

## Stage 5: Decimal in the conversion network

### Goal

Include decimal without turning every conversion into a decimal detour.

### General rule

The student should learn two different kinds of conversion:

#### Structural conversion

Use grouping when the bases are related by powers:

* binary ↔ octal;
* binary ↔ hexadecimal.

#### Value conversion

Use place values, decomposition, or division when converting:

* decimal ↔ binary;
* decimal ↔ octal;
* decimal ↔ hexadecimal.

### Decimal-to-octal

Possible methods:

* decomposition using powers of eight;
* repeated division by eight.

Example:

```text
83₁₀
```

Repeated division:

```text
83 = 8 × 10 + 3
10 = 8 × 1 + 2
1 = 8 × 0 + 1
```

Read backwards:

```text
123₈
```

### Decimal-to-hexadecimal

Use decomposition or repeated division by sixteen.

Example:

```text
254₁₀
```

```text
254 = 16 × 15 + 14
```

```text
15 = F
14 = E
```

Therefore:

```text
254₁₀ = FE₁₆
```

### Hexadecimal-to-decimal

Example:

```text
2A₁₆
```

```text
2 × 16 + 10 = 42
```

### Octal-to-decimal

Example:

```text
157₈
```

```text
1 × 64 + 5 × 8 + 7 = 111
```

### Pedagogical warning

Do not require the student to convert binary to hexadecimal by first converting it to decimal unless the task specifically asks for that method.

The direct structural relationship is the important insight.

---

## Stage 6: Converting between octal and hexadecimal

### Goal

Understand that binary can serve as a precise bridge.

### Octal-to-hexadecimal method

1. Replace each octal digit with three bits.
2. Regroup the complete binary number into groups of four.
3. Convert each four-bit group into hexadecimal.

Example:

```text
73₈
```

Octal to binary:

```text
7 → 111
3 → 011
```

```text
111011₂
```

Pad and group:

```text
0011 1011
```

Convert:

```text
3B₁₆
```

Therefore:

```text
73₈ = 3B₁₆
```

### Hexadecimal-to-octal method

1. Replace each hexadecimal digit with four bits.
2. Regroup into sets of three.
3. Convert each set into an octal digit.

### Main insight

> Binary is not merely an intermediate trick.
> It reveals how both compact systems group the same bit pattern differently.

---

## Stage 7: Bits, nibbles, and bytes

### Goal

Connect numeral-system knowledge to data storage.

### Required concepts

* A bit is one binary digit.
* A nibble is four bits.
* A byte is eight bits.
* One hexadecimal digit corresponds to one nibble.
* Two hexadecimal digits correspond to one byte.
* A byte has `2⁸ = 256` possible patterns.
* An unsigned byte represents values from `0` through `255`.

### Discovery sequence

Ask:

> How many patterns can one bit represent?

Answer:

```text
2
```

Then:

> How many patterns can two bits represent?

```text
2² = 4
```

Then:

> How many patterns can eight bits represent?

```text
2⁸ = 256
```

Finally:

> If counting begins at zero, what is the largest value?

```text
255
```

### Example representations

```text
11111111₂ = 255₁₀ = FF₁₆
```

```text
00000000₂ = 0₁₀ = 00₁₆
```

```text
10000000₂ = 128₁₀ = 80₁₆
```

### Important distinction

The module must distinguish between:

* the number of patterns: 256;
* the largest unsigned value: 255.

This should be tested explicitly because it is a common conceptual confusion.

---

## Stage 8: RGB colour representation

### Goal

Use numeral systems in a concrete computer representation.

### Core model

An RGB colour has three channels:

* Red
* Green
* Blue

In the simplified model used in this course:

* each channel uses one byte;
* each channel has a value from 0 through 255;
* each channel can be written as two hexadecimal digits;
* a colour can therefore be written using six hexadecimal digits.

Example:

```text
Red   = 255 = FF
Green = 0   = 00
Blue  = 0   = 00
```

Therefore:

```text
#FF0000
```

represents full red, no green, and no blue.

### Required examples

```text
#000000 = black
#FFFFFF = white
#FF0000 = red
#00FF00 = green
#0000FF = blue
#FFFF00 = yellow
#00FFFF = cyan
#FF00FF = magenta
```

### Important conceptual point

The student should not merely memorize colour names.

The student should reason:

> `FF` means the channel is at its maximum value.
> `00` means the channel is absent.

### Intermediate values

Introduce examples such as:

```text
#800000
#008000
#000080
#808080
#8040FF
```

The student should be able to determine:

* which channel is strongest;
* whether a colour is likely dark or bright;
* which two colours share the same red channel;
* which representation corresponds to a given channel tuple.

### Visual tasks

The bot should be able to show:

* a colour square and several possible hexadecimal codes;
* a hexadecimal code and several colour squares;
* three channel values and the resulting code;
* a partly completed code;
* a binary representation of the three bytes.

Example:

```text
11111111 10000000 00000000
```

Group into hexadecimal:

```text
FF 80 00
```

Colour code:

```text
#FF8000
```

### Avoid oversimplification

The module may describe RGB as a simplified model for digital colour.

It does not need to discuss:

* colour profiles;
* gamma correction;
* alpha channels;
* display calibration;
* perceptual colour spaces.

---

## Stage 9: Character codes

### Goal

Show that characters can be represented by assigned numbers, which can then be written in different bases.

### Core principle

> The letter itself is not binary or hexadecimal.
> A character-encoding system assigns the character a number.
> That number can be represented in binary, decimal, or hexadecimal.

### Initial scope

Use a small, clearly defined ASCII subset:

* uppercase Latin letters;
* lowercase Latin letters;
* digits;
* a few punctuation marks;
* space.

Examples:

```text
A = 65₁₀ = 41₁₆ = 01000001₂
B = 66₁₀ = 42₁₆ = 01000010₂
a = 97₁₀ = 61₁₆ = 01100001₂
0 = 48₁₀ = 30₁₆ = 00110000₂
space = 32₁₀ = 20₁₆ = 00100000₂
```

### Required insights

* `A` and `a` have different codes.
* The character `0` is not the numerical value zero.
* Hexadecimal is a way of writing the character’s assigned numerical code.
* Eight bits may be used to display the code as a byte.
* The same bit pattern may have different meanings depending on interpretation.

### Interpretation task

Show:

```text
01000001
```

Ask:

> What can this represent?

Correct explanation:

> As an unsigned number, it is 65.
> Under ASCII interpretation, code 65 represents `A`.

This distinction is central.

### Simple word exercises

The student may convert short strings using a provided table.

Example:

```text
CAT
```

```text
C = 43₁₆
A = 41₁₆
T = 54₁₆
```

Therefore:

```text
43 41 54
```

Do not require memorization of the complete ASCII table.

Provide the relevant mapping in the task or learning reference.

### Unicode boundary

The module may say:

> ASCII covers a small set of characters. Modern systems use larger standards such as Unicode.

Do not teach full Unicode or UTF-8 conversion in this version.

---

## Stage 10: Interpretation and mixed representation

### Goal

Combine the previous topics into computer-science-style reasoning.

### Example tasks

> A byte contains `01000001`.
> What is its decimal value?

> The same byte is interpreted as ASCII.
> Which character does it represent?

> Which hexadecimal value represents the binary byte `11110000`?

> Which colour has its blue channel at maximum and the other channels at zero?

> Why are two hexadecimal digits enough to represent one byte?

> A file contains the byte `00110000`.
> As an unsigned number it is 48.
> Under ASCII, which character is it?

> Which two representations show the same value?
>
> * `1111₂`
> * `17₈`
> * `15₁₀`
> * `F₁₆`

The correct result is that all four represent the same value.

### Central final idea

The student should be able to explain:

> The bit pattern does not carry its meaning by itself.
> A system or program decides whether the bits represent a number, character, colour channel, or something else.

---

# 8. Main menu for this student

The module menu should contain:

* **▶️ Practise**
* **🧭 Learn**
* **🧪 Challenges**
* **☀️ Daily task**
* **📊 My progress**
* **⚙️ Settings**

Use **Challenges** rather than ordinary school-style “Tests” if the student responds better to exploratory framing.

The teacher may still see formal assessment results.

---

# 9. Learn menu

The **🧭 Learn** section should contain:

* **How bases work**
* **Binary recap**
* **Binary ↔ Octal**
* **Binary ↔ Hexadecimal**
* **Decimal conversions**
* **Octal ↔ Hexadecimal**
* **Bits and bytes**
* **RGB colours**
* **Character codes**
* **Representation and meaning**
* **Reference tables**

## 9.1 Reference tables

Provide quick access to:

* powers of two;
* powers of eight;
* powers of sixteen;
* three-bit octal mapping;
* four-bit hexadecimal mapping;
* hexadecimal digits `A–F`;
* selected ASCII codes;
* RGB examples.

The student must not need to memorize every table before practising.

Reference access during ordinary practice may be allowed through a **Show reference** button.

In formal challenges, reference access may be hidden depending on the challenge type.

---

# 10. Practice modes

Selecting **▶️ Practise** should display:

* **Quick mix — 5 tasks**
* **Deep session — 8 tasks**
* **Binary and decimal**
* **Binary and octal**
* **Binary and hexadecimal**
* **All four systems**
* **Bits and bytes**
* **Colours**
* **Character codes**
* **My weak skills**
* **Back**

## 10.1 Quick mix

Five varied tasks.

A typical session should contain:

* one conceptual task;
* two conversions;
* one interpretation task;
* one applied task.

## 10.2 Deep session

Eight tasks with more multi-step reasoning.

A typical session should contain:

* two conceptual or explanation tasks;
* three conversions;
* one error-detection task;
* one applied data-representation task;
* one transfer task.

## 10.3 Binary and decimal

Focus on:

* positional expansion;
* binary-to-decimal;
* decimal-to-binary;
* powers of two;
* binary addition when appropriate.

## 10.4 Binary and octal

Focus on:

* three-bit grouping;
* conversion in both directions;
* detecting invalid octal digits;
* explaining why three bits correspond to one octal digit.

## 10.5 Binary and hexadecimal

Focus on:

* four-bit grouping;
* conversion in both directions;
* hexadecimal digits;
* bytes and nibbles.

## 10.6 All four systems

Include:

* comparisons;
* direct and indirect conversions;
* octal ↔ hexadecimal through binary;
* selecting equivalent representations.

## 10.7 Bits and bytes

Include:

* number of possible patterns;
* largest unsigned value;
* bit lengths;
* byte and nibble relationships;
* leading zeroes.

## 10.8 Colours

Include:

* RGB channel values;
* binary channel representations;
* hexadecimal colour codes;
* visual colour interpretation.

## 10.9 Character codes

Include:

* character-to-code;
* code-to-character;
* decimal, binary, and hexadecimal views;
* distinction between character and numeric value.

## 10.10 My weak skills

Automatically select concepts where the student:

* answers incorrectly;
* asks for hints often;
* answers correctly only after several attempts;
* confuses related concepts;
* has not reviewed the skill recently.

---

# 11. Answer interaction

The module should minimize typed input while avoiding excessive guessing.

Use two principal answer styles.

## 11.1 Multiple choice

Use for:

* conceptual questions;
* equivalent representations;
* error detection;
* selecting a colour;
* character interpretation;
* explanation choices;
* short conversions.

Usually provide four options.

## 11.2 Button-based numeral pad

For conversion tasks, the student should be able to construct an answer using onscreen buttons.

### Binary pad

Buttons:

```text
0 1
⌫ Clear Submit
```

### Octal pad

Buttons:

```text
0 1 2 3
4 5 6 7
⌫ Clear Submit
```

### Decimal pad

Buttons:

```text
1 2 3
4 5 6
7 8 9
0 ⌫ Submit
```

### Hexadecimal pad

Buttons:

```text
0 1 2 3
4 5 6 7
8 9 A B
C D E F
⌫ Clear Submit
```

This allows the student to produce an actual answer without using the Telegram keyboard.

The bot should display the currently constructed answer above the buttons.

## 11.3 Step-selection tasks

For some problems, ask the student to select the next correct step.

Example:

> Convert `10111100₂` to hexadecimal.
> What should we do first?

Options:

* Group into pairs.
* Group into threes.
* Group into fours from the right.
* Convert each bit to decimal separately.

This checks understanding of the method rather than only the final result.

---

# 12. Required question types

The module must include all of the following.

## 12.1 Positional expansion

> Which expansion represents `2F₁₆`?

## 12.2 Base identification

> Which digits are valid in base 8?

## 12.3 Direct conversion

Examples:

* binary → decimal;
* decimal → binary;
* binary → octal;
* octal → binary;
* binary → hexadecimal;
* hexadecimal → binary;
* decimal → octal;
* octal → decimal;
* decimal → hexadecimal;
* hexadecimal → decimal.

## 12.4 Cross-conversion

Examples:

* octal → hexadecimal;
* hexadecimal → octal.

## 12.5 Equivalent representations

> Which representation has the same value as `3A₁₆`?

## 12.6 Comparison

> Which is larger: `11100₂` or `31₁₀`?

## 12.7 Missing digit

> `10?1₂ = 9₁₀`
> Which digit is missing?

## 12.8 Error detection

> A student converted `111010₂` into `72₈`.
> What went wrong?

## 12.9 Method selection

> Which conversion can be performed directly by grouping bits into fours?

## 12.10 Explanation selection

> Why does one hexadecimal digit correspond to four bits?

## 12.11 Bit-count question

> How many different patterns can five bits represent?

## 12.12 Range question

> Why is the largest unsigned byte value 255 rather than 256?

## 12.13 Byte decomposition

> Split this byte into two nibbles.

## 12.14 RGB channel conversion

> Convert Red = 255, Green = 128, Blue = 0 into hexadecimal.

## 12.15 Colour recognition

Show a colour and ask for the most plausible RGB hexadecimal code.

## 12.16 Character-code conversion

> ASCII assigns `A` the decimal code 65.
> What is that code in hexadecimal?

## 12.17 Interpretation question

> The byte `00110000` is 48 as a number.
> Under ASCII, what does it represent?

## 12.18 Same bits, different meanings

> Explain how `01000001` can represent both 65 and the letter `A`.

## 12.19 Mixed transformation chain

> Convert `7B₁₆` to binary, then determine its decimal value.

## 12.20 Construct-your-own representation

> Build the eight-bit binary representation of `C4₁₆`.

---

# 13. Hint system

Hints must explain structure without immediately giving the answer.

## 13.1 Hint levels

### Hint 1: Method reminder

> Hexadecimal uses groups of four bits.

### Hint 2: Partial structure

> Group the number as `1010 11??`.

### Hint 3: Reference support

> `1010₂ = A₁₆`.

Do not offer more than three hint levels.

## 13.2 Hint consequences

Using a hint:

* must not be treated as failure;
* should be recorded separately;
* may cause the skill to return sooner;
* should not remove rewards or produce negative language.

## 13.3 Worked solution

After an incorrect answer, show a concise worked solution.

Example:

> `101101₂`
>
> Group from the right:
>
> `001 011 101`
>
> `001 = 1`, `011 = 3`, `101 = 5`
>
> So the answer is `135₈`.

---

# 14. Adaptive skill map

The student’s progress should be tracked by concept rather than by one overall percentage.

Recommended skills:

## Foundation

* representation versus value;
* positional value;
* powers of the base;
* valid digits in a base;
* meaning of `10` in different bases.

## Binary and decimal

* binary → decimal;
* decimal → binary by powers;
* decimal → binary by division;
* binary addition;
* bit-length recognition.

## Octal

* three-bit mapping;
* binary → octal;
* octal → binary;
* decimal → octal;
* octal → decimal.

## Hexadecimal

* hexadecimal digit values;
* four-bit mapping;
* binary → hexadecimal;
* hexadecimal → binary;
* decimal → hexadecimal;
* hexadecimal → decimal.

## Cross-base reasoning

* octal → hexadecimal;
* hexadecimal → octal;
* equivalent representations;
* compare values across bases;
* choose an efficient conversion route.

## Data units

* bit;
* nibble;
* byte;
* number of patterns;
* unsigned byte range;
* leading zeroes.

## RGB

* channel interpretation;
* decimal channel → hexadecimal;
* hexadecimal channel → decimal;
* complete colour code;
* visual colour reasoning;
* binary RGB representation.

## Characters

* character as an assigned code;
* ASCII decimal code;
* ASCII hexadecimal code;
* ASCII binary byte;
* numeric value versus character interpretation.

## Metaconcept

* bits require interpretation;
* hexadecimal is compact notation for bit patterns;
* the same value can have several representations;
* the same bit pattern can receive different meanings.

---

# 15. Prerequisite structure

New tasks should follow conceptual prerequisites.

Examples:

* binary-to-octal grouping requires familiarity with binary values `000–111`;
* binary-to-hexadecimal requires hexadecimal digits `A–F`;
* RGB hexadecimal tasks require byte and hexadecimal fluency;
* character-code tasks require understanding that codes are numbers;
* octal-to-hexadecimal requires both direct binary mappings;
* interpretation tasks require value-versus-representation understanding.

The student may still encounter exploratory preview questions before formal mastery, but repeated practice should respect prerequisites.

---

# 16. Adaptive selection rules

A normal session should draw approximately:

* 40% from skills currently being developed;
* 25% from weak or recently incorrect skills;
* 20% from mastered skills due for review;
* 15% from transfer or conceptual questions.

The system should avoid:

* five consecutive conversions of the same type;
* immediate repetition of the identical number;
* repeatedly using only small values;
* always using numbers aligned to full groups;
* presenting only final-answer tasks.

After a mistake:

1. explain the solution;
2. ask one or two unrelated questions;
3. return to the same concept with a different value or format;
4. revisit it on a later day.

Example:

Original mistake:

> `11010110₂` → hexadecimal

Later task:

> Which grouping is correct for converting `101101₂` to hexadecimal?

Next-day task:

> Convert `5E₁₆` to binary.

---

# 17. Difficulty progression

## Level 1: Recognition

* select valid digits;
* identify place values;
* match a four-bit group to a hexadecimal digit;
* recognize equivalent simple values.

## Level 2: Short direct conversion

* values within one nibble;
* values within one octal digit;
* decimal values below 32;
* simple one-byte values.

## Level 3: Multi-digit conversion

* eight-bit binary values;
* two-digit hexadecimal;
* two- or three-digit octal;
* decimal values through 255.

## Level 4: Cross-conversion

* octal ↔ hexadecimal;
* mixed-base comparisons;
* efficient route selection;
* error analysis.

## Level 5: Representation

* bytes;
* RGB;
* character codes;
* same bits with different interpretations.

## Level 6: Transfer and explanation

* explain why an algorithm works;
* reconstruct a missing step;
* compare alternative methods;
* solve mixed computer-representation problems.

The student should not be forced to complete every low-level exercise before receiving interesting representation tasks.

Conceptual motivation should remain visible throughout.

---

# 18. Daily tasks

The daily task should be one meaningful question, not a repetitive worksheet.

Examples:

> ☀️ Why does one octal digit correspond to three bits?

> Convert `10101100₂` to hexadecimal.

> A byte has eight bits. How many possible bit patterns are there?

> Which colour is represented by `#0000FF`?

> ASCII assigns `A` the code `41₁₆`. What is that code in binary?

> Are `1111₂`, `17₈`, `15₁₀`, and `F₁₆` equal?

After answering, offer:

* **One more**
* **Practise this skill**
* **Open explanation**
* **Done for today**

Daily tasks should alternate between:

* conversion;
* concept;
* application;
* interpretation.

Do not send only conversions every day.

---

# 19. Challenges and assessments

The module should use several focused challenges.

## 19.1 Base Foundations Challenge

Ten questions covering:

* positional notation;
* valid digits;
* powers;
* meaning of `10`;
* value versus representation.

## 19.2 Binary–Octal Challenge

Ten questions:

* three binary-to-octal;
* three octal-to-binary;
* two explanation or grouping tasks;
* one decimal bridge task;
* one error-detection task.

## 19.3 Binary–Hexadecimal Challenge

Twelve questions:

* four binary-to-hexadecimal;
* three hexadecimal-to-binary;
* two decimal/hexadecimal conversions;
* one nibble task;
* one byte task;
* one explanation question.

## 19.4 Four Systems Challenge

Fifteen questions covering:

* binary;
* octal;
* decimal;
* hexadecimal;
* comparison;
* equivalent representations;
* cross-conversion;
* efficient method choice.

## 19.5 Bits and Bytes Challenge

Ten questions covering:

* patterns;
* bit counts;
* nibbles;
* bytes;
* range;
* leading zeroes;
* hexadecimal byte representation.

## 19.6 RGB Challenge

Twelve questions:

* channel interpretation;
* decimal-to-hexadecimal channel conversion;
* hexadecimal-to-decimal channel conversion;
* full colour codes;
* binary channel representation;
* visual recognition.

## 19.7 Character Code Challenge

Ten questions:

* decimal, binary, and hexadecimal codes;
* characters versus numerical values;
* short ASCII decoding;
* interpretation of bytes.

## 19.8 Final Representation Challenge

Twenty mixed questions.

Suggested composition:

* three conceptual questions;
* six numeral-system conversions;
* two cross-base conversions;
* two byte questions;
* three RGB questions;
* three character-code questions;
* one final interpretation problem.

Do not impose a strict time limit.

Response time may be recorded for teacher information, but speed must not reduce the score.

---

# 20. Feedback after challenges

Challenge results should show more than a raw score.

Example:

> **Result: 15 of 20**
>
> Strong:
>
> * binary ↔ hexadecimal;
> * byte ranges;
> * RGB channel interpretation.
>
> Continue practising:
>
> * hexadecimal → octal;
> * character codes;
> * explaining why grouping works.
>
> Suggested next step:
>
> **Practise cross-base conversions**

The bot must not use:

* fail;
* weak student;
* poor;
* below level;
* careless.

---

# 21. Student progress page

The progress page should show:

* total tasks answered;
* active practice days;
* recent accuracy;
* skills mastered;
* skills currently developing;
* concepts that need review;
* recent challenge results;
* current learning stage.

Suggested presentation:

> **Numeral Systems**
>
> Positional systems: ██████████
> Binary ↔ Decimal: █████████░
> Binary ↔ Octal: ███████░░░
> Binary ↔ Hex: ████████░░
> Four-system conversion: █████░░░░░
> Bits and bytes: ███████░░░
> RGB: ████░░░░░░
> Character codes: ██░░░░░░░░

The student should also see:

* **What I understand well**
* **What I am discovering now**
* **Recommended practice**
* **Review a concept**

Avoid one single overall grade that hides the conceptual profile.

---

# 22. Teacher view

For this student, the teacher should be able to see:

* current curriculum stage;
* performance by skill;
* recent misconceptions;
* hint usage;
* recent daily-task activity;
* challenge history;
* whether mistakes are procedural or conceptual;
* recommended next concept;
* representations most often confused.

Useful misconception labels include:

* groups bits from the wrong side;
* confuses value with visible digits;
* confuses number of patterns with maximum value;
* treats hexadecimal letters as variables;
* converts structurally related bases through decimal unnecessarily;
* drops significant grouping information;
* confuses character digit `0` with value zero;
* interprets hexadecimal as the computer’s native storage;
* confuses RGB channel order.

The teacher should not receive only percentages.

---

# 23. Content style

## 23.1 Notation

Always show the base clearly when ambiguity is possible:

```text
1010₂
12₈
10₁₀
A₁₆
```

For button labels where subscripts are inconvenient, acceptable alternatives include:

```text
1010 (base 2)
12 (base 8)
A (base 16)
```

Do not mix unlabeled representations in one question unless recognizing ambiguity is the task.

## 23.2 Hexadecimal letters

Use uppercase:

```text
A B C D E F
```

Accept lowercase answers if typed input is ever allowed later, but display uppercase consistently.

## 23.3 Leading zeroes

Explain whether leading zeroes are:

* optional when writing a numerical value;
* useful or required when showing a fixed-width bit pattern such as a byte.

Example:

```text
A₁₆ = 1010₂
```

but as one byte:

```text
00001010₂
```

## 23.4 Language

Use precise but accessible wording.

Good:

> Four bits form sixteen possible patterns, so each pattern matches one hexadecimal digit.

Less useful:

> Just split it into groups of four because that is the rule.

---

# 24. Visual materials

The module should use deterministic educational images, not decorative AI-generated scenes.

Useful visual formats:

* place-value columns;
* power-of-base ladders;
* bit switches;
* groups of three and four bits;
* nibble and byte diagrams;
* RGB channel bars;
* colour swatches;
* character-code cards;
* diagrams showing one bit pattern with several interpretations.

Example byte diagram:

```text
1100 | 1010
 C      A
```

Example RGB diagram:

```text
Red:   FF  ██████████
Green: 80  █████░░░░░
Blue:  00  ░░░░░░░░░░
```

Images should support the reasoning.

They must not merely repeat the same text in decorative form.

---

# 25. Recommended content bank

The module should contain enough reviewed tasks to prevent obvious repetition.

Minimum content:

* 20 positional-system concept questions;
* 30 binary/decimal conversion tasks;
* 30 binary/octal tasks;
* 40 binary/hexadecimal tasks;
* 20 decimal/octal tasks;
* 25 decimal/hexadecimal tasks;
* 20 octal/hexadecimal tasks;
* 20 equivalent-representation tasks;
* 15 error-detection tasks;
* 20 bit/nibble/byte tasks;
* 25 RGB tasks;
* 20 character-code tasks;
* 20 interpretation tasks.

These may be template-based, but generated values must be validated.

The module should not present the same numerical example too frequently.

---

# 26. Rules for generated values

## 26.1 Introductory values

Use:

* small positive integers;
* values that fit clearly into four or eight bits;
* examples with visible patterns.

## 26.2 Later values

Use values from:

```text
0 through 255
```

for byte, RGB, and ASCII-related tasks.

## 26.3 Grouping variation

Include binary values whose lengths:

* are exact multiples of three;
* require padding for octal;
* are exact multiples of four;
* require padding for hexadecimal.

## 26.4 Avoid triviality

Do not overuse:

* zero;
* one;
* powers of two;
* values where every digit is identical;
* `FF`, `00`, and primary colours after the introductory stage.

## 26.5 Avoid invalid ambiguity

Every task must clearly specify:

* the source base;
* the target base;
* whether a fixed-width byte is required;
* whether leading zeroes matter.

---

# 27. Completion criteria for individual skills

A skill may be considered learned when the student:

* answers correctly across at least two different days;
* succeeds with more than one question format;
* can solve both direct and inverse forms where applicable;
* can explain or recognize why the method works;
* does not depend constantly on the reference table.

For example, binary-to-hexadecimal is not fully learned merely because the student answered several multiple-choice questions correctly.

The student should demonstrate:

* grouping;
* mapping;
* reverse conversion;
* explanation of the four-bit relationship.

---

# 28. Definition of done for the module

The numeral-systems module is complete only when every mandatory criterion below is satisfied.

## A. Student assignment

* [ ] The numeral-systems module can be assigned to the intended Telegram account.
* [ ] The times-table student continues receiving times-table tasks.
* [ ] The numeral-systems student receives numeral-systems tasks.
* [ ] Statistics remain separate between modules.
* [ ] Daily tasks use the correct student’s assigned module.
* [ ] One student’s assignment does not affect another student.
* [ ] A student with only one assigned module does not see an unnecessary topic-selection screen.

## B. Existing knowledge and progression

* [ ] The module begins with a short diagnostic recap.
* [ ] It does not unnecessarily reteach binary from the beginning.
* [ ] Positional notation is generalized to arbitrary bases.
* [ ] Binary and decimal are reviewed.
* [ ] Binary and octal are taught structurally.
* [ ] Binary and hexadecimal are taught structurally.
* [ ] Decimal conversions are included carefully.
* [ ] Octal and hexadecimal cross-conversion is included.
* [ ] Bits, nibbles, and bytes are included.
* [ ] RGB representation is included.
* [ ] Character codes are included.
* [ ] Representation versus interpretation remains a central theme.

## C. Mathematical accuracy

* [ ] Every generated conversion is mathematically correct.
* [ ] Bases are clearly labeled.
* [ ] Octal uses only digits 0–7.
* [ ] Hexadecimal uses digits 0–9 and A–F.
* [ ] Binary-to-octal grouping uses three bits.
* [ ] Binary-to-hexadecimal grouping uses four bits.
* [ ] Grouping begins from the right.
* [ ] Required padding is handled correctly.
* [ ] Byte range is presented as 0–255.
* [ ] A byte is described as having 256 possible patterns.
* [ ] RGB channels are limited to 0–255.
* [ ] Hexadecimal colour codes contain two digits per channel.
* [ ] Character codes are distinguished from characters themselves.
* [ ] Hexadecimal is never described as the computer’s underlying storage format.

## D. Practice modes

* [ ] Quick mixed practice works.
* [ ] Deep practice works.
* [ ] Binary/decimal practice works.
* [ ] Binary/octal practice works.
* [ ] Binary/hexadecimal practice works.
* [ ] Four-system practice works.
* [ ] Bits-and-bytes practice works.
* [ ] RGB practice works.
* [ ] Character-code practice works.
* [ ] Weak-skill practice works.
* [ ] Sessions include varied task types.
* [ ] The student is not given long sequences of identical conversions.

## E. Answer interaction

* [ ] Ordinary interaction requires no Telegram keyboard typing.
* [ ] Multiple-choice questions use buttons.
* [ ] Binary answers can be constructed with a binary button pad.
* [ ] Octal answers can be constructed with an octal button pad.
* [ ] Decimal answers can be constructed with a decimal button pad.
* [ ] Hexadecimal answers can be constructed with a hexadecimal button pad.
* [ ] Backspace works.
* [ ] Clear works.
* [ ] Submit works.
* [ ] The current constructed answer is visible.
* [ ] Only the first submitted answer is counted.
* [ ] Expired buttons do not change statistics.

## F. Required question types

* [ ] Positional-expansion tasks exist.
* [ ] Base-identification tasks exist.
* [ ] Direct-conversion tasks exist in all required directions.
* [ ] Cross-conversion tasks exist.
* [ ] Equivalent-representation tasks exist.
* [ ] Comparison tasks exist.
* [ ] Missing-digit tasks exist.
* [ ] Error-detection tasks exist.
* [ ] Method-selection tasks exist.
* [ ] Explanation-selection tasks exist.
* [ ] Bit-count tasks exist.
* [ ] Byte-range tasks exist.
* [ ] RGB tasks exist.
* [ ] Character-code tasks exist.
* [ ] Interpretation tasks exist.
* [ ] Mixed transformation chains exist.

## G. Feedback and hints

* [ ] Correct answers receive concise confirmation.
* [ ] Incorrect answers receive a worked explanation.
* [ ] Hints explain the method rather than merely reveal the answer.
* [ ] At most three hint levels are used.
* [ ] Hint use does not count as failure.
* [ ] A mistaken concept returns later in a different form.
* [ ] Feedback remains respectful and non-patronizing.

## H. Adaptive learning

* [ ] Progress is tracked by individual concept.
* [ ] Weak concepts receive more practice.
* [ ] Mastered concepts return for spaced review.
* [ ] Conceptual and applied questions remain in the mix.
* [ ] Prerequisites affect task selection.
* [ ] The same value is not repeated unnecessarily.
* [ ] The same task format is not repeated excessively.
* [ ] Mistakes are classified where possible.
* [ ] Correct guessing in multiple choice is not the only evidence of mastery.

## I. RGB section

* [ ] RGB channels are explained.
* [ ] Each channel is connected to one byte.
* [ ] Decimal and hexadecimal channel values are practised.
* [ ] Complete six-digit colour codes are practised.
* [ ] Visual colour tasks exist.
* [ ] Binary RGB representation is included.
* [ ] Primary and mixed colours are included.
* [ ] Intermediate channel values are included.
* [ ] RGB is not presented as a complete theory of colour.

## J. Character-code section

* [ ] The module explains that encoding assigns numbers to characters.
* [ ] Selected ASCII values are available as a reference.
* [ ] Character → decimal tasks exist.
* [ ] Character → hexadecimal tasks exist.
* [ ] Character → binary tasks exist.
* [ ] Code → character tasks exist.
* [ ] Short decoding tasks exist.
* [ ] Character `0` is distinguished from numerical zero.
* [ ] Uppercase and lowercase letters are distinguished.
* [ ] ASCII is not presented as sufficient for every language.
* [ ] Full Unicode and UTF-8 are not taught in this version.

## K. Challenges and progress

* [ ] Every defined challenge exists.
* [ ] Challenges contain the required variety.
* [ ] No strict speed requirement is imposed.
* [ ] Results show strengths and next steps.
* [ ] The student sees progress by concept.
* [ ] The teacher sees misconceptions and hint use.
* [ ] No public leaderboard exists.
* [ ] No single overall grade replaces the skill profile.

## L. Scope control

* [ ] No floating-point representation is included.
* [ ] No two’s complement is included.
* [ ] No binary fractions are included.
* [ ] No advanced Unicode encoding is included.
* [ ] No Boolean algebra course is included.
* [ ] No unrelated programming course is included.
* [ ] No runtime AI content generation is required.
* [ ] No advanced feature is added merely because the student may be capable of it.

---

# 29. Final student acceptance scenario

The module is ready when the following complete learning flow works for the assigned student:

1. The student opens the bot and sees the numeral-systems menu.
2. The student completes a short binary diagnostic.
3. The student reviews how positional bases work.
4. The student converts binary to octal by grouping into threes.
5. The student converts octal back to binary.
6. The student converts binary to hexadecimal by grouping into fours.
7. The student constructs a hexadecimal answer using buttons.
8. The student converts hexadecimal back to binary.
9. The student completes one decimal-to-hexadecimal task.
10. The student converts an octal number to hexadecimal through binary.
11. The student answers how many patterns one byte contains.
12. The student distinguishes 256 possible patterns from the maximum value 255.
13. The student converts three RGB channel values into a hexadecimal colour code.
14. The student identifies a colour from a hexadecimal code.
15. The student converts one ASCII character code between decimal, binary, and hexadecimal.
16. The student explains how the same byte may represent a number or a character.
17. The student completes a mixed challenge.
18. The student opens a progress page showing separate conceptual skills.
19. A daily numeral-systems question is sent to this student.
20. The other student continues receiving only times-table content.

The module is not complete if it merely offers a collection of base-conversion worksheets. It must connect conversion, representation, and interpretation into one coherent learning path.
