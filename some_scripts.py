from main import *
from LLM import *

import datetime
import os


def create_file_with_timestamp(info):
    # Отримуємо поточну дату та час
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Створюємо назву файлу
    file_name = f"Conversation_{timestamp}.txt"

    # Зберігаємо файл у поточній директорії
    file_path = os.path.join(os.getcwd(), file_name)

    # Відкриваємо файл для запису і записуємо інформацію
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(info)

