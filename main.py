from LLM import *

import subprocess
import flet as ft
import time
import threading
import ctypes
import atexit
from functools import partial


# Перевірка, чи встановлена програма Ollama
def is_ollama_installed():
    try:
        # Перевіряємо наявність команди ollama
        result = subprocess.run(["ollama", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


# Отримуємо список доступних моделей
def get_installed_models():
    try:
        result = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            models = [line.strip() for line in result.stdout.split("\n") if line.strip()]
            return models
        else:
            print("Error getting models:", result.stderr)
            return []
    except FileNotFoundError:
        return []


def main(page: ft.Page):
    # --- functions ---
    # change height of input feeld
    def adjust_height(e):

        if page.width >= history_container.width + 15 + 800:
            width = 800
        else:
            width = page.width - history_container.width - 15

        text = txt_input.value
        num_lines = txt_input.value.count("\n") + 1

        chars_per_line = max(int(width // (txt_input.text_size * 0.5)), 1)  # txt_input.text_size = 16
        approx_lines = max(num_lines, (len(text) // chars_per_line) + 1)
        total_lines = min(approx_lines, 3)

        txt_input.height = min(40 + (total_lines - 1) * 30, 100)  # Максимум 3 рядки
        txt_input_container.height = min(40 + (total_lines - 1) * 30, 100)
        input_txt_container.height = txt_input.height + 10  # Оновлюємо контейнер
        input_container.height = txt_input.height + 10  # Оновлюємо контейнер
        page.update()

    def handle_resize(e):
        # change the height of input feeld
        adjust_height(e)
        # close and open nav bar
        if page.window_width < 800 and history_container.width > 50:
            toggle_sidebar("close")
        elif page.window_width >= 800 and history_container.width == 50:
            toggle_sidebar("open")

    # Логіка відкриття/закриття sidebar
    def toggle_sidebar(action):
        if action == "close":
            # settings_button.visible = False
            settings_button.text = ""
            chats_column.visible = False
            line.visible = False
            name_container.visible = False
            # search_chat_button.visible = False
            # new_chat_button.visible = False
            new_chat_button.text = ""
            search_chat_button.text = ""
            animate_sidebar(200, 50)
            logo_container.visible = False
            close_button.visible = False
            open_button.visible = True
        elif action == "open":
            animate_sidebar(50, 200)

            # settings_button.visible = True
            settings_button.text = "Settings"
            chats_column.visible = True
            line.visible = True
            # search_chat_button.visible = True
            # new_chat_button.visible = True
            new_chat_button.text = "Search"
            search_chat_button.text = "New Chat"
            logo_container.visible = True
            close_button.visible = True
            open_button.visible = False
            name_container.visible = True


        history_container.update()

    # Функція анімації зміни ширини
    def animate_sidebar(start_width, end_width, step=10, delay=0.01):
        current_width = start_width
        while current_width != end_width:
            if start_width < end_width:
                current_width += step
                if current_width > end_width:
                    current_width = end_width
            else:
                current_width -= step
                if current_width < end_width:
                    current_width = end_width

            history_container.width = current_width
            history_container.update()
            time.sleep(delay)

    # Отримуємо розміри екрану
    user32 = ctypes.windll.user32

    # --- page settings ----
    page.window_width = 1200
    page.window_height = 650
    page.padding=0
    page.window_min_width = 500
    page.window_min_height = 500
    page.window_resizable = True  # Дозволяємо змінювати розмір вікна
    page.window_maximized = False  # Не максимізуємо вікно при запуску
    page.bgcolor = "#212121"

    # Обчислюємо позицію для центрування вікна
    page.window_left = (user32.GetSystemMetrics(0) - page.window_width) // 2
    page.window_top = (user32.GetSystemMetrics(1) - page.window_height) // 2

    #page.favicon = "img/logo_beta.png"
    page.title = "Local AI Assistant"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.MainAxisAlignment.START
    page.on_resize = handle_resize


    # *** Chat side ***
    # --- header ----
    def dropdown_changed(e):
        """Обробник події зміни вибору у Dropdown"""
        print(f"Вибрано: {model_chose_dropdown.value}")  # Отримуємо вибране значення

    def on_hover(e):
        """Функція зміни кольору при наведенні миші"""
        if e.data == "true":  # Якщо миша над елементом
            dropdown_container.bgcolor = ft.colors.GREY_900  # Темно-сірий фон при наведенні
        else:
            dropdown_container.bgcolor = ft.colors.TRANSPARENT  # Прозорий фон у звичайному стані
        dropdown_container.update()

    model_chose_dropdown = ft.Dropdown(
        label="",
        value="option1",  # Вибір за замовчуванням
        options=[
            ft.dropdown.Option("option1", text="Option 1"),
            ft.dropdown.Option("option2", text="Option 2"),
            ft.dropdown.Option("option3", text="Option 3"),
        ],
        on_change=dropdown_changed,
        width=200,  # Ширина Dropdown
        border_radius=10,  # Закруглені краї
        border_color="transparent",  # Приховуємо рамку
        text_style=ft.TextStyle(
            size=16,
            color=ft.colors.GREY_500,  # Сірий колір тексту
        ),
    )

    dropdown_container = ft.Container(
        content=model_chose_dropdown,
        padding=0,
        border_radius=20,
        bgcolor=ft.colors.TRANSPARENT,  # Початковий колір фону
        on_hover=on_hover,  # Виклик функції при наведенні миші
    )

    header_row = ft.Row(
        controls=[
            dropdown_container,
            ft.Container(width=30, height=30, bgcolor="blue"),
            ft.Container(width=30, height=30, bgcolor="green"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Проміжки навколо кожного елемента
        height=50,
    )
    header_container = ft.Container(
        content=header_row,
        height=50,
        padding=ft.Padding(5, 3, 5, 3),
        border_radius=10,
        bgcolor="#171717",
        alignment=ft.alignment.center,
    )

    # --- chat ---
    chat_column = ft.Column(
        controls=[
            ft.Container(width=30, height=30, bgcolor="red"),
            ft.Container(width=30, height=30, bgcolor="blue"),
            ft.Container(width=30, height=30, bgcolor="green"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Проміжки навколо кожного елемента
    )
    chat_container = ft.Container(
        content=chat_column,
        expand=True,
        padding=10,
        border_radius=10,
        bgcolor="#212121",
        alignment=ft.alignment.center,
    )

    # --- input ---
    txt_input = ft.TextField(
        text_align=ft.TextAlign.LEFT,
        filled=False,
        bgcolor="#101218",
        color="white",
        text_size=16,
        expand=True,
        border=ft.InputBorder.NONE,
        focused_bgcolor="#101218",
        focused_border_color=None,
        cursor_color="white",
        border_radius=20,
        hint_text="Type something...",
        hint_style=ft.TextStyle(
            color="gray",
            size=16,
        ),
        multiline=True,  # Дозволяємо кілька рядків
        max_lines=3,  # Обмежуємо 3 рядками
        height=40,  # Початкова висота
        on_change=adjust_height,  # Автоматично змінюємо висоту при зміні тексту
    )
    txt_input_container = ft.Container(
        content=txt_input,
        height=40,  # Початкова висота
        border_radius=20,
        padding=ft.Padding(10, -5, 5, 5),
        bgcolor="#101218",
        expand=True,
        alignment=ft.alignment.center_left,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,  # Забезпечує обрізання тексту за межами
    )
    send_text_button = ft.ElevatedButton(
        icon=ft.icons.ARROW_UPWARD,
        icon_color=ft.colors.BLACK,
        text="Send",
        width=31,
        height=30,
        bgcolor="white",
        style=ft.ButtonStyle(
            padding=4,
            alignment=ft.alignment.center
        ),
        on_click=lambda e: print("Send clicked"),
    )
    send_text_button_container = ft.Container(
        content=send_text_button,
        alignment=ft.alignment.center,
        padding=ft.Padding(0, 0, 0, 0),
    )

    input_row = ft.Row(
        controls=[
            txt_input_container,  # Обгорнутий input
            send_text_button_container
        ],
        alignment=ft.MainAxisAlignment.END,
        vertical_alignment=ft.CrossAxisAlignment.END,
        expand=True,
    )

    input_txt_container = ft.Container(
        content=input_row,
        padding=ft.Padding(5, 5, 5, 5),
        border_radius=20,
        height=40,  # Початкова висота
        bgcolor="#101218",
        alignment=ft.alignment.center,
        expand=True,
        width=800,
    )
    input_txt_container.scroll = ft.ScrollMode.AUTO

    input_container = ft.Container(
        content=input_txt_container,
        padding=5,
        border_radius=10,
        height=50,
        bgcolor="#212121",
        alignment=ft.alignment.center,
    )



    # --- input fild ---

    # *** Nav bar side ***
    # --- Logo and close ---
    logo_container = ft.Container(
        width=30,
        height=30,
        border_radius=30,
        content=ft.Image(
            src="img/logo_beta.png",  # URL або локальний шлях
            fit=ft.ImageFit.CONTAIN  # Налаштування масштабування зображення
        ),
    )

    close_button = ft.ElevatedButton(
        icon=ft.icons.CLOSE,
        icon_color=ft.colors.GREY,
        text="Close",
        width=30,
        height=30,
        bgcolor="black",
        style=ft.ButtonStyle(
            padding=3,
            alignment=ft.alignment.center  # Центрування вмісту
        ),
        on_click=lambda e: toggle_sidebar("close")
    )

    open_button = ft.ElevatedButton(
        icon=ft.icons.MENU,
        icon_color=ft.colors.WHITE,
        text="Open",
        width=30,
        height=30,
        bgcolor="black",
        visible=False,
        style=ft.ButtonStyle(
            padding=3,
            alignment=ft.alignment.center  # Центрування вмісту
        ),
        on_click=lambda e: toggle_sidebar("open")
    )

    history_hed_row = ft.Row(
        controls=[
            logo_container,
            close_button,
            open_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Проміжки навколо кожного елемента
        width=200
    )

    name_container = ft.Container(  #
        content=ft.Text(
            "AI Local Assistant",
            color="white",
            size=18,
        ),
        bgcolor="transparent",
        alignment=ft.alignment.center_left,
        padding=ft.Padding(0, 5, 0, 5),
    )
    new_chat_button = ft.TextButton(
        icon=ft.icons.ADD_BOX,
        icon_color=ft.colors.WHITE,
        text="New Chat",
        style=ft.ButtonStyle(
            padding=ft.Padding(3, 5, 5, 5),
            alignment=ft.alignment.center_left,  # Центрування вмісту
            color=ft.colors.WHITE,
            text_style=ft.TextStyle(  # Налаштування шрифту
                size=16,
                weight=ft.FontWeight.NORMAL,
            ),
        ),
        on_click=lambda e: print("new chat")
    )
    search_chat_button = ft.TextButton(
        icon=ft.icons.SEARCH,
        icon_color=ft.colors.WHITE,
        text="Search",
        style=ft.ButtonStyle(
            padding=ft.Padding(3, 5, 5, 5),
            alignment=ft.alignment.center_left,  # Центрування вмісту
            color=ft.colors.WHITE,
            text_style=ft.TextStyle(  # Налаштування шрифту
                size=16,
                weight=ft.FontWeight.NORMAL,
            ),
        ),
        on_click=lambda e: print("search chat")
    )
    settings_button = ft.TextButton(
        icon=ft.icons.SETTINGS,
        icon_color=ft.colors.WHITE,
        text="Settings",
        style=ft.ButtonStyle(
            padding=ft.Padding(3, 5, 5, 5),
            color=ft.colors.WHITE,
            alignment=ft.alignment.center_left,  # Центрування вмісту
            text_style=ft.TextStyle(
                size=16,
                weight=ft.FontWeight.NORMAL,
            ),
        ),
        on_click=lambda e: print("settings")
    )

    line = ft.Divider(color="gray", thickness=1)

    chats_column = ft.Column(
        controls=[
            ft.Container(width=30, height=30, bgcolor="red"),
            ft.Container(width=30, height=30, bgcolor="blue"),
            ft.Container(width=30, height=30, bgcolor="green"),
        ],
        alignment=ft.MainAxisAlignment.START,  # Проміжки навколо кожного елемента
    )
    chats_container = ft.Container(
        content=chats_column,
        expand=True,
        padding=10,
        border_radius=10,
        bgcolor="black",
        alignment=ft.alignment.center,
    )

    history_column = ft.Column(
        controls=[
            history_hed_row,
            name_container,
            new_chat_button,
            search_chat_button,
            line,
            chats_container,
            settings_button
        ],
        alignment=ft.MainAxisAlignment.START,  # Проміжки навколо кожного елемента
        width=200
    )
    history_container = ft.Container(
        content=history_column,
        padding=10,
        border_radius=10,
        expand=True,
        width=200,
        bgcolor="black",
        alignment=ft.alignment.center,
    )
    # --- page settings ----
    page.add(
        ft.Row(
            [
                ft.Column(
                    [
                        history_container
                    ],
                ),
                ft.Column(
                    [
                        header_container,
                        chat_container,
                        input_container
                    ],
                    expand=True,
                    spacing=0,
                )
            ],
            expand=True,
            spacing=10,
        )
    )

if __name__ == "__main__":
    try:
        ft.app(target=main, assets_dir="assets", view=ft.FLET_APP)
    except Exception as e:
        print(f"Error with page: {e}")


