import sys
from kivymd.uix.button import MDIconButton
import db
import rdb
import csv
from api_client import api
import webbrowser
from datetime import datetime, timedelta
import openpyxl
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.list import ILeftBodyTouch, OneLineAvatarIconListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.dropdownitem import MDDropDownItem
from kivy.uix.textinput import TextInput
from kivymd.uix.list import MDList, OneLineListItem
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView, FileChooserIconLayout
from kivy.properties import ListProperty, BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.core.window import Window
import platform
IS_ANDROID = platform.system() == 'Android'
# Импортируем androidstorage4kivy только на Android
if IS_ANDROID:
    from androidstorage4kivy import Chooser, SharedStorage
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.clock import Clock
import os
from kivymd.uix.label import MDLabel
import sqlite3
from paths import resource_path, service_path
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.text import LabelBase
from datetime import date
from sync import commit_crwo_number
from kivymd.app import MDApp
import re
import json
import traceback
from pathlib import Path
import threading
import socket
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from datetime import datetime, date
import calendar
from kivy.utils import platform as kivy_platform  # Вызывает родной Android filechooser

# ────────────────────────────────────────────────────────────────
# НАСТРОЙКИ СЕРВЕРА (IP / Домен)
# ────────────────────────────────────────────────────────────────
SERVER_CONFIG_FILE = "server_config.json"


