"""Тесты бота TG03 без Telegram: апдейты подаются прямо в диспетчер.

Запуск: python -m unittest -v
"""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from aiogram import Bot
from aiogram.methods import SendMessage
from aiogram.types import Update

import bot as tg_bot
import database

CHAT_ID = 555


def make_update(update_id, text=None, sticker=False):
    message = {
        'message_id': update_id,
        'date': 0,
        'chat': {'id': CHAT_ID, 'type': 'private'},
        'from': {'id': CHAT_ID, 'is_bot': False, 'first_name': 'Ира'},
    }
    if sticker:
        message['sticker'] = {
            'file_id': 's', 'file_unique_id': 's', 'type': 'regular',
            'width': 1, 'height': 1, 'is_animated': False,
            'is_video': False,
        }
    else:
        message['text'] = text
        if text.startswith('/'):
            message['entities'] = [
                {'type': 'bot_command', 'offset': 0, 'length': len(text)}
            ]
    return Update.model_validate({'update_id': update_id, 'message': message})


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'school_data.db'
        database.init_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_table_structure(self):
        with closing(sqlite3.connect(self.db)) as conn:
            columns = conn.execute('PRAGMA table_info(students)').fetchall()
        self.assertEqual(
            [(c[1], c[2], c[5]) for c in columns],
            [('id', 'INTEGER', 1), ('name', 'TEXT', 0),
             ('age', 'INTEGER', 0), ('grade', 'TEXT', 0)],
        )
        with closing(sqlite3.connect(self.db)) as conn:
            sql = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name='students'"
            ).fetchone()[0]
        self.assertIn('AUTOINCREMENT', sql)

    def test_add_student_returns_new_id(self):
        first = database.add_student('Аня', 15, '9Б', self.db)
        second = database.add_student('Петя', 16, '10А', self.db)
        self.assertEqual((first, second), (1, 2))

    def test_sql_injection_is_stored_as_text(self):
        evil = "x'); DROP TABLE students; --"
        database.add_student(evil, 10, '4А', self.db)
        with closing(sqlite3.connect(self.db)) as conn:
            rows = conn.execute('SELECT name FROM students').fetchall()
        self.assertEqual(rows, [(evil,)])


class DialogTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'school_data.db'
        database.init_db(self.db)
        patcher = mock.patch.object(database, 'DB_PATH', self.db)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

        self.bot = Bot(token='123456:TEST-TOKEN')
        self.replies = []

        async def fake_call(method, request_timeout=None):
            if isinstance(method, SendMessage):
                self.replies.append(method.text)
            return mock.MagicMock()

        call_patch = mock.patch.object(Bot, '__call__', side_effect=fake_call)
        call_patch.start()
        self.addCleanup(call_patch.stop)
        self.update_id = 0
        # Хранилище состояний у диспетчера общее — очищаем перед тестом
        tg_bot.dp.storage.storage.clear()

    async def asyncTearDown(self):
        await self.bot.session.close()

    async def send(self, text=None, sticker=False):
        self.update_id += 1
        await tg_bot.dp.feed_update(
            self.bot, make_update(self.update_id, text, sticker)
        )
        return self.replies[-1]

    def students(self):
        with closing(sqlite3.connect(self.db)) as conn:
            return conn.execute(
                'SELECT id, name, age, grade FROM students'
            ).fetchall()

    async def test_full_dialog_saves_student(self):
        self.assertIn('Как тебя зовут?', await self.send('/start'))
        self.assertEqual(await self.send('Аня'), 'Сколько тебе лет?')
        self.assertIn('В каком классе', await self.send('15'))
        reply = await self.send('9б')
        self.assertIn('данные сохранены', reply)
        self.assertIn('Запись №1', reply)
        self.assertEqual(self.students(), [(1, 'Аня', 15, '9Б')])

    async def test_wrong_age_is_asked_again(self):
        await self.send('/start')
        await self.send('Аня')
        for bad in ('пятнадцать', '3', '150', '15.5'):
            self.assertIn('целое число', await self.send(bad))
        self.assertIn('В каком классе', await self.send('15'))

    async def test_sticker_instead_of_text(self):
        await self.send('/start')
        self.assertEqual(
            await self.send(sticker=True), 'Пожалуйста, ответь текстом.'
        )

    async def test_cancel(self):
        await self.send('/start')
        await self.send('Аня')
        self.assertIn('отменена', await self.send('/cancel'))
        self.assertIn('нечего отменять', await self.send('/cancel'))
        self.assertEqual(self.students(), [])

    async def test_text_after_dialog_is_ignored(self):
        await self.send('/start')
        await self.send('Аня')
        await self.send('15')
        await self.send('9Б')
        count = len(self.replies)
        self.update_id += 1
        await tg_bot.dp.feed_update(self.bot, make_update(self.update_id, 'привет'))
        self.assertEqual(len(self.replies), count)
        self.assertEqual(len(self.students()), 1)


if __name__ == '__main__':
    unittest.main()
