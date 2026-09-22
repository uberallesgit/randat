"""
Экран входа и регистрации.

Разметка — правило <LoginWindow> в ui.kv (использует общую дизайн-систему:
ScreenHeader, ActionButton, цветовые токены). Хранение пользователей — db.py.
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

import db

# Куда переходить после успешного входа — поменяйте под свой ScreenManager.
HOME_SCREEN_NAME = "Uber"

MIN_PASSWORD_LENGTH = 6


class LoginWindow(MDScreen):
    """Поля: Имя, Фамилия, Пароль. Кнопки: Войти / Зарегистрироваться."""

    def on_pre_enter(self, *args):
        self.set_error("")

    def set_error(self, text: str) -> None:
        self.ids.error_label.text = text

    def toggle_password_visibility(self) -> None:
        field = self.ids.password
        field.password = not field.password
        self.ids.password_toggle.icon = "eye-off" if field.password else "eye"

    def _read_fields(self):
        first_name = self.ids.first_name.text.strip()
        last_name = self.ids.last_name.text.strip()
        password = self.ids.password.text
        return first_name, last_name, password

    def login(self) -> None:
        first_name, last_name, password = self._read_fields()

        if not first_name or not last_name or not password:
            self.set_error("Заполните имя, фамилию и пароль")
            return

        if db.verify_user(first_name, last_name, password):
            self.set_error("")
            self.ids.password.text = ""
            MDApp.get_running_app().go_to(HOME_SCREEN_NAME)
        else:
            self.set_error("Неверное имя, фамилия или пароль")

    def register(self) -> None:
        first_name, last_name, password = self._read_fields()

        if not first_name or not last_name or not password:
            self.set_error("Заполните имя, фамилию и пароль")
            return

        if len(password) < MIN_PASSWORD_LENGTH:
            self.set_error(f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов")
            return

        try:
            db.register_user(first_name, last_name, password)
        except db.UserAlreadyExists:
            self.set_error("Такой пользователь уже зарегистрирован")
            return

        self.set_error("")
        self.login()
