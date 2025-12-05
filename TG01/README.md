# Telegram Bot s prognozu pogody v Rostove-na-Donu

## Opisanie

Eto prostoi Telegram-bot, razrabotannyi na Python s ispol'zovaniem biblioteki **aiogram 3.0**. Bot poluchaet prognoz pogody iz API OpenWeatherMap i otpravlyaet ee v Telegram.

## Funkcional

- `/start` - pokazyvaet privetstvennoe soobshchenie
- `/weather` - poluchaet i otpravlyaet prognoz pogody v Rostove-na-Donu
- `/help` - pokazyvaet spravka ob vozmozhnostyakh bota

## Trebovaniya

- Python 3.9+
- aiogram 3.0.0
- requests 2.31.0

## Ustanovka

1. Kloniruite ili skachyte proekt
2. Ustanovite zavisimosti:
   ```bash
   pip install -r requirements.txt
   ```

## Konfiguracia

### 1. Poluchite token Telegram-bota

1. Otkroite @BotFather v Telegram
2. Otpravte komandy: `/newbot`
3. Sleduite instrukciiam
4. Skopiiruite poluchennyi token

### 2. Poluchite API klyuch OpenWeatherMap

1. Zaregistriruites' na https://openweathermap.org/api
2. Poluchite besplatnyy API klyuch (Free plan)
3. Skopiiruite klyuch

### 3. Nastroite config.py

Otkroite fayl `config.py` i zamestiте:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
```

## Zapusk bota

```bash
python bot.py
```

## Struktura proekta

- `bot.py` - glavnyy fayl s botom
- `config.py` - konfiguracia s tokenami
- `weather.py` - funkciya dlya polucheniya pogody
- `requirements.txt` - zavisimosti
- `README.md` - dokumentacia

## API

Bot ispol'zuet OpenWeatherMap API:
- Temperatura
- Opisanie pogodnykh usloviy
- Vlazhnost'
- Davlenie
- Skorost' vetra
