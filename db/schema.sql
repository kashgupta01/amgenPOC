-- SQLite schema for Target Knowledge & Decision Tracking
-- and Document Embedding Index

CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY,
    filename     TEXT    NOT NULL UNIQUE,
    source_type  TEXT    NOT NULL,
    preview      TEXT,
    embedding    BLOB    NOT NULL,
    content_hash TEXT,
    model_name   TEXT,
    indexed_at   TEXT    DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS decision_history;
DROP TABLE IF EXISTS targets;
DROP TABLE IF EXISTS evidence_items;