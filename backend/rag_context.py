import chromadb
from config import CHROMA_DB_PATH
from openai import OpenAI
import os

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name="k8s_docs")

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_context(query: str) -> str:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=[query]
    )
    embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )
    docs = [doc for doc in results["documents"][0]]
    return "\n\n".join(docs)