def get_server_url():
    """Возвращает сохраненный URL сервера или дефолтный."""
    path = service_path(SERVER_CONFIG_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("server_url", "").strip()
                if url:
                    return url
        except Exception as e:
            print(f"[config] Ошибка чтения сервера: {e}")

    # Дефолтный адрес (на случай, если файла нет)
    return "https://api.ubergoober.site:8443"


def save_server_url(url):
    """Сохраняет URL сервера в файл."""
    path = service_path(SERVER_CONFIG_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"server_url": url.strip()}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[config] Ошибка сохранения сервера: {e}")
        return False






os.environ['KIVY_GL_BACKEND'] = 'sdl2'
os.environ['KIVY_GRAPHICS'] = 'gles'
os.environ['KIVY_GLES_LIMITS'] = '0'
os.environ['KIVY_NO_ARGS'] = '1'

TEXT_COLOR = (0.2,0.2,0.2,1)#(0.25, 0.28, 0.33, 1)

print(f"[paths] cwd         = {os.getcwd()}")
print(f"[paths] __file__    = {__file__}")
print(f"[paths] ANDROID_PRIVATE = {os.environ.get('ANDROID_PRIVATE')}")
_f = resource_path('fonts/RobotoEmoji.ttf')
print(f"[paths] RobotoEmoji = {_f}")
print(f"[paths] exists      = {os.path.exists(_f)}")
if os.path.isdir(os.path.dirname(_f)):
    print(f"[paths] ls fonts/   = {os.listdir(os.path.dirname(_f))}")
else:
    print(f"[paths] fonts/ dir missing")



# ── Регистрируем Roboto с эмодзи как основной шрифт ──
LabelBase.register(
    name='Roboto',
    fn_regular=resource_path('fonts/RobotoEmoji.ttf'),
    fn_bold=resource_path('fonts/RobotoEmoji.ttf'),
    fn_italic=resource_path('fonts/RobotoEmoji.ttf'),
    fn_bolditalic=resource_path('fonts/RobotoEmoji.ttf'),
)








class SelectableLabel(TextInput):
    """TextInput readonly: скроллится, выделяется, ручки видны.
    При получении фокуса клавиатура принудительно скрывается —
    фокус остаётся, поэтому свайп-скролл работает на Android.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('readonly', True)
        kwargs.setdefault('multiline', True)
        kwargs.setdefault('background_normal', '')
        kwargs.setdefault('background_active', '')
        kwargs.setdefault('background_color', (0, 0, 0, 0))
        kwargs.setdefault('foreground_color', (0.25, 0.28, 0.33, 1))
        kwargs.setdefault('cursor_color', (0, 0, 0, 0))
        kwargs.setdefault('use_bubble', True)
        kwargs.setdefault('use_handles', True)
        # ── Скролл ──
        kwargs.setdefault('scroll_from_swipe', True)
        kwargs.setdefault('scroll_timeout', 100)
        kwargs.setdefault('scroll_distance', 15)
        kwargs.setdefault('unfocus_on_touch', False)
        kwargs.setdefault('input_type', 'text')
        super().__init__(**kwargs)

        self.bind(focus=self._on_focus)

    def _on_focus(self, instance, value):
        if value:
            # Небольшая задержка — иначе клавиатура ещё не создана
            Clock.schedule_once(self._hide_keyboard, 0.05)

    def _hide_keyboard(self, dt):
        try:
            Window.release_all_keyboards()
        except Exception as e:
            print(f"hide_keyboard: {e}")

class MyTab(MDBoxLayout, MDTabsBase):
    """Класс для вкладки MDTabs."""
    pass


class LeftCheckbox(ILeftBodyTouch, MDCheckbox):
    """Чекбокс для левой части ListItem."""
    pass


class CheckboxItem(OneLineAvatarIconListItem):
    """Строка списка с MDCheckbox слева."""

    def __init__(self, worker_name, callback, **kwargs):
        super().__init__(**kwargs)
        self.text = worker_name
        self._callback = callback

        cb = LeftCheckbox(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
        )
        cb.bind(active=lambda inst, val: self._callback(inst, val, worker_name))
        self.add_widget(cb)

#__________________________________________________________________
#  Login window
#___________________________________________________________________

# Куда переходить после успешного входа — поменяйте под свой ScreenManager.
HOME_SCREEN_NAME = "Uber"

MIN_PASSWORD_LENGTH = 8


class LoginWindow(MDScreen):
    """Поля: Имя, Фамилия, Пароль. Кнопки: Войти / Зарегистрироваться."""

    def save_server_from_login(self):
        """Сохраняет IP-адрес сервера прямо из окна авторизации."""
        url = self.ids.login_server_url.text.strip()
        if not url:
            self.set_error("Введите адрес сервера (IP или домен)")
            return

        # Если пользователь забыл указать протокол, добавляем https://
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        if save_server_url(url):
            self.ids.login_server_url.text = url
            self.set_error("Адрес сервера сохранён!")

            # Запускаем принудительную проверку связи, чтобы сразу обновить статус
            try:
                import threading
                def force_ping():
                    ok = _ping_server()
                    _server_status["state"] = "online" if ok else "offline"
                    # Обновляем UI (на случай, если окно открыто)
                    Clock.schedule_once(lambda dt: _update_ping_ui(MDApp.get_running_app()), 0)

                threading.Thread(target=force_ping, daemon=True).start()
            except Exception as e:
                print(f"[login] force_ping error: {e}")
        else:
            self.set_error("Ошибка сохранения. Проверьте права.")

    def on_kv_post(self, *_):
        """Загружаем текущий сервер при открытии окна логина."""
        try:
            self.ids.login_server_url.text = get_server_url()
        except Exception as e:
            print(f"[login] on_kv_post: {e}")


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

        self.set_error("Проверка…")

        data = api.login(first_name, last_name, password)

        if data is None:
            # Проверяем, что вернул сервер
            err = getattr(api, 'last_error', None)

            if err and err.startswith("403:"):
                # Сервер сказал: забанен или не одобрен
                detail = err.split(":", 1)[1].strip()
                self.set_error(detail)
                return

            if err == "auth_failed":
                self.set_error("Неверное имя, фамилия или пароль")
                return

            # Если сервер недоступен (offline) — пробуем локальный fallback
            try:
                if db.verify_user(first_name, last_name, password):
                    self.set_error("")
                    self.ids.password.text = ""
                    MDApp.get_running_app().go_to(HOME_SCREEN_NAME)
                    return
            except Exception as e:
                print(f"[login] fallback error: {e}")

            self.set_error("Нет сети. Попробуйте позже.")
            return

        # Успех
        print(f"[login] OK: {data['first_name']} (role={data['role']})")
        self.set_error("")
        self.ids.password.text = ""
        MDApp.get_running_app().go_to(HOME_SCREEN_NAME)

    def register(self) -> None:
        first_name, last_name, password = self._read_fields()

        if not first_name or not last_name or not password:
            self.set_error("Заполните имя, фамилию и пароль")
            return

        if len(password) < MIN_PASSWORD_LENGTH:
            self.set_error(f"Пароль должен быть не короче {MIN_PASSWORD_LENGTH} символов")
            return

        self.set_error("Регистрация…")

        ok, detail = api.register(first_name, last_name, password)

        if not ok:
            # Сервер недоступен? Пробуем локально
            try:
                db.register_user(first_name, last_name, password)
                self.set_error("")
                self.login()
                return
            except db.UserAlreadyExists:
                self.set_error("Такой пользователь уже зарегистрирован")
                return
            except Exception:
                self.set_error(detail or "Ошибка регистрации")
                return

        # Успех — сразу логинимся
        self.login()




# ────────────────────────────────────────────────────────────────
# GOORANDA — поиск БС / ARC / маршрутов
# ────────────────────────────────────────────────────────────────
class GoorandaWindow(MDScreen):
    route = None
    RDB = {}  # заполнится в on_pre_enter / on_kv_post

    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialog = None



    def on_kv_post(self, base_widget):
        """Вызывается после построения всех kv-правил.
        Обновляем бейдж и показываем именинников через небольшую задержку,
        чтобы ids и виджеты были точно готовы."""
        Clock.schedule_once(self._refresh_birthdays_ui, 0.2)

    _search_event = None

    def on_bs_name_text(self, text):
        """Живой поиск по мере ввода — только в режиме 'Адрес'."""
        # Отменяем предыдущий запланированный вызов (debounce)
        if self._search_event is not None:
            self._search_event.cancel()
            self._search_event = None

        # Живой поиск только для режима «Адрес»
        try:
            mode = self.ids.spinner_id.text
        except Exception:
            mode = ""
        if mode != "Адрес":
            return

        # Если поле пустое — очищаем вывод
        if not text.strip():
            try:
                self.ids.output_text.text = ""
            except Exception:
                pass
            return

        # 👇 НОВОЕ: запускаем поиск только с 3-го символа
        if len(text.strip()) < 3:
            return

        # Запускаем поиск через 250 мс после последнего нажатия
        self._search_event = Clock.schedule_once(
            lambda dt: self.make_output(), 0.25
        )

    def _refresh_birthdays_ui(self, *args):
        """Обновляет бейдж и output_text с именинниками."""


        # ── Бейдж ──
        try:
            count = count_upcoming_birthdays(7)
            self.ids.gooranda_header.badge_text = str(count) if count > 0 else ""
        except Exception as e:
            print(f"_refresh badge: {e}")

        # ── output_text ──
        try:
            if not self.ids.output_text.text.strip():
                text = build_upcoming_birthdays_text(7)
                if text:
                    self.ids.output_text.text = text
        except Exception as e:
            print(f"_refresh output_text: {e}")

    def on_pre_enter(self, *args):
        UberWindow.RDB = rdb.load_rdb()
        # Обновляем RDB из БД
        self.RDB = rdb.load_rdb()

        """Обновляем бейдж на иконке людей."""
        count = count_upcoming_birthdays(7)
        try:
            badge = self.ids.gooranda_header.ids.badge
            badge.text = str(count) if count > 0 else ""
        except Exception as e:
            print(f"on_pre_enter badge: {e}")

    # ── UI-хелперы ──
    def copy_to_clipboard(self, string):
        if string:
            Clipboard.copy(string)

    def open_browser(self, route):
        if route:
            webbrowser.open(route)

    def show_dialog(self, text, title="Внимание"):
        show_simple_dialog(title, text)

    # ── Формирование текста ──
    def make_output_short(self, bs, RDB):
        return (f"** {bs} **\n"
                f"Координаты : {RDB[bs].get('coordinates', '')}\n"
                f"Адрес : {RDB[bs].get('address', '')}\n"
                f"Яндекс : {RDB[bs].get('yandex_map', '')}\n"
                f"ЦТЭиСО : {RDB[bs].get('service_center', '')}\n")

    def make_output_long(self, bs, RDB):
        return (f"*** {bs} ***\n"
                f"Формат КрТ: {RDB[bs].get('arc_id', '')}\n"
                f"Приоритет: {RDB[bs].get('priority', '')}\n"
                f"Адрес : {RDB[bs].get('address', '')}\n"
                f"Координаты : {RDB[bs].get('coordinates', '')}\n"
                f"Конструктивный тип сайта: {RDB[bs].get('constructional_type', '')}\n"
                f"Арендодатель : {RDB[bs].get('rent', '')}\n"
                f"Статус: {RDB[bs].get('status', '')}\n"
                f"Трансмиссия : {RDB[bs].get('transmission', '')}\n"
                f"Доступ:{RDB[bs].get('access', '')}\n"
                f"Аппаратная: {RDB[bs].get('hw_room', '')}\n"
                f"Ответственный по стройке : {RDB[bs].get('builder', '')}\n"
                f"Подрядчик на строительство : {RDB[bs].get('contractor', '')}\n"
                f"Ответственный по трансмиссии : {RDB[bs].get('transmissionist', '')}\n"
                f"ЦТЭиСО : {RDB[bs].get('service_center', '')}\n")

    def make_output(self):
        # Снимаем выделение с output_text перед новым запросом
        try:
            self.ids.output_text.cancel_selection()
            self.ids.output_text.focus = False
        except Exception:
            pass
        RDB = self.RDB
        raw = self.ids.bs_name.text.strip()
        if not raw:
            return

        short = raw.startswith("**")
        raw = raw.replace("**", "")
        mode = self.ids.spinner_id.text

        if mode == "БС":
            if len(raw.split()) == 1:
                prefix = (4 - len(raw)) * "0"
                target = "CR" + prefix + raw
                if target not in RDB:
                    target = target.replace("CR", "SE")
                if target in RDB:
                    out = (self.make_output_short(target, RDB) if short
                           else self.make_output_long(target, RDB))
                    self.route = RDB[target].get("yandex_map", "")
                    self.ids.output_text.text = out
                else:
                    self.ids.output_text.text = "YOU ARE WRONG.."
                self.ids.bs_name.text = ""

            elif len(raw.split()) > 1:
                coords, total = [], ""
                for bs in raw.split():
                    prefix = (4 - len(bs)) * "0"
                    target = "CR" + prefix + bs
                    if target not in RDB:
                        target = target.replace("CR", "SE")
                    if target in RDB:
                        out = (self.make_output_short(target, RDB) if short
                               else self.make_output_long(target, RDB))
                        if 'latitude' in RDB[target] and 'longitude' in RDB[target]:
                            coords.append(
                                f"{RDB[target]['latitude']}%2C{RDB[target]['longitude']}")
                        total += "\n" + out
                if coords:
                    self.route = (f"https://yandex.ru/navi?rtext="
                                  f"{'~'.join(coords)}&rtt=auto")
                self.ids.output_text.text = total or "БС не найдены."
                self.ids.bs_name.text = ""

        elif mode == "ARC":
            total = ""
            for key in RDB:
                ktk = RDB[key].get("arc_id")
                if ktk and ("ARC" + raw in str(ktk)):
                    s = (f"*** {key} ***\n"
                         f"Формат КрТ: {RDB[key].get('arc_id', '')}\n"
                         f"Адрес : {RDB[key].get('address', '')}\n"
                         f"Координаты : {RDB[key].get('coordinates', '')}\n"
                         f"Конструктивный тип сайта : {RDB[key].get('constructional_type', '')}\n"
                         f"Арендодатель : {RDB[key].get('rent', '')}\n"
                         f"Статус : {RDB[key].get('status', '')}\n"
                         f"Трансмиссия : {RDB[key].get('transmission', '')}\n"
                         f"Аппаратная : {RDB[key].get('hw_room', '')}\n"
                         f"Ответственный по стройке : {RDB[key].get('builder', '')}\n"
                         f"Ответственный инженер эксплуатации: {RDB[key].get('exploiter', '')}\n"
                         f"Зона Ответственности : {RDB[key].get('service_center', '')}\n")
                    if RDB[key].get('contact'):
                        s += f"Контакты : {RDB[key]['contact']}\n"
                    total += "\n" + s
            self.ids.output_text.text = total or "Ничего не найдено."
            self.ids.bs_name.text = ""


        elif mode == "Адрес":

            # Разбиваем ввод на слова (по пробелам), регистронезависимо

            terms = [t.lower() for t in raw.split() if t]

            found = []

            for bs, info in RDB.items():

                address = str(info.get('address', '') or '')

                if not address:
                    continue

                addr_lower = address.lower()

                # Условие И: все введённые слова должны присутствовать в адресе

                if all(term in addr_lower for term in terms):
                    found.append((bs, address, info.get('coordinates', '')))

            if found:

                lines = [

                    f"{bs} | {addr} | {coords}"

                    for bs, addr, coords in sorted(found, key=lambda x: x[0])

                ]

                self.ids.output_text.text = "\n\n".join(lines)

            else:

                self.ids.output_text.text = "Ничего не найдено."



        elif mode == "ТП":
            query = raw.strip().lower()
            # Если пользователь ввёл только цифры — ищем оба варианта:
            # "тп-225" и "тп 225".
            if query.isdigit():
                variants = ["тп-" + query, "тп " + query]
            else:
                # Пользователь ввёл что-то с префиксом.
                # Приводим дефис к пробелу и наоборот — ищем оба варианта.
                normalized = query.replace("-", " ")
                variants = [query]
                if normalized != query:
                    variants.append(normalized)
                # Если ввёл "тп 218" — добавим вариант с дефисом
                if " " in query:
                    variants.append(query.replace(" ", "-"))
            found = []
            for bs, info in RDB.items():
                access = str(info.get('access', '') or '')
                if not access:
                    continue
                access_lower = access.lower()
                # Проверяем любой из вариантов вхождения
                if any(v in access_lower for v in variants):
                    found.append((bs,str(info.get('address', '') or ''),str(info.get('coordinates', '') or ''),access,))
            if found:
                lines = [
                    f"{bs} | {addr} | {coords}"
                    for bs, addr, coords, _ in sorted(found, key=lambda x: x[0])
                ]
                self.ids.output_text.text = "\n\n".join(lines)
            else:
                self.ids.output_text.text = "Ничего не найдено."
            self.ids.bs_name.text = ""



# ────────────────────────────────────────────────────────────────
# WORKER — выбор сотрудников
# ────────────────────────────────────────────────────────────────
class WorkerWindow(MDScreen):
    selected = ListProperty([])

    def on_kv_post(self, *_):
        self._all_workers = self._load_workers()
        self.refresh_workers()

    # ── Путь к файлу ──
    def _workers_file(self):
        return service_path('worker_list.txt')

    # ── Загрузка из файла ──
    def _load_workers(self):
        path = self._workers_file()
        print(f"[worker] path={path} exists={os.path.exists(path)}")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f.readlines() if l.strip()]

    # ── Сохранение в файл ──
    def _save_workers(self, workers):
        with open(self._workers_file(), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(set(workers))))
        # Обновляем кэш
        self._all_workers = sorted(set(workers))

    # ── Пересборка сетки (с учётом фильтра) ──
    def refresh_workers(self, filter_text=""):
        container = self.ids.checkbox_container
        container.clear_widgets()

        workers = self._all_workers
        if filter_text:
            ft = filter_text.lower().strip()
            workers = [w for w in workers if ft in w.lower()]

        for w in workers:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="44dp",
                spacing="4dp",
                padding=["4dp", 0, 0, 0],
            )

            cb = MDCheckbox(
                size_hint=(None, None),
                size=("32dp", "32dp"),
                active=(w in self.selected),
                pos_hint={"center_y": .5},
            )
            cb.bind(active=lambda inst, val, name=w: self._on_check(inst, val, name))

            lbl = MDLabel(
                text=w,
                theme_text_color="Custom",
                text_color= TEXT_COLOR,   #(0.106, 0.106, 0.118, 1),
                valign="middle",
                font_size="13sp",
                shorten=True,
                shorten_from="right",
            )

            row.add_widget(cb)
            row.add_widget(lbl)
            container.add_widget(row)

        self._update_selected_label()

    # ── Фильтр при вводе в поиск ──
    def filter_workers(self, text):
        self.refresh_workers(text)

    def clear_search(self):
        """Очищает поле поиска и возвращает полный список."""
        self.ids.search_field.text = ""
        self.refresh_workers()

    # ── Обработка чекбокса ──
    def _on_check(self, instance, value, worker):
        if value and worker not in self.selected:
            self.selected.append(worker)
        elif not value and worker in self.selected:
            self.selected.remove(worker)

        self._update_selected_label()
        self._sync_to_uber()

    # ── Обновить счётчик ──
    def _update_selected_label(self):
        try:
            self.ids.selected_count_label.text = f"Выбрано: {len(self.selected)}"
        except Exception:
            pass

    # ── Передать выбранных на Uber ──
    def _sync_to_uber(self):
        try:
            uber = self.manager.get_screen('Uber')
            uber.workers_selected = bool(self.selected)
            uber.ids.choose_workers_label.text = (
                ", ".join(self.selected) if self.selected
                else "Выбери исполнителей:"
            )
        except Exception as e:
            print(f"WorkerWindow → Uber: {e}")

    # ── Снять все чекбоксы ──
    def clear_all_selections(self):
        self.selected = []
        self.refresh_workers(self.ids.search_field.text)
        self._sync_to_uber()

    # ═══ Дальше идут твои методы ═══
    # add_worker_dialog, delete_worker_dialog, _confirm_delete,
    # export_workers_xlsx, import_workers_dialog, _on_import_file_selected,
    # _read_workers_from_file, _ask_import_mode — оставь как есть

    # ═══════════════════════════════════════════════════════════
    # КНОПКА «ДОБАВИТЬ СОТРУДНИКА»
    # ═══════════════════════════════════════════════════════════
    def add_worker_dialog(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.textinput import TextInput
        from kivy.metrics import dp

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12)] * 4,
        )

        title_label = Label(
            text="Введите фамилию нового сотрудника:",

            size_hint_y=None,
            height=dp(30),
            color=(0.106, 0.106, 0.118, 1),
        )
        content.add_widget(title_label)

        name_input = TextInput(
            multiline=False,
            input_type='text', # 👈 Добавил
            size_hint_y=None,
            height=dp(48),
            background_color=(0.95, 0.95, 0.97, 1),
            foreground_color=(0.106, 0.106, 0.118, 1),
            cursor_color=(0.42, 0.16, 0.85, 1),
            font_size=dp(16),
            padding=[dp(10), dp(10), dp(10), dp(10)],
        )
        content.add_widget(name_input)

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        popup = Popup(
            title="Добавить сотрудника",
            title_color=(0.42, 0.16, 0.85, 1),
            title_size=dp(16),
            separator_color=(0.85, 0.85, 0.85, 1),
            content=content,
            size_hint=(0.85, 0.45),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _save(*_):
            name = name_input.text.strip()
            if not name:
                popup.dismiss()
                return

            workers = self._load_workers()
            if name in workers:
                show_simple_dialog("Внимание", f"Сотрудник «{name}» уже есть в списке")
                return

            workers.append(name)
            self._save_workers(workers)
            popup.dismiss()
            self.refresh_workers()

        def _cancel(*_):
            popup.dismiss()

        btn_ok = Button(
            text="ДОБАВИТЬ",
            background_normal="",
            background_color=(0.42, 0.16, 0.85, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_ok.bind(on_release=_save)

        btn_cancel = Button(
            text="ОТМЕНА",
            background_normal="",
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)

        popup.open()

    # ═══════════════════════════════════════════════════════════
    # КНОПКА «УДАЛИТЬ СОТРУДНИКА»
    # ═══════════════════════════════════════════════════════════
    def delete_worker_dialog(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.scrollview import ScrollView
        from kivy.metrics import dp

        workers = self._load_workers()
        if not workers:
            show_simple_dialog("Внимание", "Список сотрудников пуст")
            return

        # Прокручиваемый список
        list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(2),
        )
        list_layout.bind(minimum_height=list_layout.setter("height"))

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        scroll.add_widget(list_layout)

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(8)] * 4,
        )
        content.add_widget(Label(
            text="Тапните по фамилии, чтобы удалить:",
            size_hint_y=None,
            height=dp(30),
            color=(0.106, 0.106, 0.118, 1),
        ))
        content.add_widget(scroll)

        popup = Popup(
            title="Удалить сотрудника",
            title_color=(0.85, 0.2, 0.2, 1),
            title_size=dp(16),
            separator_color=(0.85, 0.85, 0.85, 1),
            content=content,
            size_hint=(0.85, 0.7),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _make_delete_handler(name):
            def _delete(*_):
                popup.dismiss()
                self._confirm_delete(name)

            return _delete

        for w in workers:
            btn = Button(
                text=w,
                size_hint_y=None,
                height=dp(48),
                background_normal="",
                background_down="",
                background_color=(0.95, 0.95, 0.97, 1),
                color=(0.106, 0.106, 0.118, 1),
                font_size=dp(15),
            )
            btn.bind(on_release=_make_delete_handler(w))
            list_layout.add_widget(btn)

        popup.open()

        # ═══════════════════════════════════════════════════════════
        # ЭКСПОРТ В .xlsx
        # ═══════════════════════════════════════════════════════════
    def export_workers_xlsx(self):
        """Выгружает список сотрудников в .xlsx."""
        import platform
        from datetime import datetime
        import openpyxl

        workers = self._load_workers()
        if not workers:
            show_simple_dialog("Внимание", "Список сотрудников пуст")
            return

        # Создаём Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Сотрудники"
        ws.append(["№", "Фамилия"])
        ws.column_dimensions["A"].width = 6
        ws.column_dimensions["B"].width = 30
        for i, w in enumerate(workers, 1):
            ws.append([i, w])

        # Куда сохранять
        if platform.system() == "Android":
            save_dir = "/storage/emulated/0/Download"
            if not os.path.exists(save_dir):
                save_dir = "/storage/emulated/0"
        else:
            save_dir = os.path.expanduser("~/Downloads")
            if not os.path.exists(save_dir):
                save_dir = os.path.expanduser("~")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"workers_{timestamp}.xlsx"
        save_path = os.path.join(save_dir, filename)

        try:
            wb.save(save_path)
            show_simple_dialog(
                "Готово",
                f"Файл сохранён:\n{save_path}\n\nВсего: {len(workers)}",
            )
        except Exception as e:
            show_simple_dialog("Ошибка", f"Не удалось сохранить файл:\n{e}")

    # ═══════════════════════════════════════════════════════════
    # ИМПОРТ ИЗ ТЕКСТОВОГО ФАЙЛА
    # ═══════════════════════════════════════════════════════════
    def import_workers_dialog(self):
        """Открывает файл-менеджер для импорта списка сотрудников."""
        open_file_chooser(self._on_import_file_selected, ext=None)

    def _on_import_file_selected(self, path):
        """Вызывается после выбора файла."""
        workers = self._read_workers_from_file(path)
        if not workers:
            show_simple_dialog("Ошибка", "Не удалось прочитать файл или он пуст")
            return
        self._ask_import_mode(workers)

    def _read_workers_from_file(self, path):
        """Читает файл — поддерживает .txt, .csv, .xlsx, .xls."""
        ext = os.path.splitext(path)[1].lower()

        # ─── Excel ───
        if ext in ('.xlsx', '.xls'):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(filename=path, read_only=True, data_only=True)
                workers = []
                for sheet in wb.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        for cell in row:
                            if cell is None:
                                continue
                            name = str(cell).strip()
                            # Пропускаем заголовки, пустые и числа
                            if not name:
                                continue
                            if name.startswith(('№', 'Фамилия', 'Name', 'ID')):
                                continue
                            if name.replace('.', '').replace(',', '').isdigit():
                                continue
                            workers.append(name)
                wb.close()
                return workers
            except Exception as e:
                print(f"read xlsx error: {e}")
                return []

        # ─── Текстовый файл (.txt, .csv, .md и т.д.) ───
        encodings = ['utf-8', 'cp1251', 'maccyrillic', 'latin-1']
        best_result = []

        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    lines = [line.strip() for line in f if line.strip()]

                # Проверяем, что строки похожи на фамилии
                if self._looks_like_names(lines):
                    return lines

                # Запоминаем самый длинный результат — на случай, если всё мусор
                if len(lines) > len(best_result):
                    best_result = lines

            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                print(f"read error ({enc}): {e}")
                continue

        return best_result

    def _looks_like_names(self, lines):
        """Эвристика: строки похожи на фамилии (а не на бинарный мусор)."""
        if not lines:
            return False

        sample = lines[:10]
        good = 0

        for line in sample:
            # Длина фамилии — от 2 до 40 символов
            if not (2 <= len(line) <= 40):
                continue

            # Не менее 60% символов — буквы, пробелы, дефисы
            letters = sum(1 for ch in line if ch.isalpha() or ch in " -'")
            if letters / max(len(line), 1) >= 0.6:
                good += 1

        # Хотя бы половина строк похожа на имена
        return good >= max(1, len(sample) // 2)

    def _ask_import_mode(self, new_workers):
        """Спрашивает: дополнить или заменить существующий список."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.metrics import dp

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12)] * 4,
        )

        msg = Label(
            text=(f"Найдено сотрудников: {len(new_workers)}\n\n"
                  f"Дополнить существующий список или заменить его?"),
            color=(0.106, 0.106, 0.118, 1),
            halign="center",
            valign="middle",
        )
        msg.bind(size=lambda s, w: setattr(s, "text_size", w))
        content.add_widget(msg)

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        popup = Popup(
            title="Импорт сотрудников",
            title_color=(0.42, 0.16, 0.85, 1),
            title_size=dp(16),
            separator_color=(0.85, 0.85, 0.85, 1),
            content=content,
            size_hint=(0.9, 0.4),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _append(*_):
            popup.dismiss()
            current = self._load_workers()
            before = len(current)
            merged = sorted(set(current) | set(new_workers))
            self._save_workers(merged)
            self.refresh_workers()
            added = len(merged) - before
            show_simple_dialog(
                "Готово",
                f"Добавлено: {added}\nВсего в списке: {len(merged)}",
            )

        def _replace(*_):
            popup.dismiss()
            unique = sorted(set(new_workers))
            self._save_workers(unique)
            self.refresh_workers()
            show_simple_dialog(
                "Готово",
                f"Список заменён.\nВсего: {len(unique)}",
            )

        def _cancel(*_):
            popup.dismiss()

        btn_append = Button(
            text="ДОПОЛНИТЬ",
            background_normal="",
            background_color=(0.42, 0.16, 0.85, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=dp(13),
        )
        btn_append.bind(on_release=_append)

        btn_replace = Button(
            text="ЗАМЕНИТЬ",
            background_normal="",
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=dp(13),
        )
        btn_replace.bind(on_release=_replace)

        btn_cancel = Button(
            text="ОТМЕНА",
            background_normal="",
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1),
            bold=True,
            font_size=dp(13),
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_append)
        buttons.add_widget(btn_replace)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)

        popup.open()



    def _confirm_delete(self, name):
        """Подтверждение удаления."""

        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.metrics import dp

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12)] * 4,
        )
        content.add_widget(Label(
            text=f"Удалить сотрудника «{name}»?",
            color=(0.106, 0.106, 0.118, 1),
        ))

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        popup = Popup(
            title="Подтверждение",
            title_color=(0.85, 0.2, 0.2, 1),
            title_size=dp(16),
            separator_color=(0.85, 0.85, 0.85, 1),
            content=content,
            size_hint=(0.8, 0.3),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _yes(*_):
            workers = self._load_workers()
            if name in workers:
                workers.remove(name)
                self._save_workers(workers)

            # Убираем из выбранных, если был выбран
            if name in self.selected:
                self.selected.remove(name)

            # Синхронизируем Uber: и текст, и флаг workers_selected
            self._sync_to_uber()

            popup.dismiss()
            self.refresh_workers()

        def _no(*_):
            popup.dismiss()

        btn_yes = Button(
            text="УДАЛИТЬ",
            background_normal="",
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_yes.bind(on_release=_yes)

        btn_no = Button(
            text="ОТМЕНА",
            background_normal="",
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_no.bind(on_release=_no)

        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)

        popup.open()


# ────────────────────────────────────────────────────────────────
# RESPONSIBLES — выбор ответственного
# ────────────────────────────────────────────────────────────────
class ResponsiblesWindow(MDScreen):
    selected = ListProperty([])

    def on_kv_post(self, *_):
        workers = sorted(["Мартынов", "Бердиков", "Малатай", "Щербатый",
                          "Полуяктов", "Кобзарь", "Щербаков"])
        for w in workers:
            item = CheckboxItem(worker_name=w, callback=self._on_check)
            self.ids.respons_checkbox_container.add_widget(item)

    def _on_check(self, instance, value, worker):
        if value and worker not in self.selected:
            self.selected.append(worker)
        elif not value and worker in self.selected:
            self.selected.remove(worker)

        try:
            uber = self.manager.get_screen('Uber')
            uber.ids.choose_respons_button.text = (
                ", ".join(self.selected) if self.selected else "Выбрать ответственного"
            )
        except Exception as e:
            print(f"ResponsiblesWindow: {e}")


# ────────────────────────────────────────────────────────────────
# CRWO — вывод готовой заявки
# ────────────────────────────────────────────────────────────────
class CrwoWindow(MDScreen):

    def on_pre_leave(self, *args):
        clear_all_selections(self)

    def copy_to_clipboard(self, string):
        if string:
            Clipboard.copy(string)

    def open_browser(self, route):
        """ Открывает сгенерированную ссылку на навигатор """
        if route:
            webbrowser.open(route)



# ────────────────────────────────────────────────────────────────
# UBER — главный экран формирования заявки
# ────────────────────────────────────────────────────────────────
class UberWindow(MDScreen):
    RDB = {}
    plural = BooleanProperty(False)
    workers_selected = BooleanProperty(False)
    arrival_date = StringProperty("")  # "2026-10-10" (для логики)
    arrival_date_display = StringProperty("")  # "10.10.2026" (для UI)
    arrival_time = StringProperty("")  # "14:30"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialog = None
        self._date_reset_event = None  # ← НОВОЕ: таймер сброса даты
        # Загружаем базу
        UberWindow.RDB = rdb.load_rdb()

    def _get_owner_full_name(self):
        """ФИО владельца заявки из авторизации."""
        parts = [api.last_name, api.first_name]
        full_name = " ".join(p for p in parts if p).strip()
        return full_name or api.first_name or "—"

        # 2. Метод для проверки одиночная БС или их несколько (вызывается при вводе текста)
    def check_plural_bs(self, text):
        # Если в тексте есть пробелы, значит введено несколько БС
        if len(text.strip().split()) > 1:
            self.plural = True
        else:
            self.plural = False

    def on_kv_post(self, *_):

        # ── Владелец заявки (из авторизации) ──
        self._set_owner_from_auth()
        # Привязываем обновление номера к смене организации
        self.ids.organization.bind(text=self._update_crwo_number)
        # И к смене региона, так как номера могут отличаться по регионам
        self.ids.region_short.bind(text=self._update_crwo_number)

    def on_pre_enter(self, *args):
        UberWindow.RDB = rdb.load_rdb()
        self._set_owner_from_auth()
        # ── Если дата не выбрана — ставим сегодня ──
        if not self.arrival_date:
            today = date.today()
            self.arrival_date = today.strftime("%Y-%m-%d")
            self.arrival_date_display = today.strftime("%d.%m.%Y")
            self._update_crwo_number()
            print(f"[uber] дата по умолчанию: {self.arrival_date_display}")

    def _update_crwo_number(self, *args):
        """Запрашивает следующий свободный номер CRWO для выбранной организации."""
        from sync import check_crwo_number
        from kivy.clock import Clock

        organization = self.ids.organization.text
        region = self.ids.region_short.text

        if not organization or not region:
            return

        # Очищаем поле, пока идёт запрос
        self.ids.crwo_number.text = "..."

        def _fetch():
            # Отправляем 0, чтобы сервер вернул next_free
            result = check_crwo_number(region, 0, organization)

            if result.get("status") == "free" and "next_free" in result:
                next_num = result["next_free"]
            else:
                next_num = 1

            Clock.schedule_once(
                lambda dt: setattr(self.ids.crwo_number, 'text', str(next_num)), 0
            )

        threading.Thread(target=_fetch, daemon=True).start()

    def _set_owner_from_auth(self):
        """Владелец заявки = текущий авторизованный пользователь."""
        # ФИО из api
        parts = [api.last_name, api.first_name]
        full_name = " ".join(p for p in parts if p).strip()

        if not full_name:
            full_name = api.first_name or "—"

        self.ids.respo_view_label.text = f"Владелец заявки: {full_name}"
        print(f"[uber] владелец заявки: {full_name}")

    # ── Дата и время прибытия ──
    def open_date_picker(self):
        """Свой календарь: три колонки — день, месяц, год. Без MDDatePicker.
        По OK: сохраняет дату и запускает таймер сброса на 5 минут.
        """



        today = datetime.now().date()

        # Начальные значения: сохранённая дата ИЛИ сегодня
        if self.arrival_date:
            try:
                init = datetime.strptime(self.arrival_date, "%Y-%m-%d").date()
                if init < today:
                    init = today
            except Exception:
                init = today
        else:
            init = today

        selected = {
            "day": init.day,
            "month": init.month,
            "year": init.year,
        }

        MONTHS_RU = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
        ]

        # Годы: текущий + 4 вперёд
        YEARS = list(range(today.year, today.year + 5))

        # ── Корневой layout ──
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))

        header = MDLabel(
            text=f"Выбрано: {selected['day']:02d}.{selected['month']:02d}.{selected['year']}",
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.2, 1),
        )
        content.add_widget(header)

        body = BoxLayout(orientation="horizontal", spacing=dp(8))

        day_buttons = []
        month_buttons = []
        year_buttons = []

        def refresh_colors():
            for b in day_buttons:
                is_sel = int(b.text) == selected["day"]
                b.background_color = (0.42, 0.16, 0.85, 1) if is_sel else (0.95, 0.95, 0.97, 1)
                b.color = (1, 1, 1, 1) if is_sel else (0.2, 0.2, 0.2, 1)
            for b in month_buttons:
                is_sel = MONTHS_RU.index(b.text) + 1 == selected["month"]
                b.background_color = (0.42, 0.16, 0.85, 1) if is_sel else (0.95, 0.95, 0.97, 1)
                b.color = (1, 1, 1, 1) if is_sel else (0.2, 0.2, 0.2, 1)
            for b in year_buttons:
                is_sel = int(b.text) == selected["year"]
                b.background_color = (0.42, 0.16, 0.85, 1) if is_sel else (0.95, 0.95, 0.97, 1)
                b.color = (1, 1, 1, 1) if is_sel else (0.2, 0.2, 0.2, 1)

            header.text = f"Выбрано: {selected['day']:02d}.{selected['month']:02d}.{selected['year']}"

        def make_day_handler(d):
            def _h(*_):
                selected["day"] = d
                refresh_colors()

            return _h

        def make_month_handler(m):
            def _h(*_):
                selected["month"] = m
                # Корректируем день, если в месяце меньше дней
                max_day = calendar.monthrange(selected["year"], m)[1]
                if selected["day"] > max_day:
                    selected["day"] = max_day
                refresh_colors()

            return _h

        def make_year_handler(y):
            def _h(*_):
                selected["year"] = y
                max_day = calendar.monthrange(y, selected["month"])[1]
                if selected["day"] > max_day:
                    selected["day"] = max_day
                refresh_colors()

            return _h

        # ── Колонка «День» ──
        days_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        days_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        days_layout.bind(minimum_height=days_layout.setter("height"))
        for d in range(1, 32):
            b = Button(
                text=f"{d:02d}",
                size_hint_y=None,
                height=dp(36),
                background_normal="",
                font_size=dp(14),
            )
            b.bind(on_release=make_day_handler(d))
            day_buttons.append(b)
            days_layout.add_widget(b)
        days_scroll.add_widget(days_layout)

        # ── Колонка «Месяц» ──
        months_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        months_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        months_layout.bind(minimum_height=months_layout.setter("height"))
        for i, m_name in enumerate(MONTHS_RU, start=1):
            b = Button(
                text=m_name,
                size_hint_y=None,
                height=dp(36),
                background_normal="",
                font_size=dp(14),
            )
            b.bind(on_release=make_month_handler(i))
            month_buttons.append(b)
            months_layout.add_widget(b)
        months_scroll.add_widget(months_layout)

        # ── Колонка «Год» ──
        years_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        years_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        years_layout.bind(minimum_height=years_layout.setter("height"))
        for y in YEARS:
            b = Button(
                text=str(y),
                size_hint_y=None,
                height=dp(36),
                background_normal="",
                font_size=dp(14),
            )
            b.bind(on_release=make_year_handler(y))
            year_buttons.append(b)
            years_layout.add_widget(b)
        years_scroll.add_widget(years_layout)

        body.add_widget(days_scroll)
        body.add_widget(months_scroll)
        body.add_widget(years_scroll)
        content.add_widget(body)

        refresh_colors()  # первоначальная подсветка

        # ── Кнопки OK / Отмена ──
        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        popup = Popup(
            title="Выбор даты",
            title_color=(0, 0, 0, 1),
            title_size=dp(16),
            content=content,
            size_hint=(0.95, 0.6),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=False,
        )

        def _ok(*_):
            try:
                chosen = date(selected["year"], selected["month"], selected["day"])
            except Exception as e:
                print(f"[uber] ошибка даты: {e}")
                popup.dismiss()
                return

            if chosen < today:
                chosen = today
                print("[uber] дата в прошлом — принудительно сегодня")

            self.arrival_date = chosen.strftime("%Y-%m-%d")
            self.arrival_date_display = chosen.strftime("%d.%m.%Y")
            print(f"[uber] дата прибытия: {self.arrival_date_display}")

            # ── Таймер сброса даты на 5 минут ──
            self._schedule_date_reset()

            popup.dismiss()

        def _cancel(*_):
            popup.dismiss()

        btn_ok = Button(
            text="OK",
            background_normal="",
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_ok.bind(on_release=_ok)

        btn_cancel = Button(
            text="Отмена",
            background_normal="",
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        popup.open()

    def open_time_picker(self):
        """Диалог выбора времени: часы 0–23, минуты 00/15/30/45."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.scrollview import ScrollView
        from kivymd.uix.label import MDLabel
        from kivy.metrics import dp
        from datetime import datetime

        # Начальные значения
        if self.arrival_time:
            try:
                h0, m0 = map(int, self.arrival_time.split(":"))
            except Exception:
                h0, m0 = datetime.now().hour, 0
        else:
            now = datetime.now()
            h0 = (now.hour + 1) % 24
            m0 = 0

        HOURS = [f"{h:02d}" for h in range(24)]
        MINUTES = ["00", "15", "30", "45"]

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))

        header = MDLabel(
            text=f"Выбрано: {h0:02d}:{m0:02d}",
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.2, 1),
        )
        content.add_widget(header)

        body = BoxLayout(orientation="horizontal", spacing=dp(8))

        # ── Часы ──
        hours_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        hours_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(2),
        )
        hours_layout.bind(minimum_height=hours_layout.setter("height"))

        selected = {"h": h0, "m": m0}
        hour_buttons = []
        minute_buttons = []

        def refresh_colors():
            for b in hour_buttons:
                is_sel = int(b.text) == selected["h"]
                b.background_color = (0.42, 0.16, 0.85, 1) if is_sel else (0.95, 0.95, 0.97, 1)
                b.color = (1, 1, 1, 1) if is_sel else (0.2, 0.2, 0.2, 1)
            for b in minute_buttons:
                is_sel = int(b.text) == selected["m"]
                b.background_color = (0.42, 0.16, 0.85, 1) if is_sel else (0.95, 0.95, 0.97, 1)
                b.color = (1, 1, 1, 1) if is_sel else (0.2, 0.2, 0.2, 1)
            header.text = f"Выбрано: {selected['h']:02d}:{selected['m']:02d}"

        def make_handler(field, value):
            def _handler(*_):
                selected[field] = value
                refresh_colors()

            return _handler

        for h_str in HOURS:
            b = Button(
                text=h_str,
                size_hint_y=None,
                height=dp(36),
                background_normal="",
                font_size=dp(14),
            )
            b.bind(on_release=make_handler("h", int(h_str)))
            hour_buttons.append(b)
            hours_layout.add_widget(b)
        hours_scroll.add_widget(hours_layout)

        # ── Минуты ──
        minutes_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        minutes_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(2),
        )
        minutes_layout.bind(minimum_height=minutes_layout.setter("height"))

        for m_str in MINUTES:
            b = Button(
                text=m_str,
                size_hint_y=None,
                height=dp(36),
                background_normal="",
                font_size=dp(14),
            )
            b.bind(on_release=make_handler("m", int(m_str)))
            minute_buttons.append(b)
            minutes_layout.add_widget(b)
        minutes_scroll.add_widget(minutes_layout)

        body.add_widget(hours_scroll)
        body.add_widget(minutes_scroll)
        content.add_widget(body)

        refresh_colors()  # первоначальная подсветка

        # ── Кнопки OK / Отмена ──
        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        popup = Popup(
            title="Выбор времени",
            title_color=(0, 0, 0, 1),
            title_size=dp(16),
            content=content,
            size_hint=(0.9, 0.6),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _ok(*_):
            self.arrival_time = f"{selected['h']:02d}:{selected['m']:02d}"
            print(f"[uber] время прибытия: {self.arrival_time}")
            popup.dismiss()

        def _cancel(*_):
            popup.dismiss()

        btn_ok = Button(
            text="OK",
            background_normal="",
            background_color=(0.2, 0.6, 1, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_ok.bind(on_release=_ok)

        btn_cancel = Button(
            text="Отмена",
            background_normal="",
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)

        popup.open()

    # ── Диалог ──
    def show_dialog(self, text, title="Внимание"):
        show_simple_dialog(title, text)

    # ── Очистки ──
    def clear_description(self):
        self.ids.work_description.text = ""

    def clear_tt_number(self):
        self.ids.tt_number.text = ""

    def clear_bs_name(self):
        self.ids.bs_name.text = ""

    # ── Инкремент / декремент номера заявки ──
    def crwo_increment(self, string):
        if string.isdigit():
            self.ids.crwo_number.text = str(int(string) + 1)
        else:
            self.ids.crwo_number.text = "1"

    # def crwo_decrement(self, string):
    #     if string.isdigit():
    #         self.ids.crwo_number.text = str(int(string) - 1)
    #     else:
    #         self.ids.crwo_number.text = "0"

    # ── Валидация и старт ──
    def start(self):
        """Валидация + проверка номера CRWO на сервере."""
        # Очищаем поле генератора, если оно неактивно
        if self.ids.generator_number_box.opacity == 0:
            self.ids.generator_number.text = ""

        mode = self.ids.moto_spinner.text
        count, warn = 0, ""

        if not api.is_authorized():
            count += 1
            warn += f"{count}. Вы не авторизованы\n"

        if not self.ids.crwo_number.text:
            count += 1
            warn += f"{count}. Не заполнен номер заявки\n"

        if self.ids.choose_workers_label.text in ("Выбери исполнителей: ", ""):
            count += 1
            warn += f"{count}. Не выбран ни один сотрудник\n"

        if mode == "БС":
            if not self.ids.bs_name.text:
                count += 1
                warn += f"{count}. Не заполнен номер БС\n"
            if (self.ids.work_description_spinner.text == "Ввести свой вариант"
                    and not self.ids.work_description.text.strip()):
                count += 1
                warn += (f"{count}. Вы выбрали «Ввести свой вариант», "
                         f"но не заполнили описание работ\n")
        elif mode == "Офис":
            if not self.ids.work_description.text:
                count += 1
                warn += (f"{count}. Активен режим 'Офис', "
                         f"заполнение поля 'Описание работ' ОБЯЗАТЕЛЬНО!\n")

        if not self.arrival_date or not self.arrival_time:
            count += 1
            warn += f"{count}. Не выбрана дата и/или время прибытия\n"

        if warn:
            self.show_dialog(warn)
            return False

        # ── Проверка номера CRWO ──
        region = self.ids.region_short.text
        value_str = self.ids.crwo_number.text.strip()

        if not value_str.isdigit():
            self.show_dialog("Номер CRWO должен быть числом")
            return False

        value = int(value_str)
        print(f"[uber] start: проверка {region}-{value}")

        threading.Thread(
            target=self._check_and_proceed,
            args=(region, value),
            daemon=True,
        ).start()

        return True

    def _check_and_proceed(self, region, value):
        """Фоновая проверка номера. Вызывается из start()."""
        from sync import check_crwo_number
        from kivy.clock import Clock

        org_text = self.ids.organization.text
        if org_text == "ПО ЮСТК":
            organization = "ПО ЮСТК"
        else:
            organization = "Миранда-Медиа"

        print(f"[uber] _check_and_proceed({region}, {value}, {organization})")

        result = check_crwo_number(region, value, organization)
        print(f"[uber] check result: {result}")

        if result["status"] == "free":
            Clock.schedule_once(
                lambda dt: self._finalize_and_show(region, value, organization, forced=False),
                0,
            )
        elif result["status"] == "taken":
            Clock.schedule_once(
                lambda dt: self._show_taken_dialog(region, value, organization, result),
                0,
            )
        else:  # offline
            Clock.schedule_once(
                lambda dt: self._show_offline_and_proceed(region, value, organization),
                0,
            )

    def _finalize_and_show(self, region, value, organization, forced):
        """Сформировать заявку и перейти на CrwoWindow."""

        print(f"[uber] finalize: region={region}, value={value}, "
              f"organization={organization}, forced={forced}")

        # 1. Коммитим номер (фоном)
        commit_crwo_number(region, value, organization, forced=forced)

        # 2. Формируем текст заявки
        self.uber_make_output_sheet()

        # 3. Таймер сброса даты
        self._schedule_date_reset()

        # 4. Очистка поля генератора
        try:
            self.ids.generator_number.text = ""
        except Exception:
            pass

        # 5. Обновляем номер на следующий
        # Важно: _update_crwo_number отправит запрос и получит следующий номер
        self._update_crwo_number()

        # 6. Переход на экран заявки
        MDApp.get_running_app().go_to("CrwoWindow")
    def _schedule_date_reset(self):
        """Сбросить arrival_date через 5 минут. Отменяет предыдущий таймер."""
        from kivy.clock import Clock

        # Отменяем предыдущий таймер, если был
        if self._date_reset_event is not None:
            self._date_reset_event.cancel()
            self._date_reset_event = None

        def _reset(dt):
            """Обнулить дату — при следующем входе будет сегодня."""
            self.arrival_date = ""
            self.arrival_date_display = ""
            print("[uber] дата сброшена — при следующем входе будет сегодня")
            self._date_reset_event = None

        # 300 секунд = 5 минут
        self._date_reset_event = Clock.schedule_once(_reset, 300)
        print("[uber] таймер сброса даты установлен (5 минут)")

    def _show_taken_dialog(self, region, value, organization, result):
        """Диалог: номер уже использован в этой организации."""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivymd.uix.label import MDLabel
        from kivy.metrics import dp
        from datetime import datetime

        used_by = result.get("used_by") or "неизвестно"
        used_at = result.get("used_at") or ""
        next_free = result.get("next_free")

        try:
            dt = datetime.fromisoformat(used_at)
            used_at_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            used_at_str = used_at

        msg = (
            f"Заявка с номером CRWO_{region}_{value:08d} "
            f"уже выдавалась в «{organization}».\n\n"
            f"Кем: {used_by}\n"
            f"Когда: {used_at_str}\n\n"
            f"Что сделать?"
        )

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(MDLabel(
            text=msg, halign="center",
            size_hint_y=None, height=dp(160),
            theme_text_color="Custom", text_color=(0, 0, 0, 1),
        ))

        buttons = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint_y=None, height=dp(60))

        popup = Popup(
            title="Номер уже использован",
            title_color=(0.9, 0.3, 0.3, 1),
            title_size=dp(16),
            content=content,
            size_hint=(0.9, 0.55),
            background="", background_color=(1, 1, 1, 1),
            auto_dismiss=False,
        )

        def _force(*_):
            popup.dismiss()
            self._finalize_and_show(region, value, organization, forced=True)

        def _use_next(*_):
            popup.dismiss()
            # self.ids.crwo_number.text = str(next_free)
            self._finalize_and_show(region, next_free, organization, forced=False)

        def _cancel(*_):
            popup.dismiss()

        btn_force = Button(
            text="Использовать\nвсё равно",
            background_normal="",
            background_color=(0.9, 0.6, 0.2, 1),
            color=(1, 1, 1, 1), bold=True, font_size=dp(12),
        )
        btn_force.bind(on_release=_force)

        btn_next = Button(
            text=f"Использовать\n{next_free}",
            background_normal="",
            background_color=(0.42, 0.16, 0.85, 1),
            color=(1, 1, 1, 1), bold=True, font_size=dp(12),
        )
        btn_next.bind(on_release=_use_next)

        btn_cancel = Button(
            text="Отмена",
            background_normal="",
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1), bold=True, font_size=dp(12),
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_force)
        buttons.add_widget(btn_next)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)

        popup.open()

    def _show_offline_and_proceed(self, region, value, organization):
        """Предупреждение offline, потом формирование без коммита."""

        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivymd.uix.label import MDLabel
        from kivy.metrics import dp

        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(MDLabel(
            text=("Нет связи с сервером.\n\n"
                  "Заявка будет сформирована без проверки номера. "
                  "Если номер уже использовался — возможен дубликат."),
            halign="center",
            size_hint_y=None, height=dp(120),
            theme_text_color="Custom", text_color=(0, 0, 0, 1),
        ))

        buttons = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint_y=None, height=dp(48))

        popup = Popup(
            title="Нет связи",
            title_color=(0.9, 0.6, 0.2, 1),
            title_size=dp(16),
            content=content,
            size_hint=(0.9, 0.4),
            background="", background_color=(1, 1, 1, 1),
            auto_dismiss=False,
        )

        def _ok(*_):
            popup.dismiss()
            self._finalize_and_show(region, value, organization, forced=True)

        def _cancel(*_):
            popup.dismiss()

        btn_ok = Button(
            text="Сформировать",
            background_normal="",
            background_color=(0.42, 0.16, 0.85, 1),
            color=(1, 1, 1, 1), bold=True,
        )
        btn_ok.bind(on_release=_ok)

        btn_cancel = Button(
            text="Отмена",
            background_normal="",
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1), bold=True,
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)

        popup.open()

    # ── Формирование заявки ──
    def uber_make_output_sheet(self):
        # 1. ОБЪЯВЛЯЕМ ИНИЦИАЛЬНЫЕ ЗНАЧЕНИЯ ДЛЯ ВСЕХ ВЫХОДНЫХ ПЕРЕМЕННЫХ
        output = ""
        fin_output = ""
        checked_fin_out = ""

        ZO = {"SEV": "Севастополь", "FEO": "Феодосия", "EVP": "Евпатория",
              "YAL": "Феодосия", "SIM": "Симферополь", "KER": "Керчь"
              }.get(self.ids.region_short.text, "")

        crwo_num = self.ids.crwo_number.text
        prefix = (8 - len(crwo_num)) * "0"
        crwo_number = f"CRWO_{self.ids.region_short.text}_{prefix}{crwo_num}"
        self.plural = False
        if self.ids.organization.text == "ПО ЮСТК":
            full_name = self._get_owner_full_name()
            parts = full_name.split()
            if len(parts) >= 2:
                responsibles = parts[0] + " " + parts[1][0] + "."
            else:
                responsibles = full_name
            organization = f"🐝{self.ids.organization.text}"
        else:
            responsibles = self.ids.choose_workers_label.text
            organization = f"🍊{self.ids.organization.text}"

        spinner_val = self.ids.work_description_spinner.text
        if spinner_val == "Ввести свой вариант":
            work_desc = self.ids.work_description.text.strip()
        else:
            work_desc = spinner_val
            # Формируем строку с номером генератора (только если поле заполнено и активно)
            generator_info = ""
            if self.ids.generator_number_box.opacity == 1:
                gen_num = self.ids.generator_number.text.strip()
                if gen_num:
                    generator_info = f"\nНомер генератора: {gen_num}"

        now_dt = datetime.now()
        now = now_dt.strftime('%d.%m.%Y %H:%M')

        # Дата/время прибытия — из календаря и picker'а времени
        if self.arrival_date and self.arrival_time:
            try:
                arrive_dt = datetime.strptime(
                    f"{self.arrival_date} {self.arrival_time}",
                    "%Y-%m-%d %H:%M"
                )
                arrive = arrive_dt.strftime('%d.%m.%Y %H:%M')
            except Exception as e:
                print(f"[uber] ошибка разбора даты/времени: {e}")
                arrive = (now_dt + timedelta(hours=2)).strftime('%d.%m.%Y %H:%M')
        else:
            # Fallback — +2 часа
            arrive = (now_dt + timedelta(hours=2)).strftime('%d.%m.%Y %H:%M')

        mode = self.ids.moto_spinner.text

        if mode == "MOTO":
            output = (f'{crwo_number} / БЦ "Владимир"\n'
                      f"Адрес: г.Феодосия, ул. Чехова, д.5\n"
                      f"Тип работ: Обязательные ежедневные процедуры\n"
                      f"Описание работ: Прохождение Медицинского Осмотра, "
                      f"Открытие путевых листов.\n"
                      f"Дата/время выдачи задания: {now}\n"
                      f"Время прибытия: {arrive}\n"
                      f"Ответственный ММ : {responsibles}\n"
                      f"ЗО : {ZO}")
            # Присваиваем значение, чтобы избежать UnboundLocalError
            fin_output = output
            checked_fin_out = output

        elif mode == "Офис":
            output = (f'{crwo_number} / Офис\n'
                      f"Адрес: г.Феодосия, с.Ближнее, ул. Боевая, 2а.\n"
                      f"Тип работ: Работы на Офисе\n"
                      f"Описание работ: {work_desc}\n"
                      f"Дата/время выдачи задания: {now}\n"
                      f"Время прибытия: {arrive}\n"
                      f"Ответственный ММ : {responsibles}\n"
                      f"ЗО : {ZO}")
            # Присваиваем значение, чтобы избежать UnboundLocalError
            fin_output = output
            checked_fin_out = output


        else:  # БС
            bs = self.ids.bs_name.text.strip().upper()
            region = self.ids.region_short.text
            if len(bs.split()) == 1:

                # Если пользователь уже ввел префикс (CR или SE), используем его как есть
                if bs.startswith(("CR", "SE")):
                    target_bs = bs
                else:
                    # Пытаемся найти БС с префиксом текущего региона
                    if region == "SEV":
                        p = (4 - len(bs)) * "0"
                        target_bs = "SE" + p + bs
                    else:
                        p = (4 - len(bs)) * "0"
                        target_bs = "CR" + p + bs
                    # Если не нашли — пробуем другой префикс (умный поиск)
                    if target_bs not in self.RDB:
                        if region == "SEV":
                            p = (4 - len(bs)) * "0"
                            target_bs = "CR" + p + bs
                        else:
                            p = (4 - len(bs)) * "0"
                            target_bs = "SE" + p + bs
                if target_bs in self.RDB:
                    output = (f"{crwo_number} / {target_bs}\n"
                              f"Адрес: {self.RDB[target_bs]['address']}\n"
                              f"Координаты: {self.RDB[target_bs]['coordinates']}\n"
                              f"Тип работ: {self.ids.work_type.text}\n"
                              f"Описание работ: {work_desc}"
                              f"{generator_info}\n"
                              f"Дата/время выдачи задания: {now}\n"
                              f"Время прибытия: {arrive}\n"
                              f"Организация :{organization}\n"
                              f"Ответственный ММ : {responsibles}\n"
                              f"ЗО : {ZO}")
                    fin_output = output
                    checked_fin_out = output
                else:
                    self.show_dialog("НЕТ ТАКОЙ БС")
                    return


            else:  # Если ввели несколько БС через пробел

                bs_names = []
                checked_output = ""
                crwo_delta = 0
                for b in bs.split():
                    b = b.strip().upper()
                    region = self.ids.region_short.text
                    # Умный поиск префикса
                    if b.startswith(("CR", "SE")):
                        bs_current = b
                    else:
                        if region == "SEV":
                            p = (4 - len(b)) * "0"
                            bs_current = "SE" + p + b
                        else:
                            p = (4 - len(b)) * "0"
                            bs_current = "CR" + p + b
                        # Если не нашли — пробуем другой
                        if bs_current not in self.RDB:
                            if region == "SEV":
                                p = (4 - len(b)) * "0"
                                bs_current = "CR" + p + b
                            else:
                                p = (4 - len(b)) * "0"
                                bs_current = "SE" + p + b
                    if bs_current in self.RDB:
                        if self.ids.single_request_checkbox.active:
                            bs_names.append(bs_current)
                            checked_bs = ', '.join(bs_names)
                            checked_output = (f"{crwo_number} / {checked_bs}\n"
                                              f"Тип работ: {self.ids.work_type.text}\n"
                                              f"Описание работ: {work_desc}"
                                              f"{generator_info}\n"
                                              f"Дата/время выдачи задания: {now}\n"
                                              f"Время прибытия: {arrive}\n"
                                              f"Организация :{organization}\n"
                                              f"Ответственный ММ : {responsibles}\n"
                                              f"ЗО : {ZO}")
                            crwo_delta += 1
                        else:
                            crwo_number = f"CRWO_{region}_{prefix}{str(int(crwo_num) + crwo_delta)}"
                            output = (f"{crwo_number} / {bs_current}\n"
                                      f"Адрес: {self.RDB[bs_current]['address']}\n"
                                      f"Координаты: {self.RDB[bs_current]['coordinates']}\n"
                                      f"Тип работ: {self.ids.work_type.text}\n"
                                      f"Описание работ: {work_desc}"
                                      f"{generator_info}\n"
                                      f"Дата/время выдачи задания: {now}\n"
                                      f"Время прибытия: {arrive}\n"
                                      f"Организация :{organization}\n"
                                      f"Ответственный ММ : {responsibles}\n"
                                      f"ЗО : {ZO}")
                            crwo_delta += 1
                            if fin_output:
                                fin_output += "\n\n" + output
                            else:
                                fin_output = output
                checked_fin_out = checked_output

        # 2. ВЫВОД РЕЗУЛЬТАТА НА ЭКРАН КИВИ
        crwo_screen = self.manager.get_screen('CrwoWindow')
        if self.ids.single_request_checkbox.active:
            crwo_screen.ids.crwo_text_output.text = checked_fin_out
        else:
            crwo_screen.ids.crwo_text_output.text = fin_output


# ────────────────────────────────────────────────────────────────
# SETTINGS — обновление БД из Excel
# ────────────────────────────────────────────────────────────────
class SettingsWindow(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialog = None
        self.file_manager = None

    def on_kv_post(self, *_):
        # Загружаем текущий адрес сервера в текстовое поле при старте
        try:
            self.ids.server_url_input.text = get_server_url()
        except Exception as e:
            print(f"[settings] init server url: {e}")

    def save_server_settings(self):
        url = self.ids.server_url_input.text.strip()
        if not url:
            self.show_dialog("Адрес сервера не может быть пустым!")
            return

        # Если пользователь забыл указать протокол, добавляем https://
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        if save_server_url(url):
            self.ids.server_url_input.text = url
            self.show_dialog(
                "Адрес сервера сохранен!\n\n"
                "Изменения вступят в силу при следующем запросе.\n"
                "Возможно, потребуется перезапустить приложение."
            )
        else:
            self.show_dialog("Ошибка при сохранении. Проверьте права доступа.")

    def logout(self):
        """Выход из аккаунта."""
        api.clear_token()
        MDApp.get_running_app().go_to("LoginWindow")

    def open_file_manager(self):
        open_file_chooser(self.select_path, ext=[".xls", ".xlsx", ".csv"])

    def exit_file_manager(self, *_):
        if self.file_manager:
            self.file_manager.close()

    def select_path(self, path):
        self.exit_file_manager()
        if path.lower().endswith(('.xls', '.xlsx', '.csv')):
            self.rdb_update(path)
        else:
            self.show_dialog("Выбран некорректный формат файла!")

    def show_dialog(self, text, title="Внимание"):
        show_simple_dialog(title, text)

    def rdb_update(self, chosen_file):
        bs_list, bs_sorted, bs_dict = [], [], {}

        wb = openpyxl.load_workbook(filename=chosen_file)
        for sheet in wb.worksheets:
            for i in range(2, sheet.max_row):
                if sheet[f'a{i}'].value is not None:
                    bs_list.append(sheet[f'a{i}'].value)
        wb.close()

        for i in range(len(bs_list)):
            if i == len(bs_list) - 1:
                bs_sorted.append(bs_list[i][:6])
            elif bs_list[i][:6] == bs_list[i + 1][:6] and bs_list[i + 1][-1] > bs_list[i][-1]:
                bs_sorted.append(bs_list[i + 1][:6])
            else:
                bs_sorted.append(bs_list[i][:6])
        bs_sorted = sorted(set(bs_sorted))

        wb = openpyxl.load_workbook(filename=chosen_file)
        for sheet in wb.worksheets:
            for i in range(2, sheet.max_row + 1):
                if sheet[f'a{i}'].value is not None:
                    bs = sheet[f'a{i}'].value[:6]
                    if bs in bs_sorted:
                        bs_dict[bs] = {
                            "arc_id": sheet[f'k{i}'].value,
                            "address": sheet[f'b{i}'].value,
                            "latitude": sheet[f'c{i}'].value,
                            "longitude": sheet[f'd{i}'].value,
                            "coordinates": f"{sheet[f'c{i}'].value} {sheet[f'd{i}'].value}",
                            "yandex_map": (f"https://yandex.ru/navi/?whatshere%5Bzoom%5D=17"
                                           f"&whatshere%5Bpoint%5D={sheet[f'd{i}'].value}"
                                           f"%2C{sheet[f'c{i}'].value}"),
                            "constructional_type": sheet[f'e{i}'].value,
                            "rent": sheet[f'f{i}'].value,
                            "status": sheet[f'g{i}'].value,
                            "priority": sheet[f'q{i}'].value,
                            "transmission": sheet[f'h{i}'].value,
                            "hw_room": sheet[f'i{i}'].value,
                            "builder": sheet[f'm{i}'].value,
                            "contractor": sheet[f'p{i}'].value,
                            "exploiter": sheet[f'l{i}'].value,
                            "service_center": sheet[f'j{i}'].value,
                            "transmissionist": sheet[f'n{i}'].value,
                            "access": sheet[f'o{i}'].value,
                        }
        wb.close()

        rdb.save_rdb(bs_dict, replace=True)

        # Перезагружаем словари у экранов — перезапуск приложения не нужен
        try:
            self.manager.get_screen('Gooranda').RDB = rdb.load_rdb()
            self.manager.get_screen('Uber').RDB = rdb.load_rdb()
        except Exception as e:
            print(f"rdb_update reload: {e}")

        self.show_dialog(
            f"Обновление завершено. Записей: {len(bs_dict)}",
            title="Готово",
        )


# ────────────────────────────────────────────────────────────────
# TORUS — выбор документа и региона
# ────────────────────────────────────────────────────────────────
class TorusWindow(MDScreen):
    selected_region = StringProperty("FEO")
    path = StringProperty("")  # Объявляем свойство Kivy

    def __init__(self, **kw):
        super().__init__(**kw)
        self.file_manager = None
        self.dialog = None  # ← добавил
        self.last_path = ""  # ← запоминаем последний выбранный файл

    def open_file_manager(self):
        open_file_chooser(self.select_path, ext=[".xls", ".xlsx", ".csv"])

    def exit_file_manager(self, *_):
        if self.file_manager:
            self.file_manager.close()

    def show_dialog(self, text, title="Внимание"):
        show_simple_dialog(title, text)


    def torus_again(self, *_):
        """Повторить обработку последнего файла с текущим регионом."""
        if not self.last_path:
            show_simple_dialog(
                "Внимание",
                "Сначала выберите файл через кнопку ВЫБРАТЬ ФАЙЛ",
            )
            return
        if not os.path.exists(self.last_path):
            show_simple_dialog(
                "Внимание",
                "Последний файл не найден. Выберите его заново.",
            )
            return
        self.select_path(self.last_path)


    def torus_procedure(self, region, path):
        # ─── Оригинальные значения регионов (под MacCyrillic-кодировку CSV) ───
        if region == "FEO":
            region = "‘еодоси€"
        elif region == "EVP":
            region = "≈впатори€"
        elif region == "KER":
            region = "\xa0ерчь"
        elif region == "YAL":
            region = "ялта"
        elif region == "SIM":
            region = "—имферополь"

        # ─── Читаем CSV через встроенный csv ───
        rows = []
        with open(path, "r", encoding="MacCyrillic", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                rows.append(row)

        # ─── Помощники для приведения типов ───
        def to_float(s):
            try:
                return float(str(s).replace(",", ".").replace('"', '').strip())
            except (ValueError, TypeError):
                return None

        def to_int(s):
            try:
                return int(str(s).strip())
            except (ValueError, TypeError):
                return None

        # ─── Фильтруем по региону и приводим типы ───
        region_rows = []
        for row in rows:
            if row.get('Subregion', '').strip() != region:
                continue
            recdate = str(row.get('RECDATE', '')).split()[0] if row.get('RECDATE') else ''
            region_rows.append({
                'RECDATE': recdate,
                'vCELL': str(row.get('vCELL', '')).strip(),
                'avail_2g': to_float(row.get('Cell Avail 2G (%)')),
                'avail_3g': to_float(row.get('Cell Avail 3G (%)')),
                'avail_4g': to_float(row.get('Cell Avail 4G (%)')),
                'onair_2g': to_int(row.get('OnAir_2G')),
                'onair_3g': to_int(row.get('OnAir_3G')),
                'onair_4g': to_int(row.get('OnAir_4G')),
            })

        # ─── Проблемные соты: avail < 100 и OnAir == 1, сортировка по возрастанию ───
        def bad_cells(tech_key, onair_key):
            filtered = [
                r for r in region_rows
                if r['onair_' + onair_key] == 1
                   and r[tech_key] is not None
                   and r[tech_key] < 100
            ]
            filtered.sort(key=lambda r: r[tech_key])
            return filtered

        # ─── Уникальные БС (без CR3 и CR4) ───
        bs_set = set()
        for r in region_rows:
            vcell = r['vCELL']
            if vcell.startswith('CR3') or vcell.startswith('CR4'):
                continue
            bs_set.add(vcell[:6])
        bs_quan = len(bs_set)

        # ─── Формируем текстовые таблицы (аналог df.to_string(index=False)) ───
        def build_table(cells, tech_key):
            if not cells:
                return "(нет проблемных сот)"
            header = f"{'RECDATE':<12} {'vCELL':<12} {'Avail %':>10}"
            lines = [header, "-" * len(header)]
            for r in cells:
                lines.append(f"{r['RECDATE']:<12} {r['vCELL']:<12} {r[tech_key]:>10.3f}")
            return "\n".join(lines)

        gsm_table = build_table(bad_cells('avail_2g', '2g'), 'avail_2g')
        umts_table = build_table(bad_cells('avail_3g', '3g'), 'avail_3g')
        lte_table = build_table(bad_cells('avail_4g', '4g'), 'avail_4g')

        # ─── Средняя доступность по всем работающим сотам (OnAir == 1) ───
        def avg_avail(tech_key, onair_key):
            vals = [
                r[tech_key] for r in region_rows
                if r['onair_' + onair_key] == 1 and r[tech_key] is not None
            ]
            if not vals:
                return 0.0
            return round(sum(vals) / len(vals), 2)

        gsm_avg = avg_avail('avail_2g', '2g')
        umts_avg = avg_avail('avail_3g', '3g')
        lte_avg = avg_avail('avail_4g', '4g')

        return bs_quan, gsm_table, umts_table, lte_table, gsm_avg, umts_avg, lte_avg

    def select_path(self, path):
        self.last_path = path
        if not path.lower().endswith(('.xls', '.xlsx', '.csv')):
            show_simple_dialog("Внимание", "Неверный формат файла")
            return
        print(f"Выбран файл: {path}")
        path_to_file = path
        print(f"Регион: {self.selected_region}")
        region  = self.selected_region
        # Тут твоя логика обработки Torus-файла
        bs_quan, gsm_table, umts_table, lte_table, gsm_avg, umts_avg, lte_avg = \
            self.torus_procedure(region, path)

        network_tabs_screen = self.manager.get_screen('NetworkTabsWindow')

        # ─── Заголовок — количество БС ───
        # ⚠️ app_bar теперь MDLabel, поэтому .text, а не .title
        network_tabs_screen.ids.app_bar.text = f"Torus: {bs_quan} БС"

        # ─── Обновляем заголовки вкладок со средней доступностью ───
        # ─── Содержимое вкладок — средняя доступность в шапке каждой вкладки ───
        # MDTabs в KivyMD 1.1.1 не перерисовывает .title,
        # поэтому выводим среднее ПРЯМО В ТЕКСТЕ содержимого.
        gsm_header = f"Доступность GSM/DCS: {gsm_avg}%\n\n"
        umts_header = f"Доступность UMTS: {umts_avg}%\n\n"
        lte_header = f"Доступность LTE: {lte_avg}%\n\n"

        network_tabs_screen.ids.gsm.text = gsm_header + gsm_table
        network_tabs_screen.ids.umts.text = umts_header + umts_table
        network_tabs_screen.ids.lte.text = lte_header + lte_table

        self.manager.current = 'NetworkTabsWindow'
        self.manager.transition.direction = 'left'



# ────────────────────────────────────────────────────────────────
# NETWORK TABS — вкладки GSM / UMTS / LTE
# ────────────────────────────────────────────────────────────────
class NetworkTabsWindow(MDScreen):

    def on_pre_leave(self, *args):
        clear_all_selections(self)

    def copy_current_tab(self, *_):
        """Копирует текст активной вкладки MDTabs."""
        try:
            tabs = self.ids.tabs
            current = tabs.get_current_tab()
            # содержимое вкладки — MDScrollView, внутри которого MDLabel
            label = current.children[0]
            print(type(label))
            if label.text:
                Clipboard.copy(label.text)
                print(f"Скопировано из вкладки: {current.title}")
        except Exception as e:
            print(f"copy_current_tab error: {e}")


    def go_back(self):
        self.manager.current = 'TorusWindow'
        self.manager.transition.direction = 'right'

    def go_cancel(self):
        self.manager.current = 'Gooranda'
        self.manager.transition.direction = 'right'


# ────────────────────────────────────────────────────────────────
# BIRTHDAY — именинники и дни рождения сотрудников
# ────────────────────────────────────────────────────────────────
class BirthdayWindow(MDScreen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialog = None
        self._init_db()

    # ── Путь к БД ──
    def _db_path(self):
        return service_path('birthdays.db')

    # ── Создание таблицы ──
    def _init_db(self):
        try:
            con = sqlite3.connect(self._db_path())
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS birthdays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position TEXT,
                    name TEXT,
                    birth_date TEXT
                )
            """)
            con.commit()
            con.close()
        except Exception as e:
            print(f"_init_db: {e}")

    def on_kv_post(self, *_):
        self.refresh_tabs()

    # ── Загрузка записей из БД ──
    def _load_records(self):
        try:
            con = sqlite3.connect(self._db_path())
            cur = con.cursor()
            cur.execute("SELECT position, name, birth_date FROM birthdays")
            rows = cur.fetchall()
            con.close()
            return [{"position": r[0] or "", "name": r[1] or "", "birth_date": r[2] or ""} for r in rows]
        except Exception as e:
            #print(f"_load_records: {e}")
            return []

    # ── Парсинг даты из разных форматов ──
    def _parse_date(self, s):
        if not s:
            return None
        s = str(s).strip()
        # Убираем время, если есть
        s = s.split()[0]
        formats = [
            "%d.%m.%Y", "%d.%m.%y", "%d.%m",
            "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d/%m",
            "%d-%m-%Y", "%d-%m-%y", "%d-%m",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    # ── Список именинников на текущей неделе ──
    def _next_days(self, records, days):
        """Список именинников в ближайшие N дней (включая сегодня).
        Если ДР уже прошёл в этом году — переносится на следующий."""
        today = datetime.now().date()
        end = today + timedelta(days=days)
        result = []

        for r in records:
            bd = self._parse_date(r["birth_date"])
            if not bd:
                continue

            # ДР в этом году
            try:
                bd_this_year = bd.replace(year=today.year)
            except ValueError:  # 29.02 → 28.02
                bd_this_year = bd.replace(year=today.year, day=28)

            # Если уже прошёл — берём следующий год
            if bd_this_year < today:
                try:
                    bd_this_year = bd.replace(year=today.year + 1)
                except ValueError:
                    bd_this_year = bd.replace(year=today.year + 1, day=28)

            # Попадает в диапазон?
            if today <= bd_this_year <= end:
                result.append((r, bd_this_year))

        result.sort(key=lambda x: x[1])
        return result

    # ── Обновление трёх вкладок ──
    def refresh_tabs(self):
        records = self._load_records()
        today = datetime.now().date()

        # ── Ближайшие 7 дней ──
        week = self._next_days(records, 7)
        if not week:
            week_text = "В ближайшие 7 дней именинников нет"
        else:
            lines = ["[b]Ближайшие 7 дней:[/b]\n"]
            for r, bd in week:
                marker = "  ← СЕГОДНЯ" if bd == today else ""
                lines.append(f"• [b]{r['name']}[/b] — {bd.strftime('%d.%m')}{marker}")
                if r["position"]:
                    lines.append(f"  [i]{r['position']}[/i]")
            week_text = "\n".join(lines)

        # ── Ближайшие 30 дней ──
        month = self._next_days(records, 30)
        if not month:
            month_text = "В ближайшие 30 дней именинников нет"
        else:
            lines = ["[b]Ближайшие 30 дней:[/b]\n"]
            for r, bd in month:
                marker = "  ← СЕГОДНЯ" if bd == today else ""
                lines.append(f"• [b]{r['name']}[/b] — {bd.strftime('%d.%m')}{marker}")
                if r["position"]:
                    lines.append(f"  [i]{r['position']}[/i]")
            month_text = "\n".join(lines)

        # ── Все ──
        if not records:
            all_text = "Список пуст.\nНажмите ⬆ в шапке, чтобы загрузить файл."
        else:
            lines = [f"[b]Всего записей: {len(records)}[/b]\n"]
            for r in sorted(records, key=lambda x: x["name"].lower()):
                bd = self._parse_date(r["birth_date"])
                bd_str = bd.strftime("%d.%m.%Y") if bd else r["birth_date"] or "—"
                lines.append(f"• [b]{r['name']}[/b] — {bd_str}")
                if r["position"]:
                    lines.append(f"  [i]{r['position']}[/i]")
            all_text = "\n".join(lines)

        try:
            self.ids.week_tab.text = week_text
            self.ids.month_tab.text = month_text
            self.ids.all_tab.text = all_text
        except Exception as e:
            print(f"refresh_tabs: {e}")

    # ── Импорт из Excel / CSV ──
    def import_birthdays_dialog(self):
        open_file_chooser(self._on_file_selected, ext=[".xlsx", ".xls", ".csv"])

    def _on_file_selected(self, path):
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in (".xlsx", ".xls"):
                rows = self._read_excel(path)
            else:
                rows = self._read_csv(path)
        except Exception as e:
            show_simple_dialog("Ошибка", f"Не удалось прочитать файл:\n{e}")
            return

        if not rows:
            show_simple_dialog("Ошибка", "В файле не найдено данных")
            return

        # Спрашиваем: дополнить или заменить
        self._ask_import_mode(rows)

    def _read_excel(self, path):
        """Читает .xlsx через openpyxl. Если не получилось — пробует .xls, потом CSV."""
        import openpyxl
        try:
            wb = openpyxl.load_workbook(filename=path, data_only=True)
            ws = wb.active
            rows = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    continue
                if not row:
                    continue
                pos, name, bd = (list(row) + [None, None, None])[:3]
                name = str(name).strip() if name else ""
                if not name:
                    continue
                rows.append({
                    "position": str(pos).strip() if pos else "",
                    "name": name,
                    "birth_date": str(bd).strip() if bd else "",
                })
            wb.close()
            if rows:
                return rows
        except Exception as e:
            print(f"openpyxl failed: {e}")

        # Fallback 1: старый .xls
        rows = self._read_xls(path)
        if rows:
            return rows

        # Fallback 2: попробуем как CSV (файл мог быть переименован)
        print("trying as CSV...")
        return self._read_csv(path)

    def _read_xls(self, path):
        """Читает старый .xls (OLE2 / BIFF) через xlrd."""
        try:
            import xlrd
        except ImportError:
            print("xlrd не установлен — .xls не поддерживается")
            return []

        try:
            wb = xlrd.open_workbook(path)
            ws = wb.sheet_by_index(0)
            rows = []
            for i in range(1, ws.nrows):     # пропускаем заголовок
                row = ws.row_values(i)
                if not row or len(row) < 2:
                    continue
                pos = str(row[0]).strip() if len(row) > 0 and row[0] else ""
                name = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                bd = str(row[2]).strip() if len(row) > 2 and row[2] else ""

                # xlrd может вернуть дату как float (Excel serial date)
                if len(row) > 2 and isinstance(row[2], float):
                    try:
                        bd = xlrd.xldate_as_datetime(row[2], wb.datemode).strftime("%d.%m.%Y")
                    except Exception:
                        pass

                if not name:
                    continue
                rows.append({"position": pos, "name": name, "birth_date": bd})
            wb.release_resources()
            return rows
        except Exception as e:
            print(f"xlrd failed: {e}")
            return []

    def _read_csv(self, path):
        encodings = ["utf-8", "cp1251", "maccyrillic", "latin-1"]
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    import csv
                    # Пробуем определить разделитель
                    sample = f.read(2048)
                    f.seek(0)
                    delim = ";" if sample.count(";") > sample.count(",") else ","
                    reader = csv.reader(f, delimiter=delim)
                    rows = []
                    for i, row in enumerate(reader):
                        if i == 0:
                            continue
                        if not row or len(row) < 2:
                            continue
                        pos = row[0].strip() if len(row) > 0 else ""
                        name = row[1].strip() if len(row) > 1 else ""
                        bd = row[2].strip() if len(row) > 2 else ""
                        if not name:
                            continue
                        rows.append({"position": pos, "name": name, "birth_date": bd})
                    return rows
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                print(f"_read_csv ({enc}): {e}")
                continue
        return []

    # ── Спросить: дополнить или заменить ──
    def _ask_import_mode(self, new_rows):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.metrics import dp

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12)] * 4,
        )

        msg = Label(
            text=(f"Найдено записей: {len(new_rows)}\n\n"
                  f"Дополнить существующую базу или заменить её?"),
            color=(0.106, 0.106, 0.118, 1),
            halign="center",
            valign="middle",
        )
        msg.bind(size=lambda s, w: setattr(s, "text_size", w))
        content.add_widget(msg)

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        popup = Popup(
            title="Импорт дней рождения",
            title_color=(0.42, 0.16, 0.85, 1),
            title_size=dp(16),
            separator_color=(0.85, 0.85, 0.85, 1),
            content=content,
            size_hint=(0.9, 0.4),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _append(*_):
            popup.dismiss()
            self._save_to_db(new_rows, replace=False)
            self.refresh_tabs()
            show_simple_dialog("Готово", f"Добавлено: {len(new_rows)}")

        def _replace(*_):
            popup.dismiss()
            self._save_to_db(new_rows, replace=True)
            self.refresh_tabs()
            show_simple_dialog("Готово", f"База обновлена: {len(new_rows)} записей")

        def _cancel(*_):
            popup.dismiss()

        btn_append = Button(
            text="ДОПОЛНИТЬ", background_normal="",
            background_color=(0.42, 0.16, 0.85, 1),
            color=(1, 1, 1, 1), bold=True, font_size=dp(13),
        )
        btn_append.bind(on_release=_append)

        btn_replace = Button(
            text="ЗАМЕНИТЬ", background_normal="",
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1), bold=True, font_size=dp(13),
        )
        btn_replace.bind(on_release=_replace)

        btn_cancel = Button(
            text="ОТМЕНА", background_normal="",
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1), bold=True, font_size=dp(13),
        )
        btn_cancel.bind(on_release=_cancel)

        buttons.add_widget(btn_append)
        buttons.add_widget(btn_replace)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        popup.open()

    def _save_to_db(self, rows, replace=False):
        con = sqlite3.connect(self._db_path())
        cur = con.cursor()
        if replace:
            cur.execute("DELETE FROM birthdays")
        for r in rows:
            cur.execute(
                "INSERT INTO birthdays (position, name, birth_date) VALUES (?, ?, ?)",
                (r["position"], r["name"], r["birth_date"]),
            )
        con.commit()
        con.close()

