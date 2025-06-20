import os
import pickle
import numpy as np
import openai
import faiss

class SemanticMemory:
    """Persistent FAISS-based vector store for semantic recall."""
    def __init__(self, index_path: str = "faiss_index.bin", metadata_path: str = "index_meta.pkl"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = []
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.load()

    def load(self):
        if os.path.exists(self.index_path):
            # Load existing FAISS index and metadata
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            # Initialize a new index (1536-dim for OpenAI embeddings)
            self.index = faiss.IndexFlatL2(1536)
            self.metadata = []

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(input=texts, model="text-embedding-3-large")
        return [item.embedding for item in response.data]

    def add(self, texts: list[str], tags: list[str]):
        vectors = self.embed(texts)
        self.index.add(np.array(vectors).astype("float32"))
        self.metadata.extend(tags)
        self.save()

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        query_vec = self.embed([query])[0]
        D, I = self.index.search(np.array([query_vec]).astype("float32"), top_k)
        return [(self.metadata[i], float(D[0][j])) for j, i in enumerate(I[0])]
