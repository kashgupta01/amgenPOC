"""
Document-level embedding pipeline using sentence-transformers.

For each file in DATA_DIR, extracts full text, splits into 300-word chunks,
embeds each chunk, then mean-pools to produce one vector per document.
Vectors are stored as BLOBs in the SQLite `documents` table (same DB as targets).

Each file's content hash is stored alongside its embedding, so re-running the
index only re-embeds files that are new or changed; unchanged files reuse their
stored embedding, and rows for files no longer present are dropped.

Call build_index() to get the current index. Pass refresh=True to re-scan
the data folder for added/changed/removed files.
"""

import hashlib
import io
import pathlib
import sqlite3
from dataclasses import dataclass

import numpy as np
#why sentence transformers? Because it provides a simple interface for generating high-quality sentence and document embeddings using pre-trained models, which can be easily integrated into our pipeline for embedding various document types.
from sentence_transformers import SentenceTransformer

from config import DB_PATH
from src.data_plane import queries
from src.data_plane.data_processing import process_file
from src.utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = pathlib.Path("src/data_plane/data")
SUPPORTED = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv"}

#why this model? Bio_ClinicalBERT is trained on clinical notes (MIMIC-III), so it captures
#biomedical/oncology terminology (gene names, drug targets, mechanisms) more meaningfully
#than a general-purpose sentence model. Tradeoffs: larger model (slower to embed) and
#768-dim vectors (vs. MiniLM's 384-dim) — roughly double the storage per document.
MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"
CHUNK_WORDS = 300

#this module maintains an in-memory cache of the current index to avoid unnecessary DB queries on repeated calls to build_index() when the underlying data hasn't changed; use refresh=True to force a rescan and re-embed as needed.
_model: SentenceTransformer | None = None
_index_cache: list["DocumentEmbedding"] | None = None


#dataclass to keep information stored in the database together in one place, and to provide type hints for better code clarity and maintainability. Each DocumentEmbedding instance represents a single document's metadata and its corresponding embedding vector, making it easier to work with the data throughout the application.
@dataclass
class DocumentEmbedding:
    filename: str
    source_type: str
    preview: str
    embedding: np.ndarray

#this just initializes the model on first use and reuses it for subsequent calls, which is more efficient than loading the model multiple times.
def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

#these helper functions convert between numpy arrays and bytes for storage in the SQLite BLOB field, compute a hash of a file's content to detect changes, and split text into manageable chunks for embedding.
def _arr_to_blob(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue()

#this function ensures the database and the required table exist before we attempt to read or write embeddings, and also adds the content_hash column if it's missing (for backward compatibility with older versions of the schema).
def _blob_to_arr(blob: bytes) -> np.ndarray:
    return np.load(io.BytesIO(blob))

#this function computes a SHA-256 hash of the file's content, which allows us to detect when a file has changed since the last time it was embedded, so we only re-embed files that are new or modified.
#this is what was addded to the schema.sql file, and the _ensure_table function checks for this column and adds it if it's missing, ensuring that the application can track content changes for each document going forward.
def _file_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

#this function takes the full text of a document and splits it into chunks of a specified number of words (300 in this case) to ensure that the text is manageable for embedding, as some models have limits on input length or perform better with shorter segments.
def _chunk_text(text: str) -> list[str]:
    #
    words = text.split()
    return [" ".join(words[i : i + CHUNK_WORDS]) for i in range(0, len(words), CHUNK_WORDS)]

#the main function that synchronizes the index with the current state of the data directory: it checks for new, changed, or removed files, updates the database accordingly, and returns the current list of document embeddings. 
#This basically looks at the structure of it rather than the content of the function, which is more important for understanding how the index is maintained and updated over time as the contents of the data directory change.
def _ensure_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    #connecting to the SQLite database specified by DB_PATH, creating it if it doesn't exist, and then executing a SQL command to create the documents table if it doesn't already exist. The table includes columns for storing the filename, source type, a preview of the content, the embedding vector as a BLOB, a content hash for change detection, and a timestamp for when the document was indexed. Additionally, it checks if the content_hash column exists and adds it if it's missing, ensuring that the database schema is up-to-date for tracking document changes.
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(queries.CREATE_DOCUMENTS_TABLE)
        #Migrate in any columns missing from older versions of this table.
        #model_name records which embedding model produced each row's vector, so that
        #switching MODEL_NAME (e.g. MiniLM -> BioClinicalBERT) is detected the same way
        #a changed file is — triggering re-embedding instead of leaving stale, mismatched-
        #dimension vectors behind that would break cosine similarity in retrieve().
        cols = {row[1] for row in conn.execute(queries.PRAGMA_DOCUMENTS_TABLE_INFO)}
        if "content_hash" not in cols:
            conn.execute(queries.ALTER_DOCUMENTS_ADD_CONTENT_HASH)
        if "model_name" not in cols:
            conn.execute(queries.ALTER_DOCUMENTS_ADD_MODEL_NAME)

#this function retrieves all document embeddings from the database, converting the stored BLOBs back into numpy arrays and returning a list of DocumentEmbedding instances that represent the current state of the index.
def _load_from_db() -> list[DocumentEmbedding]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(queries.SELECT_DOCUMENTS_FOR_INDEX).fetchall()
        #the function iterates over the rows returned from the database query, converting each row into a DocumentEmbedding instance. The filename, source_type, and preview are taken directly from the row, while the embedding is converted from its stored BLOB format back into a numpy array using the _blob_to_arr helper function. The resulting list of DocumentEmbedding instances represents the current index of document embeddings that can be used for retrieval and search operations.
    return [
        DocumentEmbedding(
            filename=row[0],
            source_type=row[1],
            preview=row[2],
            embedding=_blob_to_arr(row[3]),
        )
        for row in rows
    ]

#the actual embedding happens here: the function takes a file path, processes the file to extract its full text, splits the text into chunks, generates embeddings for each chunk using the model, and then averages those chunk embeddings to produce a single embedding vector that represents the entire document. It also returns a preview of the document's content (the first 300 characters) for display purposes.
def _embed_document(model: SentenceTransformer, path: pathlib.Path) -> tuple[np.ndarray, str]:
    #from data_processing import process_file
    blocks = process_file(path)
    full_text = "\n".join(b.text for b in blocks)
    
    #using the above helper function
    chunks = _chunk_text(full_text)
    vecs = model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)

    #what is this line doing? It takes the array of chunk embeddings (vecs) and computes the mean across all chunks to produce a single embedding vector that represents the entire document. This is a common technique for aggregating multiple embeddings into one, as it captures the overall semantic content of the document while reducing it to a fixed-size vector that can be easily stored and compared against other document embeddings.
    
    return vecs.mean(axis=0), full_text[:300]

