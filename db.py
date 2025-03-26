from models import Chat, Main
from llm import call_llm
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import flet as ft
import re

from import_embedding import create_chromadb_collection
import globals

Base = declarative_base()
engine = create_engine('sqlite:///E:/LocalLLMAssistant/DataBase.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def search_chat(page):
    # Контейнер для результатів пошуку
    search_results = ft.Column(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    # Поле введення для пошуку
    search_input = ft.TextField(
        label="Search messages",
        #on_change=lambda e: update_search_results(e.control.value, search_results),
        width=380,
        border_radius=5,
        bgcolor=ft.colors.GREY_800,
        color=ft.colors.WHITE,
    )

    # Створюємо діалогове вікно
    dialog = ft.AlertDialog(
        title=ft.Text(
            "Find your chat",
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    search_input,
                    search_results,
                ],
                spacing=10,
            ),
            padding=10,
            width=400,
            height=300,
        ),
        actions=[
            #ft.TextButton("Close", on_click=lambda e: close_dialog(page)),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        bgcolor=ft.colors.GREY_900,
    )

    # Відкриваємо діалогове вікно
    page.dialog = dialog
    dialog.open = True
    page.update()



def load_chats(page, chat_column, chat_name_container, model_chose_dropdown, add_knowledge_base):
    session = Session()
    chats = session.query(Chat).order_by(Chat.Date.desc()).all()  # Сортуємо за датою (нові зверху)
    chat_controls = []

    for chat in chats:
        # Текст кнопки (назва чату)
        title_text = ft.Text(
            value=chat.Title,
            size=14,  # Шрифт 12
            color="white",  # Білий колір
            max_lines=1,  # Один рядок
            overflow=ft.TextOverflow.ELLIPSIS,  # "..." якщо текст довший
        )

        # # Текст дати (показується при наведенні)
        # date_text = ft.Text(
        #     value=chat.Date.strftime('%Y-%m-%d %H:%M'),
        #     size=9,  # Дуже дрібний шрифт
        #     color="gray",  # Сірий колір
        #     visible=False,  # Прихований за замовчуванням
        # )

        # Кнопка
        chat_button = ft.TextButton(
            content=ft.Column(
                controls=[
                    title_text,
                ],
                spacing=2,  # Маленький проміжок між назвою і датою
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=195,  # Ширина 195
            height=30,  # Висота кнопки
            style=ft.ButtonStyle(
                bgcolor={"": "transparent", "hovered": "#111111"},  # Прозорий фон, темно-сірий при наведенні
                shape=ft.RoundedRectangleBorder(radius=5),  # Радіус кутів 10
            ),
            tooltip=chat.Title,  # Підказка з повною назвою чату
            data=chat.ChatID,
            on_click=lambda e: get_chat(e.control.data, page, chat_column, chat_name_container, model_chose_dropdown, add_knowledge_base)
        )

        chat_controls.append(chat_button)

    session.close()
    return chat_controls


def get_chat(new_chat_id, page, chat_column, chat_name_container, model_chose_dropdown, add_knowledge_base):

    from ui import create_buttons

    chat_column.controls.clear()

    # get chat history
    session = Session()
    chats = session.query(Main).filter_by(ChatID=new_chat_id).all()  # Сортуємо за датою (нові зверху)

    # get the chat data
    new_chat = session.query(Chat).filter(Chat.ChatID == new_chat_id).first()

    globals.chat_id = new_chat.ChatID
    globals.title = new_chat.Title
    # update chat name
    chat_name_container.content = ft.Text(
        value=globals.title,
        color="white",
        size=18,
        max_lines=1,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    chat_name_container.update()

    globals.knowlage_base_added = new_chat.KB
    if globals.knowlage_base_added:
        globals.collection = create_chromadb_collection(globals.chat_id)
        new_style = ft.ButtonStyle(
            padding=5,
            alignment=ft.alignment.center,
            side=ft.BorderSide(1, ft.colors.GREEN),
            color=ft.colors.GREY_500,
            text_style=ft.TextStyle(size=16),
            shape=ft.RoundedRectangleBorder(radius=20),
        )
    else:
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

    globals.llm_model = new_chat.Model
    globals.collection = create_chromadb_collection(globals.chat_id)

    model_chose_dropdown.value = globals.llm_model
    model_chose_dropdown.update()

    for message in chats:

        globals.context += f"\nUser: {message.User_m}\nAI: {message.LLm_m}"
        # creating user massage
        text_width = min(10 * len(message.User_m) + 20, 560)

        logo_container2 = ft.Container(
            width=30,
            height=30,
            border_radius=30,
            content=ft.Image(
                src="img/logo_beta.png",  # URL або локальний шлях
                fit=ft.ImageFit.CONTAIN  # Налаштування масштабування зображення
            ),
        )

        user_massage = ft.Container(
            alignment=ft.alignment.center_right,
            content=ft.Text(
                message.User_m,
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
            message.LLm_m,
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

        buttons_row = create_buttons(message.LLm_m, message.User_m, chat_column)

        chat_column.controls.append(
            buttons_row
        )
        chat_column.update()

        session.close()


def save_conversation(llm_m, user_m, chat_name_container, chats_column, page, chat_column, model_chose_dropdown, add_knowledge_base):

    # Формуємо
    text = "Just create the title for this conversation without any additional information, maximum 3 words"
    collection_name = f"document_test_collection{globals.chat_id}"
    globals.title = call_llm(text, True)
    chat_name_container.content = ft.Text(
        value=globals.title,
        color="white",
        size=18,
        max_lines=1,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    chat_name_container.update()
    # Створюємо сесію для роботи з базою даних
    session = Session()

    try:
        # Перевіряємо, чи існує чат з таким ChatID
        existing_chat = session.query(Chat).filter(Chat.ChatID == globals.chat_id).first()

        if not existing_chat:
            # Якщо чату немає, створюємо новий
            new_chat = Chat(
                ChatID=globals.chat_id,  # Вказуємо ChatID явно
                Title=globals.title,
                Date=datetime.now(),  # Поточна дата і час до хвилин
                KB=globals.knowlage_base_added,
                CollectionID=collection_name,
                Model=globals.llm_model
            )
            session.add(new_chat)

            new_message = Main(
                ChatID=globals.chat_id,
                User_m=user_m,
                LLm_m=llm_m
            )
            session.add(new_message)

            session.commit()

            chats_column.controls = load_chats(page, chat_column, chat_name_container, model_chose_dropdown, add_knowledge_base)
            chats_column.update()
            print(f"Новий чат створено з ChatID: {globals.chat_id}")
        else:
            print(f"Чат з ChatID: {globals.chat_id} уже існує")

            # check if user want to regenerate response
            regenerate_message = None
            if "</>" in user_m:
                pattern = r"Just answer different way: (.*?) and ignore this: </>"
                match = re.search(pattern, user_m)
                if match:
                    user_text = match.group(1)  # Витягуємо текст між "Just answer..." і "and ignore..."
                    print(f"Витягнуто user_text: {user_text}")
                    # Перевіряємо, чи є повідомлення з таким user_text у цьому чаті
                    regenerate_message = session.query(Main).filter(
                        Main.ChatID == globals.chat_id,
                        Main.User_m.like(user_text)
                    ).first()

            if regenerate_message:
                regenerate_message.LLm_m = llm_m
                existing_chat.Title = globals.title
                existing_chat.KB = globals.knowlage_base_added
                existing_chat.Model = globals.llm_model
                session.commit()
                print(f"Оновлено LLm_m для повідомлення в чаті {globals.chat_id}")

            else:
                new_message = Main(
                    ChatID=globals.chat_id,
                    User_m=user_m,
                    LLm_m=llm_m
                )
                existing_chat.Title = globals.title
                existing_chat.KB = globals.knowlage_base_added
                existing_chat.Model = globals.llm_model
                session.commit()

                session.add(new_message)
                session.commit()

    except Exception as e:
        session.rollback()  # Відкат у разі помилки
        print(f"Помилка при збереженні чату: {e}")
    finally:
        session.close()  # Завжди закриваємо сесію



