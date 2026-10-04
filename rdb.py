# rdb.py
"""
Хранилище базы данных БС в SQLite (/service/rdb.db).
Наружу отдаёт тот же словарь {bs: {field: value}}, что и RDB.pickle,
чтобы не переписывать логику экранов.
"""
import os
import sys
import sqlite3

# ── Поля, которые храним в БД ──
RDB_FIELDS = [
    "arc_id",
    "address",
    "latitude",
    "longitude",
    "coordinates",
    "yandex_map",
    "constructional_type",
    "rent",
    "status",
    "priority",
    "transmission",
    "hw_room",
    "builder",
    "contractor",
    "exploiter",
    "service_center",
    "transmissionist",
    "access",
]

# Поля, которые должны быть REAL/INTEGER, а не TEXT
NUMERIC_FIELDS = {"latitude", "longitude"}


def _service_dir():
    """Папка service/ рядом с .exe / main.py — НЕ в _MEIPASS."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "service")
    os.makedirs(d, exist_ok=True)
    return d


def db_path():
    return os.path.join(_service_dir(), "rdb.db")


# ────────────────────────────────────────────────────────────────
# Схема
# ────────────────────────────────────────────────────────────────
def init_db():
    """Создаёт таблицу, если её нет. Безопасно вызывать много раз."""
    con = sqlite3.connect(db_path())
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bs (
            bs_key TEXT PRIMARY KEY,
            arc_id TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            coordinates TEXT,
            yandex_map TEXT,
            constructional_type TEXT,
            rent TEXT,
            status TEXT,
            priority TEXT,
            transmission TEXT,
            hw_room TEXT,
            builder TEXT,
            contractor TEXT,
            exploiter TEXT,
            service_center TEXT,
            transmissionist TEXT,
            access TEXT
        )
    """)
    # Индекс по адресу — ускоряет поиск в режиме «Адрес»
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bs_address ON bs(address)")
    con.commit()
    con.close()


# ────────────────────────────────────────────────────────────────
# Запись
# ────────────────────────────────────────────────────────────────
def save_rdb(bs_dict, replace=True):
    """
    Сохраняет словарь {bs: {field: value}} в БД.
    replace=True  — полностью заменить таблицу (как rdb_update).
    replace=False — дополнить / обновить существующие записи.
    """
    init_db()
    con = sqlite3.connect(db_path())
    cur = con.cursor()

    if replace:
        cur.execute("DELETE FROM bs")

    cols = ", ".join(RDB_FIELDS)
    placeholders = ", ".join(["?"] * len(RDB_FIELDS))
    sql = (
        f"INSERT OR REPLACE INTO bs (bs_key, {cols}) "
        f"VALUES (?, {placeholders})"
    )

    for bs, info in bs_dict.items():
        row = [bs]
        for f in RDB_FIELDS:
            v = info.get(f)
            if f in NUMERIC_FIELDS:
                try:
                    v = float(v) if v not in (None, "") else None
                except (TypeError, ValueError):
                    v = None
            else:
                v = "" if v is None else str(v)
            row.append(v)
        cur.execute(sql, row)

    con.commit()
    con.close()


# ────────────────────────────────────────────────────────────────
# Чтение
# ────────────────────────────────────────────────────────────────
def load_rdb():
    """Возвращает словарь {bs: {field: value}}. Пустой dict, если БД нет."""
    if not os.path.exists(db_path()):
        return {}

    try:
        con = sqlite3.connect(db_path())
        cur = con.cursor()
        cur.execute(f"SELECT bs_key, {', '.join(RDB_FIELDS)} FROM bs")
        rows = cur.fetchall()
        con.close()
    except Exception as e:
        print(f"[rdb] load error: {e}")
        return {}

    result = {}
    for row in rows:
        bs = row[0]
        info = {}
        for i, f in enumerate(RDB_FIELDS, start=1):
            info[f] = row[i]
        # coordinates / yandex_map — восстановим, если пусты
        if not info.get("coordinates"):
            lat, lon = info.get("latitude"), info.get("longitude")
            if lat is not None and lon is not None:
                info["coordinates"] = f"{lat} {lon}"
        if not info.get("yandex_map"):
            lat, lon = info.get("latitude"), info.get("longitude")
            if lat is not None and lon is not None:
                info["yandex_map"] = (
                    f"https://yandex.ru/navi/?whatshere%5Bzoom%5D=17"
                    f"&whatshere%5Bpoint%5D={lon}%2C{lat}"
                )
        result[bs] = info
    return result


def is_empty():
    """True, если таблица пуста или БД не существует."""
    if not os.path.exists(db_path()):
        return True
    try:
        con = sqlite3.connect(db_path())
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM bs")
        n = cur.fetchone()[0]
        con.close()
        return n == 0
    except Exception:
        return True