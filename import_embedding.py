import os
import ollama
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from docx import Document
import pandas as pd


# create collection
collection_name = "document_test_collection7"
chroma_client = chromadb.PersistentClient(path="chroma_folder")
collection = chroma_client.get_or_create_collection(name=collection_name)

# ***functions***
# load documents
def load_documents(directory_path):
    print("=== Loading documents from directory ===")
    documents = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Обробка текстових файлів (.txt)
        if filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    documents.append({"id": filename, "text": file.read()})
                print("✅ file name: "+filename)
            except Exception as e:
                print(f"Error reading TXT {filename}: {e}")

        # Обробка PDF-файлів (.pdf)
        elif filename.endswith(".pdf"):
            try:
                pdf_reader = PdfReader(file_path)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text().strip() or ""
                documents.append({"id": filename, "text": text})
                print("✅ file name: "+filename)
            except Exception as e:
                print(f"Error reading PDF {filename}: {e}")

        # Обробка Word-файлів (.docx)
        elif filename.endswith(".docx"):
            try:
                doc = Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                documents.append({"id": filename, "text": text})
                print("✅ file name: "+filename)
            except Exception as e:
                print(f"Error reading DOCX {filename}: {e}")

        # Обробка Excel-файлів (.xlsx)
        # elif filename.endswith(".xlsx"):
        #     try:
        #         # Читаємо всі листи Excel-файлу
        #         xls = pd.ExcelFile(file_path)
        #         text = ""
        #         for sheet_name in xls.sheet_names:
        #             df = pd.read_excel(file_path, sheet_name=sheet_name)
        #             # Перетворюємо DataFrame у рядок
        #             text += f"Sheet: {sheet_name}\n{df.to_string()}\n\n"
        #         documents.append({"id": filename, "text": text})
        #         print("✅ file name: "+filename)
        #         print(text)
        #     except Exception as e:
        #         print(f"Error reading XLSX {filename}: {e}")

    return documents


# eg: text = "abcdefghijklmno", chunk_size = 5, chunk_overlap = 2
# 1) abcde, 2) defgh, 3) ghijk
def split_text(text, chunk_size=1500, chunk_overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks


# generate embeddings
def get_embedding(text):
    response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    embedding = response["embedding"]
    return embedding


# Function to query documents
def query_documents(question, n_results=5):
    test_query_embedding = ollama.embeddings(model="nomic-embed-text", prompt=question)["embedding"]
    results = collection.query(query_embeddings=[test_query_embedding], n_results=n_results)
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]
    print("=== Returning relevant chunks ===")
    return relevant_chunks


# Function to generate responce based on documents
def generate_response(question, prompt):
    response = ollama.chat(
        model="llama3.2:latest",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]
    )
    return response["message"]["content"]


# ***load code***
directory_path = "./documents_for_embedding"
documents = load_documents(directory_path)

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
# original question
question = "Hello! What is this book about?"
# generation hypothetical answer to find more relevant chunks
# hypothetical_answer = generate_response(question, "Just give the hypothetical answer the question without any context")
# joined_query = f"{question} {hypothetical_answer}"
# looking for the relevant information
relevant_chunks = query_documents(question)
context = "\n\n".join(relevant_chunks)
prompt = (
        "You are an assistant for question-answering tasks. Use the following pieces of "
        "retrieved context to answer the question. If you don't know the answer, say that you"
        "don't know."
        "\n\nContext:\n" + context
)
answer = generate_response(question, prompt)
print(answer)
