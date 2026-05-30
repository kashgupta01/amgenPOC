import pytest
from src.control_plane.search import query_targets


def test_query_targets_returns_list():
    results = query_targets({})
    assert isinstance(results, list)
    assert len(results) == 5

#test_query_targets_returns_list()


def test_query_targets_record_fields():
    results = query_targets({})
    expected_fields = {"id", "name", "target_type", "disease_context", "modality",
                       "therapeutic_rationale", "scientific_concerns", "current_status",
                       "created_at", "updated_at"}
    for row in results:
        assert expected_fields == set(row.keys())


def test_query_targets_filter_by_status():
    active = query_targets({"current_status": "Active"})
    assert len(active) == 3
    assert all(row["current_status"] == "Active" for row in active)


def test_query_targets_filter_by_disease_context():
    results = query_targets({"disease_context": "lung"})
    assert len(results) >= 1
    assert all("lung" in (row["disease_context"] or "").lower() for row in results)


def test_query_targets_filter_by_target_type():
    results = query_targets({"target_type": "Kinase"})
    assert len(results) == 1
    assert results[0]["name"] == "EGFR"
