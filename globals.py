from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import subprocess
import random


template = """
Answer the question below.

Here is the conversation history: {context}

Here are some pieces of retrieved context to answer the question: {relevant_chunks} 
If you don't know the answer, say that you don't know.
If in the field above is written: “No knowledge base added” - just answer the question.


Question: {question}

Answer:
"""

# Отримуємо список доступних моделей
def get_models():
    try:
        result = subprocess.run(['ollama', 'list'], stdout=subprocess.PIPE, text=True)
        lines = result.stdout.strip().split('\n')
        models = [line.split()[0] for line in lines[1:] if line.strip() and "embed" not in line.split()[0].lower()]
        return models
    except Exception as e:
        return []



context = ""
model_list = get_models()
llm_model = model_list[0] if model_list else None  # Вибираємо першу модель, якщо є
stop_response = False
knowlage_base_added = False
collection = None
dialog = None
title = "New chat"


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