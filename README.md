# Target Knowledge & Decision Tracking Prototype

A lightweight project scaffold for a knowledge base focused on drug target evaluation, decision lineage, and evidence tracking.

## Purpose

This structure is designed to satisfy the proposal's key deliverables:
- Data modeling for target records, evidence, rationale, risks, and decision history
- SQLite-backed structured knowledge storage with update and traceability support
- Search/filter/retrieval capabilities
- Target profile and summary views
- Evidence gap detection and decision lineage tracking
- Browser-based prototype architecture for a simple UI

## Project Structure

- `src/control_plane/` - search, query, and decision orchestration logic
- `src/data_plane/` - data model, storage, and persistence layer
- `src/integration_plane/` - API interface and external integration
- `db/` - database schema and migration resources
- `docs/` - design, architecture, and model documentation
- `tests/` - validation of data model, database, and search/filter functions
- `notebooks/` - exploratory analysis or prototype data inspection

## Getting Started

1. Create a Python venv and install dependencies:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Initialize the SQLite database:
```bash
python -m src.data_plane.database
```

3. Start the prototype app:
```bash
python -m src.integration_plane.app
```

## Mapping to Core Tasks

- Data model: `src/data_plane/models.py`, `docs/data_model.md`
- Knowledge base: `src/data_plane/database.py`, `db/schema.sql`
- Search/filter: `src/control_plane/search.py`
- Summary/profile views: `src/integration_plane/app.py`
- Evidence gaps: `src/data_plane/models.py` and future logic in `src/control_plane/search.py`
- UI prototype: `src/integration_plane/app.py`
- Decision lineage: `src/data_plane/models.py` and `docs/system_design.md`
- Documentation & handoff: `docs/`
