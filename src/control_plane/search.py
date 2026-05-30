import sqlite3
from typing import Dict, List, Optional

from config import DB_PATH
from src.utils.error_handler import handle_db_errors
from src.utils.exceptions import DatabaseError, ValidationError
from src.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_FILTER_KEYS = {"disease_context", "target_type", "current_status"}


@handle_db_errors
def query_targets(filters: Dict[str, Optional[str]]) -> List[sqlite3.Row]:
    unknown = set(filters.keys()) - ALLOWED_FILTER_KEYS
    if unknown:
        raise ValidationError(f"Unknown filter keys: {unknown}")

    conditions = []
    params = []

    if filters.get("disease_context"):
        conditions.append("disease_context LIKE ?")
        params.append(f"%{filters['disease_context']}%")
    if filters.get("target_type"):
        conditions.append("target_type = ?")
        params.append(filters["target_type"])
    if filters.get("current_status"):
        conditions.append("current_status = ?")
        params.append(filters["current_status"])

    sql = "SELECT * FROM targets"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY updated_at DESC"

    logger.debug("Executing query: %s | params: %s", sql, params)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql, params)
        results = cursor.fetchall()

    logger.info("query_targets returned %d row(s) for filters: %s", len(results), filters)
    return results


def print_all_results(results):
    for row in results:
        print(dict(row))
