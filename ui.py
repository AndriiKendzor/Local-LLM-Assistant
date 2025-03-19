import flet as ft
import time
import pyperclip  # Бібліотека для роботи з буфером обміну
import ctypes
import threading
from db import save_conversation
from langchain_ollama import OllamaLLM
from llm import call_llm, is_ollama_installed, get_models
from import_embedding import load_documents, create_chromadb_collection, split_text, get_embedding

dialog = None


def build_ui(page, context, model_list, llm_model, stop_response, model, prompt, chain, knowlage_base_added, chat_id, collection):
    # check if ollama is installed
    ollama_installed = is_ollama_installed()
    available_models = get_models()

    # Якщо Ollama не встановлено або немає моделей, показуємо повідомлення про помилку
    if not ollama_installed or not available_models:
        error_message = "Ollama is not installed on your system."
        if ollama_installed:
            error_message = "No models are available. Please download a model using Ollama."

        # Створюємо вікно з повідомленням про помилку
        error_dialog = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Error",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.RED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        error_message,
                        size=18,
                        color=ft.colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Please install Ollama and download at least one model to use this application.",
                        size=16,
                        color=ft.colors.GREY_400,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.TextButton(
                        text="Visit Ollama Website",
                        icon=ft.icons.LINK,
                        icon_color=ft.colors.BLUE,
                        on_click=lambda e: page.launch_url("https://ollama.ai/"),
                        style=ft.ButtonStyle(color=ft.colors.BLUE),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            bgcolor=ft.colors.GREY_900,
            padding=20,
            border_radius=10,
            width=400,
            height=300,
            alignment=ft.alignment.center,
        )

        # Відображаємо лише вікно з помилкою
        page.add(
            ft.Container(
                content=error_dialog,
                alignment=ft.alignment.center,
                expand=True,
                bgcolor="#212121",
            )
        )
        # Повертаємо незмінені значення, оскільки інтерфейс недоступний
        return context, model_list, llm_model, stop_response, model, prompt, chain

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
        if page.window_width < 840 and history_container.width > 50:
            toggle_sidebar("close")
        elif page.window_width >= 840 and history_container.width == 50:
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
            new_chat_button.text = "New Chat"
            search_chat_button.text = "Search"
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

    def create_buttons(llm_response, user_text):
        def toggle_heart(e):
            """Перемикає іконку сердечка"""
            heart_button.icon = ft.icons.FAVORITE if heart_button.icon == ft.icons.FAVORITE_BORDER else ft.icons.FAVORITE
            heart_button.update()

        def copy_text(e):
            pyperclip.copy(llm_response)  # Копіюємо текст у буфер обміну
            copy_button.icon = ft.icons.CHECK
            copy_button.update()
            time.sleep(0.5)
            copy_button.icon = ft.icons.CONTENT_COPY
            copy_button.update()

        def generate_again(e):
            if len(chat_column.controls) >= 2:
                del chat_column.controls[-2:]
            chat_column.update()
            create_massage(f"Just answer different way: {user_text} and ignore this: </>")


        # Кнопка "сердечко" (заповнене/порожнє)
        heart_button = ft.IconButton(
            icon=ft.icons.FAVORITE_BORDER,  # Початкове значення: пусте сердечко
            icon_color=ft.colors.GREY_500,
            icon_size=13,
            width=20,
            height=20,
            padding=0,
            on_click=toggle_heart
        )

        # Кнопка "копіювати"
        copy_button = ft.IconButton(
            icon=ft.icons.CONTENT_COPY,  # Іконка копіювання
            icon_color=ft.colors.GREY_500,
            icon_size=13,
            width=20,
            height=20,
            padding=0,
            on_click=copy_text
        )

        # Кнопка "генерувати ще раз"
        regenerate_button = ft.IconButton(
            icon=ft.icons.REPLAY,  # Іконка повторного генератора
            icon_color=ft.colors.GREY_500,
            icon_size=13,
            width=20,
            height=20,
            padding=0,
            on_click=generate_again
        )

        llm_model_info = ft.Container(
            content=ft.Text(
                model_chose_dropdown.value,
                color=ft.colors.GREY_500,
                size=13,
            ),
            height=20,
            padding=0,
        )

        # Рядок з кнопками
        buttons_row = ft.Row(
            [
                heart_button,
                copy_button,
                regenerate_button,
                llm_model_info
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        button_row_cont = ft.Container(
            content=buttons_row,
            padding=ft.Padding(50, -5, 0, 0)
        )

        return button_row_cont

    def wait_animation(text_cont, stop_flag, word):
        symbols = ["|", "/", "-", r"\\"]
        idx = 0
        text_cont.value = f"{word}..."
        text_cont.update()
        while not stop_flag["stop"]:
            text_cont.value = f"{word}... {symbols[idx]}"
            text_cont.update()
            idx = (idx + 1) % len(symbols)
            time.sleep(0.2)
        text_cont.value = ""
        text_cont.update()


    def create_massage(text):

        nonlocal stop_response, context, llm_model, chain

        text = text.strip()
        if text != "":
            # stopping func
            if txt_input.value == "Creating response":
                stop_response = True
                time.sleep(0.1)
                stop_response = False
                return

            send_text_button.icon = ft.icons.STOP
            send_text_button.update()
            txt_input.value = "Creating response"
            txt_input.disabled = True
            adjust_height(None)
            txt_input.update()

            # creating user massage
            text_width = min(10 * len(text) + 20, 560)

            user_massage = ft.Container(
                alignment=ft.alignment.center_right,
                content=ft.Text(
                    text,
                    color="#E0E0E0",
                    size=16,
                    width=page.window_width * 0.7,
                    selectable=True,
                    max_lines=None,
                    no_wrap=False,
                ),
                padding=10,
                border_radius=10,
                bgcolor="#2F2F2F",
                width=text_width
            )
            if "</>" not in text:
                chat_column.controls.append(
                    ft.Row(
                        [user_massage],
                        alignment=ft.MainAxisAlignment.END,  # Вирівнювання контейнера справа
                        vertical_alignment=ft.CrossAxisAlignment.END
                    )
                )
                chat_column.update()

            llm_mrkd_style = ft.MarkdownStyleSheet(
                p_text_style=ft.TextStyle(size=16, color="white"),  # Стиль для параграфів
                h1_text_style=ft.TextStyle(size=32, color="white", weight=ft.FontWeight.BOLD),  # Заголовок 1
                h2_text_style=ft.TextStyle(size=28, color="white", weight=ft.FontWeight.W_600), # Заголовок 2
                h3_text_style=ft.TextStyle(size=24, color="white", weight=ft.FontWeight.W_500), # Заголовок 3
                code_text_style=ft.TextStyle(font_family="Courier New", size=14, color="lime"), # Стиль для коду
                a_text_style=ft.TextStyle(color="cyan", decoration=ft.TextDecoration.UNDERLINE), # Стиль для посилань
                strong_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),  # Жирний текст
                em_text_style=ft.TextStyle(italic=True),  # Курсивний текст
            )

            llm_text = ft.Markdown(
                "",
                selectable=True,
                width=page.window_width * 0.7,
                extension_set="gitHubWeb",
                code_theme="atom-one-dark",
                on_tap_link=lambda e: page.launch_url(e.data),
                md_style_sheet=llm_mrkd_style,
            )

            llm_response_cont = ft.Container(
                alignment=ft.alignment.center_left,
                content=llm_text,
                padding=10,
                border_radius=10,
                bgcolor="transparent",
                expand=True
            )

            chat_column.controls.append(
                ft.Row(
                    [
                        logo_container2,
                        llm_response_cont,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.START
                )
            )
            chat_column.update()

            # Запускаємо аніміцію очікування у синхронному режимі
            stop_flag = {"stop": False}
            animation_thread = threading.Thread(target=wait_animation, args=(llm_text, stop_flag, "Generating"))
            animation_thread.start()

            # Викликаємо LLM
            try:
                llm_response, new_context = call_llm(text, context, llm_model, chain, knowlage_base_added, collection, False)
                context = new_context  # Оновлюємо context напряму
            except Exception as e:
                llm_response = f"Some error while calling llm: \n{e}"

            # Зупиняємо аніміцію після завершення виклику LLM
            stop_flag["stop"] = True
            animation_thread.join()  # Чекаємо завершення потоку аніміції



            printed_text = ""  # copy only printed text
            for word in llm_response:
                if stop_response:
                    break
                llm_text.value += word + " ⚪"
                llm_response_cont.update()
                time.sleep(0.01)
                llm_text.value = llm_text.value.replace(" ⚪", "")
                llm_response_cont.update()
                chat_column.update()
                printed_text += word

            buttons_row = create_buttons(printed_text, text)

            chat_column.controls.append(
                buttons_row
            )
            chat_column.update()

            txt_input.value = ""
            txt_input.disabled = False
            txt_input.update()
            send_text_button.icon = ft.icons.ARROW_UPWARD
            send_text_button.update()

            save_conversation(chat_id, context, knowlage_base_added, llm_model, chain, collection, llm_response, text, chat_name_container)

            return stop_response, context, llm_model, chain



    def create_history_element(title, date):
        pass

    # Отримуємо розміри екрану
    user32 = ctypes.windll.user32

    # --- page settings ----
    page.window_width = 1200
    page.window_height = 650
    page.padding=0
    page.window_min_width = 690
    page.window_min_height = 650
    page.window_resizable = True  # Дозволяємо змінювати розмір вікна
    page.window_maximized = False  # Не максимізуємо вікно при запуску
    page.bgcolor = "#212121"
    #page.favicon = "icons/icon-192.png"
    #page.window_icon = "icons/logo_beta.ico"

    # Обчислюємо позицію для центрування вікна
    page.window_left = (user32.GetSystemMetrics(0) - page.window_width) // 2
    page.window_top = (user32.GetSystemMetrics(1) - page.window_height) // 2

    page.title = "AI Local Assistant"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.MainAxisAlignment.START
    page.on_resize = handle_resize

    # page.theme = ft.Theme(
    #     text_theme=ft.TextTheme(body_medium=ft.TextStyle(size=16, color="white"))
    # )

    # *** Chat side ***
    # --- header ----
    def dropdown_changed(e):
        nonlocal llm_model, model, chain
        """Обробник події зміни вибору у Dropdown"""
        llm_model = model_chose_dropdown.value

        model = OllamaLLM(model=llm_model)
        chain = prompt | model
        return llm_model, model, chain

    # hover effect for dropdown
    def on_hover(e):
        if e.data == "true":
            dropdown_container.bgcolor = ft.colors.GREY_900  #
        else:
            dropdown_container.bgcolor = ft.colors.TRANSPARENT
        dropdown_container.update()

    model_chose_dropdown = ft.Dropdown(
        label="",
        value=model_list[0],  # Вибір за замовчуванням
        options=[ft.dropdown.Option(model) for model in model_list],
        on_change=dropdown_changed,
        width=200,  # Ширина Dropdown
        border_radius=10,  # Закруглені краї
        border_color="transparent",  # Приховуємо рамку
        text_style=ft.TextStyle(
            size=16,
            color=ft.colors.GREY_500,  # Сірий колір тексту
            overflow=ft.TextOverflow.ELLIPSIS,
        ),

    )

    dropdown_container = ft.Container(
        content=model_chose_dropdown,
        padding=0,
        border_radius=20,
        bgcolor=ft.colors.TRANSPARENT,  # Початковий колір фону
        on_hover=on_hover,  # Виклик функції при наведенні миші
    )

    chat_name_container = ft.Container(
        content=ft.Text(
            "New chat",
            color="white",
            size=18,
            max_lines=1,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        bgcolor="transparent",
        width=200,
        alignment=ft.alignment.center,
        padding=ft.Padding(0, 5, 0, 5),
    )

    # creating reg application
    def create_rag():
        global dialog
        # Ініціалізація змінної для шляху до папки
        directory_path = [None]  # Використовуємо список, щоб змінювати значення всередині вкладених функцій

        # Функція для вибору папки
        def pick_folder(e):
            file_picker.get_directory_path()

        # Функція для обробки результату вибору папки
        def on_folder_picked(e: ft.FilePickerResultEvent):
            nonlocal knowlage_base_added
            nonlocal chat_id

            if e.path:
                # change global wariable to get AI know that KB added
                knowlage_base_added = True
                # show path
                directory_path[0] = e.path
                files_list.controls.clear()
                files_list.controls.append(
                    ft.Text(
                        spans=[
                            ft.TextSpan("Folder:", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)),
                            ft.TextSpan(f"\n{directory_path[0]}", style=ft.TextStyle(weight=ft.FontWeight.NORMAL, size=16)),
                        ]
                    )
                )
                page.update()

                # Start scanning documents
                dialog.actions.clear()
                dialog.actions.append(waiting_text)
                page.update()
                # Запускаємо аніміцію очікування у синхронному режимі
                stop_flag = {"stop": False}
                animation_thread = threading.Thread(target=wait_animation, args=(waiting_text, stop_flag, "Scanning"))
                animation_thread.start()

                # Викликаємо LLM
                try:
                    scan_documents(chat_id, directory_path[0])
                    new_style = ft.ButtonStyle(
                        padding=5,
                        alignment=ft.alignment.center,
                        side=ft.BorderSide(1, ft.colors.GREEN),
                        color=ft.colors.GREY_500,
                        text_style=ft.TextStyle(size=16),
                        shape=ft.RoundedRectangleBorder(radius=20),
                    )
                    dialog.actions.append(close_button)
                    dialog.actions.append(chose_folder_button)
                    dialog.actions.append(clean_button)
                except Exception as e:
                    files_list.controls.append(ft.Text(f"Some error while scanning: {e}\nTry again.", size=16, color=ft.colors.RED))
                    new_style = ft.ButtonStyle(
                        padding=5,
                        alignment=ft.alignment.center,
                        side=ft.BorderSide(1, ft.colors.RED),
                        color=ft.colors.GREY_500,
                        text_style=ft.TextStyle(size=16),
                        shape=ft.RoundedRectangleBorder(radius=20),
                    )
                    dialog.actions.append(chose_folder_button)

                # Зупиняємо аніміцію після завершення виклику LLM
                stop_flag["stop"] = True
                animation_thread.join()  # Чекаємо завершення потоку аніміції

                add_knowledge_base.style = new_style
                page.update()

                return knowlage_base_added

        def scan_documents(chat_id, path):
            # create collection
            nonlocal collection
            collection = create_chromadb_collection(chat_id)
            # load documents from directory
            documents = load_documents(path, files_list, page)

            chunked_documents = []
            for doc in documents:
                chunks = split_text(doc["text"])
                print("=== Splitting docs into chunks ===")
                for i, chunk in enumerate(chunks):
                    chunked_documents.append({"id": f"{doc['id']}_chunk{i + 1}", "text": chunk})

            for doc in chunked_documents:
                print("=== Generating embeddings ===")
                doc["embedding"] = get_embedding(doc["text"])

            # inserting embeddings into vector database
            for doc in chunked_documents:
                print("=== Inserting chunks into vector db ===")
                collection.upsert(
                    ids=[doc["id"]],
                    documents=[doc["text"]],
                    embeddings=[doc["embedding"]]
                )

            return collection


        files_list = ft.Column(
            controls=[],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
        )

        # Ініціалізація FilePicker
        file_picker = ft.FilePicker(on_result=on_folder_picked)
        page.overlay.append(file_picker) # Додаємо FilePicker до сторінки

        # some controls
        waiting_text = ft.Text(
            "",
            color=ft.colors.WHITE,
            size=16,
            weight=ft.FontWeight.NORMAL,
        )
        chose_folder_button = ft.ElevatedButton(
            text="Chose folder",
            icon=ft.icons.FOLDER_OPEN,
            on_click=pick_folder,
            style=ft.ButtonStyle(
                padding=10,
                shape=ft.RoundedRectangleBorder(radius=20),
                color=ft.colors.WHITE
            ),
        )

        def close_dialog(e):
            dialog.open = False
            page.update()

        close_button = ft.ElevatedButton(
            text="Redy",
            on_click=close_dialog,
            style=ft.ButtonStyle(
                padding=10,
                shape=ft.RoundedRectangleBorder(radius=20),
                color=ft.colors.WHITE
            ),
        )

        def clean_kb(e):
            nonlocal knowlage_base_added
            global dialog
            close_dialog(e)
            new_style = ft.ButtonStyle(
                padding=5,
                alignment=ft.alignment.center,
                side=ft.BorderSide(1, ft.colors.GREY_500),
                color=ft.colors.GREY_500,
                text_style=ft.TextStyle(size=16),
                shape=ft.RoundedRectangleBorder(radius=20),
            )
            add_knowledge_base.style = new_style
            page.update()
            knowlage_base_added = False
            dialog = None
            return knowlage_base_added, dialog

        clean_button = ft.ElevatedButton(
            text="Clean KB",
            on_click=clean_kb,
            style=ft.ButtonStyle(
                padding=10,
                shape=ft.RoundedRectangleBorder(radius=20),
                color=ft.colors.WHITE
            ),
        )

        if dialog is None:
            # Створюємо діалогове вікно
            dialog = ft.AlertDialog(
                title=ft.Text(
                    "RAG Document Scanner",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                content=ft.Container(
                    content=files_list,
                    padding=10,
                    width=400,
                    height=300,
                ),
                actions=[
                    chose_folder_button,
                    waiting_text
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
                bgcolor=ft.colors.GREY_900,
            )
            page.dialog = dialog

        # Відкриваємо діалогове вікно
        dialog.open = True
        page.update()


    add_knowledge_base = ft.TextButton(
        icon=ft.icons.INSERT_DRIVE_FILE,
        icon_color=ft.colors.GREY_500,  # Іконка білого кольору
        text="Knowledge base",
        width=200,
        height=40,
        style=ft.ButtonStyle(
            padding=5,
            alignment=ft.alignment.center,
            side=ft.BorderSide(1, ft.colors.GREY_500),  # Білий бордер 1px
            color=ft.colors.GREY_500,
            text_style=ft.TextStyle(
                size=16,  # Шрифт 16px
            ),
            shape=ft.RoundedRectangleBorder(radius=20),  # Закруглені краї
        ),
        on_click=lambda e: create_rag(),
    )


    header_row = ft.Row(
        controls=[
            dropdown_container,
            chat_name_container,
            add_knowledge_base,
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
        auto_scroll=True,
        expand=True,
        width=800,
        alignment=ft.MainAxisAlignment.START,
    )
    chat_column.scroll = ft.ScrollMode.AUTO

    chat_container = ft.Container(
        content=chat_column,
        expand=True,
        padding=ft.Padding(10, 20, 10, 20),
        border_radius=10,
        bgcolor="#212121",
        alignment=ft.alignment.center,
    )

    # --- info button ---
    def show_features_dialog(e):
        # Список можливостей
        features = [
            "Chat with AI locally",
            "Switch between multiple models",
            "Process images with command:" + "\n" + r"  !img:C\path\to\your\image.png!",
            "Scan your documents using Knowledge Base",
            "Save conversation history",
        ]

        # Створюємо список із можливостей
        features_list = ft.Column(
            controls=[
                ft.Text(
                    f"• {feature}",
                    size=16,
                    color=ft.colors.WHITE,
                ) for feature in features
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        # Створюємо діалогове вікно
        dialog = ft.AlertDialog(
            title=ft.Text(
                "Features of AI Local Assistant",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            content=ft.Container(
                content=features_list,
                padding=10,
                width=400,
                height=300,
            ),
            actions=[
                ft.TextButton(
                    text="Close",
                    on_click=lambda e: close_dialog(e),
                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            bgcolor=ft.colors.GREY_900,
        )

        def close_dialog(e):
            dialog.open = False
            page.update()

        # Відкриваємо діалогове вікно
        page.dialog = dialog
        dialog.open = True
        page.update()

    info_button = ft.ElevatedButton(
        content=ft.Icon(
            ft.icons.HELP_OUTLINE,
            color=ft.colors.WHITE,
            size=20,
        ),
        on_click=lambda e: show_features_dialog(e),
        style=ft.ButtonStyle(
            shape=ft.CircleBorder(),
            bgcolor="#212121",
            padding=5,
        ),
        width=30,
        height=30,
    )
    # --- info button ---
    # --- input ---
    txt_input = ft.TextField(
        text_align=ft.TextAlign.LEFT,
        filled=False,
        bgcolor="transparent",
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
        bgcolor="transparent",
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
        on_click=lambda e: create_massage(txt_input.value),
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
    input_row = ft.Row(
        controls=[
            input_txt_container,
            info_button
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.END,
        width=850,
    )
    input_container = ft.Container(
        content=input_row,
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
    # for chat
    logo_container2 = ft.Container(
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
                        input_container,
                    ],
                    expand=True,
                    spacing=0,
                )
            ],
            expand=True,
            spacing=10,
        )
    )
    return context, model_list, llm_model, stop_response, model, prompt, chain, knowlage_base_added, chat_id, collection