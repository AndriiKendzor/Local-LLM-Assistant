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
    def handle_resize(e):
        if page.window_width < 800 and history_container.width > 50:
            toggle_sidebar("close")
        elif page.window_width >= 800 and history_container.width == 50:
            toggle_sidebar("open")
    # Логіка відкриття/закриття sidebar
    def toggle_sidebar(action):
        if action == "close":
            settings_button.visible = False
            chats_container.visible = False
            line.visible = False
            name_container.visible = False
            search_chat_button.visible = False
            new_chat_button.visible = False
            animate_sidebar(200, 50)
            logo_container.visible = False
            close_button.visible = False
            open_button.visible = True
        elif action == "open":
            animate_sidebar(50, 200)

            settings_button.visible = True
            chats_container.visible = True
            line.visible = True
            search_chat_button.visible = True
            new_chat_button.visible = True
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
    header_row = ft.Row(
        controls=[
            ft.Container(width=30, height=30, bgcolor="red"),
            ft.Container(width=30, height=30, bgcolor="blue"),
            ft.Container(width=30, height=30, bgcolor="green"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Проміжки навколо кожного елемента
        height=50,
    )
    header_container = ft.Container(
        content=header_row,
        height=50,
        padding=10,
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
        height=30,
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
    )

    input_row = ft.Row(
        controls=[
            txt_input,
        ],
        alignment=ft.MainAxisAlignment.START,  # Проміжки навколо кожного елемента
        expand=True,
    )
    input_txt_container = ft.Container(
        content=input_row,
        padding=ft.Padding(10, -5, 10, 5),
        border_radius=20,
        height=40,
        bgcolor="#101218",
        alignment=ft.alignment.center,
        expand=True,
        width=800,
    )

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
    new_chat_button = ft.ElevatedButton(
        icon=ft.icons.ADD_BOX,
        icon_color=ft.colors.WHITE,
        text="New Chat",
        bgcolor="black",
        style=ft.ButtonStyle(
            padding=ft.Padding(5, 5, 5, 5),
            alignment=ft.alignment.center_left,  # Центрування вмісту
            text_style=ft.TextStyle(  # Налаштування шрифту
                size=16,
                weight=ft.FontWeight.NORMAL,
                color="white"
            ),
        ),
        on_click=lambda e: print("new chat")
    )
    search_chat_button = ft.ElevatedButton(
        icon=ft.icons.SEARCH,
        icon_color=ft.colors.WHITE,
        text="Search",
        bgcolor="black",
        style=ft.ButtonStyle(
            padding=ft.Padding(5, 5, 5, 5),
            alignment=ft.alignment.center_left,  # Центрування вмісту
            text_style=ft.TextStyle(  # Налаштування шрифту
                size=16,
                weight=ft.FontWeight.NORMAL,
                color="white"
            ),
        ),
        on_click=lambda e: print("search chat")
    )
    settings_button = ft.ElevatedButton(
        icon=ft.icons.SETTINGS,
        icon_color=ft.colors.WHITE,
        text="Settings",
        bgcolor="black",
        style=ft.ButtonStyle(
            padding=ft.Padding(5, 5, 5, 5),
            alignment=ft.alignment.center_left,  # Центрування вмісту
            text_style=ft.TextStyle(  # Налаштування шрифту
                size=16,
                weight=ft.FontWeight.NORMAL,
                color="white"
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