# ────────────────────────────────────────────────────────────────
# BLITZ REPORT — ежедневная сводка ЦТЭиСО
# ────────────────────────────────────────────────────────────────

BLITZ_PRIORITY_ORDER = ["P0", "P1", "P2", "P3", "НП"]
BLITZ_CONFIG_FILE = "blitz_config.json"


def _blitz_config_path():
    return service_path(BLITZ_CONFIG_FILE)


BLITZ_DEFAULT_CONSTANTS = {}



def blitz_load_user_constants():
    """Пользовательские константы (без базовых). Возвращает dict."""
    p = _blitz_config_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # отфильтровываем базовые — они всегда добавляются на лету
                    return {k: v for k, v in data.items()
                            if k not in BLITZ_DEFAULT_CONSTANTS}
        except Exception as e:
            print(f"[blitz] load_user_constants: {e}")
    return {}


def blitz_save_user_constants(constants):
    """Сохраняет только пользовательские константы."""
    try:
        with open(_blitz_config_path(), "w", encoding="utf-8") as f:
            json.dump(constants, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[blitz] save_user_constants: {e}")


def blitz_effective_constants():
    """Базовые + пользовательские (пользователь может переопределить базовые)."""
    merged = BLITZ_DEFAULT_CONSTANTS.copy()
    merged.update(blitz_load_user_constants())
    return merged

# ────────────────────────────────────────────────────────────────
# BLITZ REPORT — resource_plan.xlsx (приоритеты генерации)
# ────────────────────────────────────────────────────────────────
def blitz_read_resource_plan(path):
    """Читает лист 'Приоритеты БС'. Колонка B (BlackOut).
    Возвращает dict: { 'CR0001': 'генерация - приоритет 0', ... }
    """
    res = {}
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        try:
            if "Приоритеты БС" not in wb.sheetnames:
                print("[blitz] В файле нет листа 'Приоритеты БС'")
                return res

            ws = wb["Приоритеты БС"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                bts = str(row[0]).strip().upper()
                # Колонка B (индекс 1) — BlackOut
                blackout = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                if blackout:
                    res[bts] = blackout
        finally:
            wb.close()
    except Exception as e:
        print(f"[blitz] Ошибка чтения resource_plan: {e}")
    return res


# ────────────────────────────────────────────────────────────────
# BLITZ REPORT — сохранение resource_plan.xlsx между запусками
# ────────────────────────────────────────────────────────────────
def _blitz_plan_storage_path():
    return service_path("blitz_resource_plan.xlsx")


def _blitz_plan_meta_path():
    return service_path("blitz_resource_plan.json")

_server_status = {"state": "unknown", "ts": 0}  # unknown / online / offline

import urllib.parse


def _ping_server(timeout=3):
    """Проверяет TCP-соединение с сервером из настроек."""
    try:
        url = get_server_url()

        # Разбираем URL правильно (понимает и http, и https, и порты)
        parsed = urllib.parse.urlparse(url)

        # Получаем хост (IP или домен)
        host = parsed.hostname
        if not host:
            # Если urlparse не смог, пробуем простой сплит
            host = url.replace("https://", "").replace("http://", "").split(":")[0]

        # Определяем порт
        if parsed.port:
            port = parsed.port
        elif parsed.scheme == "https":
            port = 443
        else:
            port = 80

        # Пробуем подключиться
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception as e:
        print(f"[ping] error: {e}")
        return False


def _server_ping_loop(app):
    """Фоновый поток: пингует сервер раз в 15 секунд."""
    import time
    while True:
        ok = _ping_server()
        _server_status["state"] = "online" if ok else "offline"
        _server_status["ts"] = time.time()

        # Обновляем UI в главном потоке
        Clock.schedule_once(lambda dt: _update_ping_ui(app), 0)

        time.sleep(15)


def _update_ping_ui(app):
    """Рекурсивно обновляет иконку связи на ВСЕХ экранах."""
    try:
        state = _server_status["state"]

        if state == "online":
            icon_name = "cloud-check"
            color = (0.2, 0.8, 0.3, 1)  # Зеленый
        elif state == "offline":
            icon_name = "cloud-off-outline"
            color = (0.9, 0.2, 0.2, 1)  # Красный
        else:
            icon_name = "cloud-question"
            color = (0.9, 0.7, 0.1, 1)  # Желтый

        # Проходимся по всем экранам
        for screen in app.root.screens:
            # Рекурсивно ищем все виджеты класса ScreenHeader
            for child in screen.walk():
                # Проверяем по имени класса, чтобы не делать лишних импортов
                if child.__class__.__name__ == "ScreenHeader":
                    try:
                        # Внутри найденной шапки ищем нашу иконку по локальному id
                        if "ping_icon" in child.ids:
                            child.ids.ping_icon.icon = icon_name
                            child.ids.ping_icon.text_color = color
                    except Exception as e:
                        print(f"[ping] error updating widget: {e}")

    except Exception as e:
        print(f"[ping] update_ui error: {e}")


def start_ping_thread(app):
    """Запускает фоновый пинг при старте приложения."""
    t = threading.Thread(target=_server_ping_loop, args=(app,), daemon=True)
    t.start()
    print("[ping] фоновый поток запущен")


def blitz_save_plan_file(src_path):
    """Копирует выбранный файл в папку приложения."""
    import shutil

    if not src_path or not os.path.exists(src_path):
        return False, "", "Файл не найден"

    dest = _blitz_plan_storage_path()
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)

        if os.path.exists(dest):
            try:
                os.remove(dest)
            except Exception as e:
                print(f"[blitz] не удалось удалить старый файл: {e}")

        shutil.copy2(src_path, dest)

        meta = {
            "original_path": src_path,
            "original_name": os.path.basename(src_path),
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(_blitz_plan_meta_path(), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return True, dest, None

    except Exception as e:
        print(f"[blitz] save plan error: {e}")
        return False, "", str(e)


def blitz_get_saved_plan_path():
    p = _blitz_plan_storage_path()
    return p if os.path.exists(p) else ""


def blitz_get_saved_plan_info():
    p = _blitz_plan_meta_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def blitz_clear_saved_plan():
    for p in (_blitz_plan_storage_path(), _blitz_plan_meta_path()):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception as e:
            print(f"[blitz] clear saved plan: {e}")


def blitz_parse_priority(val):
    if val is None:
        return "НП"
    s = str(val).strip().lower()
    if not s:
        return "НП"

    # Ищем "приоритет 0", "приоритет 3" и т.п. (в т.ч. "генерация - приоритет 3")
    m = re.search(r"приоритет\s*(\d)", s)
    if m:
        return f"P{m.group(1)}"

    # Ищем "P0", "P1", "P2", "P3"
    m2 = re.search(r"\b(p[0-3])\b", s)
    if m2:
        return m2.group(1).upper()

    return "НП"


def blitz_format_duration(delta):
    total = int(delta.total_seconds())
    if total < 0:
        total = 0
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    if days >= 1:
        return f"{days} сут {hours} ч"
    if hours >= 1:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def blitz_parse_file_dt(path):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})_(\d{2})_(\d{2})", Path(path).name)
    return datetime(*map(int, m.groups())) if m else datetime.now()


def blitz_to_dt(val):
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                pass
    return None


def blitz_label(prio):
    if prio in ("P0", "P1"):
        return f"**{prio}:**"
    if prio == "P2":
        return f"*{prio}:*"
    return f"{prio}:"


def blitz_label_n(prio, n):
    if prio in ("P0", "P1"):
        return f"**{prio} ({n} БС):**"
    if prio == "P2":
        return f"*{prio} ({n} БС):*"
    return f"{prio} ({n} БС):"


def _blitz_load_sheet(path, sheet_name):
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    try:
        if sheet_name not in wb.sheetnames:
            return []
        ws = wb[sheet_name]
        return [r for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0]]
    finally:
        wb.close()


