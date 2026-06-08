"""
Centralized SQL query strings for the SQLite database.

Every CREATE / SELECT / INSERT / UPDATE / DELETE / ALTER / PRAGMA statement run
against the database lives here rather than scattered inline across modules,
so the full SQL surface can be reviewed and audited from one place.
"""

# ── documents table (embedding index) ────────────────────────────────────────

CREATE_DOCUMENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS documents (
        id           INTEGER PRIMARY KEY,
        filename     TEXT    NOT NULL UNIQUE,
        source_type  TEXT    NOT NULL,
        preview      TEXT,
        embedding    BLOB    NOT NULL,
        content_hash TEXT,
        model_name   TEXT,
        indexed_at   TEXT    DEFAULT CURRENT_TIMESTAMP
    )
"""

PRAGMA_DOCUMENTS_TABLE_INFO = "PRAGMA table_info(documents)"
ALTER_DOCUMENTS_ADD_CONTENT_HASH = "ALTER TABLE documents ADD COLUMN content_hash TEXT"
ALTER_DOCUMENTS_ADD_MODEL_NAME = "ALTER TABLE documents ADD COLUMN model_name TEXT"

SELECT_DOCUMENTS_SYNC_STATE = "SELECT filename, content_hash, model_name FROM documents"

DELETE_DOCUMENT_BY_FILENAME = "DELETE FROM documents WHERE filename = ?"

UPSERT_DOCUMENT = """
    INSERT INTO documents (filename, source_type, preview, embedding, content_hash, model_name)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(filename) DO UPDATE SET
        source_type  = excluded.source_type,
        preview      = excluded.preview,
        embedding    = excluded.embedding,
        content_hash = excluded.content_hash,
        model_name   = excluded.model_name,
        indexed_at   = CURRENT_TIMESTAMP
"""

SELECT_DOCUMENTS_FOR_INDEX = """
    SELECT filename, source_type, preview, embedding
    FROM documents
    ORDER BY filename
"""

# ── targets table ─────────────────────────────────────────────────────────────

INSERT_TARGET = """
    INSERT INTO targets
        (name, target_type, disease_context, modality, therapeutic_rationale,
         scientific_concerns, current_status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_TARGET_TEMPLATE = "UPDATE targets SET {set_clause} WHERE id = ?"

SELECT_TARGET_BY_ID = "SELECT * FROM targets WHERE id = ?"

SELECT_TARGETS_BASE = "SELECT * FROM targets"
TARGETS_ORDER_BY_UPDATED = " ORDER BY updated_at DESC"

# WHERE-clause fragments used by query_targets() to build a dynamic filter
FILTER_DISEASE_CONTEXT = "disease_context LIKE ?"
FILTER_TARGET_TYPE = "target_type = ?"
FILTER_CURRENT_STATUS = "current_status = ?"

DELETE_TARGET_BY_ID = "DELETE FROM targets WHERE id = ?"

# ── evidence_items table ──────────────────────────────────────────────────────

INSERT_EVIDENCE_ITEM = """
    INSERT INTO evidence_items
        (target_id, source, evidence_type, evidence_strength, summary, details, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SELECT_EVIDENCE_BY_TARGET = (
    "SELECT * FROM evidence_items WHERE target_id = ? ORDER BY created_at DESC"
)

DELETE_EVIDENCE_BY_TARGET = "DELETE FROM evidence_items WHERE target_id = ?"

# ── decision_history table ────────────────────────────────────────────────────

INSERT_DECISION = """
    INSERT INTO decision_history
        (target_id, decision, rationale, supporting_evidence,
         decision_date, changed_by, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SELECT_DECISIONS_BY_TARGET = (
    "SELECT * FROM decision_history WHERE target_id = ? ORDER BY decision_date DESC"
)

DELETE_DECISIONS_BY_TARGET = "DELETE FROM decision_history WHERE target_id = ?"
