# chat_db.py
"""
Локальное хранилище чата (SQLite): rooms, messages, outbox.
Работает офлайн. Синхронизация с сервером — через sync.py.
"""
import os
import sqlite3
from datetime import datetime

from paths import service_path


# ────────────────────────────────────────────────────────────────
# Путь к БД
# ────────────────────────────────────────────────────────────────
def _db_path():
    return service_path('chat.db')


def _connect():
    con = sqlite3.connect(_db_path())
    con.row_factory = sqlite3.Row   # доступ по имени колонки
    return con


# ────────────────────────────────────────────────────────────────
# Инициализация схемы
# ────────────────────────────────────────────────────────────────
def init_db():
    """Создать таблицы, если их нет. Безопасно вызывать много раз."""
    con = _connect()
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY,
            kind TEXT,
            title TEXT,
            crwo_ref TEXT,
            last_read_id INTEGER DEFAULT 0,
            last_seen_id INTEGER DEFAULT 0,
            last_message_id INTEGER DEFAULT 0,
            unread_count INTEGER DEFAULT 0,
            muted INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            local_id INTEGER,
            room_id INTEGER NOT NULL,
            user_id INTEGER,
            author_name TEXT,
            body TEXT NOT NULL,
            attachment_url TEXT,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'sent'
        );
        CREATE INDEX IF NOT EXISTS idx_messages_room
            ON messages(room_id, id DESC);

        CREATE TABLE IF NOT EXISTS outbox (
            local_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            attachment_url TEXT,
            created_at TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            last_error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_outbox_room
            ON outbox(room_id, local_id);
    """)
    con.commit()
    con.close()
    print(f"[chat_db] init: {_db_path()}")


# ────────────────────────────────────────────────────────────────
# ROOMS
# ────────────────────────────────────────────────────────────────
def upsert_rooms(rooms_list):
    """
    Обновить/добавить комнаты из ответа сервера.
    rooms_list — список dict из /chat/rooms.
    """
    con = _connect()
    cur = con.cursor()
    for r in rooms_list:
        cur.execute("""
            INSERT INTO rooms (id, kind, title, crwo_ref,
                               last_read_id, last_message_id,
                               unread_count, muted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                kind = excluded.kind,
                title = excluded.title,
                crwo_ref = excluded.crwo_ref,
                last_read_id = excluded.last_read_id,
                last_message_id = excluded.last_message_id,
                unread_count = excluded.unread_count,
                muted = excluded.muted
        """, (
            r["id"],
            r.get("kind", ""),
            r.get("title", ""),
            r.get("crwo_ref"),
            r.get("last_read_id", 0),
            r.get("last_message_id", 0),
            r.get("unread_count", 0),
            1 if r.get("muted") else 0,
        ))
    con.commit()
    con.close()


def get_rooms():
    """Все комнаты, отсортированные по последнему сообщению (DESC)."""
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        SELECT * FROM rooms
        ORDER BY last_message_id DESC, id ASC
    """)
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_room(room_id):
    """Одна комната по id."""
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def set_last_read(room_id, value):
    """Отметить прочитанным до message_id=value."""
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE rooms SET last_read_id = ? WHERE id = ? AND last_read_id < ?",
        (value, room_id, value),
    )
    con.commit()
    con.close()


def set_last_seen(room_id, value):
    """Запомнить, до какого id мы скачали сообщения."""
    con = _connect()
    cur = con.cursor()
    cur.execute(
        "UPDATE rooms SET last_seen_id = ? WHERE id = ? AND last_seen_id < ?",
        (value, room_id, value),
    )
    con.commit()
    con.close()


def get_last_seen(room_id):
    """До какого message_id мы скачали сообщения."""
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT last_seen_id FROM rooms WHERE id = ?", (room_id,))
    row = cur.fetchone()
    con.close()
    return row["last_seen_id"] if row else 0


def recalc_unread(room_id=None):
    """
    Пересчитать unread_count для комнат.
    unread = сообщения с id > last_read_id и user_id != мой user_id.
    """
    from api_client import api
    my_id = api.user_id or 0

    con = _connect()
    cur = con.cursor()

    if room_id is None:
        cur.execute("SELECT id, last_read_id FROM rooms")
        rooms = cur.fetchall()
    else:
        cur.execute("SELECT id, last_read_id FROM rooms WHERE id = ?", (room_id,))
        rooms = cur.fetchall()

    for room in rooms:
        cur.execute("""
            SELECT COUNT(*) AS n FROM messages
            WHERE room_id = ? AND id > ? AND (user_id IS NULL OR user_id != ?)
        """, (room["id"], room["last_read_id"], my_id))
        n = cur.fetchone()["n"]
        cur.execute("UPDATE rooms SET unread_count = ? WHERE id = ?", (n, room["id"]))

    con.commit()
    con.close()


def get_total_unread():
    """Общее число непрочитанных сообщений по всем комнатам."""
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT COALESCE(SUM(unread_count), 0) AS n FROM rooms WHERE muted = 0")
    n = cur.fetchone()["n"]
    con.close()
    return n


