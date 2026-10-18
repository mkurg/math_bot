"""Student-facing Russian copy and complete code contexts for every Python skill."""

# ruff: noqa: E501 -- Each compact row is one independently reviewable exercise.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Check:
    code: str
    question: str
    answers: tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class Edit:
    code: str
    question: str
    answers: tuple[str, str, str, str]


# (short rule, explanation after an answer, first hint). Skill IDs remain stable
# so existing mastery and attempts retain their meaning after the copy changes.
DETAILS: dict[str, tuple[str, str, str]] = {
    "PY.EXEC.ORDER": (
        "Строки верхнего уровня выполняются сверху вниз.",
        "Сначала выполняется первый print, затем второй.",
        "Проследи строки по порядку.",
    ),
    "PY.EXEC.DEF_VS_CALL": (
        "def создаёт функцию; тело запускает вызов.",
        "Тело hello не выполняется, пока нет hello().",
        "Найди вызов с круглыми скобками.",
    ),
    "PY.INDENTATION": (
        "Отступ определяет границы блока.",
        "В блок if входит только строка с отступом.",
        "Сравни отступы перед print.",
    ),
    "PY.VAR.ASSIGN": (
        "Присваивание сохраняет значение под именем.",
        "damage получает число 30.",
        "Прочитай значение справа от знака =.",
    ),
    "PY.VAR.UPDATE": (
        "Новое присваивание меняет значение одной переменной.",
        "y получило 5 до изменения x; поэтому y осталось равным 5.",
        "Следи за x и y по отдельности.",
    ),
    "PY.TYPE.INT": (
        "int — целое число.",
        "У 7 нет кавычек и десятичной точки.",
        "Сравни запись значений.",
    ),
    "PY.TYPE.FLOAT": (
        "float — число с десятичной частью.",
        "3.5 — значение типа float.",
        "Найди число с десятичной точкой.",
    ),
    "PY.TYPE.STRING": (
        "str хранит текст в кавычках.",
        "Кавычки превращают rak в строку.",
        "Проверь кавычки.",
    ),
    "PY.TYPE.BOOL": (
        "bool имеет значения True и False.",
        "False без кавычек — логическое значение.",
        "В Python первая буква заглавная.",
    ),
    "PY.TYPE.COLLECTIONS": (
        "Список записывают в квадратных скобках.",
        "Квадратные скобки создают список.",
        "Сравни виды скобок.",
    ),
    "PY.IO.PRINT": (
        "print выводит значения с пробелом между аргументами.",
        "x равно 4, а print разделяет аргументы пробелом.",
        "Подставь значение x.",
    ),
    "PY.IO.FSTRING": (
        "f-строка подставляет значения выражений в фигурных скобках.",
        "Вместо name и hp подставляются rak и 25.",
        "Замени выражения в фигурных скобках.",
    ),
    "PY.IO.INPUT": (
        "input возвращает введённый текст.",
        "Сначала виден запрос, затем введённое имя используется в print.",
        "Подставь указанный ввод в name.",
    ),
    "PY.IO.CONVERSION": (
        "int() переводит текст ввода в целое число.",
        "После int текст 10 становится числом 10, поэтому 10 + 1 равно 11.",
        "Определи тип значения перед сложением.",
    ),
    "PY.OP.ARITHMETIC": (
        "Умножение выполняется раньше сложения.",
        "Сначала 3 * 2 = 6, затем 12 + 6 = 18.",
        "Начни с умножения.",
    ),
    "PY.OP.COMPARISON": (
        "Сравнение == возвращает True или False.",
        "20 >= 20 истинно, а 20 == 0 ложно.",
        "Проверь каждое сравнение отдельно.",
    ),
    "PY.OP.BOOLEAN": (
        "and требует истинности обеих частей.",
        "Оба сравнения истинны, поэтому результат True.",
        "Вычисли обе стороны and.",
    ),
    "PY.OP.MODULO": (
        "% возвращает остаток от деления.",
        "6 делится на 3 без остатка.",
        "Раздели число на группы по три.",
    ),
    "PY.IF.BASIC": (
        "if выполняет блок при истинном условии.",
        "hp больше нуля, поэтому выполняется первая ветка.",
        "Сначала вычисли условие.",
    ),
    "PY.IF.ELIF": (
        "В цепочке if/elif/else выполняется первая подходящая ветка.",
        "Первое условие ложно, второе истинно.",
        "Проверяй ветки сверху вниз.",
    ),
    "PY.IF.NESTED": (
        "Внутренний if проверяется только после внешнего.",
        "Оба условия истинны, поэтому выполняется print.",
        "Сначала проверь внешний if.",
    ),
    "PY.LOOP.WHILE": (
        "while повторяется, пока условие истинно.",
        "Печатаются 1, 2 и 3; затем x становится 4.",
        "После изменения x проверь условие снова.",
    ),
    "PY.LOOP.UPDATE": (
        "Счётчик должен изменяться внутри цикла.",
        "Без изменения x условие остаётся истинным.",
        "Проверь, изменяется ли x.",
    ),
    "PY.LOOP.BREAK": (
        "break немедленно завершает ближайший цикл.",
        "После вывода 3 срабатывает break.",
        "Найди момент выполнения break.",
    ),
    "PY.LOOP.FOR_RANGE": (
        "range(3) даёт 0, 1 и 2.",
        "Правая граница range не включается.",
        "Начни с нуля.",
    ),
    "PY.FUNC.DEFINE": (
        "Определение функции не запускает её тело.",
        "Без вызова hello() ничего не печатается.",
        "Найди вызов функции.",
    ),
    "PY.FUNC.CALL": (
        "Вызов запускает тело функции в указанном месте.",
        "hello() выполняется между двумя print.",
        "Следи за вызовом сверху вниз.",
    ),
    "PY.FUNC.PARAMETER": (
        "Аргумент вызова становится значением параметра.",
        "Строка rak передаётся в параметр name.",
        "Подставь аргумент в параметр.",
    ),
    "PY.FUNC.RETURN": (
        "return передаёт значение обратно в место вызова.",
        "double(5) возвращает 10.",
        "Замени вызов возвращаемым значением.",
    ),
    "PY.FUNC.PRINT_VS_RETURN": (
        "print выводит значение; без return функция возвращает None.",
        "Функция печатает 10, затем переменная a получает None.",
        "Отдели вывод от возвращаемого значения.",
    ),
    "PY.IMPORT.BASIC": (
        "import подключает модуль.",
        "Функция randint находится внутри модуля random.",
        "Прочитай запись как модуль.функция.",
    ),
    "PY.RANDOM.RANDINT": (
        "randint(a, b) может вернуть обе границы.",
        "В задаче результат случайного вызова задан явно: 4.",
        "Используй заданный результат.",
    ),
    "PY.RANDOM.CHOICE": (
        "choice выбирает один элемент из списка.",
        "sword уже находится в списке.",
        "Смотри только на элементы списка.",
    ),
    "PY.DICT.BASIC": (
        "Словарь связывает ключ со значением.",
        "Ключу sword соответствует число 30.",
        "Найди значение после двоеточия.",
    ),
    "PY.DICT.ITEMS": (
        ".items() даёт пары ключ—значение.",
        "В каждой паре сначала ключ, затем его значение.",
        "Сохрани ключ и значение вместе.",
    ),
    "PY.TUPLE.BASIC": (
        "Кортеж хранит несколько значений в порядке.",
        "Имя оружия и урон вместе образуют пару.",
        "Сравни скобки и порядок значений.",
    ),
    "PY.UNPACKING": (
        "Распаковка присваивает элементы слева направо.",
        "name получает sword, damage получает 30.",
        "Соедини имена с элементами по порядку.",
    ),
    "PY.CLASS.CLASS_VS_OBJECT": (
        "Класс описывает объекты; вызов класса создаёт объект.",
        "Cat — имя класса, cat1 — созданный объект.",
        "Найди имя после class.",
    ),
    "PY.CLASS.INIT": (
        "__init__ задаёт начальное состояние нового объекта.",
        "Создание Cat вызывает __init__ именно для нового объекта.",
        "Свяжи создание объекта с его начальными атрибутами.",
    ),
    "PY.CLASS.SELF": (
        "self обозначает объект текущего вызова метода.",
        "В cat1.show() объект слева от точки — cat1.",
        "Посмотри налево от точки.",
    ),
    "PY.CLASS.ATTRIBUTE": (
        "Атрибут хранит значение отдельного объекта.",
        "При создании cat1 имя Murka сохраняется в cat1.name.",
        "Проследи присваивание self.name.",
    ),
    "PY.CLASS.METHOD": (
        "Вызов метода запускает действие объекта.",
        "В p1.attack(p2) метод attack вызван у p1.",
        "Найди объект слева от точки.",
    ),
    "PY.CLASS.MULTIPLE_OBJECTS": (
        "Разные объекты хранят независимые атрибуты.",
        "Изменение cat1.hp не меняет cat2.hp.",
        "Веди состояние каждого объекта отдельно.",
    ),
    "PY.CLASS.STATE_CHANGE": (
        "Метод может изменять атрибут объекта.",
        "hurt уменьшает hp с 10 до 7.",
        "Обнови прежнее значение hp.",
    ),
    "PY.CLASS.SELF_OTHER": (
        "В p1.attack(p2) self — p1, other — p2.",
        "Объект слева от точки получает роль self; аргумент — роль other.",
        "Раздели объект слева от точки и аргумент.",
    ),
    "GAME.STRUCTURE": (
        "Игра начинается с определений, объектов и главного цикла.",
        "Повторением ходов управляет while верхнего уровня.",
        "Найди верхнеуровневый цикл.",
    ),
    "GAME.PLAYER_STATE": (
        "p1 и p2 хранят состояние отдельно.",
        "Атакующий p1 не теряет HP при изменении p2.hp.",
        "Отметь атакующего и цель.",
    ),
    "GAME.WEAPON_SELECTION": (
        "Выбранное оружие хранится для следующих атак.",
        "Если выбирать заново каждый ход, оружие может меняться.",
        "Сравни первый и следующий вызовы.",
    ),
    "GAME.ARMOR_DAMAGE": (
        "Урон сначала снижает защиту, остаток снижает HP.",
        "Защита поглощает 100, оставшиеся 80 уменьшают HP до 520.",
        "Сначала вычти урон из защиты.",
    ),
    "GAME.MAIN_LOOP": (
        "Бой продолжается, пока живы оба игрока.",
        "and останавливает цикл, когда HP любого игрока достигает нуля.",
        "Проверь состояние обоих игроков.",
    ),
    "GAME.INITIATIVE": (
        "Инициативу сравнивают до выбора атакующего.",
        "8 больше 3, поэтому атакует p1.",
        "Используй значения в момент выбора.",
    ),
    "GAME.DEBUG_INITIATIVE": (
        "Бросок инициативы должен предшествовать выбору атакующего.",
        "Начавшийся вызов p1.attack(p2) не меняет атакующего после нового броска.",
        "Отдели решение о вызове от тела метода.",
    ),
    "GAME.CRITICAL_COUNTER": (
        "Счётчик атак принадлежит каждому игроку.",
        "Каждый третий номер делится на 3 без остатка.",
        "Посмотри на остатки 1, 2, 0.",
    ),
}


