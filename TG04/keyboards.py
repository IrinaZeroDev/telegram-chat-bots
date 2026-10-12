"""Клавиатуры бота TG04."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Задание 1. Reply-меню: кнопки появляются вместо обычной клавиатуры
# и при нажатии отправляют свой текст в чат
HELLO = 'Привет'
BYE = 'Пока'

main_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=HELLO), KeyboardButton(text=BYE)]],
    resize_keyboard=True,
)

# Задание 2. Inline-кнопки со ссылками: прикреплены к сообщению
LINKS = {
    '📰 Новости': 'https://news.google.com/?hl=ru&gl=RU&ceid=RU:ru',
    '🎵 Музыка': 'https://music.yandex.ru/',
    '🎬 Видео': 'https://www.youtube.com/',
}

links = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=text, url=url)] for text, url in LINKS.items()
])

# Задание 3. Inline-кнопки с callback: нажатие отправляет боту
# callback_data, а не текст в чат
SHOW_MORE = 'show_more'
OPTIONS = {
    'option_1': 'Опция 1',
    'option_2': 'Опция 2',
}

show_more = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Показать больше', callback_data=SHOW_MORE)]
])


def options():
    """Клавиатура с опциями собирается билдером из словаря OPTIONS."""
    builder = InlineKeyboardBuilder()
    for data, text in OPTIONS.items():
        builder.add(InlineKeyboardButton(text=text, callback_data=data))
    return builder.adjust(2).as_markup()
