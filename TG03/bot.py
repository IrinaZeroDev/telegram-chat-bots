import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import TOKEN
from database import add_student, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())

MIN_AGE, MAX_AGE = 5, 100
MAX_GRADE_LENGTH = 10


class Form(StatesGroup):
    """Шаги анкеты: бот по очереди спрашивает имя, возраст и класс."""

    name = State()
    age = State()
    grade = State()


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        'Привет! Я запишу тебя в школьную базу.\n'
        'Как тебя зовут?\n\n'
        'Отменить анкету: /cancel'
    )
    await state.set_state(Form.name)


@dp.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer('Сейчас нечего отменять. Начать: /start')
        return
    await state.clear()
    await message.answer('Анкета отменена. Начать заново: /start')


@dp.message(Form.name, F.text)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or name.startswith('/'):
        await message.answer('Напиши, пожалуйста, своё имя.')
        return
    await state.update_data(name=name)
    await message.answer('Сколько тебе лет?')
    await state.set_state(Form.age)


@dp.message(Form.age, F.text)
async def process_age(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not MIN_AGE <= int(text) <= MAX_AGE:
        await message.answer(
            f'Возраст — это целое число от {MIN_AGE} до {MAX_AGE}. '
            'Сколько тебе лет?'
        )
        return
    await state.update_data(age=int(text))
    await message.answer('В каком классе ты учишься? Например: 9Б')
    await state.set_state(Form.grade)


@dp.message(Form.grade, F.text)
async def process_grade(message: Message, state: FSMContext):
    grade = message.text.strip().upper()
    if not grade or len(grade) > MAX_GRADE_LENGTH:
        await message.answer('Напиши класс коротко, например: 9Б')
        return

    data = await state.get_data()
    try:
        student_id = add_student(data['name'], data['age'], grade)
    except Exception:
        logger.exception('Не удалось сохранить ученика')
        await message.answer(
            'Не получилось сохранить данные. Попробуй позже: /start'
        )
    else:
        logger.info('Сохранён ученик №%s', student_id)
        await message.answer(
            'Готово, данные сохранены!\n'
            f'Запись №{student_id}\n'
            f"Имя: {data['name']}\n"
            f"Возраст: {data['age']}\n"
            f'Класс: {grade}'
        )
    await state.clear()


@dp.message(Form.name)
@dp.message(Form.age)
@dp.message(Form.grade)
async def not_text(message: Message):
    """Во время анкеты бот ждёт текст, а не стикер или фото."""
    await message.answer('Пожалуйста, ответь текстом.')


async def main():
    if not TOKEN:
        raise SystemExit(
            'Не задан TELEGRAM_BOT_TOKEN: скопируйте .env.example в .env '
            'и впишите токен от @BotFather'
        )
    init_db()
    bot = Bot(token=TOKEN)
    logger.info('🚀 Бот TG03 запускается...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🙋 Бот остановлен')
