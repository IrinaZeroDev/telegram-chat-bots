import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

import keyboards as kb
from config import TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()


def user_name(user):
    """Имя для обращения: имя из профиля, иначе @username."""
    return user.first_name or user.username or 'друг'


# Задание 1. Меню с кнопками «Привет» и «Пока»

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        'Выбери кнопку в меню ниже.\n\n'
        'Ещё команды: /links — полезные ссылки, '
        '/dynamic — кнопки, которые меняются',
        reply_markup=kb.main_menu,
    )


@dp.message(F.text == kb.HELLO)
async def say_hello(message: Message):
    await message.answer(f'Привет, {user_name(message.from_user)}!')


@dp.message(F.text == kb.BYE)
async def say_bye(message: Message):
    await message.answer(f'До свидания, {user_name(message.from_user)}!')


# Задание 2. Inline-кнопки с URL-ссылками

@dp.message(Command('links'))
async def show_links(message: Message):
    await message.answer('Куда отправимся?', reply_markup=kb.links)


# Задание 3. Динамическое изменение клавиатуры

@dp.message(Command('dynamic'))
async def dynamic(message: Message):
    await message.answer('Нажми кнопку:', reply_markup=kb.show_more)


@dp.callback_query(F.data == kb.SHOW_MORE)
async def show_options(callback: CallbackQuery):
    await callback.answer()
    # Меняем кнопки в том же сообщении, а не присылаем новое
    await callback.message.edit_reply_markup(reply_markup=kb.options())


@dp.callback_query(F.data.in_(kb.OPTIONS))
async def choose_option(callback: CallbackQuery):
    option = kb.OPTIONS[callback.data]
    await callback.answer()
    await callback.message.answer(f'Вы выбрали: {option}')


async def main():
    if not TOKEN:
        raise SystemExit(
            'Не задан TELEGRAM_BOT_TOKEN: скопируйте .env.example в .env '
            'и впишите токен от @BotFather'
        )
    bot = Bot(token=TOKEN)
    logger.info('🚀 Бот TG04 запускается...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🙋 Бот остановлен')