#this function is responsible for synchronizing the document embedding index with the current state of the data directory. It checks for new, changed, or removed files by comparing the current files in the directory with the existing entries in the database using their content hashes. For new or modified files, it generates new embeddings and updates the database; for removed files, it deletes their entries from the database. Finally, it returns the updated list of document embeddings that reflect the current contents of the data directory.
def _sync_index() -> list[DocumentEmbedding]:
    """Embed new/changed files, drop rows for removed files, reuse unchanged embeddings."""
    model = get_model()

    #the function lists all files in the DATA_DIR that have a supported extension, computes their content hashes, and compares them against the existing entries in the database to determine which files are new, which have changed, and which have been removed. It then updates the database accordingly by inserting new embeddings for new or changed files and deleting entries for removed files, ensuring that the index remains accurate and up-to-date with the current state of the data directory.

    
    files = sorted(f for f in DATA_DIR.iterdir() if f.suffix.lower() in SUPPORTED)
    #if supported, log fully qualified file in logger
    for f in files:
        logger.info("Found file: %s", f)

    current_names = {f.name for f in files}

    #if there are unsupported files in the data directory, it prints a warning message listing those files, so the user is aware that they won't be included in the embedding index and can take action if needed (e.g., converting them to a supported format).
    unsupported = sorted(f.name for f in DATA_DIR.iterdir() if f.suffix.lower() not in SUPPORTED and f.is_file())
    if unsupported:
        logger.warning("Unsupported files in %s: %s", DATA_DIR, unsupported)

    with sqlite3.connect(DB_PATH) as conn:
        #track both content_hash and model_name per existing row: a file is only considered
        #"up to date" if its bytes are unchanged AND it was embedded with the current model.
        #This makes switching MODEL_NAME automatically trigger re-embedding for every
        #document, instead of leaving stale vectors from the old model (wrong dimensions,
        #incomparable via cosine similarity) sitting in the table.
        existing = {
            row[0]: (row[1], row[2])
            for row in conn.execute(queries.SELECT_DOCUMENTS_SYNC_STATE).fetchall()
        }

        #this block of code identifies files that are present in the existing database but no longer exist in the data directory (i.e., they have been removed). It constructs a list of such "stale" filenames and then executes a SQL command to delete their corresponding entries from the documents table. This ensures that the index remains clean and only contains entries for files that currently exist in the data directory, preventing stale or orphaned entries from lingering in the database.
        stale = [name for name in existing if name not in current_names]
        if stale:
            conn.executemany(queries.DELETE_DOCUMENT_BY_FILENAME, [(name,) for name in stale])
            logger.info("Removed %d document(s) no longer present: %s", len(stale), stale)

        for path in files:
            file_hash = _file_hash(path)
            if existing.get(path.name) == (file_hash, MODEL_NAME):
                continue  # unchanged file, same model — reuse existing embedding

            logger.info("Embedding: %s", path.name)
            doc_vec, preview = _embed_document(model, path)

            #UPSERT: insert a new row, or if the filename already exists (file changed,
            #or it was previously embedded with a different model), overwrite it with
            #the fresh embedding, hash, model name, and timestamp.
            conn.execute(
                queries.UPSERT_DOCUMENT,
                (path.name, path.suffix.lstrip("."), preview, _arr_to_blob(doc_vec), file_hash, MODEL_NAME),
            )

    return _load_from_db()

#this is the main function that external code should call to get the current document embedding index. It ensures that the database table exists, checks the in-memory cache for the index, and if it's not present or if a refresh is requested, it calls _sync_index() to update the index from the data directory and then returns it. This function abstracts away the details of how the index is built and maintained, providing a simple interface for other parts of the application to access the document embeddings.
def build_index(refresh: bool = False) -> list[DocumentEmbedding]:
    """Return the current document embedding index.

    On first call (or when refresh=True), scans DATA_DIR and embeds only files
    that are new or whose content hash changed since the last run; unchanged
    files reuse their stored embedding, and removed files drop out of the index.
    """
    global _index_cache
    _ensure_table()

    if _index_cache is not None and not refresh:
        return _index_cache

    _index_cache = _sync_index()
    return _index_cache
