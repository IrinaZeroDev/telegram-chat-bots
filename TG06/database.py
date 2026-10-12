"""Работа с базой данных user.db (таблица users)."""
import sqlite3
from contextlib import closing
from pathlib import Path

# База лежит рядом с ботом, откуда бы его ни запускали
DB_PATH = Path(__file__).resolve().parent / 'user.db'


def connect(db_path=None):
    """Открывает соединение; closing() гарантирует, что оно закроется."""
    return closing(sqlite3.connect(db_path or DB_PATH))


def init_db(db_path=None):
    """Создаёт таблицу users, если её ещё нет.

    telegram_id — UNIQUE: один пользователь Telegram — одна строка.
    Категории расходов — TEXT, суммы — REAL (дробные числа).
    """
    with connect(db_path) as conn, conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                category1 TEXT,
                category2 TEXT,
                category3 TEXT,
                expenses1 REAL,
                expenses2 REAL,
                expenses3 REAL
            )
        ''')


def is_registered(telegram_id, db_path=None):
    with connect(db_path) as conn:
        row = conn.execute(
            'SELECT 1 FROM users WHERE telegram_id = ?', (telegram_id,)
        ).fetchone()
    return row is not None


def register(telegram_id, name, db_path=None):
    """Добавляет пользователя. Возвращает False, если он уже был."""
    with connect(db_path) as conn, conn:
        # INSERT OR IGNORE пропускает вставку, если такой telegram_id есть,
        # rowcount показывает, добавилась ли строка
        cursor = conn.execute(
            'INSERT OR IGNORE INTO users (telegram_id, name) VALUES (?, ?)',
            (telegram_id, name),
        )
        return cursor.rowcount == 1


def save_expenses(telegram_id, expenses, db_path=None):
    """Сохраняет три пары (категория, сумма) в строку пользователя."""
    (category1, expenses1), (category2, expenses2), (category3, expenses3) = \
        expenses
    with connect(db_path) as conn, conn:
        conn.execute(
            '''UPDATE users
               SET category1 = ?, expenses1 = ?,
                   category2 = ?, expenses2 = ?,
                   category3 = ?, expenses3 = ?
               WHERE telegram_id = ?''',
            (category1, expenses1, category2, expenses2,
             category3, expenses3, telegram_id),
        )


def get_user(telegram_id, db_path=None):
    """Строка пользователя словарём или None."""
    with connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)
        ).fetchone()
    return dict(row) if row else None
