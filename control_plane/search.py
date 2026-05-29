import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "target_knowledge.db"


def query_targets(filters: Dict[str, Optional[str]]) -> List[sqlite3.Row]:
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

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql, params)
        results = cursor.fetchall()

    return results
