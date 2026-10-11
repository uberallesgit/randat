# api_client.py
"""
Единый клиент для взаимодействия KivyMD-приложения с backend-сервером.

Особенности:
- Токен хранится в service/auth.token (приватная папка приложения).
- Все запросы через requests.Session с retry.
- Публичные методы: get, post, is_authorized, save_token, clear_token.
- Утилита ws_url() для WebSocket (пригодится в этапе K7).
"""
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from paths import service_path


# ────────────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ
# ────────────────────────────────────────────────────────────────
# Пока нет домена — используем IP WSL.
# Когда купишь домен и настроишь HTTPS — поменяешь на:
#   API_URL = "https://api.tvoyproekt.ru"
API_URL = "http://172.31.101.119"      # ← ЗАМЕНИ на свой IP (hostname -I)
API_PREFIX = "/api/v1"

# Таймауты (секунды)
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 15


class ApiClient:
    def __init__(self):
        self.token = self._load_token()
        self.user_id = None
        self.role = None
        self.first_name = None
        self.last_name = None  # ← должно быть
        self.middle_name = None  # ← должно быть
        self.last_error = None  # ← новое

        # HTTP-сессия с автоматическими повторами
        self.s = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retry))
        self.s.mount("http://", HTTPAdapter(max_retries=retry))

    # ────────────────────────────────────────────────────────────
    # ТОКЕН
    # ────────────────────────────────────────────────────────────
    def _token_path(self):
        return service_path('auth.token')

    def _load_token(self):
        try:
            p = self._token_path()
            if os.path.exists(p):
                with open(p) as f:
                    return f.read().strip()
        except Exception as e:
            print(f"[api] _load_token: {e}")
        return None

    def save_token(self, token, user_id=None, role=None, first_name=None):
        """Сохранить токен и метаданные о пользователе."""
        self.token = token
        self.user_id = user_id
        self.role = role
        self.first_name = first_name
        try:
            with open(self._token_path(), 'w') as f:
                f.write(token)
        except Exception as e:
            print(f"[api] save_token: {e}")

    def clear_token(self):
        """Выход из аккаунта."""
        self.token = None
        self.user_id = None
        self.role = None
        self.first_name = None
        try:
            p = self._token_path()
            if os.path.exists(p):
                os.remove(p)
        except Exception as e:
            print(f"[api] clear_token: {e}")

    def is_authorized(self):
        """Есть ли токен. Не проверяет его валидность на сервере."""
        return bool(self.token)

    # ────────────────────────────────────────────────────────────
    # HTTP-ОБЁРТКИ
    # ────────────────────────────────────────────────────────────
    def _headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def get(self, path, **kwargs):
        """
        GET-запрос к API.
        path — например "/auth/me" (без префикса /api/v1).
        Возвращает requests.Response.
        """
        url = API_URL + API_PREFIX + path
        kwargs.setdefault('timeout', (CONNECT_TIMEOUT, READ_TIMEOUT))
        try:
            return self.s.get(url, headers=self._headers(), **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"[api] GET {path} error: {e}")
            return _offline_response(e)

    def post(self, path, json=None, **kwargs):
        """
        POST-запрос к API.
        Возвращает requests.Response.
        """
        url = API_URL + API_PREFIX + path
        kwargs.setdefault('timeout', (CONNECT_TIMEOUT, READ_TIMEOUT))
        try:
            return self.s.post(url, headers=self._headers(),
                               json=json, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"[api] POST {path} error: {e}")
            return _offline_response(e)

    def ws_url(self, path):
        """URL для WebSocket. Например ws_url('/chat/ws')."""
        base = API_URL.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}{API_PREFIX}{path}?token={self.token}"

    # ────────────────────────────────────────────────────────────
    # ВЫСОКОУРОВНЕВЫЕ ХЕЛПЕРЫ
    # ────────────────────────────────────────────────────────────
    def login(self, first_name, last_name, password):
        """
        Возвращает dict с данными или None.
        При успехе сам сохраняет токен.
        """
        r = self.post("/auth/login", json={
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        })
        if r.status_code == 200:
            data = r.json()
            self.save_token(
                data["token"],
                user_id=data.get("user_id"),
                role=data.get("role"),
                first_name=data.get("first_name"),
            )
            return data
        return None

    def register(self, first_name, last_name, password):
        """
        Возвращает (ok: bool, detail: str).
        """
        r = self.post("/auth/register", json={
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        })
        if r.status_code == 200:
            return True, ""
        try:
            detail = r.json().get("detail", "Ошибка регистрации")
        except Exception:
            detail = f"Ошибка {r.status_code}"
        return False, detail

    def fetch_me(self):
        """
        Проверить токен на сервере.
        Возвращает:
          dict  — успех (200)
          None  — токен невалиден (401) ИЛИ сервер недоступен
        Дополнительно выставляет self.last_error:
          None       — успех
          "offline"  — сеть недоступна / сервер не ответил
          "expired"  — сервер вернул 401
          "http_XXX" — прочий HTTP-код
        """
        r = self.get("/auth/me")

        if r.status_code == 200:
            self.last_error = None
            return r.json()

        if r.status_code == 401:
            self.last_error = "expired"
            return None

        if r.status_code == 0:
            # offline — сеть не отвечает
            self.last_error = "offline"
            return None

        self.last_error = f"http_{r.status_code}"
        return None


# ────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЙ КЛАСС ДЛЯ OFFLINE
# ────────────────────────────────────────────────────────────────
def _offline_response(exception):
    """
    Возвращает объект, похожий на requests.Response,
    чтобы вызывающий код мог обработать offline так же, как HTTP-ответ.
    """
    class _FakeResponse:
        status_code = 0
        text = str(exception)

        def json(self):
            return {"detail": "offline"}

        @property
        def ok(self):
            return False

    return _FakeResponse()


# ────────────────────────────────────────────────────────────────
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ────────────────────────────────────────────────────────────────
api = ApiClient()