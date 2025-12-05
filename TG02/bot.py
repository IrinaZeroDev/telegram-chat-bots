import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

from config import TOKEN
from handlers import handle_photo, handle_voice, handle_text_translation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    welcome_text = (
        "👋 Привет! Это бот TG02 для:\n\n"
        "📄 Отправка фото - бот сохранит их в папку 'img'\n"
        "🔊 Отправка голоса - бот сохранит в папку 'audio'\n"
        "🌐 Отправка текста - бот переведет на английский"
    )
    await message.answer(welcome_text)

@dp.message(F.photo)
async def photo_handler(message: Message):
    await handle_photo(message, bot)

@dp.message(F.voice)
async def voice_handler(message: Message):
    await handle_voice(message, bot)

@dp.message(F.text)
async def text_handler(message: Message):
    await handle_text_translation(message)

async def main():
    logger.info("🚀 Бот TG02 запускается...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🙋 Бот остановлен")
