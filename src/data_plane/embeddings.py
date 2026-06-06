"""
Document-level embedding pipeline using sentence-transformers.

For each file in DATA_DIR, extracts full text, splits into 300-word chunks,
embeds each chunk, then mean-pools to produce one vector per document.
Vectors are stored as BLOBs in the SQLite `documents` table (same DB as targets).

Call build_index() to build or load. Pass force=True to re-embed all documents.
"""

import io
import pathlib
import sqlite3
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer

from config import DB_PATH
from src.data_plane.data_processing import process_file

DATA_DIR = pathlib.Path("src/data_plane/data")
SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv"}
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_WORDS = 300

_model: SentenceTransformer | None = None
_index_cache: list["DocumentEmbedding"] | None = None


@dataclass
class DocumentEmbedding:
    filename: str
    source_type: str
    preview: str
    embedding: np.ndarray


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _arr_to_blob(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue()


def _blob_to_arr(blob: bytes) -> np.ndarray:
    return np.load(io.BytesIO(blob))


def _chunk_text(text: str) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + CHUNK_WORDS]) for i in range(0, len(words), CHUNK_WORDS)]


def _ensure_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY,
                filename    TEXT    NOT NULL UNIQUE,
                source_type TEXT    NOT NULL,
                preview     TEXT,
                embedding   BLOB    NOT NULL,
                indexed_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _load_from_db() -> list[DocumentEmbedding]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT filename, source_type, preview, embedding FROM documents ORDER BY filename"
        ).fetchall()
    return [
        DocumentEmbedding(
            filename=row[0],
            source_type=row[1],
            preview=row[2],
            embedding=_blob_to_arr(row[3]),
        )
        for row in rows
    ]


def _build_and_store() -> list[DocumentEmbedding]:
    model = get_model()
    files = sorted(f for f in DATA_DIR.iterdir() if f.suffix.lower() in SUPPORTED)

    doc_embeddings: list[DocumentEmbedding] = []
    rows: list[tuple] = []

    for path in files:
        print(f"Embedding: {path.name}")
        blocks = process_file(path)
        full_text = "\n".join(b.text for b in blocks)
        chunks = _chunk_text(full_text)
        if not chunks:
            continue

        vecs = model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)
        doc_vec = vecs.mean(axis=0)
        preview = full_text[:300]

        doc_embeddings.append(DocumentEmbedding(
            filename=path.name,
            source_type=path.suffix.lstrip("."),
            preview=preview,
            embedding=doc_vec,
        ))
        rows.append((path.name, path.suffix.lstrip("."), preview, _arr_to_blob(doc_vec)))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM documents")
        conn.executemany(
            "INSERT INTO documents (filename, source_type, preview, embedding) VALUES (?, ?, ?, ?)",
            rows,
        )

    print(f"Stored {len(doc_embeddings)} document embeddings in SQLite at {DB_PATH}")
    return doc_embeddings


def build_index(force: bool = False) -> list[DocumentEmbedding]:
    """Return document embeddings, loading from SQLite or building fresh."""
    global _index_cache
    _ensure_table()

    if _index_cache is not None and not force:
        return _index_cache

    if not force:
        docs = _load_from_db()
        if docs:
            _index_cache = docs
            return docs

    _index_cache = _build_and_store()
    return _index_cache
