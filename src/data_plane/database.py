import sqlite3
from pathlib import Path

from config import DB_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "db" / "schema.sql"


def initialize_database() -> None:
    logger.info("Initializing database at %s", DB_PATH)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())
        conn.commit()
    logger.info("Database initialized successfully")


if __name__ == "__main__":
    initialize_database()
