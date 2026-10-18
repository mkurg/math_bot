from __future__ import annotations

from dataclasses import dataclass
from html import escape

from app.topics.python_foundations.russian_tasks import (
    CHECKS,
    DETAILS,
    EDITS,
    localized_output_answers,
)

QUESTION_TYPES = ("recognize", "predict", "apply")


@dataclass(frozen=True, slots=True)
class Concept:
    principle: str
    check_prompt: str
    check_answers: tuple[str, str, str, str]
    explanation: str
    direction_hint: str
    misconception: str
    stdout_code: str | None = None
    stdout_inputs: tuple[str, ...] = ()
    stdout_expected: str | None = None


@dataclass(frozen=True, slots=True)
class QuestionParts:
    prompt: str
    answers: tuple[str, str, str, str]
    explanation: str
    hints: tuple[str, ...]
    misconception: str
    difficulty_level: int
    stdout_code: str | None = None
    stdout_inputs: tuple[str, ...] = ()
    stdout_expected: str | None = None


def code_block(code: str) -> str:
    return f'<pre><code class="language-python">{escape(code)}</code></pre>'


def _q(
    principle: str,
    prompt: str,
    correct: str,
    wrong_1: str,
    wrong_2: str,
    wrong_3: str,
    explanation: str,
    hint: str,
    misconception: str,
) -> Concept:
    return Concept(
        principle,
        prompt,
        (correct, wrong_1, wrong_2, wrong_3),
        explanation,
        hint,
        misconception,
    )


def _out(
    principle: str,
    code: str,
    expected: str,
    wrong_1: str,
    wrong_2: str,
    wrong_3: str,
    explanation: str,
    hint: str,
    misconception: str,
    inputs: tuple[str, ...] = (),
) -> Concept:
    input_note = ""
    if inputs:
        input_note = "\nSimulated input: " + ", ".join(repr(item) for item in inputs)
    prompt = f"What exactly is printed?{input_note}\n\n{code_block(code)}"
    return Concept(
        principle,
        prompt,
        (expected, wrong_1, wrong_2, wrong_3),
        explanation,
        hint,
        misconception,
        stdout_code=code,
        stdout_inputs=inputs,
        stdout_expected=expected,
    )


