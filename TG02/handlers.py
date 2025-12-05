import os
import logging
from aiogram import types
from google.cloud import translate_v2
from config import IMAGES_DIR, AUDIO_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_dir(directory):
    """Проверяет и создает директорию, если ее нет"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Новая директория создана: {directory}")

async def handle_photo(message: types.Message, bot):
    """
    Обрабатывает и сохраняет фото
    """
    try:
        ensure_dir(IMAGES_DIR)
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        filename = f"{IMAGES_DIR}/photo_{message.date.timestamp()}.jpg"
        await bot.download_file(file_info.file_path, filename)
        logger.info(f"Фото сохранено: {filename}")
        await message.answer(f"✅ Фото успешно сохранено!\nПуть: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении фото: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")

async def handle_voice(message: types.Message, bot):
    """
    Обрабатывает и сохраняет голосовые сообщения
    """
    try:
        ensure_dir(AUDIO_DIR)
        file_info = await bot.get_file(message.voice.file_id)
        filename = f"{AUDIO_DIR}/voice_{message.date.timestamp()}.ogg"
        await bot.download_file(file_info.file_path, filename)
        logger.info(f"Голос сохранен: {filename}")
        await message.answer(f"✅ Голосовое сообщение сохранено!\nПуть: {filename}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении голоса: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")

async def handle_text_translation(message: types.Message):
    """
    Переводит текст на английский
    """
    try:
        translator = translate_v2.Client()
        result = translator.translate_text(
            values=[message.text],
            target_language_code='en'
        )
        translated_text = result[0]['translatedText']
        await message.answer(f"🇦🇺 Оригинал: {message.text}\n\n🗒 Перевод: {translated_text}")
        logger.info(f"Текст переведен: {message.text[:50]}... -> {translated_text[:50]}...")
    except Exception as e:
        logger.error(f"Ошибка при переводе: {e}")
        await message.answer(f"❌ Ошибка перевода: {str(e)}")
