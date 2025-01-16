from LLM import *
import flet as ft
import time
import ctypes



def main(page: ft.Page):
    # Отримуємо розміри екрану
    user32 = ctypes.windll.user32
    # --- page settings ----
    page.window_width = 800
    page.window_height = 600
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

    # --- column for massages ----
    output_column = ft.Column(
        width=page.window_width,
        expand=True,
        spacing=10,
        alignment=ft.MainAxisAlignment.END,
        auto_scroll=True,
    )
    output_column.scroll = ft.ScrollMode.AUTO

    # --- container to enable scroll to last massage ----
    scrollable_container = ft.Container(
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
        text_width = min(10 * len(text) + 20, page.window_width * 0.7)
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
        scrollable_container,
        ft.Row(
            [
                txt_input,
                send_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.FLET_APP)