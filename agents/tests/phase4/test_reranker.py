"""Unit tests for the bge-reranker module (task 4.6).

Task 4.6: bge-reranker — rerank retrieved chunks by relevance to query

FlagEmbedding.FlagReranker is fully mocked.

RED: These tests fail until app/retrieval/reranker.py is implemented.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.retrieval.reranker import BGEReranker


@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {
            "id": f"doc-001_{i}",
            "text": f"Legal text chunk number {i} about the contract dispute.",
            "score": 0.9 - i * 0.05,
            "metadata": {
                "document_id": "doc-001",
                "matter_id": "matter-uuid-001",
                "chunk_index": i,
                "file_name": "brief.pdf",
                "page_number": i + 1,
            },
        }
        for i in range(5)
    ]


class TestBGERerankerInit:
    def test_instantiation_with_mock(self):
        with patch("app.retrieval.reranker.FlagReranker"):
            reranker = BGEReranker()
            assert reranker is not None

    def test_default_top_k(self):
        with patch("app.retrieval.reranker.FlagReranker"):
            reranker = BGEReranker()
            assert reranker.top_k > 0

    def test_custom_top_k(self):
        with patch("app.retrieval.reranker.FlagReranker"):
            reranker = BGEReranker(top_k=5)
            assert reranker.top_k == 5

    def test_custom_model_name(self):
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag:
            BGEReranker(model_name="BAAI/bge-reranker-large")
            # Should pass model name to FlagReranker
            mock_flag.assert_called_once()


class TestBGERerankerRerank:
    def test_rerank_returns_list(self, sample_chunks):
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.95, 0.80, 0.75, 0.60, 0.55]
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=3)
            result = reranker.rerank(
                query="What is the contract dispute about?",
                chunks=sample_chunks,
            )

        assert isinstance(result, list)

    def test_rerank_returns_at_most_top_k(self, sample_chunks):
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.95, 0.80, 0.75, 0.60, 0.55]
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=3)
            result = reranker.rerank(
                query="Contract dispute",
                chunks=sample_chunks,
            )

        assert len(result) <= 3

    def test_rerank_chunks_have_rerank_score(self, sample_chunks):
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.95, 0.80, 0.75, 0.60, 0.55]
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=5)
            result = reranker.rerank(
                query="Contract breach",
                chunks=sample_chunks,
            )

        for chunk in result:
            assert "rerank_score" in chunk

    def test_rerank_sorted_by_score_descending(self, sample_chunks):
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            # Assign scores in reverse order to test sorting
            mock_reranker.compute_score.return_value = [0.10, 0.30, 0.90, 0.50, 0.70]
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=5)
            result = reranker.rerank(
                query="Contract breach",
                chunks=sample_chunks,
            )

        scores = [c["rerank_score"] for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_empty_chunks_returns_empty(self):
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = []
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=5)
            result = reranker.rerank(query="Test", chunks=[])

        assert result == []

    def test_rerank_preserves_chunk_fields(self, sample_chunks):
        """Reranked chunks must retain all original fields."""
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.95, 0.80, 0.75, 0.60, 0.55]
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=5)
            result = reranker.rerank(
                query="Contract",
                chunks=sample_chunks,
            )

        for chunk in result:
            assert "id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk

    def test_rerank_calls_compute_score_with_pairs(self, sample_chunks):
        """FlagReranker.compute_score must be called with [query, text] pairs."""
        with patch("app.retrieval.reranker.FlagReranker") as mock_flag_cls:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]
            mock_flag_cls.return_value = mock_reranker

            reranker = BGEReranker(top_k=5)
            reranker.rerank(query="Contract breach", chunks=sample_chunks)

            call_args = mock_reranker.compute_score.call_args
            # First argument should be a list of pairs
            pairs_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("sentence_pairs")
            assert pairs_arg is not None
            assert isinstance(pairs_arg, list)
            # Each pair should be [query, chunk_text]
            for pair in pairs_arg:
                assert len(pair) == 2
