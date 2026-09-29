import asyncio
import calendar as cal
import json
import os
from datetime import datetime

import flet as ft


# =========================================================
# НАСТРОЙКИ
# =========================================================

MEMBERS_FILE = "members.json"
CALENDAR_FILE = "calendar.json"
ATTENDANCE_FILE = "attendance.json"
MEETINGS_FILE = "meetings.json"

PAGE_COLOR = "#F8F8F8"
TEXT_COLOR = "#13233D"

APP_DATA_DIR = os.getenv(
    "FLET_APP_STORAGE_DATA"
) or "."


DEFAULT_MEETINGS = {
    "13.09.2026": {
        "description":
            "Подготовка к мероприятию, "
            "распределение обязанностей "
            "и планы на месяц."
    },

    "20.09.2026": {
        "description":
            "Обсуждение предстоящего "
            "мероприятия и распределение "
            "задач между участниками."
    },

    "27.09.2026": {
        "description":
            "Подведение итогов месяца "
            "и обсуждение новых предложений."
    }
}


# =========================================================
# РАБОТА С ФАЙЛАМИ
# =========================================================

def get_data_file(filename):
    return os.path.join(
        APP_DATA_DIR,
        filename
    )


def load_json(filename, default):
    if not os.path.exists(filename):
        return default

    try:
        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return default


def save_json(filename, data):
    directory = os.path.dirname(
        os.path.abspath(filename)
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True
        )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


def load_app_json(filename, default):
    """
    На Android читает данные из постоянного
    хранилища приложения.

    При первом запуске пытается перенести
    существующий JSON из папки проекта.
    """

    storage_file = get_data_file(
        filename
    )

    if os.path.exists(storage_file):

        return load_json(
            storage_file,
            default
        )

    # Перенос старого JSON
    old_file = filename

    if os.path.exists(old_file):

        data = load_json(
            old_file,
            default
        )

        try:
            save_json(
                storage_file,
                data
            )
        except Exception:
            pass

        return data

    # Если файла вообще нет
    try:
        save_json(
            storage_file,
            default
        )
    except Exception:
        pass

    if isinstance(default, dict):
        return dict(default)

    if isinstance(default, list):
        return list(default)

    return default


def save_app_json(filename, data):
    storage_file = get_data_file(
        filename
    )

    save_json(
        storage_file,
        data
    )


# =========================================================
# УЧАСТНИКИ
# =========================================================

def load_members():
    data = load_app_json(
        MEMBERS_FILE,
        []
    )

    if not isinstance(
        data,
        list
    ):
        return []

    # Миграция старого поля "qualities"
    # в новое поле "direction".
    changed = False

    for person in data:

        if not isinstance(
            person,
            dict
        ):
            continue

        if (
            "direction" not in person
            and "qualities" in person
        ):
            person["direction"] = (
                person.get(
                    "qualities",
                    ""
                )
            )

            changed = True

        if "direction" not in person:
            person["direction"] = ""

            changed = True

        # Старое поле больше не используется.
        if "qualities" in person:
            del person["qualities"]
            changed = True

    if changed:
        save_members(data)

    return data


def save_members(participants):
    save_app_json(
        MEMBERS_FILE,
        participants
    )


# =========================================================
# ИМЯ ДЛЯ ТАБЛИЦЫ
# =========================================================

def short_name(full_name):
    parts = (
        full_name or ""
    ).strip().split()

    # Только ФАМИЛИЯ + ИМЯ.
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"

    if len(parts) == 1:
        return parts[0]

    return ""


# =========================================================
# МЕРОПРИЯТИЯ
# =========================================================

def load_calendar():
    data = load_app_json(
        CALENDAR_FILE,
        {}
    )

    if not isinstance(
        data,
        dict
    ):
        return {}

    normalized = {}
    changed = False

    for key, value in data.items():

        if not isinstance(
            value,
            dict
        ):
            continue

        event = dict(value)

        # Дата может быть:
        # 1. старым ключом JSON;
        # 2. уже сохранённым полем date.
        event_date = (
            event.get("date")
            or key
        )

        event["date"] = event_date

        normalized[event_date] = event

        if (
            key != event_date
            or value.get("date") != event_date
        ):
            changed = True

    if changed:
        save_app_json(
            CALENDAR_FILE,
            normalized
        )

    return normalized


def save_calendar(calendar_data):
    normalized = {}

    for key, value in calendar_data.items():

        if not isinstance(
            value,
            dict
        ):
            continue

        event = dict(value)

        event_date = (
            event.get("date")
            or key
        )

        event["date"] = event_date

        normalized[event_date] = event

    save_app_json(
        CALENDAR_FILE,
        normalized
    )


# =========================================================
# ЗАСЕДАНИЯ
# =========================================================

def load_meetings():
    data = load_app_json(
        MEETINGS_FILE,
        DEFAULT_MEETINGS
    )

    if not isinstance(
        data,
        dict
    ):
        data = dict(
            DEFAULT_MEETINGS
        )

        save_app_json(
            MEETINGS_FILE,
            data
        )

    return data


def save_meetings(meetings):
    save_app_json(
        MEETINGS_FILE,
        meetings
    )


# =========================================================
# БЛИЖАЙШЕЕ МЕРОПРИЯТИЕ
# =========================================================

def get_next_event(calendar_data):

    today = datetime.now().date()

    upcoming = []

    for date_str, data in calendar_data.items():

        if not isinstance(
            data,
            dict
        ):
            continue

        if not data.get("event"):
            continue

        event_date_str = (
            data.get("date")
            or date_str
        )

        try:

            item_date = datetime.strptime(
                event_date_str,
                "%d.%m.%Y"
            ).date()

            if item_date >= today:

                upcoming.append(
                    (
                        item_date,
                        data["event"]
                    )
                )

        except (
            ValueError,
            TypeError
        ):
            continue

    if not upcoming:

        return "Пока мероприятий нет"

    upcoming.sort(
        key=lambda x: x[0]
    )

    closest_date, title = upcoming[0]

    return (
        f"{title} — "
        f"{closest_date.strftime('%d.%m.%Y')}"
    )


# =========================================================
# БЛИЖАЙШИЙ ДЕНЬ РОЖДЕНИЯ
# =========================================================

def get_next_birthday():

    members = load_members()

    today = datetime.now().date()

    upcoming_birthdays = []

    for person in members:

        birthday = (
            person.get(
                "birthday",
                ""
            ) or ""
        ).strip()

        if not birthday:
            continue

        try:

            day, month, year = map(
                int,
                birthday.split(".")
            )

            birthday_date = datetime(
                today.year,
                month,
                day
            ).date()

            if birthday_date < today:

                birthday_date = datetime(
                    today.year + 1,
                    month,
                    day
                ).date()

            upcoming_birthdays.append(
                (
                    birthday_date,
                    person.get(
                        "name",
                        ""
                    )
                )
            )

        except (
            ValueError,
            IndexError,
            TypeError
        ):
            continue

    if not upcoming_birthdays:

        return "Пока дней рождений нет"

    upcoming_birthdays.sort(
        key=lambda x: x[0]
    )

    closest_date, name = (
        upcoming_birthdays[0]
    )

    return (
        f"{name} — "
        f"{closest_date.strftime('%d.%m')}"
    )


# =========================================================
# MAIN
# =========================================================