# ────────────────────────────────────────────────────────────────
# MESSAGES
# ────────────────────────────────────────────────────────────────
def save_incoming_batch(messages_list):
    """
    Сохранить массив сообщений с сервера.
    messages_list — список dict с полями id, room_id, user_id, author_name, body, created_at.
    """
    if not messages_list:
        return

    con = _connect()
    cur = con.cursor()
    for m in messages_list:
        cur.execute("""
            INSERT OR IGNORE INTO messages
            (id, room_id, user_id, author_name, body, attachment_url, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'sent')
        """, (
            m["id"],
            m["room_id"],
            m.get("user_id"),
            m.get("author_name", "?"),
            m.get("body", ""),
            m.get("attachment_url"),
            m.get("created_at", datetime.now().isoformat()),
        ))
    con.commit()
    con.close()

    # После сохранения — пересчитать unread
    room_ids = {m["room_id"] for m in messages_list}
    for rid in room_ids:
        recalc_unread(rid)


def save_local_message(room_id, body, local_id, created_at=None):
    """
    Сохранить исходящее сообщение локально (пока не отправлено).
    Возвращает local_id.
    """
    if created_at is None:
        created_at = datetime.now().isoformat()

    con = _connect()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO messages
        (id, local_id, room_id, user_id, author_name, body, created_at, status)
        VALUES (NULL, ?, ?, NULL, NULL, ?, ?, 'pending')
    """, (local_id, room_id, body, created_at))
    con.commit()
    con.close()


def move_outbox_to_messages(local_id, server_id, server_created_at=None):
    """
    После успешной отправки — обновить локальное сообщение.
    Присвоить ему серверный id и статус 'sent'.
    """
    con = _connect()
    cur = con.cursor()

    # Обновить сообщение
    if server_created_at:
        cur.execute("""
            UPDATE messages
            SET id = ?, created_at = ?, status = 'sent'
            WHERE local_id = ?
        """, (server_id, server_created_at, local_id))
    else:
        cur.execute("""
            UPDATE messages
            SET id = ?, status = 'sent'
            WHERE local_id = ?
        """, (server_id, local_id))

    # Удалить из outbox
    cur.execute("DELETE FROM outbox WHERE local_id = ?", (local_id,))

    con.commit()
    con.close()


def get_messages(room_id, limit=200):
    """
    Все сообщения комнаты, отсортированные по id (ASC).
    Сначала — pending (у которых id NULL), потом sent.
    """
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        SELECT * FROM messages
        WHERE room_id = ?
        ORDER BY
            CASE WHEN id IS NULL THEN 0 ELSE 1 END,
            COALESCE(id, 999999999999),
            local_id ASC
        LIMIT ?
    """, (room_id, limit))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_max_message_id(room_id):
    """Максимальный серверный id в комнате (не учитывает pending)."""
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) AS m FROM messages WHERE room_id = ?", (room_id,))
    m = cur.fetchone()["m"]
    con.close()
    return m


def delete_room(room_id):
    """Удалить комнату и её сообщения (при выходе из неё)."""
    con = _connect()
    cur = con.cursor()
    cur.execute("DELETE FROM messages WHERE room_id = ?", (room_id,))
    cur.execute("DELETE FROM outbox WHERE room_id = ?", (room_id,))
    cur.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    con.commit()
    con.close()


# ────────────────────────────────────────────────────────────────
# OUTBOX
# ────────────────────────────────────────────────────────────────
def add_to_outbox(room_id, body, attachment_url=None):
    """Добавить сообщение в очередь отправки. Возвращает local_id."""
    con = _connect()
    cur = con.cursor()
    created_at = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO outbox (room_id, body, attachment_url, created_at)
        VALUES (?, ?, ?, ?)
    """, (room_id, body, attachment_url, created_at))
    local_id = cur.lastrowid

    # Дублируем в messages со статусом pending
    cur.execute("""
        INSERT INTO messages
        (id, local_id, room_id, user_id, author_name, body, attachment_url, created_at, status)
        VALUES (NULL, ?, ?, NULL, NULL, ?, ?, ?, 'pending')
    """, (local_id, room_id, body, attachment_url, created_at))

    con.commit()
    con.close()
    return local_id


def get_pending_outbox(limit=50):
    """Список сообщений из очереди отправки."""
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        SELECT * FROM outbox
        WHERE attempts < 5
        ORDER BY local_id ASC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_outbox_item(local_id):
    """Одно сообщение из очереди."""
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM outbox WHERE local_id = ?", (local_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def mark_outbox_failed(local_id, error):
    """Увеличить счётчик попыток и записать ошибку."""
    con = _connect()
    cur = con.cursor()
    cur.execute("""
        UPDATE outbox
        SET attempts = attempts + 1, last_error = ?
        WHERE local_id = ?
    """, (str(error)[:200], local_id))
    con.commit()
    con.close()


# ────────────────────────────────────────────────────────────────
# УТИЛИТЫ
# ────────────────────────────────────────────────────────────────
def count_unread_total():
    """Быстрый подсчёт непрочитанных (без запроса к api)."""
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT COALESCE(SUM(unread_count), 0) AS n FROM rooms WHERE muted = 0")
    n = cur.fetchone()["n"]
    con.close()
    return n