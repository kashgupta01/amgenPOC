import sqlite3
from typing import Optional

from config import DB_PATH
from src.utils.error_handler import handle_db_errors
from src.utils.logger import get_logger
from src.data_plane.crud import (
    delete_target,
    get_decisions_by_target,
    get_evidence_by_target,
    get_target_by_id,
    insert_decision,
    insert_evidence_item,
    insert_target,
    update_target,
)
from src.data_plane.models import DecisionEntry, EvidenceItem, TargetRecord

logger = get_logger(__name__)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@handle_db_errors
def create_target(target: TargetRecord) -> int:
    with _connect() as conn:
        target_id = insert_target(conn, target)
        for item in target.evidence:
            insert_evidence_item(conn, target_id, item)
        for entry in target.decision_history:
            insert_decision(conn, target_id, entry)
    return target_id


@handle_db_errors
def get_target_with_evidence(target_id: int) -> Optional[dict]:
    with _connect() as conn:
        row = get_target_by_id(conn, target_id)
        if row is None:
            return None
        evidence = get_evidence_by_target(conn, target_id)
        decisions = get_decisions_by_target(conn, target_id)
    return {
        **dict(row),
        "evidence": [dict(e) for e in evidence],
        "decision_history": [dict(d) for d in decisions],
    }


@handle_db_errors
def add_evidence_to_target(target_id: int, item: EvidenceItem) -> int:
    with _connect() as conn:
        return insert_evidence_item(conn, target_id, item)


@handle_db_errors
def add_decision_to_target(target_id: int, entry: DecisionEntry) -> int:
    with _connect() as conn:
        return insert_decision(conn, target_id, entry)


@handle_db_errors
def update_target_status(target_id: int, new_status: str) -> None:
    with _connect() as conn:
        update_target(conn, target_id, {"current_status": new_status})


@handle_db_errors
def remove_target(target_id: int) -> None:
    with _connect() as conn:
        delete_target(conn, target_id)
