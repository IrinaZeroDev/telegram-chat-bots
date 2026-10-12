# Конфигурация Telegram-бота TG05
import os
from pathlib import Path

from dotenv import load_dotenv

# Токен и ключи хранятся в файле .env рядом с ботом (образец — .env.example),
# поэтому в репозиторий они не попадают
load_dotenv(Path(__file__).resolve().parent / '.env')

# Токен Telegram-бота от BotFather
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Ключ TheCatAPI (необязательный): без него бот присылает случайных котиков,
# с ним — ещё и ищет фото и описание по названию породы
THE_CAT_API_KEY = os.getenv('THE_CAT_API_KEY', '')
