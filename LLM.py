from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from main import *

import datetime
import os
import re

template = """
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""

context = ""

model = OllamaLLM(model="llama3.2")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


def call_llm(text):
    global context
    user_input = text
    response = chain.invoke({"context": context, "question": user_input})
    context += f"\nUser: {user_input}\nAI: {response}"
    return response


# def create_file_with_timestamp(info):
#     if info != '':
#         # Використовуємо LLM для створення заголовка
#         title = chain.invoke({"context": info, "question": "Create a headline for our entire conversation in no more than 5 words"})
#         timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         title = re.sub(r'[<>:"/\\|?*]', '',title)
#
#         # Створюємо назву файлу
#         file_name = f"{title}_{timestamp}.txt"
#         # Зберігаємо файл у поточній директорії
#         file_path = os.path.join(os.getcwd(), file_name)
#
#         # Відкриваємо файл для запису і записуємо інформацію
#         with open(file_path, 'w', encoding='utf-8') as file:
#             file.write(info)

#save conversation
#atexit.register(lambda: create_file_with_timestamp(context))