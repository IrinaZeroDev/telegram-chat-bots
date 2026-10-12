"""Тесты бота TG04 без Telegram: апдейты подаются прямо в диспетчер.

Запуск: python -m unittest -v
"""
import unittest
from unittest import mock

from aiogram import Bot
from aiogram.methods import (
    AnswerCallbackQuery,
    EditMessageReplyMarkup,
    SendMessage,
)
from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)

import bot as tg_bot
import keyboards as kb

CHAT_ID = 555
USER = {'id': CHAT_ID, 'is_bot': False, 'first_name': 'Ирина',
        'username': 'irina'}
CHAT = {'id': CHAT_ID, 'type': 'private'}


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = Bot(token='123456:TEST-TOKEN')
        self.calls = []

        async def fake_call(method, request_timeout=None):
            self.calls.append(method)
            return mock.MagicMock()

        patcher = mock.patch.object(Bot, '__call__', side_effect=fake_call)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.update_id = 0

    async def asyncTearDown(self):
        await self.bot.session.close()

    async def feed(self, **payload):
        self.update_id += 1
        update = Update.model_validate({'update_id': self.update_id, **payload})
        await tg_bot.dp.feed_update(self.bot, update)

    async def send_text(self, text, user=USER):
        message = {'message_id': self.update_id + 1, 'date': 0,
                   'chat': CHAT, 'from': user, 'text': text}
        if text.startswith('/'):
            message['entities'] = [
                {'type': 'bot_command', 'offset': 0, 'length': len(text)}
            ]
        await self.feed(message=message)

    async def press(self, data):
        bot_message = {'message_id': 100, 'date': 0, 'chat': CHAT,
                       'from': {'id': 1, 'is_bot': True, 'first_name': 'bot'},
                       'text': 'Нажми кнопку:'}
        await self.feed(callback_query={
            'id': f'cb{self.update_id}', 'from': USER, 'chat_instance': 'ci',
            'message': bot_message, 'data': data,
        })

    def sent(self, kind):
        return [c for c in self.calls if isinstance(c, kind)]

    # Задание 1
    async def test_start_shows_reply_menu(self):
        await self.send_text('/start')
        markup = self.sent(SendMessage)[-1].reply_markup
        self.assertIsInstance(markup, ReplyKeyboardMarkup)
        self.assertTrue(markup.resize_keyboard)
        self.assertEqual(
            [b.text for row in markup.keyboard for b in row],
            ['Привет', 'Пока'],
        )

    async def test_hello_and_bye_use_user_name(self):
        await self.send_text('Привет')
        await self.send_text('Пока')
        texts = [m.text for m in self.sent(SendMessage)]
        self.assertEqual(texts, ['Привет, Ирина!', 'До свидания, Ирина!'])

    async def test_name_falls_back_to_username(self):
        user = {'id': 7, 'is_bot': False, 'first_name': '',
                'username': 'irina'}
        await self.send_text('Привет', user=user)
        self.assertEqual(self.sent(SendMessage)[-1].text, 'Привет, irina!')

    # Задание 2
    async def test_links_are_three_url_buttons(self):
        await self.send_text('/links')
        markup = self.sent(SendMessage)[-1].reply_markup
        self.assertIsInstance(markup, InlineKeyboardMarkup)
        buttons = [b for row in markup.inline_keyboard for b in row]
        self.assertEqual(len(buttons), 3)
        for button in buttons:
            self.assertTrue(button.url.startswith('https://'))
        self.assertEqual(
            [b.text for b in buttons], ['📰 Новости', '🎵 Музыка', '🎬 Видео']
        )

    # Задание 3
    async def test_dynamic_shows_single_button(self):
        await self.send_text('/dynamic')
        markup = self.sent(SendMessage)[-1].reply_markup
        buttons = [b for row in markup.inline_keyboard for b in row]
        self.assertEqual([b.text for b in buttons], ['Показать больше'])
        self.assertEqual(buttons[0].callback_data, kb.SHOW_MORE)

    async def test_show_more_replaces_button_with_options(self):
        await self.press(kb.SHOW_MORE)
        edit = self.sent(EditMessageReplyMarkup)[-1]
        self.assertEqual(edit.message_id, 100)
        buttons = [b for row in edit.reply_markup.inline_keyboard for b in row]
        self.assertEqual([b.text for b in buttons], ['Опция 1', 'Опция 2'])
        self.assertEqual(len(self.sent(AnswerCallbackQuery)), 1)
        self.assertEqual(self.sent(SendMessage), [])

    async def test_option_sends_its_text(self):
        await self.press('option_1')
        await self.press('option_2')
        texts = [m.text for m in self.sent(SendMessage)]
        self.assertEqual(texts, ['Вы выбрали: Опция 1', 'Вы выбрали: Опция 2'])
        self.assertEqual(len(self.sent(AnswerCallbackQuery)), 2)


if __name__ == '__main__':
    unittest.main()