def blitz_read_om(path):
    return [
        {"alarm": r[0], "occurrence": r[1], "bts": r[2],
         "sc": r[4], "diesel_priority": r[7] if len(r) > 7 else None}
        for r in _blitz_load_sheet(path, "OM")
    ]


def blitz_read_diesel(path):
    return [
        {"bts": r[0], "alarm": r[1], "occurrence": r[2],
         "sc": r[4] if len(r) > 4 else None}
        for r in _blitz_load_sheet(path, "Diesel On")
    ]


def blitz_read_alarms(path):
    return [
        {"bts": r[0], "sc": r[1], "alarm": r[3],
         "priority": r[5] if len(r) > 5 else None}
        for r in _blitz_load_sheet(path, "Sheet")
    ]


def blitz_get_unique_scs(om_path):
    try:
        om = blitz_read_om(om_path)
        scs = sorted({r["sc"] for r in om if r["sc"]})
        return scs if scs else ["Сервисный Центр Феодосия"]
    except Exception:
        return ["Сервисный Центр Феодосия"]


def _blitz_build_ne(om, sc_name, get_prio, constants):
    result, seen = [], set()
    for r in om:
        if r["alarm"] != "NE Is Disconnected" or r["sc"] != sc_name:
            continue
        bts = r["bts"]
        if bts in seen:
            continue
        seen.add(bts)
        result.append({
            "bts": bts,
            "priority": get_prio(bts),
            "reason": "причина не указана",
        })

    for bts, reason in constants.items():
        if bts in seen:
            for x in result:
                if x["bts"] == bts:
                    x["reason"] = reason
        else:
            result.append({
                "bts": bts,
                "priority": get_prio(bts),
                "reason": reason,
            })
            seen.add(bts)
    return result


