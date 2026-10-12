import asyncio
import logging
import random

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

import config
import database
import keyboards as kb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

TIPS = [
    'Совет 1: Ведите бюджет и следите за своими расходами.',
    'Совет 2: Откладывайте часть доходов на сбережения — сразу в день '
    'зарплаты, а не «что останется».',
    'Совет 3: Покупайте товары по скидкам и распродажам, но только те, '
    'что и так были в списке.',
    'Совет 4: Перед крупной покупкой выждите 48 часов — импульсное '
    'желание часто проходит.',
    'Совет 5: Раз в месяц пересматривайте подписки и отключайте ненужные.',
    'Совет 6: Ходите в магазин сытыми и со списком покупок.',
    'Совет 7: Сравнивайте цену за килограмм или литр, а не за упаковку.',
    'Совет 8: Создайте финансовую подушку на 3–6 месяцев расходов.',
]


class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()


def parse_amount(text):
    """Сумма из текста: «1 500,50» → 1500.5. None, если это не сумма."""
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
    except ValueError:
        return None
    # float('nan') и float('inf') тоже «числа» — их не принимаем
    if not 0 <= amount < 1e12:
        return None
    return round(amount, 2)


def money(amount):
    """1500.5 → «1 500.50 ₽»."""
    return f'{amount:,.2f}'.replace(',', ' ') + ' ₽'


@dp.message(CommandStart())
async def send_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        'Привет! Я ваш личный финансовый помощник. '
        'Выберите одну из опций в меню:',
        reply_markup=kb.keyboard,
    )


@dp.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer('Сейчас нечего отменять.')
        return
    await state.clear()
    await message.answer('Ввод расходов отменён.', reply_markup=kb.keyboard)


# Регистрация

@dp.message(F.text == kb.REGISTER)
async def registration(message: Message, state: FSMContext):
    await state.clear()
    if database.register(message.from_user.id, message.from_user.full_name):
        await message.answer('Вы успешно зарегистрированы!')
    else:
        await message.answer('Вы уже зарегистрированы!')


# Курс валют

async def fetch_rates():
    """Курсы к доллару: {'RUB': 81.2, 'EUR': 0.86, ...}."""
    if config.EXCHANGE_RATE_API_KEY:
        url = ('https://v6.exchangerate-api.com/v6/'
               f'{config.EXCHANGE_RATE_API_KEY}/latest/USD')
        field = 'conversion_rates'
    else:
        url = 'https://open.er-api.com/v6/latest/USD'
        field = 'rates'
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
    return data[field]


@dp.message(F.text == kb.RATES)
async def exchange_rates(message: Message, state: FSMContext):
    await state.clear()
    try:
        rates = await fetch_rates()
        usd_to_rub = rates['RUB']
        # rates['EUR'] — сколько евро дают за 1 доллар (≈0.86),
        # поэтому 1 евро = рубли за доллар / евро за доллар
        eur_to_rub = usd_to_rub / rates['EUR']
    except (aiohttp.ClientError, TimeoutError, KeyError, ValueError):
        logger.exception('Не удалось получить курс валют')
        await message.answer('Не удалось получить данные о курсе валют!')
        return
    await message.answer(f'1 USD - {usd_to_rub:.2f} RUB\n'
                         f'1 EUR - {eur_to_rub:.2f} RUB')


# Советы по экономии

@dp.message(F.text == kb.TIPS)
async def send_tips(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(random.choice(TIPS))


# Личные финансы: три категории и расходы по ним (FSM)

@dp.message(F.text == kb.FINANCES)
async def finances(message: Message, state: FSMContext):
    await state.clear()
    # Расходы сохраняются в строку пользователя, поэтому без регистрации
    # UPDATE ничего бы не изменил — предупреждаем заранее
    if not database.is_registered(message.from_user.id):
        await message.answer(
            'Сначала нажмите «Регистрация в телеграм боте».'
        )
        return
    await state.set_state(FinancesForm.category1)
    await message.reply('Введите первую категорию расходов:\n'
                        '(отменить ввод — /cancel)')


async def ask_amount(message, state, category_field, next_state, number):
    await state.update_data({category_field: message.text.strip()})
    await state.set_state(next_state)
    await message.reply(f'Введите расходы для категории {number}:')


async def read_amount(message, state, expenses_field):
    """Сохраняет сумму в данные FSM. False — если ввели не число."""
    amount = parse_amount(message.text)
    if amount is None:
        await message.reply('Введите сумму числом, например 1500 или 249,90:')
        return False
    await state.update_data({expenses_field: amount})
    return True


@dp.message(FinancesForm.category1, F.text)
async def category1(message: Message, state: FSMContext):
    await ask_amount(message, state, 'category1', FinancesForm.expenses1, 1)


@dp.message(FinancesForm.expenses1, F.text)
async def expenses1(message: Message, state: FSMContext):
    if await read_amount(message, state, 'expenses1'):
        await state.set_state(FinancesForm.category2)
        await message.reply('Введите вторую категорию расходов:')


@dp.message(FinancesForm.category2, F.text)
async def category2(message: Message, state: FSMContext):
    await ask_amount(message, state, 'category2', FinancesForm.expenses2, 2)


@dp.message(FinancesForm.expenses2, F.text)
async def expenses2(message: Message, state: FSMContext):
    if await read_amount(message, state, 'expenses2'):
        await state.set_state(FinancesForm.category3)
        await message.reply('Введите третью категорию расходов:')


@dp.message(FinancesForm.category3, F.text)
async def category3(message: Message, state: FSMContext):
    await ask_amount(message, state, 'category3', FinancesForm.expenses3, 3)


@dp.message(FinancesForm.expenses3, F.text)
async def expenses3(message: Message, state: FSMContext):
    if not await read_amount(message, state, 'expenses3'):
        return
    data = await state.get_data()
    expenses = [(data[f'category{i}'], data[f'expenses{i}'])
                for i in (1, 2, 3)]
    database.save_expenses(message.from_user.id, expenses)
    await state.clear()
    lines = [f'• {name}: {money(amount)}' for name, amount in expenses]
    total = sum(amount for _, amount in expenses)
    await message.answer(
        'Категории и расходы сохранены!\n\n' + '\n'.join(lines)
        + f'\n\nИтого: {money(total)}',
        reply_markup=kb.keyboard,
    )


@dp.message(FinancesForm.category1)
@dp.message(FinancesForm.expenses1)
@dp.message(FinancesForm.category2)
@dp.message(FinancesForm.expenses2)
@dp.message(FinancesForm.category3)
@dp.message(FinancesForm.expenses3)
async def not_text(message: Message):
    await message.reply('Пожалуйста, ответьте текстом.')


async def main():
    if not config.TOKEN:
        raise SystemExit(
            'Не задан TELEGRAM_BOT_TOKEN: скопируйте .env.example в .env '
            'и впишите токен от @BotFather'
        )
    database.init_db()
    bot = Bot(token=config.TOKEN)
    logger.info('🚀 Финансовый бот запускается...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🙋 Бот остановлен')
