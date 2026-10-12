# Конфигурация финансового бота TG06
import os
from pathlib import Path

from dotenv import load_dotenv

# Токен и ключ хранятся в файле .env рядом с ботом (образец — .env.example),
# поэтому в репозиторий они не попадают
load_dotenv(Path(__file__).resolve().parent / '.env')

# Токен Telegram-бота от BotFather
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Ключ ExchangeRate-API (необязательный): без него курсы берутся
# с открытого адреса open.er-api.com того же сервиса
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', '')