def _blitz_build_gen(diesel, sc_name, get_prio, file_dt):
    result, seen = [], set()
    for r in diesel:
        if r["sc"] != sc_name:
            continue
        bts = r["bts"]
        if bts in seen:
            continue
        seen.add(bts)
        occ = blitz_to_dt(r["occurrence"])
        dur = blitz_format_duration(file_dt - occ) if occ else "—"
        result.append({"bts": bts, "priority": get_prio(bts), "duration": dur})
    return result


def _blitz_build_akb(alarms, sc_name, get_prio, gen_names):
    result, seen = [], set()
    for r in alarms:
        if r["alarm"] != "MAINS FAILURE" or r["sc"] != sc_name:
            continue
        bts = r["bts"]
        if bts in seen or bts in gen_names:
            continue
        seen.add(bts)
        result.append({"bts": bts, "priority": get_prio(bts)})
    return result


def _blitz_group(items):
    by_p = {}
    for it in items:
        by_p.setdefault(it["priority"], []).append(it)
    return by_p


def _blitz_format_ne(items):
    """NE DISCONNECTED — каждая станция с новой строки, с приоритетом."""
    lines, by_p = [], _blitz_group(items)
    for p in BLITZ_PRIORITY_ORDER:  # ["P0","P1","P2","P3","НП"]
        if p not in by_p:
            continue
        group_sorted = sorted(by_p[p], key=lambda x: x["bts"])
        for it in group_sorted:
            lines.append(f"{blitz_label(p)} {it['bts']} — {it['reason']}")
    return "\n".join(lines)


