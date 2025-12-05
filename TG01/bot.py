import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio

from config import TOKEN
from weather import get_weather

# Конфигурирание логгинга
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    """
    Отображает приветственное сообщение
    """
    welcome_text = (
        "\ud83d\udc4b Привет, " + message.from_user.first_name + "!\n\n"
        "Что я могу сделать:\n"
        "/start - показать это сообщение\n"
        "/weather - получить прогноз погоды в Ростове-на-Дону\n"
        "/help - показать могу"
    )
    await message.answer(welcome_text)
    logger.info(f"Пользователь {message.from_user.id} с привет")

# Обработчик команды /weather
@dp.message(Command("weather"))
async def weather_handler(message: Message):
    """
    Отправляет погоду в Ростове-на-Дону
    """
    await message.answer("⌚⁥ От не секунды и подожди...")
    
    # Получаем данные о погоде
    weather_data = get_weather()
    
    # Отправляем полученные данные
    await message.answer(weather_data)
    logger.info(f"Пользователь {message.from_user.id} спросил погоду")

# Обработчик команды /help
@dp.message(Command("help"))
async def help_handler(message: Message):
    """
    Показывает справку
    """
    help_text = (
        "🎆 Раскрываю секреты:\n\n"
        "Этот бот использует aiogram - асинхронную библиотеку для \n"
        "работы с Telegram Bot API.\n\n"
        "🌬 Он может:\n"
        "1. Отвечать на команды\n"
        "2. Получать данные о погоде из OpenWeatherMap API"
    )
    await message.answer(help_text)
    logger.info(f"Пользователь {message.from_user.id} напнал /help")

# Обработчик нереконных сообщений
@dp.message()
async def any_message_handler(message: Message):
    """
    Простое сообщение для удобства
    """
    response = (
        f"🙄 Не разумею команду '{message.text}'. \n"
        f"Пытайтесь /help а могу сделать."
    )
    await message.answer(response)
    logger.info(f"Пользователь {message.from_user.id} напсал: {message.text}")

async def main():
    """
    Основная функция для запуска диспетчера
    """
    logger.info("🚀 Бот запускается...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🙋 Бот остановлен")