CONCEPTS: dict[str, Concept] = {
    "PY.EXEC.ORDER": _out(
        "Top-level statements run from top to bottom.",
        'print("A")\nprint("C")',
        "A\nC",
        "C\nA",
        "A C",
        "Nothing",
        "The first print runs before the second one.",
        "Start at the first top-level line.",
        "cannot_locate_top_level_code",
    ),
    "PY.EXEC.DEF_VS_CALL": _out(
        "A def stores instructions; a call runs them.",
        'print("A")\n\ndef hello():\n    print("B")\n\nprint("C")',
        "A\nC",
        "A\nB\nC",
        "B\nC",
        "Nothing",
        "Python defines hello but never reaches a hello() call.",
        "Look for parentheses after the function name.",
        "definition_runs_immediately",
    ),
    "PY.INDENTATION": _q(
        "Indentation tells Python which lines belong to a block.",
        "Which print belongs to the if block?\n\n"
        + code_block('if hp > 0:\n    print("alive")\nprint("done")'),
        'print("alive")',
        'print("done")',
        "Both prints",
        "Neither print",
        "Only the indented print belongs to the if block.",
        "Compare the spaces before each print.",
        "indentation_confusion",
    ),
    "PY.VAR.ASSIGN": _out(
        "Assignment makes a name refer to a value.",
        "damage = 30\nprint(damage)",
        "30",
        "damage",
        "0",
        "Nothing",
        "The name damage refers to the integer 30.",
        "Read the value on the right side of =.",
        "assignment_vs_comparison",
    ),
    "PY.VAR.UPDATE": _out(
        "A later assignment replaces that variable's current value.",
        "x = 5\ny = x\nx = 8\nprint(x)\nprint(y)",
        "8\n5",
        "8\n8",
        "5\n5",
        "5\n8",
        "y received 5 before x changed to 8.",
        "Keep a separate current-value box for x and y.",
        "variable_update_confusion",
    ),
    "PY.TYPE.INT": _q(
        "An int is a whole number such as 7 or -3.",
        "Which value is an int?",
        "7",
        "7.0",
        '"7"',
        "True",
        "7 is a whole-number value, so its type is int.",
        "Look for a number without quotes or a decimal point.",
        "type_confusion",
    ),
    "PY.TYPE.FLOAT": _q(
        "A float is a number with a decimal part.",
        "Which value is a float?",
        "3.5",
        "3",
        '"3.5"',
        "False",
        "The decimal point makes 3.5 a float.",
        "Look for the decimal point.",
        "type_confusion",
    ),
    "PY.TYPE.STRING": _q(
        "A str stores text inside quotes.",
        "Which value is a string?",
        '"rak"',
        "rak",
        "17",
        "True",
        "Quotes make rak text, so the value is a str.",
        "Look for matching quote marks.",
        "type_confusion",
    ),
    "PY.TYPE.BOOL": _q(
        "A bool is exactly True or False.",
        "Which value is a boolean?",
        "False",
        '"False"',
        "0.0",
        "false",
        "False with a capital F and no quotes is a bool.",
        "Python's two boolean values start with capital letters.",
        "type_confusion",
    ),
    "PY.TYPE.COLLECTIONS": _q(
        "Lists, tuples, and dictionaries keep several values.",
        "Which value is a list?",
        '["sword", "axe"]',
        '("sword", "axe")',
        '{"sword": 30}',
        '"sword, axe"',
        "Square brackets create this list of two strings.",
        "Match square brackets with a list.",
        "collection_type_confusion",
    ),
    "PY.IO.PRINT": _out(
        "print sends values to stdout in the order given.",
        'x = 4\nprint("damage:", x)',
        "damage: 4",
        "damage:4",
        "x = 4",
        "damage: x",
        "print separates its two arguments with one space.",
        "Use the value of x, not the letter x.",
        "print_literal_vs_value_confusion",
    ),
    "PY.IO.FSTRING": _out(
        "An f-string replaces brace expressions with their values.",
        'name = "rak"\nhp = 25\nprint(f"{name}: hp = {hp}")',
        "rak: hp = 25",
        "name: hp = hp",
        "{name}: hp = {hp}",
        "rak hp 25",
        "The f prefix makes Python insert name and hp.",
        "Replace each expression in braces with its current value.",
        "fstring_interpolation_confusion",
    ),
    "PY.IO.INPUT": _out(
        "input returns the text typed by the user.",
        'name = input("Name: ")\nprint("Hello", name)',
        "Name: Rak\nHello Rak",
        "Hello name",
        "Name: Hello Rak",
        "Hello Rak\nName:",
        "The prompt is printed first; the simulated input is Rak.",
        "Put the provided input into name before the print call.",
        "input_value_flow_confusion",
        inputs=("Rak",),
    ),
    "PY.IO.CONVERSION": _out(
        "int() and float() convert input text to numbers.",
        'age = int(input("Age: "))\nprint(age + 1)',
        "Age: 10\n11",
        "Age: 10\n101",
        "11",
        "Age: age + 1",
        "int converts the input text '10' to the number 10.",
        "Decide whether + joins text or adds numbers.",
        "conversion_confusion",
        inputs=("10",),
    ),
    "PY.OP.ARITHMETIC": _out(
        "Arithmetic operators calculate a new numeric value.",
        "damage = 12 + 3 * 2\nprint(damage)",
        "18",
        "30",
        "17",
        "12 + 3 * 2",
        "Multiplication happens first: 3 * 2 is 6, then 12 + 6.",
        "Calculate the multiplication before the addition.",
        "arithmetic_order_confusion",
    ),
    "PY.OP.COMPARISON": _out(
        "Comparisons produce True or False; == does not assign.",
        "hp = 20\nprint(hp >= 20)\nprint(hp == 0)",
        "True\nFalse",
        "20\n0",
        "False\nTrue",
        "True\nTrue",
        "20 is at least 20, but it is not equal to 0.",
        "Evaluate each comparison separately.",
        "assignment_vs_comparison",
    ),
    "PY.OP.BOOLEAN": _out(
        "and, or, and not combine or reverse boolean values.",
        "hp = 30\ndefense = 0\nprint(hp > 0 and defense == 0)",
        "True",
        "False",
        "30",
        "0",
        "Both comparisons are True, so True and True is True.",
        "With and, both sides must be True.",
        "boolean_operator_confusion",
    ),
    "PY.OP.MODULO": _out(
        "% gives the remainder and can detect every third count.",
        "turn = 6\nprint(turn % 3)",
        "0",
        "2",
        "3",
        "6",
        "6 divides evenly by 3, leaving remainder 0.",
        "Ask what remains after making groups of 3.",
        "modulo_confusion",
    ),
    "PY.IF.BASIC": _out(
        "if runs its block only when its condition is True.",
        'hp = 20\nif hp > 0:\n    print("alive")\nelse:\n    print("dead")',
        "alive",
        "dead",
        "alive\ndead",
        "Nothing",
        "hp > 0 is True, so only the if block runs.",
        "Evaluate the condition before choosing a branch.",
        "branch_condition_confusion",
    ),
    "PY.IF.ELIF": _out(
        "An if/elif/else chain runs its first True branch only.",
        "hp = 20\n"
        'if hp > 50:\n    print("strong")\n'
        'elif hp > 0:\n    print("weak")\n'
        'else:\n    print("dead")',
        "weak",
        "strong",
        "dead",
        "strong\nweak",
        "The first condition is False and the elif condition is True.",
        "Test the branches from top to bottom and stop at the first True one.",
        "elif_order_confusion",
    ),
    "PY.IF.NESTED": _out(
        "A nested if is tested only after its outer branch is entered.",
        'hp = 5\nshield = 0\nif hp > 0:\n    if shield == 0:\n        print("open")',
        "open",
        "Nothing",
        "5\n0",
        "True",
        "Both the outer and inner conditions are True.",
        "Check the outer condition before the indented inner one.",
        "nested_branch_confusion",
    ),
    "PY.LOOP.WHILE": _out(
        "while repeats its block while its condition stays True.",
        "x = 1\nwhile x <= 3:\n    print(x)\n    x += 1",
        "1\n2\n3",
        "1\n2\n3\n4",
        "1",
        "The loop never stops",
        "The loop prints 1, 2, and 3; then x becomes 4.",
        "Recheck x <= 3 after every update.",
        "loop_condition_confusion",
    ),
    "PY.LOOP.UPDATE": _q(
        "A loop must change something that can end its condition.",
        f"What is wrong with this loop?\n\n{code_block('x = 1\nwhile x < 5:\n    print(x)')}",
        "x never changes, so the loop is infinite",
        "print cannot be used in a loop",
        "x starts too small",
        "while needs an else block",
        "Without x += 1, x < 5 remains True forever.",
        "Find the line that could make the condition become False.",
        "forgot_loop_update",
    ),
    "PY.LOOP.BREAK": _out(
        "break immediately leaves the nearest loop.",
        "x = 1\nwhile True:\n    print(x)\n    if x == 3:\n        break\n    x += 1",
        "1\n2\n3",
        "1\n2",
        "1\n2\n3\n4",
        "The loop never stops",
        "When x is 3, break runs before the next update.",
        "Locate the first moment the break condition is True.",
        "break_confusion",
    ),
    "PY.LOOP.FOR_RANGE": _out(
        "for i in range(3) uses the values 0, 1, and 2.",
        "for i in range(3):\n    print(i)",
        "0\n1\n2",
        "1\n2\n3",
        "0\n1\n2\n3",
        "3",
        "range(3) starts at 0 and stops before 3.",
        "The stop value of range is not included.",
        "range_boundary_confusion",
    ),
    "PY.FUNC.DEFINE": _q(
        "def gives a reusable block a name without running it yet.",
        f"What happens here?\n\n{code_block('def hello():\n    print("hello")')}",
        "The function is defined; nothing is printed",
        "hello is printed",
        "The function runs forever",
        "Python asks for input",
        "The body waits until a later hello() call.",
        "A definition and a call are two different events.",
        "definition_runs_immediately",
    ),
    "PY.FUNC.CALL": _out(
        "A call uses the function name followed by parentheses.",
        'def hello():\n    print("hello")\n\nprint("A")\nhello()\nprint("B")',
        "A\nhello\nB",
        "hello\nA\nB",
        "A\nB",
        "hello",
        "hello() runs the body between the two top-level prints.",
        "Jump into the body when Python reaches hello().",
        "method_call_confusion",
    ),
    "PY.FUNC.PARAMETER": _out(
        "A parameter receives the argument supplied by a call.",
        'def greet(name):\n    print("hello", name)\n\ngreet("rak")',
        "hello rak",
        "hello name",
        "rak hello",
        "Nothing",
        "The argument 'rak' becomes the local parameter name.",
        "Write name = 'rak' when entering the call.",
        "parameter_vs_argument",
    ),
    "PY.FUNC.RETURN": _out(
        "return sends a value back to the place of the call.",
        "def double(x):\n    return x * 2\n\na = double(5)\nprint(a)",
        "10",
        "5",
        "None",
        "x * 2",
        "double(5) returns 10, which is assigned to a.",
        "Replace the call with the value it returns.",
        "return_value_confusion",
    ),
    "PY.FUNC.PRINT_VS_RETURN": _out(
        "print displays a value; without return a function returns None.",
        "def double(x):\n    print(x * 2)\n\na = double(5)\nprint(a)",
        "10\nNone",
        "10",
        "None\n10",
        "5\n10",
        "The function prints 10, then implicitly returns None.",
        "Track displayed output and returned values separately.",
        "print_vs_return",
    ),
    "PY.IMPORT.BASIC": _q(
        "import makes names from another module available.",
        "After import random, which call belongs to that module?",
        "random.randint(1, 6)",
        "randint.random(1, 6)",
        "import.randint(1, 6)",
        "random = randint(1, 6)",
        "The module name comes before the dot.",
        "Read the call as module dot function.",
        "module_function_confusion",
    ),
    "PY.RANDOM.RANDINT": _q(
        "random.randint(a, b) may return either endpoint.",
        "Assume random.randint(1, 6) returns 4. What value is stored?",
        "4",
        "1",
        "6",
        "It cannot be discussed",
        "With the random result supplied, the stored value is exactly 4.",
        "Use the assumed result instead of making a new guess.",
        "random_is_not_predictable",
    ),
    "PY.RANDOM.CHOICE": _q(
        "random.choice picks one existing item from a collection.",
        "Which could random.choice(['sword', 'axe']) return?",
        "sword",
        "mace",
        "sword and axe together",
        "the number 2",
        "choice returns one item that is already in the list.",
        "Look only at the two items inside the brackets.",
        "random_is_not_predictable",
    ),
    "PY.DICT.BASIC": _q(
        "A dictionary maps each key to its value.",
        f"What is weapons['sword']?\n\n{code_block('weapons = {"sword": 30, "axe": 17}')}",
        "30",
        "sword",
        "17",
        "axe",
        "The key 'sword' maps to the value 30.",
        "Find the value after the colon for that key.",
        "dict_key_value_confusion",
    ),
    "PY.DICT.ITEMS": _q(
        ".items() provides the dictionary's key-value pairs.",
        "Which pair comes from weapons.items() for sword damage 30?",
        '("sword", 30)',
        '(30, "sword")',
        '"sword": 30',
        '["sword"]',
        ".items() pairs the key first and its value second.",
        "Keep the key and its matching value together.",
        "dict_key_value_confusion",
    ),
    "PY.TUPLE.BASIC": _q(
        "A tuple can keep a weapon name and damage together.",
        "Which value is the weapon tuple used by Fighting?",
        '("sword", 30)',
        '["sword", 30]',
        '{"sword": 30}',
        '"sword", "damage"',
        "Parentheses hold the two tuple values in order.",
        "Look for one text value and one number inside parentheses.",
        "tuple_structure_confusion",
    ),
    "PY.UNPACKING": _out(
        "Unpacking assigns tuple items to names in order.",
        'weapon = ("sword", 30)\nname, damage = weapon\nprint(name)\nprint(damage)',
        "sword\n30",
        "30\nsword",
        "weapon\nweapon",
        "sword, 30",
        "name receives the first item and damage receives the second.",
        "Match names and tuple items from left to right.",
        "unpacking_order_confusion",
    ),
    "PY.CLASS.CLASS_VS_OBJECT": _q(
        "A class is a blueprint; calling it creates an object.",
        f"Which name is the class?\n\n{code_block('class Cat:\n    pass\n\ncat1 = Cat()')}",
        "Cat",
        "cat1",
        "pass",
        "class",
        "Cat is the blueprint; cat1 is one object created from it.",
        "Find the name immediately after the class keyword.",
        "class_vs_object",
    ),
    "PY.CLASS.INIT": _q(
        "__init__ sets the starting state of each new object.",
        "When does __init__ run for cat1 = Cat('Murka')?",
        "While the new cat1 object is being created",
        "Only when cat1 is printed",
        "Before the class is defined",
        "Once at the end of the whole program",
        "Creating Cat('Murka') calls __init__ for that new object.",
        "Connect object creation with its starting attributes.",
        "init_timing_confusion",
    ),
    "PY.CLASS.SELF": _q(
        "self is the object receiving the current method call.",
        "Inside cat1.show(), what does self refer to?",
        "cat1",
        "the Cat class",
        "the show function",
        "every Cat object",
        "The object before the dot is passed as self.",
        "Read the expression to the left of .show().",
        "self_confusion",
    ),
    "PY.CLASS.ATTRIBUTE": _out(
        "object.attribute reads that object's stored value.",
        "class Cat:\n"
        "    def __init__(self, name):\n"
        "        self.name = name\n\n"
        'cat1 = Cat("Murka")\n'
        "print(cat1.name)",
        "Murka",
        "name",
        "cat1",
        "Cat",
        "__init__ stored 'Murka' in cat1.name.",
        "Trace the value assigned to self.name for cat1.",
        "attribute_lookup_confusion",
    ),
    "PY.CLASS.METHOD": _q(
        "A method call runs behavior belonging to one object.",
        "Which line calls p1's attack method?",
        "p1.attack(p2)",
        "attack.p1(p2)",
        "Player = attack(p1)",
        "p2 = p1.attack",
        "The receiver p1 comes before the dot and attack is called.",
        "Look for object dot method followed by parentheses.",
        "method_call_confusion",
    ),
    "PY.CLASS.MULTIPLE_OBJECTS": _q(
        "Objects made from one class keep independent attributes.",
        "cat1.hp becomes 7. cat2.hp started at 10. What is cat2.hp?",
        "10",
        "7",
        "17",
        "0",
        "Changing cat1.hp does not change cat2.hp.",
        "Keep one state box for each object.",
        "shared_object_state_confusion",
    ),
    "PY.CLASS.STATE_CHANGE": _out(
        "A method can update an object's attributes over time.",
        "class Hero:\n"
        "    def __init__(self):\n"
        "        self.hp = 10\n"
        "    def hurt(self):\n"
        "        self.hp -= 3\n\n"
        "h = Hero()\n"
        "h.hurt()\n"
        "print(h.hp)",
        "7",
        "10",
        "3",
        "13",
        "hurt subtracts 3 from this hero's stored hp.",
        "Update the existing hp value instead of creating a new hero.",
        "object_state_change_confusion",
    ),
    "PY.CLASS.SELF_OTHER": _q(
        "In p1.attack(p2), self is p1 and other is p2.",
        "Inside p1.attack(p2), which object is other?",
        "p2",
        "p1",
        "Player",
        "attack",
        "p1 receives the call as self; p2 is the explicit argument.",
        "Separate the object before the dot from the object in parentheses.",
        "self_other_confusion",
    ),
    "GAME.STRUCTURE": _q(
        "Definitions come first; object creation and the loop run the game.",
        "Which part repeatedly controls turns in Fighting?",
        "The main while loop",
        "The import statement",
        "The class name",
        "A comment above Player",
        "The class defines behavior, while the main while loop repeats turns.",
        "Find the top-level code that can run more than once.",
        "cannot_locate_top_level_code",
    ),
    "GAME.PLAYER_STATE": _q(
        "p1 and p2 each have their own hp, damage, and defense.",
        "p2.hp changes after p1 attacks. Which HP stays unchanged?",
        "p1.hp",
        "p2.hp",
        "Both HP values",
        "Neither HP value",
        "The target p2 changes; the attacker p1 keeps its HP.",
        "Identify the attacker and the target before changing state.",
        "shared_object_state_confusion",
    ),
    "GAME.WEAPON_SELECTION": _q(
        "An empty weapon tuple triggers one choice, then stores it.",
        "What if choose_attack() runs on every attack?",
        "The player could get a different weapon each turn",
        "The stored weapon becomes faster",
        "Defense always becomes zero",
        "The loop stops after one turn",
        "Storing self.weapon lets later attacks reuse the first choice.",
        "Compare choosing once with choosing inside every attack.",
        "weapon_storage_confusion",
    ),
    "GAME.ARMOR_DAMAGE": _q(
        "Damage removes defense first; negative overflow removes HP.",
        "HP is 600, defense is 100, and damage is 180. Final state?",
        "HP 520, defense 0",
        "HP 420, defense 100",
        "HP 600, defense -80",
        "HP 500, defense 0",
        "Defense absorbs 100; the remaining 80 reduces HP to 520.",
        "Subtract damage from defense, then move only the negative remainder.",
        "armor_hp_overflow_confusion",
    ),
    "GAME.MAIN_LOOP": _q(
        "The combat while loop repeats while both players are alive.",
        "Which condition keeps combat going?",
        "p1.hp > 0 and p2.hp > 0",
        "p1.hp > 0 or p2.hp > 0",
        "p1.hp == p2.hp",
        "p1.weapon == ()",
        "Both players must have HP above zero for another turn.",
        "Ask whether combat should continue after either player reaches zero.",
        "loop_condition_confusion",
    ),
    "GAME.INITIATIVE": _q(
        "Initiative must be compared before the attacker is selected.",
        "p1 initiative is 8 and p2 initiative is 3. Who is selected?",
        "p1",
        "p2",
        "Both attack at once",
        "A new Player is required",
        "The larger current initiative belongs to p1.",
        "Use the values that exist at the decision point.",
        "initiative_timing_confusion",
    ),
    "GAME.DEBUG_INITIATIVE": _q(
        "Roll initiative in the main loop before choosing an attacker.",
        "p1.attack(p2) has started, then initiative changes. Who attacks now?",
        "p1; the call is already executing",
        "p2; its new initiative is larger",
        "Both players restart",
        "No one; initiative cannot change",
        "New values cannot switch a method call already in progress.",
        "Separate choosing the call from code that runs inside the call.",
        "initiative_timing_confusion",
    ),
    "GAME.CRITICAL_COUNTER": _q(
        "Store turns per player and test turns % 3 == 0.",
        "Which condition detects every third attack?",
        "self.turns % 3 == 0",
        "self.turns / 3 == 0",
        "turns == 3 forever",
        "p1.turns == p2.turns",
        "Multiples of 3 have remainder zero when divided by 3.",
        "Use the remainder sequence 1, 2, 0.",
        "modulo_confusion",
    ),
}


