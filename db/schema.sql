-- SQLite schema for Target Knowledge & Decision Tracking
-- and Document Embedding Index

CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY,
    filename    TEXT    NOT NULL UNIQUE,
    source_type TEXT    NOT NULL,
    preview     TEXT,
    embedding   BLOB    NOT NULL,
    indexed_at  TEXT    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    target_type TEXT NOT NULL,
    disease_context TEXT,
    modality TEXT,
    therapeutic_rationale TEXT,
    scientific_concerns TEXT,
    current_status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id INTEGER PRIMARY KEY,
    target_id INTEGER NOT NULL,
    source TEXT,
    evidence_type TEXT,
    evidence_strength TEXT,
    summary TEXT,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(target_id) REFERENCES targets(id)
);

CREATE TABLE IF NOT EXISTS decision_history (
    id INTEGER PRIMARY KEY,
    target_id INTEGER NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT,
    supporting_evidence TEXT,
    decision_date TEXT DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT,
    notes TEXT,
    FOREIGN KEY(target_id) REFERENCES targets(id)
);
