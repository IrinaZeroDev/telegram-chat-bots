"""Обращения к внешним API.

Запросы делаются асинхронно через aiohttp (он ставится вместе с aiogram):
пока бот ждёт ответа сервера, он продолжает отвечать другим пользователям.
Синхронный requests на это время «замораживал» бы весь бот.
"""
from datetime import datetime

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=15)

GEO_URL = 'https://geocoding-api.open-meteo.com/v1/search'
FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'
CBR_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'
CAT_SEARCH_URL = 'https://api.thecatapi.com/v1/images/search'
CAT_BREEDS_URL = 'https://api.thecatapi.com/v1/breeds'


class ApiError(Exception):
    """Сервис недоступен или ответил ошибкой."""


async def get_json(url, params=None, headers=None):
    """GET-запрос, ответ разбирается как JSON."""
    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise ApiError(f'{url}: HTTP {resp.status}')
                # ЦБ отдаёт JSON с типом application/javascript,
                # поэтому проверку Content-Type отключаем
                return await resp.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as error:
        raise ApiError(f'{url}: {error!r}') from error


# Open-Meteo: погода без ключа

# Коды погоды WMO, которые возвращает Open-Meteo
WEATHER_CODES = {
    0: '☀️ ясно',
    1: '🌤 преимущественно ясно',
    2: '⛅ переменная облачность',
    3: '☁️ пасмурно',
    45: '🌫 туман',
    48: '🌫 изморозь',
    51: '🌦 лёгкая морось',
    53: '🌦 морось',
    55: '🌦 сильная морось',
    56: '🌧 ледяная морось',
    57: '🌧 сильная ледяная морось',
    61: '🌧 небольшой дождь',
    63: '🌧 дождь',
    65: '🌧 сильный дождь',
    66: '🌧 ледяной дождь',
    67: '🌧 сильный ледяной дождь',
    71: '🌨 небольшой снег',
    73: '🌨 снег',
    75: '❄️ сильный снег',
    77: '🌨 снежная крупа',
    80: '🌦 ливень',
    81: '🌧 сильный ливень',
    82: '⛈ очень сильный ливень',
    85: '🌨 снегопад',
    86: '❄️ сильный снегопад',
    95: '⛈ гроза',
    96: '⛈ гроза с градом',
    99: '⛈ сильная гроза с градом',
}


async def find_city(name):
    """Координаты города по названию или None, если город не найден."""
    data = await get_json(
        GEO_URL, params={'name': name, 'count': 1, 'language': 'ru'}
    )
    results = data.get('results')
    return results[0] if results else None


async def get_weather(city):
    """Текущая погода в точке, найденной find_city."""
    data = await get_json(FORECAST_URL, params={
        'latitude': city['latitude'],
        'longitude': city['longitude'],
        'current': 'temperature_2m,apparent_temperature,'
                   'relative_humidity_2m,weather_code,wind_speed_10m',
        'wind_speed_unit': 'ms',
        'timezone': 'auto',
    })
    return data['current']


def format_weather(city, current):
    place = ', '.join(
        part for part in (city['name'], city.get('country')) if part
    )
    sky = WEATHER_CODES.get(current['weather_code'], 'без описания')
    return (
        f'Погода: {place}\n'
        f'{sky}\n'
        f'🌡 {current["temperature_2m"]:+.0f} °C, '
        f'ощущается как {current["apparent_temperature"]:+.0f} °C\n'
        f'💧 влажность {current["relative_humidity_2m"]} %\n'
        f'💨 ветер {current["wind_speed_10m"]:.1f} м/с'
    )


# ЦБ РФ: официальные курсы валют (зеркало cbr-xml-daily.ru)

DEFAULT_CURRENCIES = ('USD', 'EUR', 'CNY')


async def get_rates():
    return await get_json(CBR_URL)


def format_rates(data, codes=DEFAULT_CURRENCIES):
    """Курсы выбранных валют. Неизвестные коды перечисляются в конце."""
    date = datetime.fromisoformat(data['Date']).strftime('%d.%m.%Y')
    valutes = data['Valute']
    lines = [f'💱 Курсы ЦБ РФ на {date}']
    unknown = []
    for code in codes:
        valute = valutes.get(code.upper())
        if valute is None:
            unknown.append(code)
            continue
        # Курс указан за Nominal единиц (например, за 10 юаней) —
        # пересчитываем за одну
        rate = valute['Value'] / valute['Nominal']
        change = rate - valute['Previous'] / valute['Nominal']
        arrow = '▲' if change > 0 else '▼' if change < 0 else '='
        lines.append(
            f'{valute["CharCode"]} ({valute["Name"]}): '
            f'{rate:.2f} ₽ {arrow} {abs(change):.2f}'
        )
    if unknown:
        lines.append('Не знаю валюты: ' + ', '.join(unknown))
    return '\n'.join(lines)


# TheCatAPI: случайный котик работает без ключа,
# список пород — только с ключом THE_CAT_API_KEY

def cat_headers(api_key):
    return {'x-api-key': api_key} if api_key else None


async def random_cat(api_key=None, breed_id=None):
    """Ссылка на случайное фото кошки (при breed_id — этой породы)."""
    params = {'breed_ids': breed_id} if breed_id else None
    data = await get_json(
        CAT_SEARCH_URL, params=params, headers=cat_headers(api_key)
    )
    if not data:
        raise ApiError('TheCatAPI вернул пустой список')
    return data[0]['url']


_breeds_cache = []


async def get_breeds(api_key):
    """Список пород загружается один раз и дальше берётся из памяти."""
    if not _breeds_cache:
        _breeds_cache.extend(
            await get_json(CAT_BREEDS_URL, headers=cat_headers(api_key))
        )
    return _breeds_cache


def match_breed(breeds, query):
    """Порода по названию или id: сначала точное совпадение, потом начало."""
    query = query.strip().lower()
    for breed in breeds:
        if query in (breed['name'].lower(), breed['id'].lower()):
            return breed
    for breed in breeds:
        if breed['name'].lower().startswith(query):
            return breed
    return None


def format_breed(breed):
    text = (
        f'🐱 {breed["name"]}\n'
        f'Происхождение: {breed.get("origin", "—")}\n'
        f'Характер: {breed.get("temperament", "—")}\n'
        f'Продолжительность жизни: {breed.get("life_span", "—")} лет\n\n'
        f'{breed.get("description", "")}'
    )
    # Подпись к фото в Telegram — не длиннее 1024 символов
    return text if len(text) <= 1024 else text[:1023] + '…'