STDOUT_SKILLS = tuple(key for key, concept in CONCEPTS.items() if concept.stdout_code)


_RECOGNITION_DISTRACTORS = (
    "Каждый блок с отступом выполняется сразу.",
    "Все переменные и объекты всегда хранят одно значение.",
    "Порядок строк никогда не влияет на результат.",
)


def question_parts(skill_key: str, question_type: str) -> QuestionParts:
    try:
        concept = CONCEPTS[skill_key]
    except KeyError as exc:
        raise ValueError(f"unknown Python Foundations skill: {skill_key}") from exc
    rule, explanation, hint = DETAILS[skill_key]
    check = CHECKS.get(skill_key)
    code = concept.stdout_code if concept.stdout_code is not None else check.code if check else None
    if code is None:
        raise ValueError(f"missing code context for {skill_key}")
    if question_type == "recognize":
        return QuestionParts(
            prompt=f"Какое правило помогает понять этот код?\n\n{code_block(code)}",
            answers=(rule, *_RECOGNITION_DISTRACTORS),
            explanation=explanation,
            hints=(hint, rule),
            misconception=concept.misconception,
            difficulty_level=1,
        )
    if question_type == "predict":
        if concept.stdout_code is None:
            assert check is not None
            prompt = f"{check.question}\n\n{code_block(check.code)}"
            answers = check.answers
        else:
            input_note = ""
            if concept.stdout_inputs:
                values = ", ".join(repr(value) for value in concept.stdout_inputs)
                input_note = f"\nВвод пользователя: {values}."
            prompt = f"Что точно выведет программа?{input_note}\n\n{code_block(code)}"
            answers = localized_output_answers(concept.check_answers)
        return QuestionParts(
            prompt=prompt,
            answers=answers,
            explanation=explanation,
            hints=(hint, rule, explanation),
            misconception=concept.misconception,
            difficulty_level=2,
            stdout_code=concept.stdout_code,
            stdout_inputs=concept.stdout_inputs,
            stdout_expected=concept.stdout_expected,
        )
    if question_type == "apply":
        edit = EDITS[skill_key]
        return QuestionParts(
            prompt=f"{edit.question}\n\n{code_block(edit.code)}",
            answers=edit.answers,
            explanation=explanation,
            hints=(hint, rule, explanation),
            misconception=concept.misconception,
            difficulty_level=3,
        )
    raise ValueError(f"unsupported question type: {question_type}")
