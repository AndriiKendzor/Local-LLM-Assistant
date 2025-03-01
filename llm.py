import subprocess
import re
import ollama

# Перевірка, чи встановлена програма Ollama
def is_ollama_installed():
    try:
        # Перевіряємо наявність команди ollama
        result = subprocess.run(["ollama", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

# Отримуємо список доступних моделей
def get_models():
    try:
        result = subprocess.run(['ollama', 'list'], stdout=subprocess.PIPE, text=True)
        lines = result.stdout.strip().split('\n')
        models = [line.split()[0] for line in lines[1:] if line.strip()]
        return []
    except Exception as e:
        return []


template = """
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""

def call_llm(text, context, llm_model, chain):
    print(f"Активна модель: {llm_model}")
    user_input = text

    request_data = {
        "context": context,
        "question": user_input
    }

    # check if image is added
    img_pattern = r"!img:\s*(.*?)!"  # Шаблон для пошуку посилання
    img_match = re.search(img_pattern, text)

    if img_match:
        img_path = img_match.group(1)
        print(img_path)
        try:
            response = ollama.chat(
                model="llava:latest",
                messages=[
                    {"role": "user", "content": user_input, "images": [img_path]}
                ]
            )
            img_response = response["message"]["content"]
            context += f"\nUser: {user_input}\nAI: {img_response}"
            return img_response, context
        except Exception as e:
            img_response = "An error with image procesing"
            return img_response, context
    else:
        response = chain.invoke(request_data)
        context += f"\nUser: {user_input}\nAI: {response}"
        return response, context


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