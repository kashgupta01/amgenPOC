"""Tests for document retrieval pipeline and regex filter utility."""

import re
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.control_plane.retrieval import _cosine, retrieve
from src.data_plane.embeddings import DocumentEmbedding, _chunk_text
from src.integration_plane.app import _compile_filter


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_doc(filename: str, source_type: str, vec: list) -> DocumentEmbedding:
    return DocumentEmbedding(
        filename=filename,
        source_type=source_type,
        preview="preview text",
        embedding=np.array(vec, dtype=float),
    )


def _mock_encoder(query_vec: list) -> MagicMock:
    """Mock SentenceTransformer whose encode() returns query_vec as a 2-D array."""
    mock = MagicMock()
    mock.encode.return_value = np.array([query_vec])
    return mock


# ── _compile_filter ────────────────────────────────────────────────────────────

class TestCompileFilter:
    def test_empty_string_returns_none(self):
        assert _compile_filter("") is None

    def test_whitespace_only_returns_none(self):
        assert _compile_filter("   ") is None

    def test_valid_pattern_returns_compiled_regex(self):
        assert isinstance(_compile_filter("egfr"), re.Pattern)

    def test_matching_is_case_insensitive(self):
        pattern = _compile_filter("egfr")
        assert pattern.search("EGFR_study.pdf")
        assert pattern.search("egfr_analysis.docx")
        assert not pattern.search("BRCA1_report.pdf")

    def test_invalid_regex_returns_none(self):
        assert _compile_filter("(unclosed") is None
        assert _compile_filter("[bad") is None

    def test_alternation_matches_either_type(self):
        pattern = _compile_filter("pdf|docx")
        assert pattern.search("report.pdf")
        assert pattern.search("study.docx")
        assert not pattern.search("data.xlsx")

    def test_start_anchor_limits_match_position(self):
        pattern = _compile_filter("^EGFR")
        assert pattern.search("EGFR_mutation.pdf")
        assert not pattern.search("study_EGFR.pdf")


# ── _chunk_text ────────────────────────────────────────────────────────────────

class TestChunkText:
    def test_empty_text_returns_empty_list(self):
        assert _chunk_text("") == []

    def test_short_text_is_one_chunk(self):
        text = " ".join(["word"] * 100)
        assert len(_chunk_text(text)) == 1

    def test_long_text_splits_into_equal_chunks(self):
        text = " ".join(["word"] * 900)
        chunks = _chunk_text(text)
        assert len(chunks) == 3
        assert all(len(c.split()) == 300 for c in chunks)

    def test_remainder_becomes_final_shorter_chunk(self):
        text = " ".join(["word"] * 350)
        chunks = _chunk_text(text)
        assert len(chunks) == 2
        assert len(chunks[0].split()) == 300
        assert len(chunks[1].split()) == 50


# ── _cosine ────────────────────────────────────────────────────────────────────

class TestCosine:
    def test_identical_vectors_score_one(self):
        v = np.array([1.0, 0.0, 0.0])
        assert abs(_cosine(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors_score_zero(self):
        a, b = np.array([1.0, 0.0]), np.array([0.0, 1.0])
        assert abs(_cosine(a, b)) < 1e-6

    def test_opposite_vectors_score_negative_one(self):
        a, b = np.array([1.0, 0.0]), np.array([-1.0, 0.0])
        assert abs(_cosine(a, b) + 1.0) < 1e-6


# ── retrieve ───────────────────────────────────────────────────────────────────

class TestRetrieve:
    def test_results_sorted_by_score_descending(self):
        docs = [
            _make_doc("low.pdf",  "pdf", [0.0, 1.0]),  # orthogonal to query → lowest
            _make_doc("high.pdf", "pdf", [1.0, 0.0]),  # parallel to query  → highest
            _make_doc("mid.pdf",  "pdf", [0.7, 0.7]),  # diagonal            → middle
        ]
        with patch("src.control_plane.retrieval.get_model", return_value=_mock_encoder([1.0, 0.0])), \
             patch("src.control_plane.retrieval.build_index", return_value=docs):
            results = retrieve("test query", k=3)

        assert results[0]["filename"] == "high.pdf"
        assert results[1]["filename"] == "mid.pdf"
        assert results[2]["filename"] == "low.pdf"

    def test_k_limits_number_of_results(self):
        docs = [_make_doc(f"doc{i}.pdf", "pdf", [1.0, 0.0]) for i in range(10)]
        with patch("src.control_plane.retrieval.get_model", return_value=_mock_encoder([1.0, 0.0])), \
             patch("src.control_plane.retrieval.build_index", return_value=docs):
            assert len(retrieve("query", k=3)) == 3

    def test_k_larger_than_index_returns_all(self):
        docs = [_make_doc("only.pdf", "pdf", [1.0, 0.0])]
        with patch("src.control_plane.retrieval.get_model", return_value=_mock_encoder([1.0, 0.0])), \
             patch("src.control_plane.retrieval.build_index", return_value=docs):
            assert len(retrieve("query", k=10)) == 1

    def test_result_contains_required_fields(self):
        docs = [_make_doc("egfr.pdf", "pdf", [1.0, 0.0])]
        with patch("src.control_plane.retrieval.get_model", return_value=_mock_encoder([1.0, 0.0])), \
             patch("src.control_plane.retrieval.build_index", return_value=docs):
            result = retrieve("egfr", k=1)[0]
        assert set(result.keys()) == {"filename", "source_type", "score", "preview"}

    def test_empty_index_returns_empty_list(self):
        with patch("src.control_plane.retrieval.get_model", return_value=_mock_encoder([1.0, 0.0])), \
             patch("src.control_plane.retrieval.build_index", return_value=[]):
            assert retrieve("query", k=5) == []

    def test_score_is_rounded_to_four_decimal_places(self):
        docs = [_make_doc("doc.pdf", "pdf", [0.6, 0.8])]
        with patch("src.control_plane.retrieval.get_model", return_value=_mock_encoder([1.0, 0.0])), \
             patch("src.control_plane.retrieval.build_index", return_value=docs):
            score = retrieve("query", k=1)[0]["score"]
        assert score == round(score, 4)
