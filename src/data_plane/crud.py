import sqlite3
from typing import Optional

from src.data_plane.models import DecisionEntry, EvidenceItem, TargetRecord


def insert_target(conn: sqlite3.Connection, target: TargetRecord) -> int:
    cursor = conn.execute(
        """
        INSERT INTO targets
            (name, target_type, disease_context, modality, therapeutic_rationale,
             scientific_concerns, current_status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            target.name,
            target.target_type,
            target.disease_context,
            target.modality,
            target.therapeutic_rationale,
            target.scientific_concerns,
            target.current_status,
            target.created_at.isoformat(),
            target.updated_at.isoformat(),
        ),
    )
    return cursor.lastrowid


def update_target(conn: sqlite3.Connection, target_id: int, fields: dict) -> None:
    allowed = {
        "name", "target_type", "disease_context", "modality",
        "therapeutic_rationale", "scientific_concerns", "current_status", "updated_at",
    }
    filtered = {k: v for k, v in fields.items() if k in allowed}
    if not filtered:
        return
    set_clause = ", ".join(f"{k} = ?" for k in filtered)
    conn.execute(
        f"UPDATE targets SET {set_clause} WHERE id = ?",
        (*filtered.values(), target_id),
    )


def delete_target(conn: sqlite3.Connection, target_id: int) -> None:
    conn.execute("DELETE FROM evidence_items WHERE target_id = ?", (target_id,))
    conn.execute("DELETE FROM decision_history WHERE target_id = ?", (target_id,))
    conn.execute("DELETE FROM targets WHERE id = ?", (target_id,))


def get_target_by_id(conn: sqlite3.Connection, target_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM targets WHERE id = ?", (target_id,)
    ).fetchone()


def insert_evidence_item(conn: sqlite3.Connection, target_id: int, item: EvidenceItem) -> int:
    cursor = conn.execute(
        """
        INSERT INTO evidence_items
            (target_id, source, evidence_type, evidence_strength, summary, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            target_id,
            item.source,
            item.evidence_type,
            item.evidence_strength,
            item.summary,
            item.details,
            item.created_at.isoformat(),
        ),
    )
    return cursor.lastrowid


def get_evidence_by_target(conn: sqlite3.Connection, target_id: int) -> list:
    return conn.execute(
        "SELECT * FROM evidence_items WHERE target_id = ? ORDER BY created_at DESC",
        (target_id,),
    ).fetchall()


def insert_decision(conn: sqlite3.Connection, target_id: int, entry: DecisionEntry) -> int:
    cursor = conn.execute(
        """
        INSERT INTO decision_history
            (target_id, decision, rationale, supporting_evidence,
             decision_date, changed_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            target_id,
            entry.decision,
            entry.rationale,
            entry.supporting_evidence,
            entry.decision_date.isoformat(),
            entry.changed_by,
            entry.notes,
        ),
    )
    return cursor.lastrowid


def get_decisions_by_target(conn: sqlite3.Connection, target_id: int) -> list:
    return conn.execute(
        "SELECT * FROM decision_history WHERE target_id = ? ORDER BY decision_date DESC",
        (target_id,),
    ).fetchall()