# These skills are not stdout exercises. Each still shows the entire fragment
# needed to answer, rather than relying on an unseen program or previous card.
CHECKS: dict[str, Check] = {
    "PY.INDENTATION": Check(
        'hp = 5\nif hp > 0:\n    print("жив")\nprint("конец")',
        "Какая строка находится внутри if?",
        ('print("жив")', 'print("конец")', "Обе строки print", "Ни одна строка"),
    ),
    "PY.TYPE.INT": Check(
        "value = 7\nprint(type(value).__name__)",
        "Какой тип у value?",
        ("int", "float", "str", "bool"),
    ),
    "PY.TYPE.FLOAT": Check(
        "value = 3.5\nprint(type(value).__name__)",
        "Какой тип у value?",
        ("float", "int", "str", "bool"),
    ),
    "PY.TYPE.STRING": Check(
        'value = "rak"\nprint(type(value).__name__)',
        "Какой тип у value?",
        ("str", "int", "float", "bool"),
    ),
    "PY.TYPE.BOOL": Check(
        "value = False\nprint(type(value).__name__)",
        "Какой тип у value?",
        ("bool", "str", "int", "float"),
    ),
    "PY.TYPE.COLLECTIONS": Check(
        'weapons = ["sword", "axe"]\nprint(type(weapons).__name__)',
        "Какой тип у weapons?",
        ("list", "tuple", "dict", "str"),
    ),
    "PY.LOOP.UPDATE": Check(
        "x = 1\nwhile x < 5:\n    print(x)",
        "Почему цикл не заканчивается?",
        (
            "x не изменяется",
            "print нельзя вызывать в цикле",
            "x должен начинаться с 5",
            "для while нужен else",
        ),
    ),
    "PY.FUNC.DEFINE": Check(
        'def hello():\n    print("привет")',
        "Что появится при запуске этого файла?",
        ("Ничего", "привет", "hello", "Ошибка ввода"),
    ),
    "PY.IMPORT.BASIC": Check(
        "import random\nnumber = random.randint(1, 6)",
        "Какая запись вызывает функцию из модуля?",
        (
            "random.randint(1, 6)",
            "randint.random(1, 6)",
            "import.randint(1, 6)",
            "random = randint(1, 6)",
        ),
    ),
    "PY.RANDOM.RANDINT": Check(
        "import random\nroll = random.randint(1, 6)\nprint(roll)",
        "Предположим, randint вернул 4. Что выведет print?",
        ("4", "1", "6", "Определить невозможно"),
    ),
    "PY.RANDOM.CHOICE": Check(
        'import random\nweapons = ["sword", "axe"]\nweapon = random.choice(weapons)',
        "Каким может быть weapon?",
        ("sword", "mace", "sword и axe одновременно", "2"),
    ),
    "PY.DICT.BASIC": Check(
        'weapons = {"sword": 30, "axe": 17}\nprint(weapons["sword"])',
        "Что выведет print?",
        ("30", "sword", "17", "axe"),
    ),
    "PY.DICT.ITEMS": Check(
        'weapons = {"sword": 30}\nfor name, damage in weapons.items():\n    print(name, damage)',
        "Что выведет print?",
        ("sword 30", "30 sword", "sword", "30"),
    ),
    "PY.TUPLE.BASIC": Check(
        'weapon = ("sword", 30)\nprint(type(weapon).__name__)',
        "Какой тип у weapon?",
        ("tuple", "list", "dict", "str"),
    ),
    "PY.CLASS.CLASS_VS_OBJECT": Check(
        "class Cat:\n    pass\n\ncat1 = Cat()",
        "Как называется класс?",
        ("Cat", "cat1", "pass", "class"),
    ),
    "PY.CLASS.INIT": Check(
        'class Cat:\n    def __init__(self, name):\n        self.name = name\n\ncat1 = Cat("Мурка")',
        "Когда выполнится __init__?",
        ("При создании cat1", "При печати cat1", "До объявления class", "В конце программы"),
    ),
    "PY.CLASS.SELF": Check(
        'class Cat:\n    def show(self):\n        print("мяу")\n\ncat1 = Cat()\ncat1.show()',
        "Какой объект обозначает self внутри show?",
        ("cat1", "класс Cat", "метод show", "все объекты Cat"),
    ),
    "PY.CLASS.METHOD": Check(
        "class Player:\n    def __init__(self):\n        self.hp = 10\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()\np1.attack(p2)",
        "Чей метод attack выполняется?",
        ("p1", "p2", "класса без объекта", "обоих игроков"),
    ),
    "PY.CLASS.MULTIPLE_OBJECTS": Check(
        "class Cat:\n    def __init__(self):\n        self.hp = 10\n\ncat1 = Cat()\ncat2 = Cat()\ncat1.hp = 7\nprint(cat2.hp)",
        "Что выведет print?",
        ("10", "7", "17", "0"),
    ),
    "PY.CLASS.SELF_OTHER": Check(
        "class Cat:\n    def __init__(self):\n        self.hp = 10\n    def hit(self, other):\n        other.hp -= 1\n\ncat1 = Cat()\ncat2 = Cat()\ncat1.hit(cat2)",
        "Какой объект обозначает other внутри hit?",
        ("cat2", "cat1", "класс Cat", "метод hit"),
    ),
    "GAME.STRUCTURE": Check(
        "class Player:\n    def __init__(self):\n        self.hp = 2\n    def attack(self, other):\n        other.hp -= 1\n\np1 = Player()\np2 = Player()\nwhile p1.hp > 0 and p2.hp > 0:\n    p1.attack(p2)",
        "Какая часть повторяет ходы?",
        ("цикл while", "объявление class", "создание p1", "объявление метода"),
    ),
    "GAME.PLAYER_STATE": Check(
        "class Player:\n    def __init__(self):\n        self.hp = 20\n\np1 = Player()\np2 = Player()\np2.hp -= 5\nprint(p1.hp, p2.hp)",
        "Какие значения будут выведены?",
        ("20 15", "15 15", "15 20", "20 20"),
    ),
    "GAME.WEAPON_SELECTION": Check(
        'class Player:\n    def __init__(self):\n        self.weapon = ()\n    def choose_attack(self):\n        return ("sword", 30)\n    def attack(self):\n        if self.weapon == ():\n            self.weapon = self.choose_attack()\n        return self.weapon\n\np1 = Player()\np1.attack()\np1.attack()',
        "Что произойдёт при второй атаке?",
        (
            "Сохранённое оружие используется снова",
            "Оружие выбирается заново",
            "Цикл завершится",
            "Защита станет нулём",
        ),
    ),
    "GAME.ARMOR_DAMAGE": Check(
        "hp = 600\ndefense = 100\ndefense -= 180\nif defense < 0:\n    hp += defense\n    defense = 0\nprint(hp, defense)",
        "Какие значения будут выведены?",
        ("520 0", "420 100", "600 -80", "500 0"),
    ),
    "GAME.MAIN_LOOP": Check(
        'class Player:\n    def __init__(self, hp):\n        self.hp = hp\n    def attack(self, other):\n        other.hp -= 1\n\np1 = Player(10)\np2 = Player(0)\nwhile p1.hp > 0 and p2.hp > 0:\n    p1.attack(p2)\nprint("конец")',
        "Выполнится ли атака?",
        ("Нет, цикл не начнётся", "Да, один раз", "Да, пока жив p1", "Цикл бесконечный"),
    ),
    "GAME.INITIATIVE": Check(
        'class Player:\n    def __init__(self, initiative):\n        self.iniciativa = initiative\n    def attack(self, other):\n        print("атака")\n\np1 = Player(8)\np2 = Player(3)\nif p1.iniciativa > p2.iniciativa:\n    p1.attack(p2)\nelse:\n    p2.attack(p1)',
        "Кто атакует?",
        ("p1", "p2", "оба", "нужен новый Player"),
    ),
    "GAME.DEBUG_INITIATIVE": Check(
        'class Player:\n    def __init__(self, initiative):\n        self.iniciativa = initiative\n    def attack(self, other):\n        self.iniciativa = 2\n        other.iniciativa = 9\n        print("атака")\n\np1 = Player(8)\np2 = Player(3)\nif p1.iniciativa > p2.iniciativa:\n    p1.attack(p2)',
        "После нового броска внутри attack кто атакует?",
        ("p1", "p2", "оба начинают заново", "никто"),
    ),
    "GAME.CRITICAL_COUNTER": Check(
        "class Player:\n    def __init__(self):\n        self.turns = 0\n        self.hp = 20\n    def attack(self, other):\n        self.turns += 1\n        if self.turns % 3 == 0:\n            other.hp -= 5\n\np1 = Player()\np2 = Player()\nfor _ in range(3):\n    p1.attack(p2)",
        "При каком номере атаки впервые сработает ветка if?",
        ("3", "1", "2", "4"),
    ),
}


