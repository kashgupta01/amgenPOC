# Data Model Overview

This model is built for flexible target records across diseases, target types, and modalities.

## Core Entities

- `Target`
  - Biological context
  - Therapeutic rationale
  - Scientific concerns
  - Status and lifecycle
  - Cross-disease applicability

- `EvidenceItem`
  - Source metadata
  - Evidence strength
  - Structured summary
  - Detail fields for semi-structured content

- `DecisionHistory`
  - Decision actions (advance, pause, deprioritize)
  - Supporting evidence
  - Rationale and notes
  - Audit trail for lineage tracking

## Adaptability Requirements

- Multiple disease contexts should be supported through free-text and structured tags.
- Target types should include genes, pathways, proteins, and other modalities.
- Modalities can represent small molecules, biologics, cell therapy, and more.
- Decision status must be queryable and updateable over time.

## Traceability

Each target record is designed to retain historical decisions and change rationale.
This supports scientist review and reuse of prior evaluations.
