import json
from random import randint

from icontract import require
from PIL import Image

im = Image.open("card_images.jpg")

CARDS_PER_ROW = 10
CARD_SIZE_X = 129
CARD_SIZE_Y = 227
BASE_X = 92
BASE_Y = 22
GUTTERS_X = (10, 6, 6, 6, 7, 6, 14, 7, 9)
GUTTERS_Y = (8, 8, 8, 8, 8, 8, 6)
CARDS = 78


@require(lambda no: 0 <= no < CARDS)
def get_image(im: Image, no: int, reversed=False):
    """no is zero-based"""
    x_idx = no % CARDS_PER_ROW
    y_idx = no // CARDS_PER_ROW
    x = BASE_X + x_idx * CARD_SIZE_X + sum(GUTTERS_X[:x_idx])
    y = BASE_Y + y_idx * CARD_SIZE_Y + sum(GUTTERS_Y[:y_idx])
    card = im.crop((x, y, x + CARD_SIZE_X, y + CARD_SIZE_Y))
    return card.rotate(180) if reversed else card


MAJOR_NAMES = [
    "Шут",
    "Маг",
    "Жрица",
    "Императрица",
    "Император",
    "Жрец",
    "Влюбленные",
    "Колесница",
    "Справедливость",
    "Отшельник",
    "Колесо Фортуны",
    "Сила",
    "Повешенный",
    "Смерть",
    "Умеренность",
    "Дьявол",
    "Башня",
    "Звезда",
    "Луна",
    "Солнце",
    "Суд",
    "Мир",
]
MINOR_SUITS = ["жезлов", "кубков", "пентаклей", "мечей"]
MINOR_RANKS = [
    "Туз",
    "Двойка",
    "Тройка",
    "Четверка",
    "Пятерка",
    "Шестерка",
    "Семерка",
    "Восьмерка",
    "Девятка",
    "Десятка",
    "Паж",
    "Рыцарь",
    "Королева",
    "Король",
]

assert len(MAJOR_NAMES) + len(MINOR_RANKS) * len(MINOR_SUITS) == CARDS


@require(lambda no: 0 <= no < CARDS)
def get_name(no: int, reversed=False):
    if no < len(MAJOR_NAMES):
        name = MAJOR_NAMES[no]
    else:
        offset = no - len(MAJOR_NAMES)
        rank = MINOR_RANKS[offset % len(MINOR_RANKS)]
        suit = MINOR_SUITS[offset // len(MINOR_RANKS)]
        name = " ".join([rank, suit])
    return name + " (перевёрнуто)" if reversed else name


GENERAL = "Общее значение"
LOVE = "Значение в любви и отношениях"
SITUATION = "Значение в ситуации и вопросе"
CARD_OF_THE_DAY = "Значение карты дня"
ADVICE = "Совет карты"

SECTIONS = {
    GENERAL: True,
    LOVE: True,
    SITUATION: True,
    CARD_OF_THE_DAY: False,
    ADVICE: False,
}


def get_random_card(sect) -> tuple:
    no = randint(0, CARDS - 1)
    if SECTIONS[sect]:
        reversed = bool(randint(0, 1))
        meaning = meanings[sect]["reversed" if reversed else "upright"]
    else:
        reversed = False
        meaning = meanings[sect]
    return get_name(no, reversed), get_image(im, no, reversed), meaning


with open("meanings.json") as f:
    meanings = json.load(f)
