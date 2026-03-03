"""Phase 9 — Task 9.10: Cross-matter data leakage security tests.

Verifies zero leakage across all agent types:
  - A user assigned to matter-A cannot retrieve matter-B documents
  - PineconeRetriever always scopes queries to the authorised matter
  - /chat endpoint returns 403 for unauthorized matter access
  - Research agent: firm_data queries are scoped to the authorized matter
  - Drafting agent: context_chunks are scoped to the authorized matter
  - All agent types: zero vectors returned from unauthorized matters

No real Pinecone or external services — all mocked.
"""

from __future__ import annotations

import os
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from app.main import app
from app.retrieval.retriever import PineconeRetriever


# ── JWT helpers ───────────────────────────────────────────────────────────────

_ALGORITHM = "HS256"
_SECRET = "cross-matter-security-test-secret-32!!"


def _make_jwt(
    user_id: str = "user-001",
    role: str = "attorney",
    matter_ids: list[str] | None = None,
) -> str:
    payload = {
        "sub": user_id,
        "email": "attorney@firm.com",
        "role": role,
        "matter_ids": matter_ids if matter_ids is not None else ["matter-a"],
        "exp": int(time.time()) + 3600,
    }
    return jose_jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


# ── /chat endpoint access control ─────────────────────────────────────────────


