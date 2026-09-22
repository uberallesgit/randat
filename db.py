"""
SQLite-хранилище пользователей для экрана логина/регистрации.

Пароль никогда не хранится в открытом виде: для каждого пользователя
генерируется случайная соль, а хеш пароля считается через PBKDF2-HMAC
(модуль hashlib из стандартной библиотеки Python — внешние зависимости
не нужны).
"""

import hashlib
import secrets
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("users.db")

_PBKDF2_ITERATIONS = 200_000
_HASH_ALGO = "sha256"


class UserAlreadyExists(Exception):
    """Пользователь с такими именем и фамилией уже зарегистрирован."""


def _get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """
    Создаёт таблицу users, если её ещё нет.
    Вызывать один раз при старте приложения (например, в App.on_start).
    """
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name    TEXT NOT NULL,
                last_name     TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                salt          TEXT NOT NULL,
                UNIQUE (first_name, last_name)
            )
            """
        )


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        _HASH_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    ).hex()


def register_user(first_name: str, last_name: str, password: str) -> None:
    """
    Регистрирует нового пользователя.
    Бросает UserAlreadyExists, если пользователь с таким именем и фамилией уже есть.
    """
    first_name = first_name.strip()
    last_name = last_name.strip()

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)

    try:
        with _get_connection() as conn:
            conn.execute(
                "INSERT INTO users (first_name, last_name, password_hash, salt) "
                "VALUES (?, ?, ?, ?)",
                (first_name, last_name, password_hash, salt.hex()),
            )
    except sqlite3.IntegrityError as exc:
        raise UserAlreadyExists(
            f"Пользователь {first_name} {last_name} уже зарегистрирован"
        ) from exc


def verify_user(first_name: str, last_name: str, password: str) -> bool:
    """Возвращает True, если имя/фамилия/пароль совпадают с записью в базе."""
    first_name = first_name.strip()
    last_name = last_name.strip()

    with _get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash, salt FROM users WHERE first_name = ? AND last_name = ?",
            (first_name, last_name),
        ).fetchone()

    if row is None:
        return False

    stored_hash, salt_hex = row
    candidate_hash = _hash_password(password, bytes.fromhex(salt_hex))
    return secrets.compare_digest(candidate_hash, stored_hash)
