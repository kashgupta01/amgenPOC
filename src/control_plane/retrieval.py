"""
Semantic document retrieval using cosine similarity against prebuilt embeddings.
"""

import numpy as np

from src.data_plane.embeddings import build_index, get_model


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Embed query and return top-k most relevant documents by cosine similarity."""
    model = get_model()
    docs = build_index()

    query_vec = model.encode([query], convert_to_numpy=True)[0]

    scored = sorted(
        [
            {
                "filename": doc.filename,
                "source_type": doc.source_type,
                "score": round(_cosine(query_vec, doc.embedding), 4),
                "preview": doc.preview,
            }
            for doc in docs
        ],
        key=lambda x: x["score"],
        reverse=True,
    )

    return scored[:k]
