import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

import api
import config
import keyboards as kb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

HELP = (
    'Я собираю данные из трёх открытых API:\n\n'
    '🌤 /weather <город> — погода сейчас (Open-Meteo)\n'
    '💱 /rates [коды валют] — курсы ЦБ РФ, например /rates USD KZT\n'
    '🐱 /cat — случайный котик (TheCatAPI)\n'
    '🐱 /cat <порода> — фото и описание породы, например /cat Siamese\n\n'
    'Или просто нажимай кнопки меню.'
)
UNAVAILABLE = '😿 Сервис сейчас не отвечает, попробуй чуть позже.'


class WeatherForm(StatesGroup):
    city = State()


@dp.message(CommandStart())
@dp.message(Command('help'))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HELP, reply_markup=kb.main_menu)


# Погода

async def send_weather(message: Message, city_name: str):
    try:
        city = await api.find_city(city_name)
        if city is None:
            await message.answer(
                f'Не нашёл город «{city_name}». Проверь название.'
            )
            return
        current = await api.get_weather(city)
    except api.ApiError:
        logger.exception('Open-Meteo недоступен')
        await message.answer(UNAVAILABLE)
        return
    await message.answer(api.format_weather(city, current))


@dp.message(Command('weather'))
async def weather_command(message: Message, command: CommandObject,
                          state: FSMContext):
    if command.args:
        await state.clear()
        await send_weather(message, command.args.strip())
    else:
        await ask_city(message, state)


@dp.message(F.text == kb.WEATHER)
async def ask_city(message: Message, state: FSMContext):
    # Город спрашиваем отдельным сообщением — бот запоминает,
    # что следующий текст будет названием города (FSM из урока TG03)
    await state.set_state(WeatherForm.city)
    await message.answer('В каком городе узнать погоду?')


# Курсы валют

@dp.message(Command('rates'))
@dp.message(F.text == kb.RATES)
async def rates(message: Message, state: FSMContext,
                command: CommandObject = None):
    await state.clear()
    codes = command.args.split() if command and command.args else None
    try:
        data = await api.get_rates()
    except api.ApiError:
        logger.exception('ЦБ РФ недоступен')
        await message.answer(UNAVAILABLE)
        return
    if codes:
        await message.answer(api.format_rates(data, codes))
    else:
        await message.answer(api.format_rates(data))


# Котики

@dp.message(Command('cat'))
@dp.message(F.text == kb.CAT)
async def cat(message: Message, state: FSMContext,
              command: CommandObject = None):
    await state.clear()
    breed_query = command.args if command else None
    if breed_query and not config.THE_CAT_API_KEY:
        await message.answer(
            'Поиск по породе работает с ключом TheCatAPI '
            '(THE_CAT_API_KEY в .env). А пока — случайный котик:'
        )
        breed_query = None
    try:
        if breed_query:
            breeds = await api.get_breeds(config.THE_CAT_API_KEY)
            breed = api.match_breed(breeds, breed_query)
            if breed is None:
                await message.answer(
                    f'Не знаю породу «{breed_query}». Названия пород — '
                    'по-английски, например Bengal, Siamese, Sphynx.'
                )
                return
            photo = await api.random_cat(config.THE_CAT_API_KEY, breed['id'])
            caption = api.format_breed(breed)
        else:
            photo = await api.random_cat(config.THE_CAT_API_KEY)
            caption = 'Держи котика 🐾'
    except api.ApiError:
        logger.exception('TheCatAPI недоступен')
        await message.answer(UNAVAILABLE)
        return
    await message.answer_photo(photo=photo, caption=caption)


# Обработчик стоит после команд и кнопок: если, пока бот ждёт город,
# нажать другую кнопку, сработает она, а не поиск города «💱 Курсы валют»
@dp.message(WeatherForm.city, F.text)
async def weather_for_city(message: Message, state: FSMContext):
    await state.clear()
    await send_weather(message, message.text.strip())


@dp.message()
async def unknown(message: Message):
    await message.answer('Не понял 🙂 Выбери кнопку в меню или набери /help',
                         reply_markup=kb.main_menu)


async def main():
    if not config.TOKEN:
        raise SystemExit(
            'Не задан TELEGRAM_BOT_TOKEN: скопируйте .env.example в .env '
            'и впишите токен от @BotFather'
        )
    bot = Bot(token=config.TOKEN)
    logger.info('🚀 Бот TG05 запускается...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🙋 Бот остановлен')
