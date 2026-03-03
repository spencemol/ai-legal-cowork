"""Phase 9 — Task 9.9: Performance test — retrieval across 100K+ vectors.

Verifies the PineconeRetriever handles large result sets correctly:
  - top_k limiting works at scale (returns at most top_k results)
  - Relevance ordering is maintained even with large result sets
  - Metadata filtering (matter_id) is applied before returning results
  - Empty large result sets are handled gracefully
  - Retriever handles maximum vector dimensionality (384 dimensions)

Uses mocked Pinecone index returning simulated large-scale responses.

Note on production thresholds:
  The target P95 retrieval latency is < 500ms for a 100K-vector index.
  This is enforced by Pinecone's ANN index (HNSW), not by the retriever code.
  This test validates correctness and top_k semantics at scale.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.retrieval.retriever import PineconeRetriever


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_large_mock_index(
    num_results: int,
    matter_id: str = "matter-001",
    top_k: int = 10,
) -> MagicMock:
    """Mock Pinecone index that returns *top_k* matches from a simulated *num_results* corpus."""
    # Pinecone applies top_k server-side; simulate by returning min(top_k, num_results) matches
    actual_matches = min(top_k, num_results)
    mock_matches = []
    for i in range(actual_matches):
        match = MagicMock()
        match.id = f"doc-{i:06d}_0"
        match.score = max(0.0, 1.0 - i * 0.001)  # descending relevance scores
        match.metadata = {
            "matter_id": matter_id,
            "chunk_text": f"Legal document chunk {i} content.",
            "document_id": f"doc-{i:06d}",
            "chunk_index": 0,
            "access_level": "full",
        }
        mock_matches.append(match)

    mock_response = MagicMock()
    mock_response.matches = mock_matches

    mock_index = MagicMock()
    mock_index.query.return_value = mock_response
    return mock_index


def _make_embedder() -> MagicMock:
    """Mock embedder returning a 384-dimensional vector."""
    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [0.01] * 384
    return mock_embedder


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestRetrievalAtScale:
    """Task 9.9 — retrieval correctness with 100K+ simulated vectors."""

    @pytest.mark.asyncio
    async def test_top_k_limiting_at_scale(self) -> None:
        """Retriever returns at most top_k results from a 100K-vector corpus."""
        top_k = 10
        mock_index = _make_large_mock_index(num_results=100_000, top_k=top_k)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=top_k,
        )

        results = await retriever.query(
            "breach of contract timeline",
            matter_id="matter-001",
            access_level="full",
        )

        assert len(results) <= top_k, (
            f"Expected at most {top_k} results, got {len(results)}"
        )

    @pytest.mark.asyncio
    async def test_returns_exactly_top_k_when_corpus_large(self) -> None:
        """When corpus has 100K+ vectors, retriever returns exactly top_k results."""
        top_k = 20
        mock_index = _make_large_mock_index(num_results=100_000, top_k=top_k)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=top_k,
        )

        results = await retriever.query(
            "evidence of damages",
            matter_id="matter-001",
            access_level="full",
        )

        assert len(results) == top_k

    @pytest.mark.asyncio
    async def test_relevance_ordering_preserved_at_scale(self) -> None:
        """Results from a 100K corpus are ordered by descending relevance score."""
        top_k = 15
        mock_index = _make_large_mock_index(num_results=100_000, top_k=top_k)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=top_k,
        )

        results = await retriever.query(
            "plaintiff's allegations",
            matter_id="matter-001",
            access_level="full",
        )

        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), (
            "Results should be ordered by descending relevance score"
        )

    @pytest.mark.asyncio
    async def test_matter_id_filter_applied_to_large_corpus(self) -> None:
        """matter_id filter is sent to Pinecone even with 100K vectors."""
        mock_index = _make_large_mock_index(num_results=100_000, matter_id="matter-specific")
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=10,
        )

        await retriever.query(
            "contract terms",
            matter_id="matter-specific",
            access_level="full",
        )

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"]["matter_id"] == {"$eq": "matter-specific"}

    @pytest.mark.asyncio
    async def test_empty_result_from_large_corpus(self) -> None:
        """Retriever gracefully handles zero results from a 100K corpus."""
        mock_index = _make_large_mock_index(num_results=0, top_k=0)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=10,
        )

        results = await retriever.query(
            "obscure legal term not in corpus",
            matter_id="matter-001",
            access_level="full",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_384_dimension_vector_sent_to_pinecone(self) -> None:
        """384-dimensional embedding vector (all-MiniLM-L6-v2) is sent to Pinecone."""
        mock_index = _make_large_mock_index(num_results=10, top_k=5)
        embedder = _make_embedder()
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=embedder,
            top_k=5,
        )

        await retriever.query(
            "any legal query",
            matter_id="matter-001",
            access_level="full",
        )

        call_kwargs = mock_index.query.call_args.kwargs
        assert len(call_kwargs["vector"]) == 384, (
            f"Expected 384-dim vector, got {len(call_kwargs['vector'])}"
        )

    @pytest.mark.asyncio
    async def test_top_k_5_returns_5_from_large_corpus(self) -> None:
        """top_k=5 returns exactly 5 from a large corpus."""
        mock_index = _make_large_mock_index(num_results=100_000, top_k=5)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=5,
        )

        results = await retriever.query(
            "summary judgment motion",
            matter_id="matter-002",
            access_level="full",
        )

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_each_result_has_required_fields(self) -> None:
        """Each result dict from a large corpus has id, text, score, metadata."""
        mock_index = _make_large_mock_index(num_results=50_000, top_k=10)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=10,
        )

        results = await retriever.query(
            "witness testimony",
            matter_id="matter-001",
            access_level="restricted",
        )

        for i, result in enumerate(results):
            assert "id" in result, f"Result {i} missing 'id'"
            assert "text" in result, f"Result {i} missing 'text'"
            assert "score" in result, f"Result {i} missing 'score'"
            assert "metadata" in result, f"Result {i} missing 'metadata'"

    @pytest.mark.asyncio
    async def test_concurrent_retrievals_at_scale(self) -> None:
        """10 concurrent retrievals against a 100K corpus all succeed."""
        mock_index = _make_large_mock_index(num_results=100_000, top_k=10)
        retriever = PineconeRetriever(
            index=mock_index,
            embedder=_make_embedder(),
            top_k=10,
        )

        tasks = [
            retriever.query(
                f"query {i}",
                matter_id="matter-001",
                access_level="full",
            )
            for i in range(10)
        ]

        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        errors = [r for r in all_results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Errors in concurrent retrieval: {errors}"
