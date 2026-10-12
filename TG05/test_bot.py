"""Тесты бота TG05 без Telegram и без интернета.

Апдейты подаются прямо в диспетчер, а функции внешних API подменяются
заглушками с заранее известными ответами.

Запуск: python -m unittest -v
"""
import unittest
from unittest import mock

from aiogram import Bot
from aiogram.methods import SendMessage, SendPhoto
from aiogram.types import ReplyKeyboardMarkup, Update

import api
import bot as tg_bot
import config

CHAT_ID = 555
USER = {'id': CHAT_ID, 'is_bot': False, 'first_name': 'Ирина'}
CHAT = {'id': CHAT_ID, 'type': 'private'}

KAZAN = {'name': 'Казань', 'country': 'Россия',
         'latitude': 55.79, 'longitude': 49.12}
CURRENT = {'temperature_2m': 12.6, 'apparent_temperature': 10.8,
           'relative_humidity_2m': 71, 'weather_code': 3,
           'wind_speed_10m': 2.04}
RATES = {
    'Date': '2026-10-13T11:30:00+03:00',
    'Valute': {
        'USD': {'CharCode': 'USD', 'Name': 'Доллар США', 'Nominal': 1,
                'Value': 83.9194, 'Previous': 84.9101},
        'EUR': {'CharCode': 'EUR', 'Name': 'Евро', 'Nominal': 1,
                'Value': 94.0407, 'Previous': 93.5},
        'CNY': {'CharCode': 'CNY', 'Name': 'Юань', 'Nominal': 1,
                'Value': 12.5432, 'Previous': 12.5432},
        'KZT': {'CharCode': 'KZT', 'Name': 'Тенге', 'Nominal': 100,
                'Value': 16.5, 'Previous': 16.4},
    },
}
BREEDS = [
    {'id': 'beng', 'name': 'Bengal', 'origin': 'United States',
     'temperament': 'Alert, Agile', 'life_span': '12 - 15',
     'description': 'Bengals are a lot of fun.'},
    {'id': 'siam', 'name': 'Siamese', 'origin': 'Thailand',
     'temperament': 'Active, Social', 'life_span': '12 - 15',
     'description': 'Siamese love to talk.'},
]
CAT_URL = 'https://cdn2.thecatapi.com/images/test.jpg'