# A different, self-contained program for the construction/debugging level.
# The code is always shown before asking for a missing or changed line.
EDITS: dict[str, Edit] = {
    "PY.EXEC.ORDER": Edit(
        'print("A")\nprint("B")',
        "Как сделать так, чтобы сначала вывелось B?",
        (
            "Поменять строки print местами",
            "Добавить def перед первым print",
            "Заменить print на input",
            "Добавить else",
        ),
    ),
    "PY.EXEC.DEF_VS_CALL": Edit(
        'def hello():\n    print("привет")\n\nprint("готово")',
        "Какую строку добавить после определения функции, чтобы увидеть привет?",
        ("hello()", "def hello", "print = hello", "return hello"),
    ),
    "PY.INDENTATION": Edit(
        'hp = 5\nif hp > 0:\n    print("жив")\nprint("конец")',
        "Как сделать, чтобы конец печаталось только при hp > 0?",
        (
            'Добавить отступ перед print("конец")',
            'Убрать отступ перед print("жив")',
            "Заменить if на def",
            "Убрать двоеточие",
        ),
    ),
    "PY.VAR.ASSIGN": Edit(
        "damage = 0\nprint(damage)",
        "Какую строку изменить, чтобы вывести 30?",
        ("damage = 30", "damage == 30", "print = 30", "30 = damage"),
    ),
    "PY.VAR.UPDATE": Edit(
        "x = 5\ny = x\nx = 8\nprint(y)",
        "Как изменить y вместе с x?",
        (
            "После x = 8 добавить y = x",
            "Убрать print(y)",
            "Заменить x = 8 на x == 8",
            "Добавить print(x)",
        ),
    ),
    "PY.TYPE.INT": Edit(
        'score = "7"\nprint(score + 1)',
        "Как получить число 8 без ошибки?",
        ('score = int("7")', 'score = str("7")', 'score == "7"', 'score = "7" + 1'),
    ),
    "PY.TYPE.FLOAT": Edit(
        "price = 3\nprint(price / 2)",
        "Как явно записать price как float?",
        ("price = 3.0", 'price = "3"', "price == 3", "price = True"),
    ),
    "PY.TYPE.STRING": Edit(
        "name = rak\nprint(name)",
        "Как сохранить слово rak как строку?",
        ('name = "rak"', "name = rak()", "name == rak", "str = rak"),
    ),
    "PY.TYPE.BOOL": Edit(
        'alive = "False"\nif alive:\n    print("да")',
        "Как сохранить именно логическое False?",
        ("alive = False", 'alive = "false"', "alive = 0.0", "alive == False"),
    ),
    "PY.TYPE.COLLECTIONS": Edit(
        'weapons = ("sword", "axe")\nprint(type(weapons).__name__)',
        "Как сделать weapons списком?",
        (
            'weapons = ["sword", "axe"]',
            'weapons = {"sword": "axe"}',
            'weapons = "sword, axe"',
            "weapons = True",
        ),
    ),
    "PY.IO.PRINT": Edit(
        'hp = 20\nprint("hp")',
        "Как вывести значение переменной hp?",
        ("print(hp)", 'print("hp")', "hp.print()", "print = hp"),
    ),
    "PY.IO.FSTRING": Edit(
        'name = "rak"\nhp = 25\nprint("name: hp = hp")',
        "Как подставить оба значения?",
        (
            'print(f"{name}: hp = {hp}")',
            'print("name: hp = hp")',
            'print(f"name: hp = hp")',
            "print({name}, {hp})",
        ),
    ),
    "PY.IO.INPUT": Edit(
        'name = ""\nprint("Привет", name)',
        "Как получить имя от пользователя?",
        ('name = input("Имя: ")', 'input = name("Имя: ")', "print(name)", "name == input"),
    ),
    "PY.IO.CONVERSION": Edit(
        'age = input("Возраст: ")\nprint(age + 1)',
        "Как исправить сложение текста и числа?",
        (
            'age = int(input("Возраст: "))',
            'age = input(int("Возраст: "))',
            'age == input("Возраст: ")',
            "int = age(input())",
        ),
    ),
    "PY.OP.ARITHMETIC": Edit(
        "damage = 12 + 3 * 2\nprint(damage)",
        "Как получить 30, сначала сложив 12 и 3?",
        ("damage = (12 + 3) * 2", "damage = 12 + (3 * 2)", "damage = 12 + 3 + 2", "damage == 30"),
    ),
    "PY.OP.COMPARISON": Edit(
        'hp = 0\nif hp = 0:\n    print("конец")',
        "Как исправить условие?",
        ("if hp == 0:", "if hp = 0:", "if hp != 0:", "0 = hp"),
    ),
    "PY.OP.BOOLEAN": Edit(
        'hp = 10\ndefense = 0\nif hp > 0 or defense > 0:\n    print("можно")',
        "Как потребовать выполнения обоих условий?",
        ("Заменить or на and", "Заменить if на print", "Заменить > на =", "Убрать defense"),
    ),
    "PY.OP.MODULO": Edit(
        'turns = 6\nif turns == 3:\n    print("критический")',
        "Как узнавать каждую третью атаку, а не только третью?",
        ("if turns % 3 == 0:", "if turns / 3 == 0:", "if turns == 3:", "if turns % 2 == 0:"),
    ),
    "PY.IF.BASIC": Edit(
        'hp = 0\nif hp > 0:\n    print("жив")',
        "Как вывести конец, если hp не больше нуля?",
        (
            'Добавить else:\n    print("конец")',
            "Заменить if на while",
            'Добавить print("конец") внутри if',
            "Убрать условие",
        ),
    ),
    "PY.IF.ELIF": Edit(
        'hp = 20\nif hp > 50:\n    print("сильный")\nelse:\n    print("побеждён")',
        "Как отдельно обработать живого игрока с hp от 1 до 50?",
        (
            "Добавить elif hp > 0: перед else",
            "Заменить else на def",
            "Добавить второй if после else",
            "Убрать hp > 50",
        ),
    ),
    "PY.IF.NESTED": Edit(
        'hp = 5\nshield = 0\nif hp > 0:\n    print("жив")',
        "Как вывести без щита только если оба условия выполнены?",
        (
            'Внутри if добавить if shield == 0:\n    print("без щита")',
            "Поставить print до if",
            "Заменить hp > 0 на shield = 0",
            "Добавить while True",
        ),
    ),
    "PY.LOOP.WHILE": Edit(
        "x = 1\nwhile x <= 3:\n    print(x)\n    x += 1",
        "Как остановиться после вывода 2?",
        (
            "Заменить x <= 3 на x <= 2",
            "Убрать x += 1",
            "Заменить while на if",
            "Добавить x = 1 внутри цикла",
        ),
    ),
    "PY.LOOP.UPDATE": Edit(
        "x = 1\nwhile x < 5:\n    print(x)",
        "Какая строка внутри цикла завершит счёт?",
        ("x += 1", "x == 1", "x + 1", "x = 1"),
    ),
    "PY.LOOP.BREAK": Edit(
        "x = 1\nwhile True:\n    print(x)\n    x += 1",
        "Как завершить цикл при x == 4 до следующего вывода?",
        (
            "После x += 1 добавить if x == 4: break",
            "Убрать print(x)",
            "Добавить x == 4",
            "Заменить True на False",
        ),
    ),
    "PY.LOOP.FOR_RANGE": Edit(
        "for i in range(3):\n    print(i)",
        "Как вывести ещё и число 3?",
        (
            "Заменить range(3) на range(4)",
            "Заменить range(3) на range(2)",
            "Заменить for на if",
            "Убрать отступ",
        ),
    ),
    "PY.FUNC.DEFINE": Edit(
        'print("привет")\nprint("привет")',
        "Как объединить повторение в функцию без её запуска при определении?",
        (
            'def hello():\n    print("привет")',
            'hello = print("привет")',
            "def hello",
            "return hello",
        ),
    ),
    "PY.FUNC.CALL": Edit(
        'def shout(word):\n    print(word)\n\nprint("готово")',
        "Как вызвать shout со словом привет?",
        ('shout("привет")', 'def shout("привет")', 'shout["привет"]', "print = shout"),
    ),
    "PY.FUNC.PARAMETER": Edit(
        'def greet():\n    print("Привет", name)\n\ngreet("Миша")',
        "Как передать имя в функцию?",
        ("def greet(name):", "def greet(): name", "greet = def(name)", "def name(greet):"),
    ),
    "PY.FUNC.RETURN": Edit(
        "def double(x):\n    print(x * 2)\n\na = double(5)\nprint(a)",
        "Как передать 10 в переменную a?",
        (
            "Заменить print(x * 2) на return x * 2",
            "Добавить второй print(x * 2)",
            "Убрать вызов double(5)",
            "Заменить x на None",
        ),
    ),
    "PY.FUNC.PRINT_VS_RETURN": Edit(
        "def double(x):\n    print(x * 2)\n\na = double(5)\nprint(a)",
        "Как сделать результатом вывода только 10?",
        (
            "Заменить print(x * 2) на return x * 2",
            "Убрать print(a)",
            "Добавить ещё один print(x * 2)",
            "Заменить a на None",
        ),
    ),
    "PY.IMPORT.BASIC": Edit(
        "number = random.randint(1, 6)\nprint(number)",
        "Какую строку добавить в начало?",
        ("import random", "random = import", "import randint.random", "def random"),
    ),
    "PY.RANDOM.RANDINT": Edit(
        "import random\n\ndef d6():\n    return 0",
        "Как возвращать целое число от 1 до 6?",
        (
            "return random.randint(1, 6)",
            "return random.randint(6)",
            "return randint.random(1, 6)",
            "return random.choice(1, 6)",
        ),
    ),
    "PY.RANDOM.CHOICE": Edit(
        'import random\nweapons = ["sword", "axe"]\nweapon = weapons',
        "Как сохранить в weapon один случайный элемент?",
        (
            "weapon = random.choice(weapons)",
            "weapon = random.randint(weapons)",
            "weapon = random.choice(2)",
            "weapon = weapons.items()",
        ),
    ),
    "PY.DICT.BASIC": Edit(
        'weapons = {}\nprint(weapons["sword"])',
        "Как добавить урон меча до print?",
        (
            'weapons["sword"] = 30',
            'weapons["sword"] == 30',
            'weapons = ["sword", 30]',
            "weapons[30] = 30",
        ),
    ),
    "PY.DICT.ITEMS": Edit(
        'weapons = {"sword": 30}\nfor pair in weapons:\n    print(pair)',
        "Как пройти по парам ключ—значение?",
        (
            "for pair in weapons.items():",
            "for pair in weapons.values:",
            "for pair in weapons.keys:",
            "for pair in weapons[0]:",
        ),
    ),
    "PY.TUPLE.BASIC": Edit(
        'name = "sword"\ndamage = 30\nweapon = None',
        "Как сохранить имя и урон одной парой?",
        (
            "weapon = (name, damage)",
            "weapon = {name: damage}",
            "weapon = [name, damage, None]",
            "weapon == (name, damage)",
        ),
    ),
    "PY.UNPACKING": Edit(
        'weapon = ("sword", 30)\nname = None\ndamage = None',
        "Как извлечь оба значения по порядку?",
        (
            "name, damage = weapon",
            "damage, name = weapon",
            "name = damage = weapon",
            "weapon = name, damage",
        ),
    ),
    "PY.CLASS.CLASS_VS_OBJECT": Edit(
        "class Cat:\n    pass\n\ncat1 = None",
        "Как создать объект класса Cat?",
        ("cat1 = Cat()", "cat1 = Cat", "Cat = cat1()", "cat1 == Cat()"),
    ),
    "PY.CLASS.INIT": Edit(
        'class Cat:\n    def __init__(self, name):\n        pass\n\ncat1 = Cat("Мурка")',
        "Как сохранить имя при создании cat1?",
        ("self.name = name", "name.self = self", "self == name", "return name = self"),
    ),
    "PY.CLASS.SELF": Edit(
        "class Cat:\n    def __init__(self):\n        self.hp = 10\n    def heal(self):\n        self.hp += 1\n\ncat1 = Cat()\ncat1.heal()",
        "Какой объект изменяет self.hp?",
        ("cat1", "класс Cat", "все объекты Cat", "метод heal"),
    ),
    "PY.CLASS.ATTRIBUTE": Edit(
        'class Cat:\n    def __init__(self, name):\n        self.name = name\n\ncat1 = Cat("Мурка")\nprint(cat1)',
        "Как вывести сохранённое имя?",
        ("print(cat1.name)", "print(Cat.name)", "print(self.name)", "print(name)"),
    ),
    "PY.CLASS.METHOD": Edit(
        "class Player:\n    def __init__(self):\n        self.hp = 10\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()",
        "Как заставить p1 атаковать p2?",
        ("p1.attack(p2)", "p2.attack = p1", "attack(p1).p2", "Player.attack = p2"),
    ),
    "PY.CLASS.MULTIPLE_OBJECTS": Edit(
        'class Cat:\n    def __init__(self, name):\n        self.name = name\n        self.hp = 10\n\ncat1 = Cat("Мурка")\ncat2 = cat1\ncat1.hp = 7',
        "Как создать независимого второго кота?",
        ('cat2 = Cat("Барсик")', "cat2 = cat1", "Cat = cat1 + cat2", "cat1.name = cat2"),
    ),
    "PY.CLASS.STATE_CHANGE": Edit(
        "class Hero:\n    def __init__(self):\n        self.hp = 10\n    def hurt(self):\n        pass",
        "Как уменьшить hp на 3 внутри hurt?",
        ("self.hp -= 3", "self.hp == 3", "hp.self - 3", "self = hp - 3"),
    ),
    "PY.CLASS.SELF_OTHER": Edit(
        "class Cat:\n    def __init__(self):\n        self.hp = 10\n    def hit(self, other):\n        pass\n\ncat1 = Cat()\ncat2 = Cat()\ncat1.hit(cat2)",
        "Как уменьшить hp цели на 5?",
        ("other.hp -= 5", "self.hp -= 5", "other = hp - 5", "Cat.hp -= 5"),
    ),
    "GAME.STRUCTURE": Edit(
        "class Player:\n    def __init__(self):\n        self.hp = 10\n    def attack(self, other):\n        other.hp -= 1\n\np1 = Player()\np2 = Player()\np1.attack(p2)",
        "Как повторять атаки, пока оба игрока живы?",
        (
            "Добавить while p1.hp > 0 and p2.hp > 0: вокруг вызова",
            "Перенести вызов внутрь class",
            "Заменить p1 на Player",
            "Добавить второй import",
        ),
    ),
    "GAME.PLAYER_STATE": Edit(
        "class Player:\n    def __init__(self):\n        self.hp = 20\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()\np1.attack(p2)",
        "Как вывести HP игрока-цели после атаки?",
        ("print(p2.hp)", "print(p1.hp)", "print(Player.hp)", "print(self.p1.hp)"),
    ),
    "GAME.WEAPON_SELECTION": Edit(
        'class Player:\n    def __init__(self):\n        self.weapon = ()\n    def choose_attack(self):\n        return ("sword", 30)\n    def attack(self):\n        attack_name, damage = self.choose_attack()\n        return attack_name, damage\n\np1 = Player()\np1.attack()\np1.attack()',
        "Как не выбирать оружие заново при каждой атаке?",
        (
            "Сохранить пару в self.weapon и использовать её далее",
            "Вызывать choose_attack дважды",
            "Обнулить self.weapon перед каждой атакой",
            "Создавать нового Player каждый ход",
        ),
    ),
    "GAME.ARMOR_DAMAGE": Edit(
        "class Player:\n    def __init__(self):\n        self.hp = 600\n        self.defense = 100\n\nother = Player()\nother.defense -= 180\nif other.defense < 0:\n    pass",
        "Как перенести остаток урона в HP?",
        (
            "other.hp += other.defense\nother.defense = 0",
            "other.hp -= other.defense\nother.defense = -80",
            "other.hp = 0\nother.defense = 80",
            "self.hp += 80\nother.defense = 0",
        ),
    ),
    "GAME.MAIN_LOOP": Edit(
        "class Player:\n    def __init__(self):\n        self.hp = 10\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()\nwhile p1.hp > 0 or p2.hp > 0:\n    p1.attack(p2)",
        "Как завершать бой при гибели любого игрока?",
        ("Заменить or на and", "Заменить while на if", "Заменить > на ==", "Убрать p2.hp"),
    ),
    "GAME.INITIATIVE": Edit(
        'class Player:\n    def __init__(self, initiative):\n        self.iniciativa = initiative\n    def attack(self, other):\n        print("атака")\n\np1 = Player(8)\np2 = Player(3)\nif p1.iniciativa > p2.iniciativa:\n    p1.attack(p2)\nelse:\n    p2.attack(p1)',
        "Где бросить инициативу для текущего хода?",
        (
            "Перед сравнением в главном цикле",
            "Внутри уже начавшейся attack",
            "После вывода победителя",
            "Только при создании игроков",
        ),
    ),
    "GAME.DEBUG_INITIATIVE": Edit(
        'class Player:\n    def __init__(self, name):\n        self.name = name\n        self.hp = 20\n        self.weapon = ()\n        self.iniciativa = 8\n\np1 = Player("p1")\np2 = Player("p2")\np2.hp = 7\np2.weapon = ("axe", 17)\nif p1.iniciativa == p2.iniciativa:\n    p2 = Player("p2")\n\n# HP и оружие p2 уже сброшены.',
        "Как перебросить только инициативу при ничьей?",
        (
            "Изменить p1.iniciativa и p2.iniciativa",
            "Создать обоих игроков заново",
            "Обнулить HP обоих",
            "Выбрать новое оружие для p2",
        ),
    ),
    "GAME.CRITICAL_COUNTER": Edit(
        "class Player:\n    def __init__(self):\n        self.turns = 0\n    def attack(self, other):\n        self.turns += 1\n        pass",
        "Как узнать, что эта атака — каждая третья?",
        (
            "if self.turns % 3 == 0:",
            "if self.turns / 3 == 0:",
            "if self.turns == 3:",
            "if other.turns % 3 == 0:",
        ),
    ),
}


