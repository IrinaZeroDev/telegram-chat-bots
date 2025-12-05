# Telegram-бот TG02 с обработкой фото, голоса и переводом текста

## Описание

Это адвансированный Telegram-бот на aiogram 3.0, который обрабатывает:

1. **Фото** - сохраняются в папке `img` с временным меткой
2. **Голосовые сообщения** - сохраняются в папке `audio` в формате OGG
3. **Перевод текста** - все тексты переводятся на английский через Google Translate

## Требования

- Python 3.9+
- aiogram 3.0.0
- requests 2.31.0
- google-cloud-translate 3.11.1

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

1. Откройте `config.py`
2. Вставьте ваш токен:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
```

## Запуск

```bash
python bot.py
```

## Файлы проекта

- `bot.py` - основной файл бота
- `config.py` - конфигурация
- `handlers.py` - обработчики для фото, голоса и перевода
- `requirements.txt` - зависимости
