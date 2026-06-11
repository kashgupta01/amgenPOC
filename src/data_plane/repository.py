#what is this file doing? This file defines a repository layer for managing targets, evidence, and decisions in a SQLite database. It provides functions to create, retrieve, update, and delete target records, as well as to add evidence and decisions associated with those targets. The repository abstracts away the database interactions and provides a clean interface for the rest of the application to work with the data. It uses a connection function to establish a connection to the database and a set of CRUD functions defined in the src.data_plane.crud module to perform the necessary database operations. Additionally, it includes error handling through the use of a decorator to manage database errors gracefully.

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
    logger.info("Creating target %r with %d evidence item(s) and %d decision(s)",
                target.name, len(target.evidence), len(target.decision_history))
    with _connect() as conn:
        target_id = insert_target(conn, target)
        for item in target.evidence:
            insert_evidence_item(conn, target_id, item)
        for entry in target.decision_history:
            insert_decision(conn, target_id, entry)
    logger.info("Target %r created with id=%d", target.name, target_id)
    return target_id


@handle_db_errors
def get_target_with_evidence(target_id: int) -> Optional[dict]:
    logger.debug("Fetching target id=%d with evidence and decisions", target_id)
    with _connect() as conn:
        row = get_target_by_id(conn, target_id)
        if row is None:
            logger.warning("get_target_with_evidence: target id=%d not found", target_id)
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
    logger.info("Adding evidence to target id=%d (type=%s)", target_id, item.evidence_type)
    with _connect() as conn:
        return insert_evidence_item(conn, target_id, item)


@handle_db_errors
def add_decision_to_target(target_id: int, entry: DecisionEntry) -> int:
    logger.info("Adding decision %r to target id=%d", entry.decision, target_id)
    with _connect() as conn:
        return insert_decision(conn, target_id, entry)


@handle_db_errors
def update_target_status(target_id: int, new_status: str) -> None:
    logger.info("Updating target id=%d status to %r", target_id, new_status)
    with _connect() as conn:
        update_target(conn, target_id, {"current_status": new_status})


@handle_db_errors
def remove_target(target_id: int) -> None:
    logger.info("Removing target id=%d", target_id)
    with _connect() as conn:
        delete_target(conn, target_id)
    logger.info("Target id=%d removed", target_id)
