import os
import sys
import db
import csv
import pickle
import webbrowser
from datetime import datetime, timedelta
import openpyxl
from kivy.lang import Builder
from kivy.core.clipboard import Clipboard
from kivymd.app import MDApp
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
from kivy.uix.popup import Popup
from kivymd.uix.list import MDList, OneLineListItem
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.properties import StringProperty, ListProperty, BooleanProperty
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
from kivy.uix.filechooser import FileChooserIconView, FileChooserIconLayout
import os
from kivymd.uix.label import MDLabel
import sqlite3
import re

os.environ['KIVY_GL_BACKEND'] = 'sdl2'
os.environ['KIVY_GRAPHICS'] = 'gles'
os.environ['KIVY_GLES_LIMITS'] = '0'
os.environ['KIVY_NO_ARGS'] = '1'

TEXT_COLOR = (0.2,0.2,0.2,1)#(0.25, 0.28, 0.33, 1)



from kivy.graphics import Color, RoundedRectangle




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

# ────────────────────────────────────────────────────────────────
# Пути к ресурсам (учитываем PyInstaller)
# ────────────────────────────────────────────────────────────────
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def service_path(filename):
    """Файлы service/ пишутся рядом с .exe / main.py — НЕ в _MEIPASS."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    service_dir = os.path.join(base, 'service')
    os.makedirs(service_dir, exist_ok=True)
    return os.path.join(service_dir, filename)


#__________________________________________________________________
#  Login window
#___________________________________________________________________

# Куда переходить после успешного входа — поменяйте под свой ScreenManager.
HOME_SCREEN_NAME = "Uber"

MIN_PASSWORD_LENGTH = 6


class LoginWindow(MDScreen):
    """Поля: Имя, Фамилия, Пароль. Кнопки: Войти / Зарегистрироваться."""


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




# ────────────────────────────────────────────────────────────────
# GOORANDA — поиск БС / ARC / маршрутов
# ────────────────────────────────────────────────────────────────
class GoorandaWindow(MDScreen):
    route = None

    try:
        with open(resource_path('RDB.pickle'), "rb") as f:
            RDB = pickle.load(f)
    except FileNotFoundError:
        RDB = {}

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
        print("=== _refresh_birthdays_ui вызван ===")

        # ── Бейдж ──
        try:
            count = count_upcoming_birthdays(7)
            print(f"[Gooranda] count={count}")
            self.ids.gooranda_header.badge_text = str(count) if count > 0 else ""
            print(f"[Gooranda] badge_text={self.ids.gooranda_header.badge_text!r}")
        except Exception as e:
            print(f"_refresh badge: {e}")

        # ── output_text ──
        try:
            if not self.ids.output_text.text.strip():
                text = build_upcoming_birthdays_text(7)
                print(f"[Gooranda] text len={len(text)}")
                if text:
                    self.ids.output_text.text = text
        except Exception as e:
            print(f"_refresh output_text: {e}")

    def on_pre_enter(self, *args):
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

            # Поиск базовых станций по номеру ТП (подстанции).

            # Пользователь вводит, например, "225" или "ТП-225".

            # Ищем совпадение в RDB[bs]['access'].

            query = raw.strip().lower()

            # Если пользователь ввёл только цифры — добавим префикс "тп-"

            # для точного совпадения с форматом хранения ("ТП-225").

            if query.isdigit():
                query = "тп-" + query

            found = []

            for bs, info in RDB.items():

                access = str(info.get('access', '') or '')

                if not access:
                    continue

                access_lower = access.lower()

                # Ищем вхождение номера ТП в поле access

                if query in access_lower:
                    found.append((

                        bs,

                        str(info.get('address', '') or ''),

                        str(info.get('coordinates', '') or ''),

                        access,

                    ))

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
        from kivy.uix.popup import Popup
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
        from kivy.uix.popup import Popup
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
        from kivy.uix.popup import Popup
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
        from kivy.uix.popup import Popup
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
    workers_selected = BooleanProperty(False)  # ← добавить

    def __init__(self, **kw):
        super().__init__(**kw)
        self.dialog = None
        # Загружаем базу
        try:
            with open(resource_path('RDB.pickle'), "rb") as f:
                UberWindow.RDB = pickle.load(f)
        except FileNotFoundError:
            UberWindow.RDB = {}

        # 2. Метод для проверки одиночная БС или их несколько (вызывается при вводе текста)
    def check_plural_bs(self, text):
        # Если в тексте есть пробелы, значит введено несколько БС
        if len(text.strip().split()) > 1:
            self.plural = True
        else:
            self.plural = False

    def on_kv_post(self, *_):
        # Номер заявки
        try:
            with open(service_path('crwo_cnt.txt'), "r", encoding="utf-8") as f:
                self.ids.crwo_number.text = f.read().strip()
        except FileNotFoundError:
            self.ids.crwo_number.text = ""
        # Ответственный
        try:
            with open(service_path('responsible.txt'), "r", encoding="utf-8") as f:
                self.ids.respo_worker.text = f.read().strip()
        except FileNotFoundError:
            self.ids.respo_worker.text = ""

        if self.ids.respo_worker.text.strip():
            self.ids.respo_view_label.text = f"Владелец заявки: {self.ids.respo_worker.text.strip()}"
            self.ids.respo_edit_box.height = 0
            self.ids.respo_edit_box.opacity = 0
            self.ids.respo_edit_box.disabled = True
            self.ids.respo_view_box.height = dp(56)
            self.ids.respo_view_box.opacity = 1
            self.ids.respo_view_box.disabled = False

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
            self.ids.crwo_number.text = "0"

    def crwo_decrement(self, string):
        if string.isdigit():
            self.ids.crwo_number.text = str(int(string) - 1)
        else:
            self.ids.crwo_number.text = "0"

    # ── Запись в service/ ──
    def write_crwo_list(self, value):
        with open(service_path('crwo_cnt.txt'), "w", encoding="utf-8") as f:
            f.write(str(value))

    def write_responsible_worker(self, value):
        with open(service_path('responsible.txt'), "w", encoding="utf-8") as f:
            f.write(str(value))

    def assign_responsible(self, *_):
        print("=== assign_responsible вызван ===")
        """Присвоить владельца: скрыть поле ввода, показать Label."""
        name = self.ids.respo_worker.text.strip()
        if not name:
            self.show_dialog("Введите фамилию, прежде чем присвоить")
            return

        # Сохраняем в файл
        self.write_responsible_worker(name)

        # Обновляем Label
        self.ids.respo_view_label.text = f"Владелец заявки:  {name}"

        # Скрываем поле ввода
        self.ids.respo_edit_box.height = 0
        self.ids.respo_edit_box.opacity = 0
        self.ids.respo_edit_box.disabled = True

        # Показываем Label
        self.ids.respo_view_box.height = dp(56)
        self.ids.respo_view_box.opacity = 1
        self.ids.respo_view_box.disabled = False

    def edit_responsible(self, *_):
        """Вернуть поле ввода обратно, чтобы можно было изменить."""
        self.ids.respo_edit_box.height = dp(56)
        self.ids.respo_edit_box.opacity = 1
        self.ids.respo_edit_box.disabled = False

        self.ids.respo_view_box.height = 0
        self.ids.respo_view_box.opacity = 0
        self.ids.respo_view_box.disabled = True

    # ── Валидация и старт ──
    def start(self):
        mode = self.ids.moto_spinner.text
        count, warn = 0, ""

        if not self.ids.crwo_number.text:
            count += 1; warn += f"{count}. Не заполнен номер заявки\n"
        if not self.ids.respo_worker.text:
            count += 1; warn += f"{count}. Нужно ввести фамилию ответственного\n"
        if self.ids.choose_workers_label.text in ("Выбери исполнителей: ", ""):
            count += 1; warn += f"{count}. Не выбран ни один сотрудник\n"

        if mode == "БС":
            if not self.ids.bs_name.text:
                count += 1; warn += f"{count}. Не заполнен номер БС\n"
            # if self.ids.tt_spinner.text == "TT" and not self.ids.tt_number.text:
            #     count += 1; warn += f"{count}. Не заполнен номер ТТ\n"

            if self.ids.work_description_spinner.text == "Ввести свой вариант" \
                    and not self.ids.work_description.text.strip():
                count += 1
                warn += f"{count}. Вы выбрали «Ввести свой вариант», но не заполнили описание работ\n"
        elif mode == "Офис":
            if not self.ids.work_description.text:
                count += 1; warn += (f"{count}. Активен режим 'Офис', "
                                     f"заполнение поля 'Описание работ' ОБЯЗАТЕЛЬНО!\n")

        if warn:
            self.show_dialog(warn)
            return False

        self.uber_make_output_sheet()
        return True

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
            responsibles = self.ids.respo_worker.text
            organization = f"🐝{self.ids.organization.text}"
        else:
            responsibles = self.ids.choose_workers_label.text
            organization = f"🍊{self.ids.organization.text}"

        t = self.ids.time_to_go_spinner.text
        hours = 2 if t == "Назначить время" else int(t.split()[0])

        spinner_val = self.ids.work_description_spinner.text
        if spinner_val == "Ввести свой вариант":
            work_desc = self.ids.work_description.text.strip()
        else:
            work_desc = spinner_val

        now = datetime.now().strftime('%d.%m.%Y %H:%M')
        arrive = (datetime.now() + timedelta(hours=hours)).strftime('%d.%m.%Y %H:%M')

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
            bs = self.ids.bs_name.text
            if len(bs.split()) == 1:
                if bs not in self.RDB:
                    if self.ids.region_short.text == "SEV":
                        p = (4 - len(bs)) * "0"
                        bs = "SE" + p + bs
                    else:
                        p = (4 - len(bs)) * "0"
                        bs = "CR" + p + bs
                if bs in self.RDB:
                    output = (f"{crwo_number} / {bs}\n"
                              # f"Номер ТТ: {self.ids.tt_number.text}\n"
                              f"Адрес: {self.RDB[bs]['address']}\n"
                              f"Координаты: {self.RDB[bs]['coordinates']}\n"
                              f"Тип работ: {self.ids.work_type.text}\n"
                              f"Описание работ: {work_desc}\n"
                              f"Дата/время выдачи задания: {now}\n"
                              f"Время прибытия: {arrive}\n"
                              f"Организация :{organization}\n"
                              f"Ответственный ММ : {responsibles}\n"
                              f"ЗО : {ZO}")
                    # Переносим результат в финальные переменные
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
                    bs_current = b  # Используем новую переменную, чтобы не портить исходный список bs
                    if bs_current not in self.RDB:
                        if self.ids.region_short.text == "SEV":
                            p = (4 - len(bs_current)) * "0"
                            bs_current = "SE" + p + bs_current
                        else:
                            p = (4 - len(bs_current)) * "0"
                            bs_current = "CR" + p + bs_current

                    # ВАЖНО: проверка существования БС перенесена на один уровень назад (к if/else)
                    if bs_current in self.RDB:
                        if self.ids.single_request_checkbox.active:

                            bs_names.append(bs_current)
                            checked_bs = ', '.join(bs_names)
                            checked_output = (f"{crwo_number} / {checked_bs}\n"
                                              #f"Номер ТТ: {self.ids.tt_number.text}\n"
                                              f"Тип работ: {self.ids.work_type.text}\n"
                                              f"Описание работ: {work_desc}\n"
                                              f"Дата/время выдачи задания: {now}\n"
                                              f"Время прибытия: {arrive}\n"
                                              f"Организация :{organization}\n"
                                              f"Ответственный ММ : {responsibles}\n"
                                              f"ЗО : {ZO}")
                            crwo_delta +=1

                        else:

                            crwo_number = f"CRWO_{self.ids.region_short.text}_{prefix}{str(int(crwo_num) + crwo_delta)}"
                            output = (f"{crwo_number} / {bs_current}\n"
                                      #f"Номер ТТ: {self.ids.tt_number.text}\n"
                                      f"Адрес: {self.RDB[bs_current]['address']}\n"
                                      f"Координаты: {self.RDB[bs_current]['coordinates']}\n"
                                      f"Тип работ: {self.ids.work_type.text}\n"
                                      f"Описание работ: {work_desc}\n"
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

                # После завершения цикла форматируем результат
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

        with open(resource_path('RDB.pickle'), "wb") as f:
            pickle.dump(bs_dict, f)

        self.show_dialog(
            "Обновление завершено. Чтобы изменения вступили в силу, "
            "перезагрузите приложение.",
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
        import os
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
            print(f"_load_records: {e}")
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
        from kivy.uix.popup import Popup
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
    def on_start(self):
        db.init_db()



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
    TIME_OPTIONS = ["Назначить время", "1 час", "2 часа",
                    "3 часа", "4 часа", "5 часов", "6 часов"]
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

        sm = WindowManager()
        #sm.add_widget(LoginWindow(name="LoginWindow"))
        sm.add_widget(GoorandaWindow(name="Gooranda"))
        sm.add_widget(UberWindow(name="Uber"))
        sm.add_widget(WorkerWindow(name="WorkerWindow"))
        sm.add_widget(ResponsiblesWindow(name="Responsibles"))
        sm.add_widget(CrwoWindow(name="CrwoWindow"))
        sm.add_widget(SettingsWindow(name="SettingsWindow"))
        sm.add_widget(TorusWindow(name="TorusWindow"))
        sm.add_widget(NetworkTabsWindow(name="NetworkTabsWindow"))
        sm.add_widget(BirthdayWindow(name="BirthdayWindow"))

        Window.softinput_mode = 'below_target'
        Window.softinput_mode_target_margin = dp(20)  # 20dp запаса

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

    def go_to(self, screen_name, direction="left"):
        self._blur_all_inputs()  # ← ПЕРЕД сменой экрана
        self.root.current = screen_name
        self.root.transition.direction = direction

    def go_back(self, screen_name):
        self._blur_all_inputs()  # ← ПЕРЕД сменой экрана
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
            # Callback запускаем ПОСЛЕ того, как Popup полностью закроется —
            # иначе на MIUI (Xiaomi) перерисовка layout'а с активным Popup
            # вызывает нативный краш.
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

    def open_work_type_menu(self, caller):
        self.open_menu(caller, self.WORK_TYPE_OPTIONS)

    def open_time_menu(self, caller):
        self.open_menu(caller, self.TIME_OPTIONS)

    def open_work_desc_menu(self, caller):
        def on_select(value):
            try:
                uber = self.root.get_screen("Uber")
                box = uber.ids.custom_desc_box

                if value == "Ввести свой вариант":
                    box.height = dp(110)
                    box.opacity = 1
                    box.disabled = False
                    Clock.schedule_once(
                        lambda dt: setattr(uber.ids.work_description, "focus", True),
                        0.3,
                    )
                else:
                    box.height = 0
                    box.opacity = 0
                    box.disabled = True
                    uber.ids.work_description.text = ""
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
    print(f"[count] db_path = {db_path}")
    print(f"[count] exists = {os.path.exists(db_path)}")

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

    print(f"[count] записей в БД: {len(rows)}")

    today = datetime.now().date()
    end = today + timedelta(days=days)
    print(f"[count] сегодня={today}, конец диапазона={end}")
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

        print(f"[count]   '{name}' — {bd} → {bd_this_year}")

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
    import platform, os

    if platform.system() == 'Android':
        from androidstorage4kivy import Chooser, SharedStorage
        from kivy.app import App        # ← добавить

        def chooser_callback(shared_file_list):
            print(f"[Chooser] callback, files={shared_file_list}")
            if not shared_file_list:
                return
            try:
                ss = SharedStorage()
                private_file_path = ss.copy_from_shared(shared_file_list[0])
                print(f"[Chooser] copied to {private_file_path}")
                if private_file_path:
                    # ⚠️ ВАЖНО: переключаемся в главный поток Kivy —
                    # только там можно создавать Popup/виджеты.
                    Clock.schedule_once(
                        lambda dt: on_select(private_file_path), 0
                    )
            except Exception as e:
                print(f"[Chooser] callback error: {e}")
                # и ошибку показываем тоже из главного потока
                Clock.schedule_once(
                    lambda dt: show_simple_dialog(
                        "Ошибка", f"Не удалось открыть файл:\n{e}"
                    ), 0
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
    ...

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