class FormatTests(unittest.TestCase):
    def test_weather_text(self):
        self.assertEqual(api.format_weather(KAZAN, CURRENT), (
            'Погода: Казань, Россия\n'
            '☁️ пасмурно\n'
            '🌡 +13 °C, ощущается как +11 °C\n'
            '💧 влажность 71 %\n'
            '💨 ветер 2.0 м/с'
        ))

    def test_unknown_weather_code(self):
        text = api.format_weather(KAZAN, {**CURRENT, 'weather_code': 42})
        self.assertIn('без описания', text)

    def test_rates_default_currencies(self):
        self.assertEqual(api.format_rates(RATES), (
            '💱 Курсы ЦБ РФ на 13.10.2026\n'
            'USD (Доллар США): 83.92 ₽ ▼ 0.99\n'
            'EUR (Евро): 94.04 ₽ ▲ 0.54\n'
            'CNY (Юань): 12.54 ₽ = 0.00'
        ))

    def test_rate_is_per_one_unit(self):
        text = api.format_rates(RATES, ['kzt', 'XYZ'])
        self.assertIn('KZT (Тенге): 0.17 ₽ ▲ 0.00', text)
        self.assertIn('Не знаю валюты: XYZ', text)

    def test_match_breed(self):
        self.assertEqual(api.match_breed(BREEDS, ' SIAMESE ')['id'], 'siam')
        self.assertEqual(api.match_breed(BREEDS, 'beng')['id'], 'beng')
        self.assertEqual(api.match_breed(BREEDS, 'Sia')['id'], 'siam')
        self.assertIsNone(api.match_breed(BREEDS, 'Мейн-кун'))

    def test_breed_caption_fits_telegram_limit(self):
        long_breed = {**BREEDS[0], 'description': 'м' * 2000}
        self.assertEqual(len(api.format_breed(long_breed)), 1024)


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = Bot(token='123456:TEST-TOKEN')
        self.calls = []

        async def fake_call(method, request_timeout=None):
            self.calls.append(method)
            return mock.MagicMock()

        self.patch(Bot, '__call__', side_effect=fake_call)
        self.find_city = self.patch(api, 'find_city', return_value=KAZAN)
        self.get_weather = self.patch(api, 'get_weather',
                                      return_value=CURRENT)
        self.get_rates = self.patch(api, 'get_rates', return_value=RATES)
        self.random_cat = self.patch(api, 'random_cat', return_value=CAT_URL)
        self.get_breeds = self.patch(api, 'get_breeds', return_value=BREEDS)
        self.update_id = 0
        # Хранилище состояний у диспетчера общее — очищаем перед тестом
        tg_bot.dp.storage.storage.clear()

    def patch(self, target, name, **kwargs):
        if name != '__call__':
            kwargs.setdefault('new_callable', mock.AsyncMock)
        patcher = mock.patch.object(target, name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    async def asyncTearDown(self):
        await self.bot.session.close()

    async def send(self, text):
        self.update_id += 1
        message = {'message_id': self.update_id, 'date': 0,
                   'chat': CHAT, 'from': USER, 'text': text}
        if text.startswith('/'):
            length = len(text.split()[0])
            message['entities'] = [
                {'type': 'bot_command', 'offset': 0, 'length': length}
            ]
        update = Update.model_validate(
            {'update_id': self.update_id, 'message': message}
        )
        await tg_bot.dp.feed_update(self.bot, update)
        return self.calls[-1]

    async def test_start_shows_menu(self):
        reply = await self.send('/start')
        self.assertIn('/weather', reply.text)
        self.assertIsInstance(reply.reply_markup, ReplyKeyboardMarkup)

    async def test_weather_with_city_argument(self):
        reply = await self.send('/weather Казань')
        self.find_city.assert_awaited_once_with('Казань')
        self.get_weather.assert_awaited_once_with(KAZAN)
        self.assertTrue(reply.text.startswith('Погода: Казань, Россия'))

    async def test_weather_button_asks_city_then_answers(self):
        reply = await self.send('🌤 Погода')
        self.assertEqual(reply.text, 'В каком городе узнать погоду?')
        reply = await self.send('Казань')
        self.find_city.assert_awaited_once_with('Казань')
        self.assertTrue(reply.text.startswith('Погода: Казань'))
        # Состояние сброшено: следующий текст — уже не город
        reply = await self.send('Москва')
        self.assertIn('Не понял', reply.text)

    async def test_other_button_while_waiting_for_city(self):
        await self.send('🌤 Погода')
        reply = await self.send('💱 Курсы валют')
        self.assertIn('Курсы ЦБ РФ', reply.text)
        self.find_city.assert_not_awaited()

    async def test_city_not_found(self):
        self.find_city.return_value = None
        reply = await self.send('/weather Ыыы')
        self.assertEqual(reply.text, 'Не нашёл город «Ыыы». Проверь название.')
        self.get_weather.assert_not_awaited()

    async def test_service_unavailable(self):
        self.get_rates.side_effect = api.ApiError('timeout')
        with self.assertLogs(tg_bot.logger, 'ERROR'):
            reply = await self.send('/rates')
        self.assertEqual(reply.text, tg_bot.UNAVAILABLE)

    async def test_rates_with_codes(self):
        reply = await self.send('/rates usd kzt')
        self.assertIn('USD (Доллар США)', reply.text)
        self.assertIn('KZT (Тенге)', reply.text)
        self.assertNotIn('EUR', reply.text)

    async def test_random_cat_photo(self):
        reply = await self.send('🐱 Котик')
        self.assertIsInstance(reply, SendPhoto)
        self.assertEqual(reply.photo, CAT_URL)

    async def test_breed_without_key_sends_random_cat(self):
        with mock.patch.object(config, 'THE_CAT_API_KEY', ''):
            await self.send('/cat Siamese')
        texts = [c.text for c in self.calls if isinstance(c, SendMessage)]
        self.assertIn('ключом TheCatAPI', texts[0])
        self.assertIsInstance(self.calls[-1], SendPhoto)
        self.get_breeds.assert_not_awaited()

    async def test_breed_with_key(self):
        with mock.patch.object(config, 'THE_CAT_API_KEY', 'key'):
            reply = await self.send('/cat siamese')
        self.random_cat.assert_awaited_once_with('key', 'siam')
        self.assertIsInstance(reply, SendPhoto)
        self.assertTrue(reply.caption.startswith('🐱 Siamese'))

    async def test_unknown_breed(self):
        with mock.patch.object(config, 'THE_CAT_API_KEY', 'key'):
            reply = await self.send('/cat Мейн-кун')
        self.assertIn('Не знаю породу «Мейн-кун»', reply.text)
        self.random_cat.assert_not_awaited()


if __name__ == '__main__':
    unittest.main()