def main(page: ft.Page):

    page.title = "Совет обучающихся"

    page.bgcolor = PAGE_COLOR

    page.padding = 0

    page.spacing = 0

    page.fonts = {
        "MainFont":
            "fonts/ofont_ru_FindSans_Pro.ttf"
    }

    page.theme = ft.Theme(
        font_family="MainFont"
    )

    content = ft.Container(
        expand=True,
        bgcolor=PAGE_COLOR
    )

    navigation = ft.Container(
        bgcolor=PAGE_COLOR
    )

    root = ft.Container(
        expand=True,
        bgcolor=PAGE_COLOR
    )

    active_page = "home"

    calendar_data = load_calendar()

    current_calendar_date = {
        "value": datetime.now()
    }


    # =====================================================
    # АДАПТИВНОСТЬ
    # =====================================================

    def get_width():

        return page.width or 1000


    def get_height():

        return page.height or 700


    def is_phone():

        return get_width() < 600


    def is_tablet():

        return (
            600 <= get_width() < 1100
        )


    def dialog_width(
        default=500
    ):

        return min(
            default,
            max(
                280,
                get_width() - 30
            )
        )


    # =====================================================
    # ДИАЛОГИ
    # =====================================================

    def open_dialog(dialog):

        page.show_dialog(
            dialog
        )


    def close_dialog(dialog):

        dialog.open = False

        page.update()


    # =====================================================
    # СТИЛИ КНОПОК
    # =====================================================

    def button_style():

        return ft.ButtonStyle(
            color=TEXT_COLOR,
            bgcolor=PAGE_COLOR
        )


    def text_button_style():

        return ft.ButtonStyle(
            color=TEXT_COLOR,
            bgcolor=PAGE_COLOR
        )


    # =====================================================
    # ЧАСЫ
    # =====================================================

    clock = ft.Text(

        "00:00",

        size=300,

        weight=ft.FontWeight.BOLD,

        color=TEXT_COLOR,

        text_align=ft.TextAlign.CENTER
    )


    # =====================================================
    # НАВИГАЦИЯ
    # =====================================================

    def nav_item(
        icon,
        tooltip,
        handler,
        size
    ):

        icon_size = (
            32
            if size <= 70
            else 48
            if size <= 100
            else 72
        )

        return ft.Container(

            width=size,

            height=size,

            alignment=ft.Alignment.CENTER,

            bgcolor=PAGE_COLOR,

            border_radius=12,

            tooltip=tooltip,

            on_click=handler,

            content=ft.Icon(
                icon,
                size=icon_size,
                color=TEXT_COLOR
            )
        )


    def make_navigation():

        phone = is_phone()

        tablet = is_tablet()

        # -----------------------------------------------
        # ТЕЛЕФОН
        # -----------------------------------------------

        if phone:

            navigation.width = None

            navigation.height = 64

            navigation.padding = 0

            navigation.bgcolor = PAGE_COLOR

            navigation.content = ft.Row(

                controls=[

                    nav_item(
                        ft.Icons.HOME,
                        "Главная",
                        home,
                        62
                    ),

                    nav_item(
                        ft.Icons.EVENT_AVAILABLE,
                        "Посещаемость",
                        attendance,
                        62
                    ),

                    nav_item(
                        ft.Icons.CALENDAR_MONTH,
                        "Календарь",
                        calendar,
                        62
                    )
                ],

                alignment=(
                    ft.MainAxisAlignment
                    .SPACE_AROUND
                ),

                vertical_alignment=(
                    ft.CrossAxisAlignment.CENTER
                )
            )

            root.content = ft.Column(

                controls=[

                    content,

                    navigation
                ],

                expand=True,

                spacing=0
            )

        # -----------------------------------------------
        # ПЛАНШЕТ / ПК
        # -----------------------------------------------

        else:

            sidebar_width = (
                90
                if tablet
                else 200
            )

            button_size = (
                66
                if tablet
                else 150
            )

            navigation.width = (
                sidebar_width
            )

            navigation.height = None

            navigation.bgcolor = PAGE_COLOR

            navigation.padding = (

                4

                if tablet

                else ft.Padding.only(
                    left=40
                )
            )

            navigation.content = ft.Column(

                controls=[

                    nav_item(
                        ft.Icons.HOME,
                        "Главная",
                        home,
                        button_size
                    ),

                    nav_item(
                        ft.Icons.EVENT_AVAILABLE,
                        "Посещаемость",
                        attendance,
                        button_size
                    ),

                    nav_item(
                        ft.Icons.CALENDAR_MONTH,
                        "Календарь",
                        calendar,
                        button_size
                    )
                ],

                expand=True,

                alignment=(
                    ft.MainAxisAlignment
                    .SPACE_EVENLY
                ),

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                )
            )

            root.content = ft.Row(

                controls=[

                    navigation,

                    content
                ],

                expand=True,

                spacing=0
            )


    # =====================================================
    # ГЛАВНАЯ
    # =====================================================

    def home(e=None):

        nonlocal active_page

        active_page = "home"

        phone = is_phone()

        tablet = is_tablet()

        if phone:

            clock.size = max(

                72,

                min(
                    120,
                    get_width() * 0.30
                )
            )

        elif tablet:

            clock.size = 180

        else:

            clock.size = 250

        # Всегда подгружаем актуальные данные.
        calendar_data.clear()

        calendar_data.update(
            load_calendar()
        )

        next_event = get_next_event(
            calendar_data
        )

        next_birthday = (
            get_next_birthday()
        )

        event_card = ft.Container(

            width=(
                get_width() - 24
                if phone
                else 500
            ),

            height=(
                180
                if phone
                else 230
            ),

            padding=(
                24
                if phone
                else 50
            ),

            border_radius=(
                28
                if phone
                else 60
            ),

            bgcolor=PAGE_COLOR,

            border=ft.Border.all(
                1,
                TEXT_COLOR
            ),

            content=ft.Column(

                controls=[

                    ft.Text(

                        "Ближайшие мероприятия",

                        size=(
                            18
                            if phone
                            else 20
                        ),

                        weight=(
                            ft.FontWeight.BOLD
                        ),

                        color=TEXT_COLOR
                    ),

                    ft.Text(

                        next_event,

                        size=(
                            16
                            if phone
                            else 18
                        ),

                        color=TEXT_COLOR,

                        max_lines=3,

                        overflow=(
                            ft.TextOverflow.ELLIPSIS
                        )
                    )
                ],

                spacing=12
            )
        )

        birthday_card = ft.Container(

            width=(
                get_width() - 24
                if phone
                else 550
            ),

            height=(
                180
                if phone
                else 230
            ),

            padding=(
                24
                if phone
                else 50
            ),

            border_radius=(
                28
                if phone
                else 60
            ),

            bgcolor=PAGE_COLOR,

            border=ft.Border.all(
                1,
                TEXT_COLOR
            ),

            content=ft.Column(

                controls=[

                    ft.Text(

                        "Ближайшие дни рождения",

                        size=(
                            18
                            if phone
                            else 20
                        ),

                        weight=(
                            ft.FontWeight.BOLD
                        ),

                        color=TEXT_COLOR
                    ),

                    ft.Text(

                        next_birthday,

                        size=(
                            16
                            if phone
                            else 18
                        ),

                        color=TEXT_COLOR,

                        max_lines=2,

                        overflow=(
                            ft.TextOverflow.ELLIPSIS
                        )
                    )
                ],

                spacing=12
            )
        )

        if phone:

            cards = ft.Column(

                controls=[

                    event_card,

                    birthday_card
                ],

                spacing=14,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                )
            )

        else:

            cards = ft.Row(

                controls=[

                    event_card,

                    birthday_card
                ],

                alignment=(
                    ft.MainAxisAlignment.CENTER
                ),

                spacing=40
            )

        content.content = ft.Container(

            expand=True,

            bgcolor=PAGE_COLOR,

            content=ft.Column(

                controls=[

                    ft.Container(

                        height=(
                            260
                            if phone
                            else 400
                        ),

                        alignment=(
                            ft.Alignment(0, 0)
                        ),

                        bgcolor=PAGE_COLOR,

                        content=clock
                    ),

                    ft.Container(

                        padding=ft.Padding.only(

                            left=(
                                12
                                if phone
                                else 35
                            ),

                            right=(
                                12
                                if phone
                                else 35
                            ),

                            bottom=15
                        ),

                        bgcolor=PAGE_COLOR,

                        content=cards
                    )
                ],

                expand=True,

                scroll=ft.ScrollMode.AUTO,

                horizontal_alignment=(
                    ft.CrossAxisAlignment.CENTER
                )
            )
        )

        make_navigation()

        page.update()


    # =====================================================
    # ПОСЕЩАЕМОСТЬ
    # =====================================================

    def attendance(e=None):

        nonlocal active_page

        active_page = "attendance"

        participants = load_members()

        meetings = load_meetings()

        saved_attendance = load_app_json(
            ATTENDANCE_FILE,
            {}
        )

        if not isinstance(
            saved_attendance,
            dict
        ):
            saved_attendance = {}

        attendance_data = {}

        # -----------------------------------------------
        # Загрузка существующих дат
        # -----------------------------------------------

        for date in meetings:

            attendance_data[
                date
            ] = {}

            saved_date = (
                saved_attendance.get(
                    date,
                    {}
                )
            )

            if not isinstance(
                saved_date,
                dict
            ):
                saved_date = {}

            for person in participants:

                name = person.get(
                    "name",
                    ""
                )

                status = saved_date.get(
                    name,
                    ""
                )

                if status not in [
                    "+",
                    "-"
                ]:
                    status = ""

                attendance_data[
                    date
                ][name] = status


        # =================================================
        # ДОБАВЛЕНИЕ УЧАСТНИКА
        # =================================================

        def add_participant(e=None):

            width = min(

                400,

                max(
                    270,
                    get_width() - 45
                )
            )

            name_field = ft.TextField(

                label="ФИО",

                autofocus=True,

                width=width,

                color=TEXT_COLOR
            )

            class_field = ft.TextField(

                label="Класс",

                width=width,

                color=TEXT_COLOR
            )

            birthday_field = ft.TextField(

                label=(
                    "Дата рождения "
                    "(ДД.ММ.ГГГГ)"
                ),

                width=width,

                color=TEXT_COLOR
            )

            hobbies_field = ft.TextField(

                label="Хобби",

                width=width,

                color=TEXT_COLOR
            )

            direction_field = ft.TextField(

                label="Направление",

                width=width,

                color=TEXT_COLOR
            )


            def create_participant(e):

                name = (
                    name_field.value
                    or ""
                ).strip()

                if not name:

                    name_field.error_text = (
                        "Введите ФИО"
                    )

                    page.update()

                    return

                for person in participants:

                    if (
                        person.get(
                            "name",
                            ""
                        ).lower()
                        == name.lower()
                    ):

                        name_field.error_text = (
                            "Такой участник "
                            "уже существует"
                        )

                        page.update()

                        return

                new_person = {

                    "name": name,

                    "class": (
                        class_field.value
                        or ""
                    ).strip(),

                    "birthday": (
                        birthday_field.value
                        or ""
                    ).strip(),

                    "hobbies": (
                        hobbies_field.value
                        or ""
                    ).strip(),

                    "direction": (
                        direction_field.value
                        or ""
                    ).strip(),

                    "history": []
                }

                participants.append(
                    new_person
                )

                save_members(
                    participants
                )

                for date in attendance_data:

                    attendance_data[
                        date
                    ][name] = ""

                save_app_json(
                    ATTENDANCE_FILE,
                    attendance_data
                )

                close_dialog(
                    dialog
                )

                render_page()


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    "Добавить участника",

                    size=24,

                    weight=ft.FontWeight.BOLD,

                    color=TEXT_COLOR
                ),

                content=ft.Container(

                    width=dialog_width(
                        500
                    ),

                    content=ft.Column(

                        controls=[

                            name_field,

                            class_field,

                            birthday_field,

                            hobbies_field,

                            direction_field
                        ],

                        spacing=10,

                        tight=True,

                        scroll=ft.ScrollMode.AUTO
                    )
                ),

                actions=[

                    ft.TextButton(

                        "Отмена",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    ),

                    ft.Button(

                        "Добавить",

                        icon=ft.Icons.ADD,

                        on_click=create_participant,

                        style=button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # КАРТОЧКА УЧАСТНИКА
        # =================================================

        def open_participant_card(person):

            def delete_from_card(e):

                close_dialog(
                    dialog
                )

                confirm_delete_participant(
                    person
                )


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    person.get(
                        "name",
                        ""
                    ),

                    size=24,

                    weight=ft.FontWeight.BOLD,

                    color=TEXT_COLOR
                ),

                content=ft.Container(

                    width=dialog_width(
                        550
                    ),

                    content=ft.Column(

                        controls=[

                            ft.Text(

                                (
                                    "Класс: "
                                    f"{person.get('class') or 'Не указан'}"
                                ),

                                color=TEXT_COLOR
                            ),

                            ft.Divider(
                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                "Дата рождения",

                                weight=ft.FontWeight.BOLD,

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                person.get(
                                    "birthday"
                                ) or "Не указана",

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                "Хобби",

                                weight=ft.FontWeight.BOLD,

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                person.get(
                                    "hobbies"
                                ) or "Не указаны",

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                "Направление",

                                weight=ft.FontWeight.BOLD,

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                person.get(
                                    "direction"
                                ) or "Не указано",

                                color=TEXT_COLOR
                            )
                        ],

                        spacing=10,

                        tight=True,

                        scroll=ft.ScrollMode.AUTO
                    )
                ),

                actions=[

                    ft.TextButton(

                        "Изменить",

                        style=text_button_style(),

                        on_click=lambda e: (

                            close_dialog(
                                dialog
                            ),

                            edit_participant(
                                person
                            )
                        )
                    ),

                    ft.TextButton(

                        "Удалить",

                        style=text_button_style(),

                        on_click=delete_from_card
                    ),

                    ft.TextButton(

                        "Закрыть",

                        style=text_button_style(),

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            )
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # РЕДАКТИРОВАНИЕ УЧАСТНИКА
        # =================================================

        def edit_participant(person):

            width = min(

                400,

                max(
                    270,
                    get_width() - 45
                )
            )

            name_field = ft.TextField(

                label="ФИО",

                value=person.get(
                    "name",
                    ""
                ),

                width=width,

                color=TEXT_COLOR
            )

            class_field = ft.TextField(

                label="Класс",

                value=person.get(
                    "class",
                    ""
                ),

                width=width,

                color=TEXT_COLOR
            )

            birthday_field = ft.TextField(

                label="Дата рождения",

                value=person.get(
                    "birthday",
                    ""
                ),

                width=width,

                color=TEXT_COLOR
            )

            hobbies_field = ft.TextField(

                label="Хобби",

                value=person.get(
                    "hobbies",
                    ""
                ),

                width=width,

                color=TEXT_COLOR
            )

            direction_field = ft.TextField(

                label="Направление",

                value=person.get(
                    "direction",
                    ""
                ),

                width=width,

                color=TEXT_COLOR
            )

            old_name = person.get(
                "name",
                ""
            )


            def save_changes(e):

                new_name = (
                    name_field.value
                    or ""
                ).strip()

                if not new_name:

                    name_field.error_text = (
                        "Введите ФИО"
                    )

                    page.update()

                    return

                if new_name != old_name:

                    for other in participants:

                        if (
                            other is not person
                            and other.get(
                                "name",
                                ""
                            ).lower()
                            == new_name.lower()
                        ):

                            name_field.error_text = (
                                "Такой участник "
                                "уже существует"
                            )

                            page.update()

                            return

                    for date in attendance_data:

                        if old_name in (
                            attendance_data[
                                date
                            ]
                        ):

                            status = (
                                attendance_data[
                                    date
                                ][old_name]
                            )

                            del attendance_data[
                                date
                            ][old_name]

                            attendance_data[
                                date
                            ][new_name] = status

                person["name"] = new_name

                person["class"] = (
                    class_field.value
                    or ""
                ).strip()

                person["birthday"] = (
                    birthday_field.value
                    or ""
                ).strip()

                person["hobbies"] = (
                    hobbies_field.value
                    or ""
                ).strip()

                person["direction"] = (
                    direction_field.value
                    or ""
                ).strip()

                # Старое поле удаляем.
                person.pop(
                    "qualities",
                    None
                )

                save_members(
                    participants
                )

                save_app_json(
                    ATTENDANCE_FILE,
                    attendance_data
                )

                close_dialog(
                    dialog
                )

                render_page()


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    "Изменить участника",

                    color=TEXT_COLOR
                ),

                content=ft.Container(

                    width=dialog_width(
                        500
                    ),

                    content=ft.Column(

                        controls=[

                            name_field,

                            class_field,

                            birthday_field,

                            hobbies_field,

                            direction_field
                        ],

                        spacing=10,

                        tight=True,

                        scroll=ft.ScrollMode.AUTO
                    )
                ),

                actions=[

                    ft.TextButton(

                        "Отмена",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Сохранить",

                        on_click=save_changes,

                        style=text_button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # УДАЛЕНИЕ УЧАСТНИКА
        # =================================================

        def confirm_delete_participant(
            person
        ):

            name = person.get(
                "name",
                ""
            )

            def delete_participant(e):

                if person in participants:

                    participants.remove(
                        person
                    )

                for date in attendance_data:

                    attendance_data[
                        date
                    ].pop(
                        name,
                        None
                    )

                save_members(
                    participants
                )

                save_app_json(
                    ATTENDANCE_FILE,
                    attendance_data
                )

                close_dialog(
                    dialog
                )

                render_page()


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    "Удалить участника?",

                    color=TEXT_COLOR
                ),

                content=ft.Text(

                    (
                        f"Удалить «{name}»?\n\n"
                        "Участник будет удалён "
                        "из списка и посещаемости."
                    ),

                    color=TEXT_COLOR
                ),

                actions=[

                    ft.TextButton(

                        "Отмена",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Удалить",

                        on_click=delete_participant,

                        style=text_button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # ПРОСМОТР ЗАСЕДАНИЯ
        # =================================================

        def open_meeting(date):

            if date not in meetings:
                return

            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    f"Заседание {date}",

                    color=TEXT_COLOR
                ),

                content=ft.Container(

                    width=dialog_width(
                        600
                    ),

                    content=ft.Column(

                        controls=[

                            ft.Text(

                                "Дата:",

                                weight=(
                                    ft.FontWeight.BOLD
                                ),

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                date,

                                color=TEXT_COLOR
                            ),

                            ft.Divider(
                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                "Что обсуждали:",

                                weight=(
                                    ft.FontWeight.BOLD
                                ),

                                color=TEXT_COLOR
                            ),

                            ft.Text(

                                meetings[
                                    date
                                ].get(

                                    "description",

                                    "Информация отсутствует."
                                ),

                                color=TEXT_COLOR
                            )
                        ],

                        spacing=10,

                        tight=True,

                        scroll=ft.ScrollMode.AUTO
                    )
                ),

                actions=[

                    ft.TextButton(

                        "Изменить информацию",

                        on_click=lambda e: (

                            close_dialog(
                                dialog
                            ),

                            edit_meeting(
                                date
                            )
                        ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Удалить заседание",

                        on_click=lambda e: (

                            close_dialog(
                                dialog
                            ),

                            confirm_delete_meeting(
                                date
                            )
                        ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Закрыть",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # РЕДАКТИРОВАНИЕ ЗАСЕДАНИЯ
        # =================================================

        def edit_meeting(date):

            if date not in meetings:
                return

            description_field = ft.TextField(

                label="Что обсуждали?",

                value=meetings[
                    date
                ].get(
                    "description",
                    ""
                ),

                multiline=True,

                min_lines=4,

                max_lines=8,

                color=TEXT_COLOR
            )


            def save_changes(e):

                description = (
                    description_field.value
                    or ""
                ).strip()

                if not description:

                    description = (
                        "Информация отсутствует."
                    )

                meetings[
                    date
                ][
                    "description"
                ] = description

                save_meetings(
                    meetings
                )

                close_dialog(
                    dialog
                )

                render_page()


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    f"Изменить заседание {date}",

                    color=TEXT_COLOR
                ),

                content=ft.Container(

                    width=dialog_width(
                        600
                    ),

                    content=description_field
                ),

                actions=[

                    ft.TextButton(

                        "Отмена",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Сохранить",

                        on_click=save_changes,

                        style=text_button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # УДАЛЕНИЕ ЗАСЕДАНИЯ
        # =================================================

        def confirm_delete_meeting(date):

            def delete_meeting(e):

                meetings.pop(
                    date,
                    None
                )

                save_meetings(
                    meetings
                )

                attendance_data.pop(
                    date,
                    None
                )

                save_app_json(
                    ATTENDANCE_FILE,
                    attendance_data
                )

                close_dialog(
                    dialog
                )

                render_page()


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    "Удалить заседание?",

                    color=TEXT_COLOR
                ),

                content=ft.Text(

                    f"Удалить заседание {date}?",

                    color=TEXT_COLOR
                ),

                actions=[

                    ft.TextButton(

                        "Отмена",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Удалить",

                        on_click=delete_meeting,

                        style=text_button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # ПОСЕЩАЕМОСТЬ
        # =================================================

        def change_status(
            person_name,
            date
        ):

            if date not in attendance_data:

                attendance_data[
                    date
                ] = {}

            current = (
                attendance_data[
                    date
                ].get(
                    person_name,
                    ""
                )
            )

            if current == "":

                new_status = "+"

            elif current == "+":

                new_status = "-"

            else:

                new_status = ""

            attendance_data[
                date
            ][
                person_name
            ] = new_status

            save_app_json(
                ATTENDANCE_FILE,
                attendance_data
            )

            render_page()


        def attendance_button(
            person_name,
            date
        ):

            current = (
                attendance_data[
                    date
                ].get(
                    person_name,
                    ""
                )
            )

            if current == "+":

                bgcolor = "#F4FB8C"

            elif current == "-":

                bgcolor = "#B1BDCE"

            else:

                bgcolor = PAGE_COLOR

            return ft.TextButton(

                current or "—",

                width=50,

                height=40,

                style=ft.ButtonStyle(

                    color=TEXT_COLOR,

                    bgcolor=bgcolor,

                    padding=0,

                    alignment=(
                        ft.Alignment.CENTER
                    )
                ),

                on_click=lambda e:
                    change_status(
                        person_name,
                        date
                    )
            )


        # =================================================
        # ДОБАВЛЕНИЕ ЗАСЕДАНИЯ
        # =================================================

        def add_meeting(e=None):

            selected_date = {
                "value": None
            }

            description_field = ft.TextField(

                label="Что обсуждали?",

                multiline=True,

                min_lines=3,

                max_lines=6,

                color=TEXT_COLOR
            )

            date_text = ft.Text(

                "Дата не выбрана",

                color=TEXT_COLOR
            )


            def choose_date(e):

                def set_meeting_date(
                    value
                ):

                    selected_date[
                        "value"
                    ] = value

                    date_text.value = (
                        value.strftime(
                            "%d.%m.%Y"
                        )
                    )

                    page.update()

                open_custom_date_picker(
                    set_meeting_date
                )


            def save_meeting_click(e):

                value = selected_date[
                    "value"
                ]

                if value is None:

                    date_text.value = (
                        "Сначала выберите дату"
                    )

                    page.update()

                    return

                date_text_value = (
                    value.strftime(
                        "%d.%m.%Y"
                    )
                )

                if date_text_value in meetings:

                    date_text.value = (
                        "На эту дату "
                        "заседание уже есть"
                    )

                    page.update()

                    return

                meetings[
                    date_text_value
                ] = {

                    "date":
                        date_text_value,

                    "description":
                        description_field.value
                        or "Информация отсутствует."
                }

                save_meetings(
                    meetings
                )

                attendance_data[
                    date_text_value
                ] = {}

                for person in participants:

                    attendance_data[
                        date_text_value
                    ][
                        person["name"]
                    ] = ""

                save_app_json(
                    ATTENDANCE_FILE,
                    attendance_data
                )

                close_dialog(
                    dialog
                )

                render_page()


            dialog = ft.AlertDialog(

                modal=True,

                bgcolor=PAGE_COLOR,

                title=ft.Text(

                    "Добавить заседание",

                    color=TEXT_COLOR
                ),

                content=ft.Container(

                    width=dialog_width(
                        600
                    ),

                    content=ft.Column(

                        controls=[

                            ft.Button(

                                "Выбрать дату",

                                icon=(
                                    ft.Icons
                                    .CALENDAR_MONTH
                                ),

                                on_click=choose_date,

                                style=button_style()
                            ),

                            date_text,

                            description_field
                        ],

                        tight=True,

                        spacing=10,

                        scroll=ft.ScrollMode.AUTO
                    )
                ),

                actions=[

                    ft.TextButton(

                        "Отмена",

                        on_click=lambda e:
                            close_dialog(
                                dialog
                            ),

                        style=text_button_style()
                    ),

                    ft.TextButton(

                        "Добавить",

                        on_click=(
                            save_meeting_click
                        ),

                        style=text_button_style()
                    )
                ]
            )

            open_dialog(
                dialog
            )


        # =================================================
        # ОТРИСОВКА
        # =================================================

        def render_page():

            phone = is_phone()

            def class_number(person):

                class_value = person.get(
                    "class",
                    ""
                )

                if not class_value:
                    return 999

                digits = ""

                for char in class_value:

                    if char.isdigit():

                        digits += char

                    else:

                        break

                if digits:

                    return int(
                        digits
                    )

                return 999


            participants.sort(

                key=lambda person: (

                    class_number(person),

                    person.get(
                        "class",
                        ""
                    ),

                    person.get(
                        "name",
                        ""
                    )
                )
            )


            participant_width = (
                165
                if phone
                else 250
            )

            class_width = (
                65
                if phone
                else 80
            )

            date_width = (
                100
                if phone
                else 130
            )

            row_height = (
                48
                if phone
                else 55
            )

            left_width = (
                participant_width
                + class_width
            )

            border = ft.Border.all(
                1,
                TEXT_COLOR
            )


            # ---------------------------------------------
            # ЛЕВАЯ ЧАСТЬ
            # ---------------------------------------------

            left_rows = [

                ft.Row(

                    controls=[

                        ft.Container(

                            width=participant_width,

                            height=row_height,

                            alignment=(
                                ft.Alignment.CENTER
                            ),

                            bgcolor=PAGE_COLOR,

                            border=border,

                            content=ft.Text(

                                "Участник",

                                size=(
                                    12
                                    if phone
                                    else 14
                                ),

                                weight=(
                                    ft.FontWeight.BOLD
                                ),

                                color=TEXT_COLOR
                            )
                        ),

                        ft.Container(

                            width=class_width,

                            height=row_height,

                            alignment=(
                                ft.Alignment.CENTER
                            ),

                            bgcolor=PAGE_COLOR,

                            border=border,

                            content=ft.Text(

                                "Класс",

                                size=(
                                    12
                                    if phone
                                    else 14
                                ),

                                weight=(
                                    ft.FontWeight.BOLD
                                ),

                                color=TEXT_COLOR
                            )
                        )
                    ],

                    spacing=0
                )
            ]


            for person in participants:

                left_rows.append(

                    ft.Row(

                        controls=[

                            ft.Container(

                                width=participant_width,

                                height=row_height,

                                alignment=(
                                    ft.Alignment.CENTER
                                ),

                                bgcolor=PAGE_COLOR,

                                border=border,

                                content=ft.TextButton(

                                    # В таблице только фамилия + имя.
                                    short_name(
                                        person.get(
                                            "name",
                                            ""
                                        )
                                    ),

                                    width=participant_width,

                                    height=row_height,

                                    style=ft.ButtonStyle(

                                        color=TEXT_COLOR,

                                        bgcolor=PAGE_COLOR,

                                        padding=0
                                    ),

                                    on_click=lambda e,
                                    p=person:
                                        open_participant_card(
                                            p
                                        )
                                )
                            ),

                            ft.Container(

                                width=class_width,

                                height=row_height,

                                alignment=(
                                    ft.Alignment.CENTER
                                ),

                                bgcolor=PAGE_COLOR,

                                border=border,

                                content=ft.Text(

                                    person.get(
                                        "class",
                                        ""
                                    ),

                                    size=(
                                        12
                                        if phone
                                        else 14
                                    ),

                                    color=TEXT_COLOR
                                )
                            )
                        ],

                        spacing=0
                    )
                )


            left_column = ft.Column(

                controls=left_rows,

                spacing=0
            )


            # ---------------------------------------------
            # ПРАВАЯ ЧАСТЬ
            # ---------------------------------------------

            right_rows = []

            header = []


            for date in meetings:

                header.append(

                    ft.Container(

                        width=date_width,

                        height=row_height,

                        alignment=(
                            ft.Alignment.CENTER
                        ),

                        bgcolor=PAGE_COLOR,

                        border=border,

                        content=ft.TextButton(

                            date,

                            width=date_width,

                            height=row_height,

                            style=ft.ButtonStyle(

                                color=TEXT_COLOR,

                                bgcolor=PAGE_COLOR,

                                padding=0
                            ),

                            on_click=lambda e,
                            d=date:
                                open_meeting(
                                    d
                                )
                        )
                    )
                )


            right_rows.append(

                ft.Row(

                    controls=header,

                    spacing=0
                )
            )


            for person in participants:

                cells = []

                for date in meetings:

                    cells.append(

                        ft.Container(

                            width=date_width,

                            height=row_height,

                            alignment=(
                                ft.Alignment.CENTER
                            ),

                            bgcolor=PAGE_COLOR,

                            border=border,

                            content=attendance_button(

                                person.get(
                                    "name",
                                    ""
                                ),

                                date
                            )
                        )
                    )

                right_rows.append(

                    ft.Row(

                        controls=cells,

                        spacing=0
                    )
                )


            right_column = ft.Column(

                controls=right_rows,

                spacing=0
            )


            table = ft.Row(

                controls=[

                    ft.Container(

                        width=left_width,

                        content=left_column
                    ),

                    ft.Container(

                        content=right_column
                    )
                ],

                spacing=0,

                scroll=ft.ScrollMode.ALWAYS,

                expand=True
            )


            # ---------------------------------------------
            # КНОПКИ
            # ---------------------------------------------

            if phone:

                action_buttons = ft.Row(

                    controls=[

                        ft.IconButton(

                            icon=ft.Icons.PERSON_ADD,

                            icon_color=TEXT_COLOR,

                            tooltip=(
                                "Добавить участника"
                            ),

                            on_click=add_participant
                        ),

                        ft.IconButton(

                            icon=ft.Icons.ADD,

                            icon_color=TEXT_COLOR,

                            tooltip=(
                                "Добавить заседание"
                            ),

                            on_click=add_meeting
                        )
                    ],

                    spacing=0
                )

            else:

                action_buttons = ft.Row(

                    controls=[

                        ft.Button(

                            "Добавить участника",

                            icon=ft.Icons.PERSON_ADD,

                            on_click=add_participant,

                            style=button_style()
                        ),

                        ft.Button(

                            "Добавить заседание",

                            icon=ft.Icons.ADD,

                            on_click=add_meeting,

                            style=button_style()
                        )
                    ],

                    spacing=8
                )


            # ---------------------------------------------
            # ВЫВОД
            # ---------------------------------------------

            content.content = ft.Container(

                expand=True,

                bgcolor=PAGE_COLOR,

                padding=(
                    6
                    if phone
                    else 12
                ),

                content=ft.Column(

                    controls=[

                        ft.Row(

                            controls=[

                                ft.Text(

                                    "Посещаемость",

                                    size=(
                                        24
                                        if phone
                                        else 30
                                    ),

                                    weight=(
                                        ft.FontWeight.BOLD
                                    ),

                                    color=TEXT_COLOR
                                ),

                                ft.Container(
                                    expand=True
                                ),

                                action_buttons
                            ],

                            vertical_alignment=(
                                ft.CrossAxisAlignment
                                .CENTER
                            )
                        ),

                        ft.Divider(
                            color=TEXT_COLOR
                        ),

                        ft.Container(

                            expand=True,

                            content=table
                        )
                    ],

                    expand=True,

                    spacing=8,

                    scroll=ft.ScrollMode.AUTO
                )
            )

            make_navigation()

            page.update()


        render_page()


    # =====================================================
    # ВЫБОР ДАТЫ
    # =====================================================

    def open_custom_date_picker(
        on_select,
        initial_date=None
    ):

        selected_date = (
            initial_date
            or datetime.now()
        )

        month_names = [

            "Январь",
            "Февраль",
            "Март",
            "Апрель",
            "Май",
            "Июнь",
            "Июль",
            "Август",
            "Сентябрь",
            "Октябрь",
            "Ноябрь",
            "Декабрь"
        ]


        def build_picker():

            nonlocal selected_date

            year = selected_date.year

            month = selected_date.month

            month_days = cal.monthcalendar(
                year,
                month
            )


            def previous_month(e):

                nonlocal selected_date

                if month == 1:

                    selected_date = datetime(
                        year - 1,
                        12,
                        1
                    )

                else:

                    selected_date = datetime(
                        year,
                        month - 1,
                        1
                    )

                build_picker()


            def next_month(e):

                nonlocal selected_date

                if month == 12:

                    selected_date = datetime(
                        year + 1,
                        1,
                        1
                    )

                else:

                    selected_date = datetime(
                        year,
                        month + 1,
                        1
                    )

                build_picker()


            week_names = ft.Row(

                controls=[

                    ft.Text(
                        "Пн",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Вт",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Ср",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Чт",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Пт",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Сб",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Вс",
                        expand=True,
                        text_align=(
                            ft.TextAlign.CENTER
                        ),
                        color=TEXT_COLOR
                    )
                ],

                spacing=0
            )


            rows = []


            for week in month_days:

                cells = []


                for day in week:

                    if day == 0:

                        cells.append(

                            ft.Container(

                                expand=True,

                                height=45,

                                bgcolor=PAGE_COLOR
                            )
                        )

                    else:

                        def select_day(
                            e,
                            selected_day=day,
                            selected_year=year,
                            selected_month=month
                        ):

                            chosen = datetime(

                                selected_year,

                                selected_month,

                                selected_day
                            )

                            dialog.open = False

                            page.update()

                            on_select(
                                chosen
                            )


                        cells.append(

                            ft.Container(

                                expand=True,

                                height=45,

                                alignment=(
                                    ft.Alignment.CENTER
                                ),

                                bgcolor=PAGE_COLOR,

                                border_radius=8,

                                on_click=select_day,

                                content=ft.Text(

                                    str(day),

                                    color=TEXT_COLOR,

                                    size=16,

                                    text_align=(
                                        ft.TextAlign.CENTER
                                    )
                                )
                            )
                        )


                rows.append(

                    ft.Row(

                        controls=cells,

                        spacing=0
                    )
                )


            dialog.content = ft.Container(

                width=dialog_width(
                    500
                ),

                content=ft.Column(

                    controls=[

                        ft.Row(

                            controls=[

                                ft.IconButton(

                                    icon=(
                                        ft.Icons
                                        .CHEVRON_LEFT
                                    ),

                                    icon_color=TEXT_COLOR,

                                    on_click=(
                                        previous_month
                                    )
                                ),

                                ft.Container(

                                    expand=True,

                                    alignment=(
                                        ft.Alignment.CENTER
                                    ),

                                    content=ft.Text(

                                        (
                                            f"{month_names[month - 1]} "
                                            f"{year}"
                                        ),

                                        size=20,

                                        weight=(
                                            ft.FontWeight.BOLD
                                        ),

                                        color=TEXT_COLOR
                                    )
                                ),

                                ft.IconButton(

                                    icon=(
                                        ft.Icons
                                        .CHEVRON_RIGHT
                                    ),

                                    icon_color=TEXT_COLOR,

                                    on_click=next_month
                                )
                            ]
                        ),

                        week_names,

                        *rows
                    ],

                    spacing=0
                )
            )

            page.update()


        dialog = ft.AlertDialog(

            modal=True,

            bgcolor=PAGE_COLOR,

            title=ft.Text(

                "Выберите дату",

                color=TEXT_COLOR
            ),

            content=ft.Container(

                width=dialog_width(
                    500
                ),

                height=330
            ),

            actions=[

                ft.TextButton(

                    "Отмена",

                    on_click=lambda e:
                        close_dialog(
                            dialog
                        ),

                    style=text_button_style()
                )
            ]
        )


        open_dialog(
            dialog
        )

        build_picker()


    # =====================================================
    # КАЛЕНДАРЬ
    # =====================================================

    def calendar(e=None):

        nonlocal active_page

        active_page = "calendar"

        # ВАЖНО:
        # каждый вход в календарь заново читает файл.
        calendar_data.clear()

        calendar_data.update(
            load_calendar()
        )


        def build_calendar():

            current_date = (
                current_calendar_date[
                    "value"
                ]
            )

            year = current_date.year

            month = current_date.month

            phone = is_phone()

            month_days = cal.monthcalendar(
                year,
                month
            )

            month_names = [

                "Январь",
                "Февраль",
                "Март",
                "Апрель",
                "Май",
                "Июнь",
                "Июль",
                "Август",
                "Сентябрь",
                "Октябрь",
                "Ноябрь",
                "Декабрь"
            ]


            # ---------------------------------------------
            # НАЗАД
            # ---------------------------------------------

            def previous_month(e):

                if month == 1:

                    current_calendar_date[
                        "value"
                    ] = datetime(

                        year - 1,

                        12,

                        1
                    )

                else:

                    current_calendar_date[
                        "value"
                    ] = datetime(

                        year,

                        month - 1,

                        1
                    )

                build_calendar()


            # ---------------------------------------------
            # ВПЕРЁД
            # ---------------------------------------------

            def next_month(e):

                if month == 12:

                    current_calendar_date[
                        "value"
                    ] = datetime(

                        year + 1,

                        1,

                        1
                    )

                else:

                    current_calendar_date[
                        "value"
                    ] = datetime(

                        year,

                        month + 1,

                        1
                    )

                build_calendar()


            # =============================================
            # СОЗДАНИЕ МЕРОПРИЯТИЯ
            # =============================================

            def create_event(e):

                selected_date = {
                    "value": None
                }

                photo_path = {
                    "value": None
                }

                event_field = ft.TextField(

                    label=(
                        "Название мероприятия"
                    ),

                    color=TEXT_COLOR
                )

                date_text = ft.Text(

                    "Дата не выбрана",

                    color=TEXT_COLOR
                )

                photo_container = ft.Container(

                    bgcolor=PAGE_COLOR
                )

                file_picker = ft.FilePicker()


                async def pick_photo(e):

                    files = (

                        await
                        file_picker.pick_files(

                            allow_multiple=False,

                            allowed_extensions=[

                                "jpg",

                                "jpeg",

                                "png"
                            ]
                        )
                    )

                    if not files:
                        return

                    photo_path[
                        "value"
                    ] = files[0].path

                    photo_width = min(

                        300,

                        max(
                            220,
                            get_width() - 70
                        )
                    )

                    photo_container.content = (

                        ft.Image(

                            src=files[0].path,

                            width=photo_width,

                            height=180,

                            fit=ft.BoxFit.COVER
                        )
                    )

                    page.update()


                def choose_date(e):

                    def receive_date(
                        value
                    ):

                        selected_date[
                            "value"
                        ] = value

                        date_text.value = (
                            value.strftime(
                                "%d.%m.%Y"
                            )
                        )

                        page.update()


                    open_custom_date_picker(
                        receive_date,
                        initial_date=(
                            selected_date[
                                "value"
                            ]
                            or current_calendar_date[
                                "value"
                            ]
                        )
                    )


                def save_event(e):

                    value = selected_date[
                        "value"
                    ]

                    if value is None:

                        date_text.value = (
                            "Сначала выберите дату"
                        )

                        page.update()

                        return

                    title = (
                        event_field.value
                        or ""
                    ).strip()

                    if not title:

                        event_field.error_text = (
                            "Введите название мероприятия"
                        )

                        page.update()

                        return

                    date_string = (
                        value.strftime(
                            "%d.%m.%Y"
                        )
                    )

                    # Не разрешаем две записи
                    # на одну дату.
                    if date_string in calendar_data:

                        date_text.value = (
                            "На эту дату уже "
                            "есть мероприятие"
                        )

                        page.update()

                        return

                    # Дата хранится и как ключ,
                    # и внутри самого объекта.
                    calendar_data[
                        date_string
                    ] = {

                        "date":
                            date_string,

                        "event":
                            title,

                        "photo":
                            photo_path[
                                "value"
                            ]
                    }

                    # Физически записываем JSON.
                    save_calendar(
                        calendar_data
                    )

                    # Сразу перепроверяем чтением.
                    calendar_data.clear()

                    calendar_data.update(
                        load_calendar()
                    )

                    current_calendar_date[
                        "value"
                    ] = datetime(

                        value.year,

                        value.month,

                        1
                    )

                    close_dialog(
                        dialog
                    )

                    build_calendar()


                dialog = ft.AlertDialog(

                    modal=True,

                    bgcolor=PAGE_COLOR,

                    title=ft.Text(

                        "Новое мероприятие",

                        color=TEXT_COLOR
                    ),

                    content=ft.Container(

                        width=dialog_width(
                            600
                        ),

                        content=ft.Column(

                            controls=[

                                ft.Button(

                                    "Выбрать дату",

                                    icon=(
                                        ft.Icons
                                        .CALENDAR_MONTH
                                    ),

                                    on_click=choose_date,

                                    style=button_style()
                                ),

                                date_text,

                                event_field,

                                ft.Text(

                                    "Фото",

                                    color=TEXT_COLOR
                                ),

                                ft.Button(

                                    "Добавить фото",

                                    icon=ft.Icons.IMAGE,

                                    on_click=pick_photo,

                                    style=button_style()
                                ),

                                photo_container
                            ],

                            tight=True,

                            spacing=10,

                            scroll=ft.ScrollMode.AUTO
                        )
                    ),

                    actions=[

                        ft.TextButton(

                            "Отмена",

                            on_click=lambda e:
                                close_dialog(
                                    dialog
                                ),

                            style=text_button_style()
                        ),

                        ft.TextButton(

                            "Создать",

                            on_click=save_event,

                            style=text_button_style()
                        )
                    ]
                )

                page.services.append(
                    file_picker
                )

                open_dialog(
                    dialog
                )


            # =============================================
            # ОТКРЫТИЕ ДНЯ
            # =============================================

            def open_date(day):

                date_string = (

                    f"{day:02d}."

                    f"{month:02d}."

                    f"{year}"
                )

                event = calendar_data.get(
                    date_string
                )


                if event is None:

                    dialog = ft.AlertDialog(

                        modal=True,

                        bgcolor=PAGE_COLOR,

                        title=ft.Text(

                            f"Дата: {date_string}",

                            color=TEXT_COLOR
                        ),

                        content=ft.Text(

                            (
                                "На эту дату "
                                "мероприятий нет."
                            ),

                            color=TEXT_COLOR
                        ),

                        actions=[

                            ft.TextButton(

                                "Закрыть",

                                on_click=lambda e:
                                    close_dialog(
                                        dialog
                                    ),

                                style=(
                                    text_button_style()
                                )
                            )
                        ]
                    )

                    open_dialog(
                        dialog
                    )

                    return


                # =========================================
                # ИЗМЕНЕНИЕ
                # =========================================

                def edit_event(e):

                    event_field = ft.TextField(

                        label=(
                            "Название мероприятия"
                        ),

                        value=event.get(
                            "event",
                            ""
                        ),

                        color=TEXT_COLOR
                    )

                    old_date = event.get(
                        "date",
                        date_string
                    )

                    selected_date = {
                        "value":
                            datetime.strptime(
                                old_date,
                                "%d.%m.%Y"
                            )
                    }

                    date_text = ft.Text(

                        old_date,

                        color=TEXT_COLOR
                    )

                    photo_path = {

                        "value":
                            event.get(
                                "photo"
                            )
                    }

                    photo_container = ft.Container(

                        bgcolor=PAGE_COLOR
                    )

                    photo_width = min(

                        300,

                        max(
                            220,
                            get_width() - 70
                        )
                    )

                    if event.get("photo"):

                        photo_container.content = (

                            ft.Image(

                                src=event[
                                    "photo"
                                ],

                                width=photo_width,

                                height=180,

                                fit=ft.BoxFit.COVER
                            )
                        )

                    file_picker = ft.FilePicker()


                    async def pick_photo(e):

                        files = (

                            await
                            file_picker.pick_files(

                                allow_multiple=False,

                                allowed_extensions=[

                                    "jpg",

                                    "jpeg",

                                    "png"
                                ]
                            )
                        )

                        if not files:
                            return

                        photo_path[
                            "value"
                        ] = files[0].path

                        photo_container.content = (

                            ft.Image(

                                src=files[0].path,

                                width=photo_width,

                                height=180,

                                fit=ft.BoxFit.COVER
                            )
                        )

                        page.update()


                    def choose_date(e):

                        def receive_date(
                            value
                        ):

                            selected_date[
                                "value"
                            ] = value

                            date_text.value = (
                                value.strftime(
                                    "%d.%m.%Y"
                                )
                            )

                            page.update()


                        open_custom_date_picker(

                            receive_date,

                            initial_date=(
                                selected_date[
                                    "value"
                                ]
                            )
                        )


                    def save_event_changes(e):

                        title = (

                            event_field.value

                            or ""

                        ).strip()

                        if not title:

                            event_field.error_text = (

                                "Введите название мероприятия"
                            )

                            page.update()

                            return

                        new_date = (

                            selected_date[
                                "value"
                            ].strftime(
                                "%d.%m.%Y"
                            )
                        )

                        # Если дату изменили —
                        # проверяем конфликт.
                        if (
                            new_date != old_date
                            and new_date in calendar_data
                        ):

                            date_text.value = (
                                "На эту дату уже "
                                "есть мероприятие"
                            )

                            page.update()

                            return

                        # Удаляем старый ключ.
                        calendar_data.pop(
                            old_date,
                            None
                        )

                        # Записываем новый ключ
                        # и новую дату.
                        calendar_data[
                            new_date
                        ] = {

                            "date":
                                new_date,

                            "event":
                                title,

                            "photo":
                                photo_path[
                                    "value"
                                ]
                        }

                        save_calendar(
                            calendar_data
                        )

                        # Перечитываем после сохранения.
                        calendar_data.clear()

                        calendar_data.update(
                            load_calendar()
                        )

                        current_calendar_date[
                            "value"
                        ] = datetime(

                            selected_date[
                                "value"
                            ].year,

                            selected_date[
                                "value"
                            ].month,

                            1
                        )

                        close_dialog(
                            edit_dialog
                        )

                        build_calendar()


                    edit_dialog = ft.AlertDialog(

                        modal=True,

                        bgcolor=PAGE_COLOR,

                        title=ft.Text(

                            "Изменить мероприятие",

                            color=TEXT_COLOR
                        ),

                        content=ft.Container(

                            width=dialog_width(
                                600
                            ),

                            content=ft.Column(

                                controls=[

                                    event_field,

                                    ft.Button(

                                        "Изменить дату",

                                        icon=(
                                            ft.Icons
                                            .CALENDAR_MONTH
                                        ),

                                        on_click=choose_date,

                                        style=(
                                            button_style()
                                        )
                                    ),

                                    date_text,

                                    ft.Text(

                                        "Фото",

                                        color=TEXT_COLOR
                                    ),

                                    ft.Button(

                                        "Изменить фото",

                                        icon=(
                                            ft.Icons
                                            .IMAGE
                                        ),

                                        on_click=pick_photo,

                                        style=(
                                            button_style()
                                        )
                                    ),

                                    photo_container
                                ],

                                tight=True,

                                spacing=10,

                                scroll=ft.ScrollMode.AUTO
                            )
                        ),

                        actions=[

                            ft.TextButton(

                                "Отмена",

                                on_click=lambda e:
                                    close_dialog(
                                        edit_dialog
                                    ),

                                style=(
                                    text_button_style()
                                )
                            ),

                            ft.TextButton(

                                "Сохранить",

                                on_click=(
                                    save_event_changes
                                ),

                                style=(
                                    text_button_style()
                                )
                            )
                        ]
                    )

                    page.services.append(
                        file_picker
                    )

                    open_dialog(
                        edit_dialog
                    )


                # =========================================
                # УДАЛЕНИЕ
                # =========================================

                def delete_event(e):

                    def confirm_delete(e):

                        calendar_data.pop(
                            date_string,
                            None
                        )

                        save_calendar(
                            calendar_data
                        )

                        close_dialog(
                            confirm_dialog
                        )

                        close_dialog(
                            dialog
                        )

                        build_calendar()


                    confirm_dialog = ft.AlertDialog(

                        modal=True,

                        bgcolor=PAGE_COLOR,

                        title=ft.Text(

                            "Удалить мероприятие?",

                            color=TEXT_COLOR
                        ),

                        content=ft.Text(

                            (
                                "Это действие "
                                "нельзя отменить."
                            ),

                            color=TEXT_COLOR
                        ),

                        actions=[

                            ft.TextButton(

                                "Отмена",

                                on_click=lambda e:
                                    close_dialog(
                                        confirm_dialog
                                    ),

                                style=(
                                    text_button_style()
                                )
                            ),

                            ft.TextButton(

                                "Удалить",

                                on_click=confirm_delete,

                                style=(
                                    text_button_style()
                                )
                            )
                        ]
                    )

                    open_dialog(
                        confirm_dialog
                    )


                # =========================================
                # ПРОСМОТР
                # =========================================

                stored_date = event.get(
                    "date",
                    date_string
                )

                controls = [

                    ft.Text(

                        event.get(
                            "event",
                            ""
                        ),

                        size=20,

                        weight=(
                            ft.FontWeight.BOLD
                        ),

                        color=TEXT_COLOR,

                        text_align=(
                            ft.TextAlign.CENTER
                        )
                    )
                ]

                controls.insert(
                    0,
                    ft.Text(
                        f"Дата: {stored_date}",
                        color=TEXT_COLOR
                    )
                )


                if event.get("photo"):

                    controls.append(

                        ft.Image(

                            src=event[
                                "photo"
                            ],

                            width=min(

                                300,

                                max(
                                    220,
                                    get_width() - 70
                                )
                            ),

                            height=180,

                            fit=ft.BoxFit.COVER
                        )
                    )


                dialog = ft.AlertDialog(

                    modal=True,

                    bgcolor=PAGE_COLOR,

                    title=ft.Text(

                        "Мероприятие",

                        color=TEXT_COLOR
                    ),

                    content=ft.Container(

                        width=dialog_width(
                            600
                        ),

                        content=ft.Column(

                            controls=controls,

                            spacing=10,

                            tight=True,

                            horizontal_alignment=(

                                ft.CrossAxisAlignment
                                .CENTER
                            ),

                            scroll=ft.ScrollMode.AUTO
                        )
                    ),

                    actions=[

                        ft.TextButton(

                            "Изменить",

                            on_click=edit_event,

                            style=text_button_style()
                        ),

                        ft.TextButton(

                            "Закрыть",

                            on_click=lambda e:
                                close_dialog(
                                    dialog
                                ),

                            style=text_button_style()
                        ),

                        ft.TextButton(

                            "Удалить",

                            on_click=delete_event,

                            style=text_button_style()
                        )
                    ]
                )

                open_dialog(
                    dialog
                )


            # =============================================
            # ДНИ НЕДЕЛИ
            # =============================================

            week_days = ft.Row(

                controls=[

                    ft.Text(
                        "Пн",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Вт",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Ср",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Чт",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Пт",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Сб",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    ),

                    ft.Text(
                        "Вс",
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                        color=TEXT_COLOR
                    )
                ],

                spacing=0
            )


            # =============================================
            # СЕТКА
            # =============================================

            calendar_rows = []

            available_height = (

                get_height()

                - (
                    160
                    if phone
                    else 180
                )
            )

            cell_height = max(

                60,

                min(

                    120,

                    int(
                        available_height / 6
                    )
                )
            )


            for week in month_days:

                row = ft.Row(

                    controls=[],

                    expand=True,

                    spacing=0
                )


                for day in week:

                    if day == 0:

                        cell = ft.Container(

                            expand=True,

                            height=cell_height,

                            bgcolor=PAGE_COLOR
                        )

                    else:

                        date_string = (

                            f"{day:02d}."

                            f"{month:02d}."

                            f"{year}"
                        )

                        event = calendar_data.get(
                            date_string
                        )

                        cell_controls = [

                            ft.Text(

                                str(day),

                                size=(
                                    14
                                    if phone
                                    else 16
                                ),

                                color=TEXT_COLOR
                            )
                        ]


                        if event:

                            if event.get("event"):

                                cell_controls.append(

                                    ft.Text(

                                        event[
                                            "event"
                                        ],

                                        size=(
                                            10
                                            if phone
                                            else 13
                                        ),

                                        color=TEXT_COLOR,

                                        max_lines=(
                                            2
                                            if phone
                                            else 1
                                        ),

                                        overflow=(
                                            ft.TextOverflow
                                            .ELLIPSIS
                                        ),

                                        text_align=(
                                            ft.TextAlign.CENTER
                                        )
                                    )
                                )


                            if event.get("photo"):

                                cell_controls.append(

                                    ft.Image(

                                        src=event[
                                            "photo"
                                        ],

                                        width=(
                                            55
                                            if phone
                                            else 80
                                        ),

                                        height=(
                                            32
                                            if phone
                                            else 50
                                        ),

                                        fit=ft.BoxFit.COVER
                                    )
                                )


                        cell = ft.Container(

                            expand=True,

                            height=cell_height,

                            bgcolor=PAGE_COLOR,

                            border=ft.Border.all(

                                1,

                                TEXT_COLOR
                            ),

                            padding=4,

                            on_click=lambda e,

                            d=day:

                                open_date(
                                    d
                                ),

                            content=ft.Column(

                                controls=cell_controls,

                                spacing=3,

                                horizontal_alignment=(

                                    ft.CrossAxisAlignment
                                    .CENTER
                                )
                            )
                        )


                    row.controls.append(
                        cell
                    )


                calendar_rows.append(
                    row
                )


            # =============================================
            # ВЫВОД
            # =============================================

            content.content = ft.Container(

                expand=True,

                bgcolor=PAGE_COLOR,

                padding=(

                    4

                    if phone

                    else 12
                ),

                content=ft.Column(

                    controls=[

                        ft.Row(

                            controls=[

                                ft.IconButton(

                                    icon=(
                                        ft.Icons
                                        .CHEVRON_LEFT
                                    ),

                                    icon_color=TEXT_COLOR,

                                    on_click=(
                                        previous_month
                                    ),

                                    style=ft.ButtonStyle(

                                        color=TEXT_COLOR,

                                        bgcolor=PAGE_COLOR
                                    )
                                ),

                                ft.Container(

                                    expand=True,

                                    alignment=(
                                        ft.Alignment.CENTER
                                    ),

                                    content=ft.Text(

                                        (
                                            f"{month_names[month - 1]} "
                                            f"{year}"
                                        ),

                                        size=(
                                            21
                                            if phone
                                            else 25
                                        ),

                                        weight=(
                                            ft.FontWeight.BOLD
                                        ),

                                        color=TEXT_COLOR
                                    )
                                ),

                                ft.IconButton(

                                    icon=(
                                        ft.Icons
                                        .CHEVRON_RIGHT
                                    ),

                                    icon_color=TEXT_COLOR,

                                    on_click=(
                                        next_month
                                    ),

                                    style=ft.ButtonStyle(

                                        color=TEXT_COLOR,

                                        bgcolor=PAGE_COLOR
                                    )
                                ),

                                ft.IconButton(

                                    icon=ft.Icons.ADD,

                                    icon_color=TEXT_COLOR,

                                    on_click=create_event,

                                    style=ft.ButtonStyle(

                                        color=TEXT_COLOR,

                                        bgcolor=PAGE_COLOR
                                    )
                                )
                            ],

                            spacing=0
                        ),

                        week_days,

                        *calendar_rows
                    ],

                    expand=True,

                    spacing=0
                )
            )

            make_navigation()

            page.update()


        build_calendar()


    # =====================================================
    # ИЗМЕНЕНИЕ РАЗМЕРА / ПОВОРОТ ЭКРАНА
    # =====================================================

    last_size = {
        "width": None,
        "height": None
    }


    def page_resized(e):

        width = page.width

        height = page.height

        if (

            last_size["width"] == width

            and last_size["height"] == height
        ):

            return

        last_size["width"] = width

        last_size["height"] = height


        if active_page == "home":

            home()

        elif active_page == "attendance":

            attendance()

        elif active_page == "calendar":

            calendar()


    page.on_resize = page_resized


    # =====================================================
    # ЗАПУСК
    # =====================================================

    page.add(
        root
    )

    make_navigation()

    home()


    # =====================================================
    # ЧАСЫ
    # =====================================================

    async def update_clock():

        while True:

            try:

                clock.value = (
                    datetime.now().strftime(
                        "%H:%M"
                    )
                )

                page.update()

            except RuntimeError:

                break

            await asyncio.sleep(1)


    page.run_task(
        update_clock
    )


ft.app(
    target=main
)