def _blitz_format_akb(items):
    lines, by_p = [], _blitz_group(items)
    for p in BLITZ_PRIORITY_ORDER:
        if p not in by_p:
            continue
        group_sorted = sorted(by_p[p], key=lambda x: x["bts"])

        if len(group_sorted) == 1:
            lines.append(f"{blitz_label(p)} {group_sorted[0]['bts']}")
        else:
            joined = ", ".join(it["bts"] for it in group_sorted)
            lines.append(f"{blitz_label_n(p, len(group_sorted))} {joined}")

    return "\n".join(lines)


def _blitz_format_gen(items):
    lines, by_p = [], _blitz_group(items)
    for p in BLITZ_PRIORITY_ORDER:
        if p not in by_p:
            continue
        group_sorted = sorted(by_p[p], key=lambda x: x["bts"])

        if len(group_sorted) == 1:
            it = group_sorted[0]
            lines.append(f"{blitz_label(p)} {it['bts']} — {it['duration']}")
        else:
            joined = "; ".join(
                f"{it['bts']} — {it['duration']}" for it in group_sorted
            )
            lines.append(f"{blitz_label_n(p, len(group_sorted))} {joined}")

    return "\n".join(lines)


def blitz_build_report(om_path, alarms_path, sc_name, constants, plan_path=None):
    om = blitz_read_om(om_path)
    diesel = blitz_read_diesel(om_path)
    alarms = blitz_read_alarms(alarms_path)
    file_dt = blitz_parse_file_dt(om_path)

    # ── Загружаем приоритеты из resource_plan (BlackOut) ──
    gen_prio = {}
    if plan_path and os.path.exists(plan_path):
        raw_plan = blitz_read_resource_plan(plan_path)
        for bts, blackout_str in raw_plan.items():
            p = blitz_parse_priority(blackout_str)
            if p != "НП":
                gen_prio[bts] = p
        print(f"[blitz] Загружено приоритетов: {len(gen_prio)}")

    def get_prio(bts):
        return gen_prio.get(bts, "НП")

    ne = _blitz_build_ne(om, sc_name, get_prio, constants)
    gen = _blitz_build_gen(diesel, sc_name, get_prio, file_dt)
    akb = _blitz_build_akb(alarms, sc_name, get_prio, {g["bts"] for g in gen})

    now = datetime.now()
    short_sc = sc_name.replace("Сервисный Центр ", "")
    out = [
        f"📡 ЦТЭиСО {short_sc} — сводка", "",
        f"📅 Дата формирования: {now.strftime('%d.%m.%Y')}",
        f"🕐 Время формирования: {now.strftime('%H:%M')}", "", "---", "",
        f" 🔴 NE DISCONNECTED ({len(ne)} БС)", "",
        _blitz_format_ne(ne) if ne else "0 БС", "",
        f" 🔋 На АКБ: {len(akb)} БС", "",
        _blitz_format_akb(akb) if akb else "0 БС", "",
        f" ⚡ На Генерации: {len(gen)} БС", "",
        _blitz_format_gen(gen) if gen else "0 БС",
    ]
    return "\n".join(out)

def _blitz_search_dirs():
    """Папки, где ищем файлы (Android и Desktop)."""
    candidates = []
    if IS_ANDROID:
        try:
            candidates.append(MDApp.get_running_app().user_data_dir)
        except Exception:
            pass
        candidates.append("/storage/emulated/0/Download")
        candidates.append("/storage/emulated/0/Documents")
        candidates.append("/storage/emulated/0")
    else:
        up = os.environ.get("USERPROFILE")
        if up:
            candidates.append(os.path.join(up, "Downloads"))
        home = os.path.expanduser("~")
        candidates.append(os.path.join(home, "Downloads"))
        candidates.append(os.path.join(home, "Загрузки"))
        candidates.append(home)

    valid = [d for d in candidates if os.path.isdir(d)]
    # убираем дубликаты, сохраняя порядок
    seen, out = set(), []
    for d in valid:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out if out else ["/"]

