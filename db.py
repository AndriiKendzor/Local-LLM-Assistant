from models import Chat, Main
from llm import call_llm
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import flet as ft
import re

Base = declarative_base()
engine = create_engine('sqlite:///E:/LocalLLMAssistant/DataBase.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def save_conversation(chat_id, context, knowlage_base_added, llm_model, chain, collection, llm_m, user_m, chat_name_container):
    # Формуємо
    text = "Create a title for this conversation"
    collection_name = f"document_test_collection{chat_id}"
    title = call_llm(text, context, llm_model, chain, knowlage_base_added, collection, True)
    chat_name_container.content = ft.Text(
        value=title,
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
        existing_chat = session.query(Chat).filter(Chat.ChatID == chat_id).first()

        if not existing_chat:
            # Якщо чату немає, створюємо новий
            new_chat = Chat(
                ChatID=chat_id,  # Вказуємо ChatID явно
                Title=title,
                Date=datetime.now(),  # Поточна дата і час до хвилин
                KB=knowlage_base_added,
                CollectionID=collection_name,
                Model=llm_model
            )
            session.add(new_chat)

            new_message = Main(
                ChatID=chat_id,
                User_m=user_m,
                LLm_m=llm_m
            )
            session.add(new_message)

            session.commit()
            print(f"Новий чат створено з ChatID: {chat_id}")
        else:
            print(f"Чат з ChatID: {chat_id} уже існує")

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
                        Main.ChatID == chat_id,
                        Main.User_m.like(user_text)
                    ).first()

            if regenerate_message:
                regenerate_message.LLm_m = llm_m
                existing_chat.Title = title
                existing_chat.KB = knowlage_base_added
                existing_chat.Model = llm_model
                session.commit()
                print(f"Оновлено LLm_m для повідомлення в чаті {chat_id}")

            else:
                new_message = Main(
                    ChatID=chat_id,
                    User_m=user_m,
                    LLm_m=llm_m
                )
                existing_chat.Title = title
                existing_chat.KB = knowlage_base_added
                existing_chat.Model = llm_model
                session.commit()

                session.add(new_message)
                session.commit()

    except Exception as e:
        session.rollback()  # Відкат у разі помилки
        print(f"Помилка при збереженні чату: {e}")
    finally:
        session.close()  # Завжди закриваємо сесію


