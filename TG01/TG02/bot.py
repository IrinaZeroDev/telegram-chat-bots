import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

from config import TOKEN
from handlers import handle_photo, handle_voice, handle_text_translation

# Настройка логгинга
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обработчик /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    welcome_text = (
        "👋 Привет! Это бот TG02 для:\n\n"
        "📄 Отправка фото - бот сохранит их в папку 'img'\n"
        "🔊 Отправка голоса - бот сохранит в папку 'audio'\n"
        "🌐 Отправка текста - бот переведет на английский\n"
        "/help - Понить справку"
    )
    await message.answer(welcome_text)
    logger.info(f"Пользователь {message.from_user.id} с начал")

# Обработчик /help
@dp.message(Command("help"))
async def help_handler(message: Message):
    help_text = (
        "📄 **ФУНКЦИОНАЛ:**\n\n"
        "1. **Отправьте фото**\n"
        "   Бот сохранит все фото в папке `img`\n\n"
        "2. **Отправьте голосовые сообщения**\n"
        "   Голоса сохраняются в папке `audio`\n\n"
        "3. **Отправьте текст**\n"
        "   Любой текст будет переведен \u0434 о английского"
    )
    await message.answer(help_text)

# Обработчик для фото
@dp.message(F.photo)
async def photo_handler(message: Message):
    await handle_photo(message, bot)

# Обработчик для голоса
@dp.message(F.voice)
async def voice_handler(message: Message):
    await handle_voice(message, bot)

# Обработчик для обычного текста (u0438сключая команды)
@dp.message(F.text)
async def text_handler(message: Message):
    await handle_text_translation(message)

async def main():
    """
    Основная функция для запуска бота
    """
    logger.info("🚀 Бот TG02 запускается...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🙋 Бот остановлен")