def open_file_chooser_search(on_select, prefix_filter=None, title="Выберите файл"):
    """Popup с живым поиском по имени файла.

    :param on_select: callable(path) — вызывается при выборе файла
    :param prefix_filter: callable(filename) -> bool — доп. фильтр по имени
    :param title: заголовок Popup
    """
    search_dirs = _blitz_search_dirs()

    # ── Поле поиска ──
    search_box = MDBoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(48),
        spacing=dp(8),
        padding=[dp(4), 0, dp(4), 0],
    )
    search_field = TextInput(
        hint_text="Введите часть имени файла…",
        multiline=False,
        input_type="text",
        size_hint_y=None,
        height=dp(44),
        background_color=(0.95, 0.95, 0.97, 1),
        foreground_color=TEXT_COLOR,
        cursor_color=(0.42, 0.16, 0.85, 1),
        font_size=dp(15),
        padding=[dp(10), dp(10), dp(10), dp(10)],
    )
    search_box.add_widget(search_field)

    # ── Список файлов ──
    list_layout = BoxLayout(
        orientation="vertical",
        size_hint_y=None,
        spacing=dp(2),
        padding=[dp(4)] * 4,
    )
    list_layout.bind(minimum_height=list_layout.setter("height"))

    list_scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
    list_scroll.add_widget(list_layout)

    # ── Нижние кнопки ──
    buttons = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(48),
        spacing=dp(8),
        padding=[dp(8), 0, dp(8), 0],
    )

    popup = Popup(
        title=title,
        title_color=TEXT_COLOR,
        title_size=dp(16),
        separator_color=(0.85, 0.85, 0.85, 1),
        size_hint=(0.95, 0.9),
        background="",
        background_color=(1, 1, 1, 1),
        auto_dismiss=True,
    )

    def _choose_file(full_path):
        popup.dismiss()
        # откладываем вызов, чтобы Popup успел закрыться (MIUI!)
        Clock.schedule_once(lambda dt: on_select(full_path), 0.15)

    def _rebuild_list(search_text=""):
        list_layout.clear_widgets()

        st = search_text.lower().strip()
        found = []

        for d in search_dirs:
            try:
                for fname in os.listdir(d):
                    full = os.path.join(d, fname)
                    if not os.path.isfile(full):
                        continue
                    # применяем внешний фильтр (например, «site_not_air»)
                    if prefix_filter and not prefix_filter(fname):
                        continue
                    # применяем живой поиск
                    if st and st not in fname.lower():
                        continue
                    found.append((fname, full))
            except Exception:
                continue

        # убираем дубли по полному пути, сортируем по дате изменения (новые сверху)
        uniq = {}
        for fname, full in found:
            uniq[full] = fname
        items = []
        for full, fname in uniq.items():
            try:
                mtime = os.path.getmtime(full)
            except Exception:
                mtime = 0
            items.append((mtime, fname, full))
        items.sort(key=lambda x: x[0], reverse=True)

        if not items:
            list_layout.add_widget(Label(
                text="Файлы не найдены",
                color=TEXT_COLOR,
                size_hint_y=None,
                height=dp(40),
            ))
            return

        for _, fname, full in items:
            btn = Button(
                text=fname,
                size_hint_y=None,
                height=dp(52),
                background_normal="",
                background_down="",
                background_color=(0.95, 0.95, 0.97, 1),
                color=TEXT_COLOR,
                font_size=dp(14),
                halign="left",
                valign="middle",
            )
            # перенос длинных имён
            btn.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w - dp(16), None)),
            )
            btn.bind(on_release=lambda x, p=full: _choose_file(p))
            list_layout.add_widget(btn)

    def _cancel(*_):
        popup.dismiss()

    btn_cancel = Button(
        text="ОТМЕНА",
        background_normal="",
        background_color=(0.9, 0.3, 0.3, 1),
        color=(1, 1, 1, 1),
        bold=True,
    )
    btn_cancel.bind(on_release=_cancel)
    buttons.add_widget(btn_cancel)

    # ── Сборка контента ──
    content = BoxLayout(orientation="vertical", spacing=dp(4), padding=dp(4))
    content.add_widget(search_box)
    content.add_widget(list_scroll)
    content.add_widget(buttons)

    popup.content = content

    # ── События ──
    search_field.bind(text=lambda inst, val: _rebuild_list(val))

    # Строим список после открытия (чтобы размеры виджетов были готовы)
    Clock.schedule_once(lambda dt: _rebuild_list(""), 0.1)

    popup.open()
    return popup


# ────────────────────────────────────────────────────────────────
# BLITZ REPORT — экран
# ────────────────────────────────────────────────────────────────
class BlitzReportWindow(MDScreen):
    """Экран быстрой сводки ЦТЭиСО."""

    def __init__(self, **kw):
        self.user_constants = blitz_load_user_constants()
        super().__init__(**kw)

    def on_kv_post(self, *_):
        try:
            self.ids.blitz_sc.values = (
                "Сервисный Центр Феодосия",
                "Сервисный Центр Симферополь",
            )
        except Exception:
            pass

        # Восстанавливаем сохранённый resource_plan
        saved = blitz_get_saved_plan_path()
        if saved:
            try:
                self.ids.blitz_plan_path.text = saved
                info = blitz_get_saved_plan_info()
                name = info.get("original_name", os.path.basename(saved))
                saved_at = info.get("saved_at", "")
                self.ids.blitz_plan_status.text = (
                    f"✅ {name} (загружен {saved_at})"
                )
                self.ids.blitz_plan_status.text_color = (0.2, 0.6, 0.2, 1)
            except Exception as e:
                print(f"[blitz] restore plan: {e}")

        Clock.schedule_once(lambda dt: self._refresh_constants_list(), 0.1)

    def on_pre_enter(self, *args):
        try:
            UberWindow.RDB = rdb.load_rdb()
        except Exception:
            pass

    def on_pre_leave(self, *args):
        clear_all_selections(self)

    # ── Работа с константами ──
    def _refresh_constants_list(self):
        try:
            container = self.ids.blitz_constants_list
        except Exception:
            return

        container.clear_widgets()

        constants = getattr(self, "user_constants", None) or {}

        if not constants:
            container.add_widget(MDLabel(
                text="Пользовательских констант нет. Добавьте БС ниже.",
                theme_text_color="Custom",
                text_color=(0.5, 0.5, 0.5, 1),
                font_size="13sp",
                size_hint_y=None,
                height="32dp",
                halign="center",
            ))
            return

        for bts, reason in sorted(constants.items()):
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="44dp",
                spacing="6dp",
                padding=["8dp", 0, "4dp", 0],
            )

            text = MDLabel(
                text=f"{bts} — {reason}",
                theme_text_color="Custom",
                text_color=TEXT_COLOR,
                font_size="13sp",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
            row.add_widget(text)

            del_btn = MDIconButton(
                icon="delete",
                theme_text_color="Custom",
                text_color=(0.85, 0.2, 0.2, 1),
                size_hint=(None, None),
                size=("36dp", "36dp"),
                pos_hint={"center_y": .5},
            )
            del_btn.bind(
                on_release=lambda x, b=bts: self.delete_constant(b)
            )
            row.add_widget(del_btn)

            container.add_widget(row)

    def add_constant(self):
        """Читает два поля, добавляет пару БС → причина в словарь."""
        try:
            bts = self.ids.blitz_new_bts.text.strip().upper()
            reason = self.ids.blitz_new_reason.text.strip()
        except Exception as e:
            print(f"[blitz] add_constant read: {e}")
            return

        if not bts or not reason:
            show_simple_dialog(
                "Внимание",
                "Заполните номер БС и причину неэфира.",
            )
            return

        # Пользователь может переопределить базовую — предупреждаем
        if bts in BLITZ_DEFAULT_CONSTANTS:
            show_simple_dialog(
                "Внимание",
                f"БС {bts} уже есть в базовых константах. "
                f"Если сохранить — ваша причина заменит базовую.",
            )

        self.user_constants[bts] = reason
        blitz_save_user_constants(self.user_constants)

        # очищаем поля
        self.ids.blitz_new_bts.text = ""
        self.ids.blitz_new_reason.text = ""

        self._refresh_constants_list()

    def delete_constant(self, bts):
        """Удаляет пользовательскую константу."""
        if bts in self.user_constants:
            del self.user_constants[bts]
            blitz_save_user_constants(self.user_constants)
            self._refresh_constants_list()

    # ── Выбор файла: site_not_air ──
    def pick_om_file(self):
        def is_om(fname):
            n = fname.lower()
            return (
                n.endswith((".xlsx", ".xls"))
                and ("site_not_air" in n or "not_air" in n)
            )

        def on_select(path):
            try:
                self.ids.blitz_om_path.text = path
                scs = blitz_get_unique_scs(path)
                self.ids.blitz_sc.values = scs
                if scs:
                    self.ids.blitz_sc.text = scs[0]
            except Exception as e:
                show_simple_dialog("Ошибка", f"Не удалось прочитать файл OM:\n{e}")

        open_file_chooser_search(
            on_select,
            prefix_filter=is_om,
            title="Файл site_not_air",
        )

    # ── Выбор файла: Список аварий ──
    def pick_alarms_file(self):
        def is_alarms(fname):
            n = fname.lower()
            return n.endswith((".xlsx", ".xls")) and "авари" in n

        def on_select(path):
            self.ids.blitz_alarms_path.text = path

        open_file_chooser_search(
            on_select,
            prefix_filter=is_alarms,
            title="Файл «Список аварий»",
        )

    def pick_plan_file(self):
        """Выбор resource_plan.xlsx с сохранением между запусками."""

        def is_plan(fname):
            n = fname.lower()
            return n.endswith((".xlsx", ".xls")) and "resource" in n

        def on_select(path):
            if not path:
                return
            ok, saved_path, err = blitz_save_plan_file(path)
            if not ok:
                show_simple_dialog("Ошибка", f"Не удалось сохранить файл:\n{err}")
                return

            try:
                self.ids.blitz_plan_path.text = saved_path
                info = blitz_get_saved_plan_info()
                name = info.get("original_name", os.path.basename(saved_path))
                saved_at = info.get("saved_at", "")
                self.ids.blitz_plan_status.text = (
                    f"✅ {name} (загружен {saved_at})"
                )
                self.ids.blitz_plan_status.text_color = (0.2, 0.6, 0.2, 1)
            except Exception as e:
                print(f"[blitz] pick_plan_file UI: {e}")

            show_simple_dialog(
                "Готово",
                f"Файл сохранён.\n\n"
                f"Оригинал: {path}\n"
                f"Копия:    {saved_path}\n\n"
                f"Файл будет использоваться при следующем запуске автоматически."
            )

        open_file_chooser_search(
            on_select,
            prefix_filter=is_plan,
            title="Выберите resource_plan.xlsx",
        )

    def clear_saved_plan(self):
        """Сброс сохранённого файла."""
        blitz_clear_saved_plan()
        try:
            self.ids.blitz_plan_path.text = ""
            self.ids.blitz_plan_status.text = "❌ Файл не загружен"
            self.ids.blitz_plan_status.text_color = (0.85, 0.2, 0.2, 1)
        except Exception:
            pass

    # ── Формирование отчёта ──
    def generate(self):
        try:
            om_path = self.ids.blitz_om_path.text.strip()
            alarms_path = self.ids.blitz_alarms_path.text.strip()
            plan_path = self.ids.blitz_plan_path.text.strip()
            sc_name = self.ids.blitz_sc.text

            if not om_path or not os.path.exists(om_path):
                show_simple_dialog("Ошибка", "Не выбран файл site_not_air (*.xlsx).")
                return
            if not alarms_path or not os.path.exists(alarms_path):
                show_simple_dialog("Ошибка", "Не выбран файл «Список аварий» (*.xlsx).")
                return
            if not plan_path or not os.path.exists(plan_path):
                show_simple_dialog(
                    "Ошибка",
                    "Не загружен resource_plan.xlsx.\n"
                    "Нажмите «📥 ЗАГРУЗИТЬ resource_plan»."
                )
                return

            # Пользовательские константы (для причин NE)
            constants = self.user_constants.copy()

            self.ids.blitz_text_output.text = blitz_build_report(
                om_path, alarms_path, sc_name, constants, plan_path
            )
        except Exception as e:
            self.ids.blitz_text_output.text = (
                f"Ошибка при формировании отчёта:\n{e}\n\n{traceback.format_exc()}"
            )

    # ── Копирование / очистка ──
    def copy_to_clipboard(self, string):
        if string:
            Clipboard.copy(string)

    def clear_report(self):
        try:
            self.ids.blitz_text_output.text = ""
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────
# КОРНЕВОЙ SCREEN MANAGER
# ────────────────────────────────────────────────────────────────
class WindowManager(MDScreenManager):
    """ScreenManager, который при каждой смене экрана снимает выделение
    со всех SelectableLabel — иначе ручки выделения (они рисуются в Window)
    остаются висеть поверх других экранов."""

    def on_current(self, instance, value):
        super().on_current(instance, value)
        # Откладываем на 1 кадр, чтобы transition успел начаться
        Clock.schedule_once(self._clear_all_selections, 0.05)

    def _clear_all_selections(self, *_):
        for screen in self.screens:
            for child in screen.walk():
                if isinstance(child, SelectableLabel):
                    try:
                        child.cancel_selection()
                        child.focus = False
                    except Exception:
                        pass


# ────────────────────────────────────────────────────────────────
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ────────────────────────────────────────────────────────────────
class UberGoorandaApp(MDApp):
    PUBLIC_SCREENS = {"LoginWindow"}  # ← экраны, доступные без токена

    def go_to(self, screen_name, direction="left"):
        if screen_name not in self.PUBLIC_SCREENS and not api.is_authorized():
            screen_name = "LoginWindow"
            direction = "right"
        self._blur_all_inputs()
        self.root.current = screen_name
        self.root.transition.direction = direction

    def go_back(self, screen_name):
        if screen_name not in self.PUBLIC_SCREENS and not api.is_authorized():
            screen_name = "LoginWindow"
        self._blur_all_inputs()
        self.root.current = screen_name
        self.root.transition.direction = "right"

    def on_start(self):
        db.init_db()
        rdb.init_db()
        # ── Запускаем индикатор связи ──
        start_ping_thread(self)

        # ── Проверка токена ──
        if api.is_authorized():
            me = api.fetch_me()
            if me:
                # Токен валиден — автологин
                api.user_id = me["id"]
                api.role = me["role"]
                api.first_name = me["first_name"]
                api.last_name = me.get("last_name")
                Clock.schedule_once(
                    lambda dt: self.go_to("Gooranda"), 0.3
                )
                return

            # Токен есть, но fetch_me вернул None — разбираемся почему
            err = getattr(api, "last_error", None)

            if err == "expired":
                # Сервер явно сказал «токен невалиден» — чистим
                print("[app] токен протух (401) — очищаем, логинимся заново")
                api.clear_token()
                # остаёмся на LoginWindow (sm.current уже = "LoginWindow")

            elif err == "offline":
                # Сеть недоступна — НЕ трогаем токен, работаем офлайн
                print("[app] сервер недоступен — работаем в offline-режиме")
                # пользователь остаётся на LoginWindow, но токен сохранён;
                # при попытке открыть защищённый экран — редирект не сработает
                # (is_authorized=True), но HTTP-запросы вернут offline.
                # Это лучше, чем каждый раз вводить пароль.
                # Можно сразу переходить в Gooranda, если хочешь:
                Clock.schedule_once(
                    lambda dt: self.go_to("Gooranda"), 0.3
                )

            else:
                # Что-то другое (500 и т.п.) — оставляем токен на всякий случай
                print(f"[app] /auth/me ошибка ({err}) — остаёмся на LoginWindow")

        else:
            print("[app] токена нет — показываем LoginWindow")



    # ── Списки вариантов для меню ──
    TT_OPTIONS = ["TT", "Без ТТ"]
    MOTO_OPTIONS = ["БС", "Офис", "MOTO"]
    REGION_OPTIONS = ["FEO", "EVP", "KER", "SIM", "SEV", "YAL"]
    ORGANIZATION_OPTIONS = ["Миранда-Медиа", "ПО ЮСТК"]
    WORK_TYPE_OPTIONS = [
        "🚑 АВР", "🔋 ДГУ", "🛠 ППР", "⚙️ ТО",
        "📸 ДВ", "🔑 РАБОТЫ ПО ЗАДАНИЮ",
        "❤️ Обязательные процедуры",
    ]

    WORK_DESC_OPTIONS = [
        "⚙️ Провести ТО Базовой станции",
        "🪫 Запитать БС от ДГУ",
        "⛽️Заправка генераторов Базовых Станций",
        "🌿 Обкосить траву по периметру БС",
        "❤️ Прохождение МО и ТО",
        "Ввести свой вариант",
    ]
    MODE_OPTIONS = ["БС", "ARC", "ТП", "Адрес"]

    def on_pause(self):
        """Перед сворачиванием приложения — снимаем выделение."""
        self._blur_all_inputs()
        return True

    def on_resume(self):
        """После возврата — снимаем выделение на случай, если оно осталось."""
        Clock.schedule_once(lambda dt: self._blur_all_inputs(), 0.1)

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Teal"


        Builder.load_file(resource_path('ui.kv'))

        # Регистрируем эмодзи-шрифт
        LabelBase.register(
            name='Emoji',
            fn_regular=resource_path('fonts/NotoEmoji-Regular.ttf'),
        )

        sm = WindowManager()
        sm.add_widget(LoginWindow(name="LoginWindow"))
        sm.add_widget(GoorandaWindow(name="Gooranda"))
        sm.add_widget(UberWindow(name="Uber"))
        sm.add_widget(WorkerWindow(name="WorkerWindow"))
        sm.add_widget(ResponsiblesWindow(name="Responsibles"))
        sm.add_widget(CrwoWindow(name="CrwoWindow"))
        sm.add_widget(SettingsWindow(name="SettingsWindow"))
        sm.add_widget(TorusWindow(name="TorusWindow"))
        sm.add_widget(NetworkTabsWindow(name="NetworkTabsWindow"))
        sm.add_widget(BirthdayWindow(name="BirthdayWindow"))
        sm.add_widget(BirthdayWindow(name="BirthdayWindow"))
        sm.add_widget(BlitzReportWindow(name="BlitzReport"))

        sm.current = "LoginWindow"

        Window.softinput_mode = 'below_target'
        Window.softinput_mode_target_margin = dp(20)

        return sm

    # ── Навигация ──
        # ── Навигация ──
    def _blur_all_inputs(self):
        """Снимает выделение и фокус со всех TextInput ДО смены экрана.
        На Android ручки выделения — это нативные View поверх Activity,
        и они закрываются корректно, только пока TextInput ещё активен.
        """
        from kivy.core.window import Window
        try:
            for screen in self.root.screens:
                for child in screen.walk():
                    if isinstance(child, TextInput):
                        try:
                            child.cancel_selection()
                        except Exception:
                            pass
                        try:
                            child.focus = False
                        except Exception:
                            pass
        except Exception as e:
            print(f"_blur_all_inputs: {e}")

        # Дополнительно — закрыть клавиатуру
        try:
            Window.release_all_keyboards()
        except Exception:
            pass

    PUBLIC_SCREENS = {"LoginWindow"}

    def go_to(self, screen_name, direction="left"):
        if screen_name not in self.PUBLIC_SCREENS and not api.is_authorized():
            screen_name = "LoginWindow"
        self._blur_all_inputs()
        self.root.current = screen_name
        self.root.transition.direction = direction

    def go_back(self, screen_name):
        if screen_name not in self.PUBLIC_SCREENS and not api.is_authorized():
            screen_name = "LoginWindow"
        self._blur_all_inputs()
        self.root.current = screen_name
        self.root.transition.direction = "right"

    # ── Универсальное открытие меню по имени поля ──
    def open_menu(self, caller, options, on_select=None):
        """Простой Popup со списком кнопок (замена MDDropdownMenu для Adreno)."""

        # Прокручиваемый список кнопок
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(2),
            padding=[dp(4), dp(4), dp(4), dp(4)],
        )
        content.bind(minimum_height=content.setter("height"))

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        scroll.add_widget(content)

        # Popup с фиксированным размером в процентах экрана
        popup = Popup(
            title="Выберите",
            title_color=(0, 0, 0, 1),
            title_size=dp(16),
            separator_color=(0.85, 0.85, 0.85, 1),
            content=scroll,
            size_hint=(0.8, 0.6),
            background="",
            background_color=(1, 1, 1, 1),
            auto_dismiss=True,
        )

        def _sel(v):
            caller.text = v
            popup.dismiss()
            if on_select:
                Clock.schedule_once(lambda dt: on_select(v), 0.15)

        for opt in options:
            b = Button(
                text=opt,
                size_hint_y=None,
                height=dp(52),
                background_normal="",
                background_down="",
                background_color=(0.95, 0.95, 0.97, 1),
                color=(0, 0, 0, 1),
                font_size=dp(15),
            )
            b.bind(on_release=lambda x, v=opt: _sel(v))
            content.add_widget(b)

        popup.open()

    def open_mode_menu(self, caller):
        self.open_menu(caller, self.MODE_OPTIONS)

    def open_tt_menu(self, caller):
        self.open_menu(caller, self.TT_OPTIONS)

    def open_moto_menu(self, caller):
        self.open_menu(caller, self.MOTO_OPTIONS)

    def open_region_menu(self, caller):
        def on_region(value):
            try:
                torus = self.root.get_screen("TorusWindow")
                torus.selected_region = value
            except Exception as e:
                print(f"open_region_menu: {e}")

        self.open_menu(caller, self.REGION_OPTIONS, on_select=on_region)

    def open_organization_menu(self, caller):
        self.open_menu(caller, self.ORGANIZATION_OPTIONS)

    def open_blitz_sc_menu(self, caller):
        # Значения берём из текущего списка Spinner'а
        try:
            options = list(caller.values) or [
                "Сервисный Центр Феодосия",
                "Сервисный Центр Симферополь",
            ]
        except Exception:
            options = [
                "Сервисный Центр Феодосия",
                "Сервисный Центр Симферополь",
            ]
        self.open_menu(caller, options)

    def open_work_type_menu(self, caller):
        self.open_menu(caller, self.WORK_TYPE_OPTIONS)

    def open_work_desc_menu(self, caller):
        def on_select(value):
            try:
                uber = self.root.get_screen("Uber")

                # 1. Всегда сначала сбрасываем ОБА поля в скрытое состояние
                uber.ids.custom_desc_box.height = 0
                uber.ids.custom_desc_box.opacity = 0
                uber.ids.custom_desc_box.disabled = True
                uber.ids.work_description.text = ""

                uber.ids.generator_number_box.height = 0
                uber.ids.generator_number_box.opacity = 0
                uber.ids.generator_number_box.disabled = True
                uber.ids.generator_number.text = ""

                # 2. Теперь включаем только то, что нужно для выбранного варианта
                if value == "Ввести свой вариант":
                    uber.ids.custom_desc_box.height = dp(110)
                    uber.ids.custom_desc_box.opacity = 1
                    uber.ids.custom_desc_box.disabled = False
                    Clock.schedule_once(
                        lambda dt: setattr(uber.ids.work_description, "focus", True),
                        0.3,
                    )
                elif "ДГУ" in value:
                    # Показываем поле для номера генератора
                    uber.ids.generator_number_box.height = dp(56)
                    uber.ids.generator_number_box.opacity = 1
                    uber.ids.generator_number_box.disabled = False
                # Для остальных вариантов оба поля остаются скрытыми

            except Exception as e:
                print(f"open_work_desc_menu error: {e}")

        self.open_menu(caller, self.WORK_DESC_OPTIONS, on_select=on_select)

    # _set_mode — УДАЛИТЬ полностью

