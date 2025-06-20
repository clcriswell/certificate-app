from typing import List, Tuple
from .config import SourceDoc
from .faiss_index import SemanticMemory

def rank_sources(query: str, sources: List[SourceDoc]) -> List[Tuple[SourceDoc, float]]:
    """Rank source documents by semantic similarity to the query."""
    sm = SemanticMemory()
    query_vec = sm.embed([query])[0]
    results: List[Tuple[SourceDoc, float]] = []
    for doc in sources:
        # For large docs, use first 1000 characters for embedding
        doc_vec = sm.embed([doc.content[:1000]])[0]
        distance = sum((a - b) ** 2 for a, b in zip(query_vec, doc_vec)) ** 0.5
        # Use negative distance so that higher score = more similar
        results.append((doc, -distance))
    return sorted(results, key=lambda x: x[1], reverse=True)
