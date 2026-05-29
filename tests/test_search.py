import pytest
from src.control_plane.search import query_targets


def test_query_targets_returns_list():
    results = query_targets({})
    assert isinstance(results, list)
