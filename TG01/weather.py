import requests
from config import WEATHER_API_KEY, CITY, CITY_RU, LANG, UNITS

def get_weather():
    """
    Получает прогноз погоды из OpenWeatherMap API
    Возвращает: строку с температурой и описанием погоды
    """
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": CITY,
            "appid": WEATHER_API_KEY,
            "lang": LANG,
            "units": UNITS
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Проверяет ошибки HTTP
        
        data = response.json()
        
        # Экстрактируем нужные данные
        temperature = data['main']['temp']
        description = data['weather'][0]['description']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        pressure = data['main']['pressure']
        wind_speed = data['wind']['speed']
        
        # Формируем сообщение с погодой
        weather_message = (
            f"\ud83c\udf2c Погода в г. {CITY_RU}:\n\n"
            f"🌡️ Температура: {temperature}°C\n"
            f"🌫 Ощущается как: {feels_like}°C\n"
            f"📊 Описание: {description.capitalize()}\n"
            f"💧 Влажность: {humidity}%\n"
            f"📉 Давление: {pressure} эМ\n"
            f"🌬 Скорость ветра: {wind_speed} м/с"
        )
        
        return weather_message
    
    except requests.exceptions.RequestException as e:
        return f"❌ Ошибка при запросе к API: {str(e)}"
    except KeyError:
        return "❌ Основные данные твсо не найдены. Повторите попытку."
    except Exception as e:
        return f"❌ Непревиденная ошибка: {str(e)}"
