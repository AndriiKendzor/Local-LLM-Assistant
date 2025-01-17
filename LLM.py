from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

from main import *
from some_scripts import *

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
    #save conversation
    atexit.register(lambda: create_file_with_timestamp(context))
    return response

