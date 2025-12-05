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
2. Otpravte komandy:
   - `/newbot` - dlya sozdaniya novogo bota
   - Sleduite instrukciiam
3. Skopiiruite poluchennyi token

### 2. Poluchite API klyuch OpenWeatherMap

1. Zaregistriruites' na https://openweathermap.org/api
2. Poluchite besplatnyy API klyuch (Free plan)
3. Skopiiruite klyuch

### 3. Nastroite config.py

Otkroite fayl `config.py` i zamestiте:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Vstavte vash token
WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"  # Vstavte vash API klyuch
```

## Zapusk bota

Dlya zapuska bota vypolnite:

```bash
python bot.py
```

Bot nachnot slushat' soobshcheniya i budет ready prinimat' komandy.

## Struktura proekta

- `bot.py` - glavnyy fayl s botom i obrabotchikami komand
- `config.py` - konfiguracia s tokenami i parametrami
- `weather.py` - funkciya dlya polucheniya pogody iz API
- `requirements.txt` - zavisimosti proekta
- `README.md` - dokumentacia

## API

Bot ispol'zuet OpenWeatherMap API dlya polucheniya dannykh o pogode:
- Temperatura (v gradusakh Cel'siya)
- "Oshchushchaetsia kak" temperatura
- Opisanie pogodnykh usloviy
- Vlazhnost'
- Davlenie
- Skorost' vetra

## Oshibki

Esli bot ne rabotaet:

1. Proverite, chto token v `config.py` verno nastroyen
2. Proverite, chto API klyuch v `config.py` verno nastroyen
3. Proverite internet-soedinenije
4. Proverite, chto vse biblioteki ustanovleny: `pip install -r requirements.txt`

## Litsenziya

MIT
