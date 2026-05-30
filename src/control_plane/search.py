import sqlite3
from typing import Dict, List, Optional

from config import DB_PATH


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

        #what does fetchall do? 
        #fetchall() retrieves all the rows of a query result, returning them as a list of tuples. An empty list is returned if there are no more rows to fetch.
        results = cursor.fetchall()
    #print("These are the results: ", print_all_results(results))
    return results

def print_all_results(results):
    #print(results.dtype(sqlite3.Row))
    for row in results:
        print(dict(row))