OUTPUT_LABELS = {
    "Nothing": "Ничего",
    "The loop never stops": "Цикл не заканчивается",
}


def localized_output_answers(
    answers: tuple[str, str, str, str],
) -> tuple[str, str, str, str]:
    return tuple(OUTPUT_LABELS.get(answer, answer) for answer in answers)  # type: ignore[return-value]


MISCONCEPTION_LABELS = {
    "arithmetic_order_confusion": "Порядок действий",
    "armor_hp_overflow_confusion": "Остаток урона после защиты",
    "assignment_vs_comparison": "Присваивание и сравнение",
    "attribute_lookup_confusion": "Чтение атрибута",
    "boolean_operator_confusion": "Логические операции",
    "branch_condition_confusion": "Выбор ветки",
    "break_confusion": "Выход из цикла",
    "cannot_locate_top_level_code": "Код верхнего уровня",
    "class_vs_object": "Класс и объект",
    "collection_type_confusion": "Виды коллекций",
    "conversion_confusion": "Преобразование ввода",
    "definition_runs_immediately": "Определение и вызов функции",
    "dict_key_value_confusion": "Ключ и значение словаря",
    "elif_order_confusion": "Порядок веток elif",
    "forgot_loop_update": "Изменение счётчика цикла",
    "fstring_interpolation_confusion": "Подстановка в f-строке",
    "indentation_confusion": "Отступы",
    "init_timing_confusion": "Запуск __init__",
    "initiative_timing_confusion": "Момент выбора инициативы",
    "input_value_flow_confusion": "Значение из input",
    "loop_condition_confusion": "Условие цикла",
    "method_call_confusion": "Вызов метода",
    "module_function_confusion": "Функция модуля",
    "modulo_confusion": "Остаток от деления",
    "nested_branch_confusion": "Вложенное условие",
    "object_state_change_confusion": "Изменение состояния объекта",
    "parameter_vs_argument": "Параметр и аргумент",
    "print_literal_vs_value_confusion": "Текст и значение в print",
    "print_vs_return": "Вывод и возвращаемое значение",
    "random_is_not_predictable": "Случайный результат",
    "range_boundary_confusion": "Граница range",
    "return_value_confusion": "Значение return",
    "self_confusion": "Значение self",
    "self_other_confusion": "self и other",
    "shared_object_state_confusion": "Независимое состояние объектов",
    "tuple_structure_confusion": "Кортеж",
    "type_confusion": "Типы значений",
    "unpacking_order_confusion": "Порядок распаковки",
    "variable_update_confusion": "Обновление переменной",
    "weapon_storage_confusion": "Хранение выбранного оружия",
}
