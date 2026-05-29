# System Design

## Architecture

- `src/data_plane/models.py` defines the domain objects for targets, evidence, and decisions.
- `src/data_plane/database.py` provides SQLite schema creation and persistence support.
- `src/control_plane/search.py` implements search and filter functions for discovery.
- `src/integration_plane/app.py` is the entrypoint for a lightweight browser-based prototype.

## Goals

- Easily store structured and semi-structured data.
- Maintain decision lineage and traceability.
- Enable filtering by disease, evidence strength, status, and type.
- Highlight missing data and evidence gaps.
- Provide a prototype UI for registration and review of target records.

## Future Extensions

- Add AI-assisted annotation workflows.
- Add export/import and versioned audit entries.
- Add authentication and collaboration features.
