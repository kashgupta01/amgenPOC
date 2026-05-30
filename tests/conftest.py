import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"

_SEED_TARGETS = [
    ("EGFR",  "Kinase",           "non-small cell lung cancer", "Small molecule", "Overexpressed in NSCLC",         "Resistance mutations",          "Active"),
    ("KRAS",  "Oncogene",         "lung cancer",                "Small molecule", "Driver mutation in NSCLC",       "Historically undruggable",      "Active"),
    ("PD-L1", "Checkpoint",       "melanoma",                   "Antibody",       "Immune evasion target",          "Autoimmune side effects",       "Active"),
    ("BRCA1", "Tumor Suppressor", "breast cancer",              "PARP inhibitor", "Synthetic lethality approach",   "Germline testing required",     "Inactive"),
    ("ALK",   "Fusion Protein",   "lung cancer",                "Small molecule", "ALK rearrangements in NSCLC",    "CNS penetration challenges",    "Deprioritized"),
]


@pytest.fixture(scope="session", autouse=True)
def seeded_db(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "target_knowledge.db"
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
        conn.executemany(
            """INSERT INTO targets
               (name, target_type, disease_context, modality,
                therapeutic_rationale, scientific_concerns, current_status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            _SEED_TARGETS,
        )

    with patch("config.DB_PATH", db_path), \
         patch("src.control_plane.search.DB_PATH", db_path), \
         patch("src.data_plane.repository.DB_PATH", db_path):
        yield db_path
