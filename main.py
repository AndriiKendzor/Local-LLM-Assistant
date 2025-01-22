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
            return []
        else:
            print("Error getting models:", result.stderr)
            return []
    except FileNotFoundError:
        return []


def main(page: ft.Page):
    # Отримуємо розміри екрану
    user32 = ctypes.windll.user32

    def on_resize(e):
        output_column.width = page.window_width  # Оновлюємо ширину колонки
        output_column.update()  # Оновлюємо контейнер

    # --- page settings ----
    page.window_width = 800
    page.window_height = 650
    page.window_resizable = False  # Дозволяємо змінювати розмір вікна
    page.window_maximized = False  # Не максимізуємо вікно при запуску
    page.bgcolor = "black"

    # Обчислюємо позицію для центрування вікна
    page.window_left = (user32.GetSystemMetrics(0) - page.window_width) // 2
    page.window_top = (user32.GetSystemMetrics(1) - page.window_height) // 2

    page.window_icon = "img/only_logo_resized.ico"
    page.title = "Local AI Assistant"
    page.vertical_alignment = ft.MainAxisAlignment.END
    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.on_resize = on_resize

    # --- show error massage ---
    def show_temporary_message(page, message, color="red", duration=3):
        # Контейнер із повідомленням
        error_message_container = ft.Container(
            content=ft.Text(message, color=color, size=16),
            padding=10,
            bgcolor="#C0C0C0",
            border_radius=10,
            width=400,
            height=50,
            alignment=ft.alignment.center,
            opacity=0,  # Початкова прозорість
        )

        # Позиціювання контейнера поверх усіх елементів
        overlay_container = ft.Stack(
            [
                error_message_container
            ],
            expand=True,
            alignment=ft.alignment.top_center
        )
        # Додаємо контейнер на сторінку
        send_button.disabled = True
        send_button.update()
        txt_input.disabled = True
        txt_input.update()
        page.overlay.append(overlay_container)
        page.update()

        # Налаштування відступу для повідомлення
        def position_message():
            error_message_container.margin = ft.Margin(50, 50, 50, 50)  # Відступ зверху: 50px
            error_message_container.update()

        # Функція для анімації показу і видалення повідомлення
        def animate_message():
            position_message()  # Додаємо відступ
            # Плавне з'явлення
            for i in range(1, 11):  # Анімація в 10 кроків
                error_message_container.opacity = i / 10
                error_message_container.update()
                time.sleep(0.05)

        # Запускаємо анімацію у фоновому потоці
        threading.Thread(target=animate_message, daemon=True).start()

    # --- chose AI model ---
    def dropdown_changed(dropdown):
        if not is_ollama_installed():
            show_temporary_message(page, "Ollama is not installed on your computer.")
            return None

        models = get_installed_models()
        if not models:
            show_temporary_message(page, "No models found on Ollama.")
            return None

        dropdown.options = [ft.dropdown.Option(model) for model in models]
        # Якщо список опцій порожній
        if len(dropdown.options) == 0:
            dropdown.label = "No model selected"  # Змінюємо текст у полі
            dropdown.value = None  # Знімаємо вибір
        else:
            # Встановлюємо першу опцію, якщо нічого не вибрано
            if not dropdown.value:
                dropdown.value = dropdown.options[0].key
            dropdown.label = ""  # Оновлюємо текст у полі
            print(dropdown.value)
        dropdown.update()  # Оновлюємо вигляд Dropdown

    # Ініціалізація Dropdown
    select_model = ft.Dropdown(
        options=[],
        on_change=lambda e: dropdown_changed(e.control),
        label="No model selected",
        value=None,  # Початково немає вибору
        width=200,
        bgcolor="#101010",
        border_radius=10,
    )

    # --- header ----
    header = ft.Container(
        content=select_model,
        height=50,
        bgcolor="black",
        border_radius=10,
    )

    # --- column for massages ----
    output_column = ft.Column(
        expand=True,
        spacing=10,
        alignment=ft.MainAxisAlignment.END,
        auto_scroll=True,
        width=page.window_width
    )
    output_column.scroll = ft.ScrollMode.AUTO

    # --- container to enable scroll to last massage ----
    chat_container = ft.Container(
        content=output_column,
        bgcolor="#000011",
        padding=10,
        border_radius=10,
        expand=True,
    )

    # --- text input feeld ---
    txt_input = ft.TextField(
        text_align=ft.TextAlign.LEFT,
        expand=1,
        height=50,
        bgcolor="#101010",
        border_color="#101010",
        border_width=2,
        border_radius=20,
        width=page.window_width * 0.85
    )

    def create_massage(text):
        # Створюємо контейнер із текстом
        text_width = min(10 * len(text) + 20, 560)
        message_container = ft.Container(
            content=ft.Text(
                text,
                color="white",
                width=page.window_width * 0.7,
                selectable=True,
                max_lines=None,  # Дозволяє необмежену кількість рядків
                no_wrap=False,  # Дозволяє перенесення тексту
            ),
            bgcolor="#202020",
            padding=10,
            border_radius=10,
            width=text_width,
            alignment=ft.alignment.center_right,
        )
        return message_container

    # --- send button ---
    send_button = ft.Container(
        content=ft.Icon(name=ft.Icons.SEND, color="white", size=20),
        width=50,
        height=50,
        bgcolor="black",
        border=ft.border.all(1, "white"),
        border_radius=50,
        alignment=ft.alignment.Alignment(0, 0),
    )

    # Функція для ховер-ефекту
    def btn_on_hover(e):
        if e.data == "true":
            send_button.bgcolor = "#303030"
        else:
            send_button.bgcolor = "black"
        send_button.update()
    # Додаємо ховер-ефект, click
    send_button.on_hover = btn_on_hover

    def btn_on_click(e):
        # Отримуємо текст із текстового поля
        text = txt_input.value.strip()
        if text:  # Якщо текст не порожній

            send_button.disabled = True
            send_button.update()
            txt_input.value = "Creating response"  # Очищаємо текстове поле
            txt_input.disabled = True
            txt_input.update()

            user_message_container = create_massage(f"You:\n{text}")
            output_column.controls.append(
                ft.Row(
                    [user_message_container],
                    alignment=ft.MainAxisAlignment.END,  # Вирівнювання контейнера справа
                    vertical_alignment=ft.CrossAxisAlignment.END
                )
            )
            output_column.update()


            llm_text = call_llm(text)
            llm_massage_container = create_massage(f"LLM:\n{llm_text}")
            output_column.controls.append(
                ft.Row(
                    [llm_massage_container],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.END
                )
            )
            output_column.update()

            txt_input.value = ""
            txt_input.disabled = False
            txt_input.update()
            send_button.disabled = False
            send_button.update()

    send_button.on_click = btn_on_click
    txt_input.on_submit = btn_on_click

    # --- page settings ----
    page.add(
        header,
        chat_container,
        ft.Row(
            [
                txt_input,
                send_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    )
    # update dropdown menu with models
    dropdown_changed(select_model)


if __name__ == "__main__":
    try:
        ft.app(target=main, view=ft.FLET_APP)
    except Exception as e:
        print(f"Error with page: {e}")


