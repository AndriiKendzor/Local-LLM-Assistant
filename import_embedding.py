import os
import ollama
import chromadb
from chromadb.utils import embedding_functions
from PyPDF2 import PdfReader
from docx import Document
import flet as ft
import pandas as pd


# create collection
def create_chromadb_collection(chat_id):
    collection_name = f"document_test_collection{chat_id}"
    chroma_client = chromadb.PersistentClient(path="chroma_folder")
    collection = chroma_client.get_or_create_collection(name=collection_name)
    return collection

# ***functions***
# load documents
def load_documents(directory_path, files_list, page):
    print("=== Loading documents from directory ===")
    documents = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Обробка текстових файлів (.txt)
        if filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    documents.append({"id": filename, "text": file.read()})

                files_list.controls.append(ft.Text("✅ file name: "+filename, size=16))
                page.update()
            except Exception as e:
                files_list.controls.append(ft.Text(f"Error reading TXT {filename}: {e}",  size=16, color=ft.colors.RED))
                page.update()

        # Обробка PDF-файлів (.pdf)
        elif filename.endswith(".pdf"):
            try:
                pdf_reader = PdfReader(file_path)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text().strip() or ""
                documents.append({"id": filename, "text": text})
                files_list.controls.append(ft.Text("✅ file name: " + filename, size=16))
                page.update()
            except Exception as e:
                files_list.controls.append(ft.Text(f"Error reading TXT {filename}: {e}", size=16, color=ft.colors.RED))
                page.update()

        # Обробка Word-файлів (.docx)
        elif filename.endswith(".docx"):
            try:
                doc = Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                documents.append({"id": filename, "text": text})
                files_list.controls.append(ft.Text("✅ file name: " + filename, size=16))
                page.update()
            except Exception as e:
                files_list.controls.append(ft.Text(f"Error reading TXT {filename}: {e}", size=16, color=ft.colors.RED))
                page.update()

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
def query_documents(question, collection_name, n_results=5):
    test_query_embedding = ollama.embeddings(model="nomic-embed-text", prompt=question)["embedding"]
    results = collection_name.query(query_embeddings=[test_query_embedding], n_results=n_results)
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]
    print("=== Returning relevant chunks ===")
    return relevant_chunks

