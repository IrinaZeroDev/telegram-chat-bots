"""Клавиатура финансового бота."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

REGISTER = 'Регистрация в телеграм боте'
RATES = 'Курс валют'
TIPS = 'Советы по экономии'
FINANCES = 'Личные финансы'

button_registr = KeyboardButton(text=REGISTER)
button_exchange_rates = KeyboardButton(text=RATES)
button_tips = KeyboardButton(text=TIPS)
button_finances = KeyboardButton(text=FINANCES)

keyboard = ReplyKeyboardMarkup(keyboard=[
    [button_registr, button_exchange_rates],
    [button_tips, button_finances],
], resize_keyboard=True)
