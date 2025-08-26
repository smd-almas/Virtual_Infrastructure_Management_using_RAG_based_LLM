import os
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

# Load OpenAI client with API key
load_dotenv()  # This loads variables from .env into environment

api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Setup ChromaDB client
chroma_client = chromadb.PersistentClient(
    path="chroma_data",
    settings=Settings(allow_reset=True)
)

# Create or load the document collection
collection = chroma_client.get_or_create_collection(name="k8s_docs")

def embed_and_store(doc_id: str, text: str, metadata: dict):
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]  # input must be a list
        )
        embedding = response.data[0].embedding
        collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata],
            embeddings=[embedding]
        )
        print(f"[+] Stored doc_id {doc_id}")
    except Exception as e:
        print(f"[Embedding Error] {e}")

def search_docs(query: str, n_results: int = 3):
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]  # input must be a list
        )
        query_embedding = response.data[0].embedding
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results
    except Exception as e:
        print(f"[Search Error] {e}")
        return {"documents": [[]], "metadatas": [[]]}

def generate_answer(query: str, context: str) -> str:
    """
    Uses GPT-4 Turbo to generate an answer based on retrieved context.
    """
    try:
        prompt = (
            "You are a helpful Kubernetes assistant. Use the following documentation to answer the question.\n\n"
            f"Documentation:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"
        )

        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a Kubernetes expert assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Answer Generation Error] {str(e)}"
