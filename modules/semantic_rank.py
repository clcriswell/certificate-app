from typing import List, Tuple
from .config import SourceDoc
from .faiss_index import SemanticMemory

def rank_sources(query: str, sources: List[SourceDoc]) -> List[Tuple[SourceDoc, float]]:
    """Rank source documents by semantic similarity to the query."""
    sm = SemanticMemory()

    # If embedding the query fails, return original order
    query_vecs = sm.embed([query])
    if not query_vecs:
        return [(doc, 0.0) for doc in sources]

    query_vec = query_vecs[0]
    results: List[Tuple[SourceDoc, float]] = []
    for doc in sources:
        # For large docs, use first 1000 characters for embedding
        doc_vecs = sm.embed([doc.content[:1000]])
        if not doc_vecs:
            # Skip unembeddable docs (rank them last)
            results.append((doc, float("-inf")))
            continue

        doc_vec = doc_vecs[0]
        distance = sum((a - b) ** 2 for a, b in zip(query_vec, doc_vec)) ** 0.5
        # Use negative distance so that higher score = more similar
        results.append((doc, -distance))

    return sorted(results, key=lambda x: x[1], reverse=True)
