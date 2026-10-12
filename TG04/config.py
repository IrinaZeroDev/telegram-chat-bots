# Конфигурация Telegram-бота TG04
import os
from pathlib import Path

from dotenv import load_dotenv

# Токен хранится в файле .env рядом с ботом (образец — .env.example),
# поэтому в репозиторий он не попадает
load_dotenv(Path(__file__).resolve().parent / '.env')

# Токен Telegram-бота от BotFather
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
