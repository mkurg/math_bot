"""Short, ordered examples displayed with each Russian lesson."""

# ruff: noqa: E501 -- Keep each small program together as one curriculum datum.

LESSON_CODE: dict[str, str] = {
    "diagnostic": 'print("A")\n\ndef hello():\n    print("B")\n\nprint("C")',
    "values": "x = 5\ny = x\nx = 8\nprint(x)\nprint(y)",
    "io": 'name = input("Имя: ")\nhp = 25\nprint(f"{name}: hp = {hp}")',
    "conditions": 'hp = 20\nif hp > 50:\n    print("сильный")\nelif hp > 0:\n    print("жив")\nelse:\n    print("конец")',
    "loops": "x = 1\nwhile x <= 3:\n    print(x)\n    x += 1",
    "modulo": "for turns in range(1, 7):\n    print(turns, turns % 3)",
    "functions": "def double(x):\n    return x * 2\n\nresult = double(5)\nprint(result)",
    "randomness": 'import random\n\nroll = random.randint(1, 6)\nweapon = random.choice(["sword", "axe"])',
    "collections": 'weapons = {"sword": 30, "axe": 17}\nweapon = ("sword", 30)\nname, damage = weapon\nprint(name, damage)',
    "classes": 'class Cat:\n    def __init__(self, name):\n        self.name = name\n        self.hp = 10\n\ncat1 = Cat("Мурка")',
    "methods": "class Cat:\n    def __init__(self):\n        self.hp = 10\n    def hit(self, other):\n        other.hp -= 1\n\ncat1 = Cat()\ncat2 = Cat()\ncat1.hit(cat2)",
    "terminology": "import random\n\nclass Player:\n    def __init__(self, hp):\n        self.hp = hp\n\np1 = Player(random.randint(10, 20))",
    "lab1_init": "class Player:\n    def __init__(self, name):\n        self.name = name\n        self.hp = 600\n        self.damage = 150\n        self.defense = 100\n        self.iniciativa = 0\n        self.weapon = ()",
    "lab2_weapons": 'import random\n\nweapons = {"sword": 30, "axe": 17}\nattack_name, damage = random.choice(list(weapons.items()))\nweapon = (attack_name, damage)\nprint(weapon)',
    "lab3_attack": "class Player:\n    def __init__(self):\n        self.hp = 20\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()\np1.attack(p2)",
    "lab4_armor": "hp = 600\ndefense = 100\ndamage = 180\n\ndefense -= damage\nif defense < 0:\n    hp += defense\n    defense = 0\nprint(hp, defense)",
    "lab5_objects": "class Player:\n    def __init__(self):\n        self.hp = 20\n\np1 = Player()\np2 = Player()\np2.hp -= 5\nprint(p1.hp, p2.hp)",
    "lab6_loop": 'class Player:\n    def __init__(self):\n        self.hp = 10\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()\nwhile p1.hp > 0 and p2.hp > 0:\n    p1.attack(p2)\nprint("победитель:", p1.hp > 0)',
    "lab7_initiative": 'class Player:\n    def __init__(self, initiative):\n        self.iniciativa = initiative\n    def attack(self, other):\n        print("атака")\n\np1 = Player(8)\np2 = Player(3)\nif p1.iniciativa > p2.iniciativa:\n    p1.attack(p2)\nelse:\n    p2.attack(p1)',
    "lab8_refactor": "import random\n\nclass Player:\n    def __init__(self):\n        self.hp = 10\n        self.iniciativa = 0\n    def attack(self, other):\n        other.hp -= 5\n\np1 = Player()\np2 = Player()\nwhile p1.hp > 0 and p2.hp > 0:\n    p1.iniciativa = random.randint(1, 20)\n    p2.iniciativa = random.randint(1, 20)\n    if p1.iniciativa == p2.iniciativa:\n        continue\n    if p1.iniciativa > p2.iniciativa:\n        p1.attack(p2)\n    else:\n        p2.attack(p1)",
    "lab9_critical": "class Player:\n    def __init__(self):\n        self.hp = 600\n        self.defense = 100\n    def attack(self, other, damage):\n        other.defense -= damage\n\n# Задача: добавить счётчик и критический удар.",
    "d20": "import random\n\ndef d20():\n    return random.randint(1, 20)\n\nprint(d20())",
}
