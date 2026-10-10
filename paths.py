# paths.py
"""
Утилиты путей, не зависящие от main.py.
Используется и в main.py, и в api_client.py, и в rdb.py, и в chat_db.py,
чтобы избежать циклических импортов.
"""
import os
import sys


def resource_path(relative_path):
    """Пути к ресурсам внутри APK (только для чтения)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def service_path(filename):
    """Файлы service/ — рядом с .exe / main.py — НЕ в _MEIPASS.
    На Android это приватная папка приложения.
    """
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    service_dir = os.path.join(base, 'service')
    os.makedirs(service_dir, exist_ok=True)
    return os.path.join(service_dir, filename)