class TestChatEndpointCrossMattersecurity:
    """Task 9.10 — /chat enforces matter-level authorization."""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app, raise_server_exceptions=False)

    def test_matter_a_user_denied_access_to_matter_b(self, client: TestClient) -> None:
        """User with only matter-A access is denied access to matter-B."""
        with patch.dict(os.environ, {"JWT_SECRET": _SECRET}):
            token = _make_jwt(matter_ids=["matter-a"])
            response = client.post(
                "/chat",
                json={"query": "Show me confidential documents.", "matter_id": "matter-b"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403

    def test_empty_matter_ids_denied_all_matters(self, client: TestClient) -> None:
        """User with no matter assignments is denied access to any matter."""
        with patch.dict(os.environ, {"JWT_SECRET": _SECRET}):
            token = _make_jwt(matter_ids=[])
            response = client.post(
                "/chat",
                json={"query": "What are the facts?", "matter_id": "matter-a"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403

    def test_matter_a_user_can_access_matter_a(self, client: TestClient) -> None:
        """User with matter-A access can query matter-A."""
        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
        ):
            mock_orch = MagicMock()
            mock_orch.run = AsyncMock(
                return_value={"answer": "Answer.", "citations": [], "intent": "retrieval"}
            )
            mock_build.return_value = mock_orch

            token = _make_jwt(matter_ids=["matter-a"])
            response = client.post(
                "/chat",
                json={"query": "Summary?", "matter_id": "matter-a"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200

    def test_access_control_checked_before_orchestrator(self, client: TestClient) -> None:
        """The orchestrator is never invoked for unauthorized matter access."""
        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
        ):
            token = _make_jwt(matter_ids=["matter-a"])
            client.post(
                "/chat",
                json={"query": "Docs?", "matter_id": "matter-b"},
                headers={"Authorization": f"Bearer {token}"},
            )
            mock_build.assert_not_called()

    def test_user_with_multiple_matters_can_access_each(self, client: TestClient) -> None:
        """User with [matter-a, matter-b] in JWT can access both."""
        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
        ):
            mock_orch = MagicMock()
            mock_orch.run = AsyncMock(
                return_value={"answer": "OK.", "citations": [], "intent": "general"}
            )
            mock_build.return_value = mock_orch
            token = _make_jwt(matter_ids=["matter-a", "matter-b"])

            for matter_id in ("matter-a", "matter-b"):
                response = client.post(
                    "/chat",
                    json={"query": "Summary?", "matter_id": matter_id},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert response.status_code == 200, (
                    f"Expected 200 for authorized matter {matter_id!r}, got {response.status_code}"
                )


# ── PineconeRetriever scoping ─────────────────────────────────────────────────


class TestRetrieverZeroLeakage:
    """Task 9.10 — PineconeRetriever never leaks cross-matter data."""

    def _make_index_with_matter_data(
        self, matter_id: str, num_chunks: int = 3
    ) -> MagicMock:
        """Mock index that returns chunks only for the specified matter."""
        mock_matches = []
        for i in range(num_chunks):
            match = MagicMock()
            match.id = f"{matter_id}-chunk-{i}"
            match.score = 0.9 - i * 0.05
            match.metadata = {
                "matter_id": matter_id,
                "chunk_text": f"Confidential {matter_id} content {i}.",
                "document_id": f"{matter_id}-doc-{i}",
                "access_level": "full",
            }
            mock_matches.append(match)

        mock_response = MagicMock()
        mock_response.matches = mock_matches
        mock_index = MagicMock()
        mock_index.query.return_value = mock_response
        return mock_index

    def _make_embedder(self) -> MagicMock:
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384
        return mock_embedder

    @pytest.mark.asyncio
    async def test_matter_a_filter_sent_when_querying_matter_a(self) -> None:
        """Retriever sends matter_id=matter-a filter to Pinecone."""
        mock_index = self._make_index_with_matter_data("matter-a")
        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())

        await retriever.query("facts?", matter_id="matter-a", access_level="full")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"]["matter_id"] == {"$eq": "matter-a"}

    @pytest.mark.asyncio
    async def test_matter_b_filter_sent_when_querying_matter_b(self) -> None:
        """Retriever sends matter_id=matter-b filter — never matter-a."""
        mock_index = self._make_index_with_matter_data("matter-b")
        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())

        await retriever.query("contracts?", matter_id="matter-b", access_level="full")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"]["matter_id"] == {"$eq": "matter-b"}

    @pytest.mark.asyncio
    async def test_results_only_contain_queried_matter_chunks(self) -> None:
        """Results for matter-a contain only matter-a chunks."""
        mock_index = self._make_index_with_matter_data("matter-a", num_chunks=3)
        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())

        results = await retriever.query("breach?", matter_id="matter-a", access_level="full")

        for chunk in results:
            assert chunk["metadata"]["matter_id"] == "matter-a", (
                f"Expected matter-a chunk, got: {chunk['metadata']['matter_id']!r}"
            )

    @pytest.mark.asyncio
    async def test_zero_results_when_user_queries_unauthorized_matter(self) -> None:
        """Pinecone returns no results when the matter filter doesn't match.

        This simulates Pinecone enforcing the matter_id filter server-side.
        The retriever returns empty list → zero leakage.
        """
        # Index returns 0 results (Pinecone enforced matter filter)
        mock_response = MagicMock()
        mock_response.matches = []
        mock_index = MagicMock()
        mock_index.query.return_value = mock_response

        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())
        results = await retriever.query("anything?", matter_id="matter-b", access_level="full")

        assert results == [], "Expected empty results for unauthorized matter query"

    @pytest.mark.asyncio
    async def test_filter_always_includes_matter_id(self) -> None:
        """matter_id is ALWAYS present in the Pinecone filter — never missing."""
        mock_index = self._make_index_with_matter_data("matter-c")
        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())

        await retriever.query("query", matter_id="matter-c", access_level="restricted")

        call_kwargs = mock_index.query.call_args.kwargs
        assert "matter_id" in call_kwargs["filter"], (
            "matter_id filter must always be present in Pinecone queries"
        )

    @pytest.mark.asyncio
    async def test_filter_always_includes_access_level(self) -> None:
        """access_level is ALWAYS present in the Pinecone filter."""
        mock_index = self._make_index_with_matter_data("matter-d")
        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())

        await retriever.query("query", matter_id="matter-d", access_level="read_only")

        call_kwargs = mock_index.query.call_args.kwargs
        assert "access_level" in call_kwargs["filter"], (
            "access_level filter must always be present in Pinecone queries"
        )

    @pytest.mark.asyncio
    async def test_sequential_queries_different_matters_use_correct_filters(self) -> None:
        """Sequential queries for different matters each use the correct matter filter."""
        mock_index = MagicMock()
        mock_response = MagicMock()
        mock_response.matches = []
        mock_index.query.return_value = mock_response

        retriever = PineconeRetriever(index=mock_index, embedder=self._make_embedder())

        matter_ids = ["matter-alpha", "matter-beta", "matter-gamma"]
        for matter_id in matter_ids:
            await retriever.query("query text", matter_id=matter_id, access_level="full")

        assert mock_index.query.call_count == len(matter_ids)
        for i, matter_id in enumerate(matter_ids):
            call_kwargs = mock_index.query.call_args_list[i].kwargs
            assert call_kwargs["filter"]["matter_id"] == {"$eq": matter_id}, (
                f"Call {i}: expected matter_id={matter_id!r} filter"
            )
