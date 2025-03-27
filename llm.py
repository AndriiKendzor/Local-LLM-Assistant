import re
import ollama
import os
from import_embedding import query_documents
import globals
# Перевірка, чи встановлена програма Ollama


def call_llm(text, title):
    print(f"Активна модель: {globals.llm_model}")
    user_input = text

    if title:
        request_data = {
            "context": globals.context,
            "relevant_chunks": "No knowledge base added",
            "question": user_input
        }
        response = globals.chain.invoke(request_data)
        return response
    else:
        # check if knowlage base added
        if globals.knowlage_base_added:
            relevant_chunks = query_documents(user_input, globals.collection)
            print(relevant_chunks)
            relevant_chunks = "\n\n".join(relevant_chunks)
            request_data = {
                "context": globals.context,
                "relevant_chunks": relevant_chunks,
                "question": user_input
            }
            print("knowlage_base_added YES")
        else:
            request_data = {
                "context": globals.context,
                "relevant_chunks": "No knowledge base added",
                "question": user_input
            }
            print("knowlage_base_added NO")
        # check if image is added
        img_pattern = r"!img:\s*(.*?)!"  # Шаблон для пошуку посилань
        img_matches = re.findall(img_pattern, user_input)  # Знаходимо всі збіги

        if img_matches:
            img_paths = img_matches  # Список усіх знайдених шляхів до зображень
            # Перевіряємо, чи всі файли існують
            valid_img_paths = [path for path in img_paths if os.path.exists(path)]
            if not valid_img_paths:
                return "No valid image paths found"

            print("Знайдені зображення:", img_paths)
            try:
                response = ollama.chat(
                    model=globals.llm_model,
                    messages=[
                        {"role": "user", "content": user_input, "images": img_paths}
                    ]
                )
                img_response = response["message"]["content"]
                globals.context += f"\nUser: {user_input}\nAI: {img_response}"
                return img_response
            except Exception as e:
                img_response = f"An error with image processing: {e}"
                return img_response
        else:
            response = globals.chain.invoke(request_data)
            globals.context += f"\nUser: {user_input}\nAI: {response}"
            return response
