import chromadb, ollama
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RAG API")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("docs")

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3.2"

def embed(text):
    return ollama.embeddings(model=EMBED_MODEL, prompt=text)["embedding"]

class Doc(BaseModel):
    id: str
    text: str

class Question(BaseModel):
    question: str

@app.get("/")
def health():
    return {"status": "RAG API running"}

@app.post("/ingest")
def ingest(doc: Doc):
    collection.upsert(ids=[doc.id], documents=[doc.text], embeddings=[embed(doc.text)])
    return {"status": "added", "id": doc.id}

@app.post("/ask")
def ask(q: Question):
    results = collection.query(query_embeddings=[embed(q.question)], n_results=3)
    chunks = results["documents"][0]
    context = "\n".join(chunks)
    prompt = f"Answer only from this context. If not found, say you don't know.\n\nContext:\n{context}\n\nQuestion: {q.question}"
    resp = ollama.chat(model=LLM_MODEL, messages=[{"role": "user", "content": prompt}])
    return {"answer": resp["message"]["content"], "sources": chunks}
