import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI
from chromadb.utils import embedding_functions

# load .env
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# chosing embedding model
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=openai_key, model_name="text-embedding-3-small"
)

# creating chromadb
chroma_client = chromadb.PersistentClient(path="chroma_folder")
collection_name = "document_test_collection"
# collection it is like table in sql
collection = chroma_client.get_or_create_collection(
    name=collection_name, embedding_function=openai_ef
)

# import LLM to chat
client = OpenAI(api_key=openai_key)


# load documents
def load_documents(directory_path):
    print("=== Loading documents from directory ===")
    documents = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            with open(
                    os.path.join(directory_path, filename)
            ) as file:
                documents.append({"id": filename, "text": file.read()})
    return documents


# eg: text = "abcdefghijklmno", chunk_size = 5, chunk_overlap = 2
# 1) abcde, 2) defgh, 3) ghijk
def split_text(text, chunk_size=1000, chunk_overlap=20):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - chunk_overlap
    return chunks


directory_path = "./documents_for_embedding"
documents = load_documents(directory_path)

chunked_documents = []
for doc in documents:
    chunks = split_text(doc["text"])
    print("=== Splitting docs into chunks ===")
    for i, chunk in enumerate(chunks):
        chunked_documents.append({"id": f"{doc['id']}_chunk{i + 1}", "text": chunk})


# generate embeddings
def get_openai_embedding(text):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    embedding = response.data[0].embedding
    print("=== Generating embeddings ===")
    return embedding


for doc in chunked_documents:
    print("=== Generating embeddings ===")
    doc["embedding"] = get_openai_embedding(doc["text"])

# inserting embeddings into vector database
for doc in chunked_documents:
    print("=== Inserting chunks into vector db ===")
    collection.upsert(
        ids=[doc["id"]], documents=[doc["text"]], embeddings=[doc["embedding"]]
    )


# Function to query documents
def query_documents(question, n_results=2):
    results = collection.query(query_texts=question, n_results=n_results)
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]
    print("=== Returning relevant chunks ===")
    return relevant_chunks


# Function to generate responce based on documents
def generate_response(question, relevant_chunk):
    context = "\n\n".join(relevant_chunk)
    prompt = (
            "You are an assistant for question-answering tasks. Use the following pieces of "
            "retrieved context to answer the question. If you don't know the answer, say that you"
            "don't know. Use three sentences maximum and keep the answer concise."
            "\n\nContext:\n" + context + "\n\nQuestion:\n\n" + question
    )

    resource = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )

    answer = resource.choices[0].message
    return answer


question = "When I wanted to ask Rostik about trading service?"
relevant_chunks = query_documents(question)
answer = generate_response(question, relevant_chunks)

print(answer)
