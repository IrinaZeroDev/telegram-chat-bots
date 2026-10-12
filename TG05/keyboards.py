"""Клавиатуры бота TG05."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

WEATHER = '🌤 Погода'
RATES = '💱 Курсы валют'
CAT = '🐱 Котик'

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=WEATHER), KeyboardButton(text=RATES)],
        [KeyboardButton(text=CAT)],
    ],
    resize_keyboard=True,
)
