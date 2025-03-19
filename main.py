import flet as ft
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from llm import get_models, template
from ui import build_ui
import random

context = ""
model_list = get_models()
llm_model = model_list[0] if model_list else None  # Вибираємо першу модель, якщо є
stop_response = False
knowlage_base_added = False
collection = None


def generate_random_code():
    i = 0
    code = ""
    while (i <= 5):
        random_number = random.randint(0, 9)
        code += str(random_number)
        i += 1

    return code


chat_id = generate_random_code()
print(chat_id)

# Ініціалізація LLM
if llm_model:
    model = OllamaLLM(model=llm_model)
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
else:
    model = None
    prompt = None
    chain = None

def main(page: ft.Page):
    global context, model_list, llm_model, stop_response, model, prompt, chain, knowlage_base_added, chat_id, collection
    build_ui(page, context, model_list, llm_model, stop_response, model, prompt, chain, knowlage_base_added, chat_id, collection)

if __name__ == "__main__":
    try:
        ft.app(target=main,  assets_dir="assets", view=ft.FLET_APP)
    except Exception as e:
        print(f"Error with page: {e}")