def show_simple_dialog(title, text):

    from kivy.uix.label import Label
    from kivy.uix.button import Button


    content = BoxLayout(
        orientation="vertical",
        spacing=dp(10),
        padding=[dp(12), dp(12), dp(12), dp(12)],
    )

    # Текст с прокруткой (если длинный)
    scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
    msg = Label(
        text=text,
        halign="left",
        valign="top",
        color=(0, 0, 0, 1),
        font_size=dp(14),
        size_hint_y=None,
        markup=True,
    )
    msg.bind(
        width=lambda inst, w: setattr(inst, "text_size", (w, None)),
        texture_size=lambda inst, ts: setattr(inst, "height", ts[1]),
    )
    scroll.add_widget(msg)
    content.add_widget(scroll)

    btn = Button(
        text="OK",
        size_hint_y=None,
        height=dp(48),
        background_normal="",
        background_down="",
        background_color=(0.2, 0.6, 1, 1),
        color=(1, 1, 1, 1),
        font_size=dp(16),
        bold=True,
    )
    content.add_widget(btn)

    popup = Popup(
        title=title,
        title_color=(0, 0, 0, 1),
        title_size=dp(16),
        separator_color=(0.85, 0.85, 0.85, 1),
        content=content,
        size_hint=(0.85, 0.55),
        background="",
        background_color=(1, 1, 1, 1),
        auto_dismiss=True,
    )

    btn.bind(on_release=popup.dismiss)
    popup.open()

def _parse_date_str(s):
    """Парсит дату из разных форматов. Возвращает date или None."""
    if not s:
        return None
    s = str(s).strip().split()[0]
    formats = [
        "%d.%m.%Y", "%d.%m.%y", "%d.%m",
        "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d/%m",
        "%d-%m-%Y", "%d-%m-%y", "%d-%m",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def count_upcoming_birthdays(days=7):
    """Сколько сотрудников отмечают ДР в ближайшие N дней (включая сегодня)."""
    db_path = service_path('birthdays.db')


    if not os.path.exists(db_path):
        return 0

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT name, birth_date FROM birthdays")
        rows = cur.fetchall()
        con.close()
    except Exception as e:
        print(f"[count] ошибка чтения БД: {e}")
        return 0



    today = datetime.now().date()
    end = today + timedelta(days=days)

    count = 0

    for (name, bd_str) in rows:
        bd = _parse_date_str(bd_str)
        if not bd:
            print(f"[count]   '{name}' — дата '{bd_str}' НЕ распарсилась")
            continue

        try:
            bd_this_year = bd.replace(year=today.year)
        except ValueError:
            bd_this_year = bd.replace(year=today.year, day=28)

        if bd_this_year < today:
            try:
                bd_this_year = bd.replace(year=today.year + 1)
            except ValueError:
                bd_this_year = bd.replace(year=today.year + 1, day=28)



        if today <= bd_this_year <= end:
            count += 1

    print(f"[count] итог: {count}")
    return count

def build_upcoming_birthdays_text(days=7):
    """Формирует текст со списком именинников ближайших N дней (без markup)."""
    db_path = service_path('birthdays.db')
    if not os.path.exists(db_path):
        return ""

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT name, position, birth_date FROM birthdays")
        rows = cur.fetchall()
        con.close()
    except Exception as e:
        print(f"build_upcoming_birthdays_text: {e}")
        return ""

    if not rows:
        return ""

    today = datetime.now().date()
    end = today + timedelta(days=days)
    upcoming = []

    for (name, position, bd_str) in rows:
        bd = _parse_date_str(bd_str)
        if not bd:
            continue

        try:
            bd_this_year = bd.replace(year=today.year)
        except ValueError:
            bd_this_year = bd.replace(year=today.year, day=28)

        if bd_this_year < today:
            try:
                bd_this_year = bd.replace(year=today.year + 1)
            except ValueError:
                bd_this_year = bd.replace(year=today.year + 1, day=28)

        if today <= bd_this_year <= end:
            upcoming.append((name, position or "", bd_this_year, bd_this_year == today))

    if not upcoming:
        return ""

    upcoming.sort(key=lambda x: x[2])

    # ── Собираем текст ──
    lines = []
    lines.append("-" * 70)
    lines.append(f"  БЛИЖАЙШИЕ ДНИ РОЖДЕНИЯ")
    lines.append("-" * 70)
    lines.append("")

    for name, position, bd, is_today in upcoming:
        date_str = bd.strftime("%d.%m")
        lines.append(f"{date_str}  {name}")
        if position:
            lines.append(f"      {position}")
        if is_today:
            lines.append(f"      ← СЕГОДНЯ")
        lines.append("")  # пустая строка между записями

    lines.append("-" * 70)
    return "\n".join(lines)


def open_file_chooser(on_select, ext=None, start_path=None):
    print(f"[chooser] kivy_platform = {kivy_platform}")  # отладка

    if kivy_platform == 'android':
        print("[chooser] entering Android branch")
        from androidstorage4kivy import Chooser, SharedStorage
        from kivy.app import App

        def chooser_callback(shared_file_list):
            print(f"[Chooser] callback, files={shared_file_list}")
            if not shared_file_list:
                return
            try:
                ss = SharedStorage()
                private_file_path = ss.copy_from_shared(shared_file_list[0])
                print(f"[Chooser] copied to {private_file_path}")
                if private_file_path:
                    Clock.schedule_once(lambda dt: on_select(private_file_path), 0)
                else:
                    Clock.schedule_once(
                        lambda dt: show_simple_dialog("Ошибка", "Не удалось скопировать файл"), 0
                    )
            except Exception as e:
                print(f"[Chooser] callback error: {e}")
                Clock.schedule_once(
                    lambda dt: show_simple_dialog("Ошибка", f"Не удалось открыть файл:\n{e}"), 0
                )

        try:
            chooser = Chooser(chooser_callback)
            app = App.get_running_app()
            if app:
                app._active_chooser = chooser
            print("[Chooser] вызов choose_content")
            chooser.choose_content("*/*")
        except Exception as e:
            print(f"[Chooser] ошибка создания: {e}")
            show_simple_dialog("Ошибка", f"Не удалось открыть файловый менеджер:\n{e}")
        return

    # ─── Windows / Linux: FileChooserListView в Popup ───
    if not start_path:
        candidates = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~"),
            "/",
        ]
        for c in candidates:
            if os.path.exists(c):
                start_path = c
                break
        else:
            start_path = "/"

    chooser = FileChooserListView(path=start_path)



    # ── Тёмно-серый цвет для всех Label внутри chooser ──
    def _apply_dark_colors(*_):
        for child in chooser.walk():
            if isinstance(child, Label):
                child.color = TEXT_COLOR
                child.font_size = dp(14)
            if hasattr(child, 'foreground_color'):
                child.foreground_color = TEXT_COLOR
            if hasattr(child, 'disabled_color'):
                child.disabled_color = (0.5, 0.5, 0.5, 1)

    Clock.schedule_once(_apply_dark_colors, 0.1)
    Clock.schedule_once(_apply_dark_colors, 0.5)
    Clock.schedule_once(_apply_dark_colors, 1.0)
    chooser.bind(path=lambda *_: Clock.schedule_once(_apply_dark_colors, 0.2))
    chooser.bind(files=lambda *_: Clock.schedule_once(_apply_dark_colors, 0.2))

    # ── Нижние кнопки ──
    buttons = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(48),
        spacing=dp(8),
        padding=[dp(8), 0, dp(8), 0],
    )

    def _choose(*_):
        sel = chooser.selection
        if sel:
            popup.dismiss()
            on_select(sel[0])

    def _cancel(*_):
        popup.dismiss()

    btn_ok = Button(
        text="ВЫБРАТЬ",
        background_normal="",
        background_color=(0.2, 0.6, 1, 1),
        color=(1, 1, 1, 1),
        bold=True,
    )
    btn_ok.bind(on_release=_choose)

    btn_cancel = Button(
        text="ОТМЕНА",
        background_normal="",
        background_color=(0.9, 0.3, 0.3, 1),
        color=(1, 1, 1, 1),
        bold=True,
    )
    btn_cancel.bind(on_release=_cancel)

    buttons.add_widget(btn_ok)
    buttons.add_widget(btn_cancel)

    # ── Отвязываем chooser, если он уже где-то был ──
    if chooser.parent:
        chooser.parent.remove_widget(chooser)

    # ── Собираем контент в отдельный BoxLayout ДО создания Popup ──
    root_box = BoxLayout(orientation="vertical", spacing=dp(4), padding=dp(4))
    root_box.add_widget(chooser)
    root_box.add_widget(buttons)

    popup = Popup(
        title="Выберите файл",
        title_color=TEXT_COLOR,
        title_size=dp(16),
        separator_color=(0.85, 0.85, 0.85, 1),
        content=root_box,
        size_hint=(0.95, 0.85),
        background="",
        background_color=(1, 1, 1, 1),
        auto_dismiss=True,
    )

    popup.open()

def clear_all_selections(screen):
    """Рекурсивно снимает выделение со всех SelectableLabel на экране.
    Нужно вызывать при уходе с экрана, иначе ручки выделения
    остаются висеть поверх других окон.
    """
    for child in screen.walk():
        if isinstance(child, SelectableLabel):
            try:
                child.cancel_selection()
            except Exception:
                pass
            try:
                child.focus = False
            except Exception:
                pass

def colorize_output(text):
    """Раскрашивает ключевые поля в тексте через Kivy-markup."""
    if not text:
        return text

    # Цвета
    COLOR_BOLD   = "e8960d"   # оранжевый — заголовки
    COLOR_ADDR   = "007AFF"   # синий — адрес
    COLOR_COORD  = "34c759"   # зелёный — координаты
    COLOR_WHO    = "af52de"   # фиолетовый — люди (ФИО)

    lines = []
    for line in text.split("\n"):
        stripped = line.strip()

        # Заголовки "*** CR0122 ***" или "** CR0122 **"
        if stripped.startswith("***") or stripped.startswith("**"):
            lines.append(f"[b][color={COLOR_BOLD}]{line}[/color][/b]")
        # Адрес
        elif stripped.startswith("Адрес"):
            lines.append(f"[color={COLOR_ADDR}]{line}[/color]")
        # Координаты
        elif stripped.startswith("Координаты"):
            lines.append(f"[color={COLOR_COORD}]{line}[/color]")
        # ФИО ответственных
        elif ("Ответственный" in stripped or "Подрядчик" in stripped
              or "Выдал заявку" in stripped):
            lines.append(f"[b]{line}[/b]")
        else:
            lines.append(line)

    return "\n".join(lines)


if __name__ == '__main__':
    UberGoorandaApp().run()