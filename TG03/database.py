"""Работа с базой данных school_data.db (таблица students)."""
import sqlite3
from contextlib import closing
from pathlib import Path

# База лежит рядом с ботом, откуда бы его ни запускали
DB_PATH = Path(__file__).resolve().parent / 'school_data.db'


def connect(db_path=None):
    """Открывает соединение; closing() гарантирует, что оно закроется."""
    return closing(sqlite3.connect(db_path or DB_PATH))


def init_db(db_path=None):
    """Создаёт таблицу students, если её ещё нет."""
    with connect(db_path) as conn, conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                grade TEXT NOT NULL
            )
        ''')


def add_student(name, age, grade, db_path=None):
    """Добавляет ученика и возвращает номер (id) новой записи.

    Значения передаются через «?», а не подставляются в текст запроса:
    так введённый пользователем текст не может изменить сам SQL-запрос.
    """
    with connect(db_path) as conn, conn:
        cursor = conn.execute(
            'INSERT INTO students (name, age, grade) VALUES (?, ?, ?)',
            (name, age, grade),
        )
        return cursor.lastrowid
