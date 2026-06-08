"""
Semantic document retrieval using cosine similarity against prebuilt embeddings.
"""

import numpy as np

from src.data_plane.embeddings import build_index, get_model

#cosine similarity is a common metric used to measure the similarity between two non-zero vectors in an inner product space. It is defined as the cosine of the angle between them, which ranges from -1 (completely opposite) to 1 (completely similar), with 0 indicating orthogonality (no similarity). In the context of document retrieval, cosine similarity is often used to compare the embedding vector of a query with the embedding vectors of documents in an index, allowing us to rank documents based on their relevance to the query.
def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

#this function is responsible for retrieving the most relevant documents based on a given query. It first obtains the embedding model and builds the current index of document embeddings. Then, it encodes the query into an embedding vector and calculates the cosine similarity between the query vector and each document's embedding in the index. The results are sorted by similarity score in descending order, and the top-k most relevant documents are returned as a list of dictionaries containing the filename, source type, similarity score, and a preview of the document's content.
def retrieve(query: str, k: int = 5) -> list[dict]:
    """Embed query and return top-k most relevant documents by cosine similarity."""
    model = get_model()
    docs = build_index()

    #this is where the query is converted into an embedding vector using the same model that was used to generate the document embeddings. The resulting query_vec is a numerical representation of the query that can be compared against the document embeddings in the index to determine their relevance based on cosine similarity.
    query_vec = model.encode([query], convert_to_numpy=True)[0]

    #sorts the documents in descending order of their cosine similarity with the query vector. 
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
