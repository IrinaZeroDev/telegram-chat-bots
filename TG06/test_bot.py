"""Тесты финансового бота без Telegram и без интернета.

Запуск: python -m unittest -v
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import aiohttp
from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import ReplyKeyboardMarkup, Update

import bot as tg_bot
import database
import keyboards as kb

CHAT_ID = 555
USER = {'id': CHAT_ID, 'is_bot': False, 'first_name': 'Ирина',
        'last_name': 'Иванова'}
CHAT = {'id': CHAT_ID, 'type': 'private'}
RATES = {'USD': 1, 'RUB': 80.0, 'EUR': 0.8}


class HelperTests(unittest.TestCase):
    def test_parse_amount(self):
        cases = {'1500': 1500.0, '249,90': 249.9, '1 500.5': 1500.5,
                 '0': 0.0, 'сто': None, '-5': None, 'nan': None,
                 'inf': None, '': None}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(tg_bot.parse_amount(text), expected)

    def test_money(self):
        self.assertEqual(tg_bot.money(12345.5), '12 345.50 ₽')


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / 'user.db'
        database.init_db(self.db)

    def test_register_once(self):
        self.assertTrue(database.register(1, 'Аня', self.db))
        self.assertFalse(database.register(1, 'Аня', self.db))
        self.assertTrue(database.is_registered(1, self.db))
        self.assertFalse(database.is_registered(2, self.db))

    def test_save_expenses(self):
        database.register(1, 'Аня', self.db)
        database.register(2, 'Петя', self.db)
        database.save_expenses(
            1, [('Еда', 100.0), ('Кино', 20.5), ('Такси', 7.0)], self.db
        )
        user = database.get_user(1, self.db)
        self.assertEqual(
            [user[k] for k in ('category1', 'expenses1', 'category2',
                               'expenses2', 'category3', 'expenses3')],
            ['Еда', 100.0, 'Кино', 20.5, 'Такси', 7.0],
        )
        # Чужая строка не изменилась
        self.assertIsNone(database.get_user(2, self.db)['category1'])


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / 'user.db'
        database.init_db(self.db)
        self.patch(database, 'DB_PATH', new=self.db)
        self.fetch_rates = self.patch(
            tg_bot, 'fetch_rates', new_callable=mock.AsyncMock,
            return_value=RATES,
        )

        self.bot = Bot(token='123456:TEST-TOKEN')
        self.calls = []

        async def fake_call(method, request_timeout=None):
            self.calls.append(method)
            return mock.MagicMock()

        self.patch(Bot, '__call__', side_effect=fake_call)
        self.update_id = 0
        # Хранилище состояний у диспетчера общее — очищаем перед тестом
        tg_bot.dp.storage.storage.clear()

    def patch(self, target, name, **kwargs):
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
            message['entities'] = [
                {'type': 'bot_command', 'offset': 0, 'length': len(text)}
            ]
        update = Update.model_validate(
            {'update_id': self.update_id, 'message': message}
        )
        await tg_bot.dp.feed_update(self.bot, update)
        return self.calls[-1].text

    async def test_start_shows_menu(self):
        await self.send('/start')
        markup = self.calls[-1].reply_markup
        self.assertIsInstance(markup, ReplyKeyboardMarkup)
        self.assertEqual(
            [b.text for row in markup.keyboard for b in row],
            [kb.REGISTER, kb.RATES, kb.TIPS, kb.FINANCES],
        )

    async def test_registration(self):
        self.assertEqual(await self.send(kb.REGISTER),
                         'Вы успешно зарегистрированы!')
        self.assertEqual(await self.send(kb.REGISTER),
                         'Вы уже зарегистрированы!')
        self.assertEqual(database.get_user(CHAT_ID)['name'], 'Ирина Иванова')

    async def test_exchange_rates(self):
        self.assertEqual(await self.send(kb.RATES),
                         '1 USD - 80.00 RUB\n1 EUR - 100.00 RUB')

    async def test_exchange_rates_error(self):
        self.fetch_rates.side_effect = aiohttp.ClientError()
        with self.assertLogs(tg_bot.logger, 'ERROR'):
            reply = await self.send(kb.RATES)
        self.assertEqual(reply, 'Не удалось получить данные о курсе валют!')

    async def test_tip_is_from_list(self):
        self.assertIn(await self.send(kb.TIPS), tg_bot.TIPS)

    async def test_finances_require_registration(self):
        reply = await self.send(kb.FINANCES)
        self.assertIn('Сначала нажмите', reply)
        self.assertIn('Сейчас нечего отменять', await self.send('/cancel'))

    async def test_full_finances_dialog(self):
        await self.send(kb.REGISTER)
        self.assertIn('первую категорию', await self.send(kb.FINANCES))
        self.assertIn('категории 1', await self.send('Еда'))
        self.assertIn('числом', await self.send('много'))
        self.assertIn('вторую категорию', await self.send('12 000,50'))
        self.assertIn('категории 2', await self.send('Транспорт'))
        self.assertIn('третью категорию', await self.send('3000'))
        self.assertIn('категории 3', await self.send('Развлечения'))
        reply = await self.send('2500')
        self.assertIn('Категории и расходы сохранены!', reply)
        self.assertIn('• Еда: 12 000.50 ₽', reply)
        self.assertIn('Итого: 17 500.50 ₽', reply)

        user = database.get_user(CHAT_ID)
        self.assertEqual(
            (user['category1'], user['expenses1'], user['category3'],
             user['expenses3']),
            ('Еда', 12000.5, 'Развлечения', 2500.0),
        )
        # Состояние сброшено: после диалога снова работает меню
        self.assertIn(await self.send(kb.TIPS), tg_bot.TIPS)

    async def test_menu_button_interrupts_dialog(self):
        await self.send(kb.REGISTER)
        await self.send(kb.FINANCES)
        self.assertIn('1 USD', await self.send(kb.RATES))
        self.assertIsNone(database.get_user(CHAT_ID)['category1'])
        self.assertIn('Сейчас нечего отменять', await self.send('/cancel'))

    async def test_cancel(self):
        await self.send(kb.REGISTER)
        await self.send(kb.FINANCES)
        await self.send('Еда')
        self.assertEqual(await self.send('/cancel'), 'Ввод расходов отменён.')
        self.assertIsNone(database.get_user(CHAT_ID)['category1'])


if __name__ == '__main__':
    unittest.main()
