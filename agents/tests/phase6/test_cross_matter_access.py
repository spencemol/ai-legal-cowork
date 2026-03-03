"""Phase 6 — Task 6.6: Cross-matter access control tests.

Verifies that:
  - A user assigned only to matter A cannot retrieve matter B documents
  - The Pinecone retriever correctly scopes queries to authorized matter IDs
  - The /chat endpoint returns 403 for unauthorized matter access
  - Access control is enforced at both the route level and the retriever level

No real Pinecone or Postgres is used — all external services are mocked.
"""

from __future__ import annotations

import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from app.main import app
from app.retrieval.retriever import PineconeRetriever


# ---------------------------------------------------------------------------
# JWT helper
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"
_SECRET = "cross-matter-test-secret-minimum-32!!"


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


# ---------------------------------------------------------------------------
# Route-level access control tests
# ---------------------------------------------------------------------------


class TestCrossWaterRouteAccessControl:
    """Task 6.6 — /chat endpoint enforces matter-level authorization."""

    @pytest.fixture
    def client(self):
        return TestClient(app, raise_server_exceptions=False)

    def test_user_with_matter_a_only_is_denied_matter_b(self, client):
        """User assigned to matter-a only gets 403 when querying matter-b."""
        with patch.dict(os.environ, {"JWT_SECRET": _SECRET}):
            token = _make_jwt(matter_ids=["matter-a"])
            response = client.post(
                "/chat",
                json={"query": "Show me the documents.", "matter_id": "matter-b"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403

    def test_user_with_matter_a_only_is_denied_matter_b_detail(self, client):
        """403 response includes a meaningful error message."""
        with patch.dict(os.environ, {"JWT_SECRET": _SECRET}):
            token = _make_jwt(matter_ids=["matter-a"])
            response = client.post(
                "/chat",
                json={"query": "Show me the docs.", "matter_id": "matter-b"},
                headers={"Authorization": f"Bearer {token}"},
            )
        body = response.json()
        assert "detail" in body
        assert "matter" in body["detail"].lower() or "access" in body["detail"].lower()

    def test_user_with_no_matter_assignments_is_denied(self, client):
        """User with empty matter_ids list is denied access to any matter."""
        with patch.dict(os.environ, {"JWT_SECRET": _SECRET}):
            token = _make_jwt(matter_ids=[])
            response = client.post(
                "/chat",
                json={"query": "Show me the docs.", "matter_id": "matter-a"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 403

    def test_user_assigned_to_matter_b_can_access_matter_b(self, client):
        """User with matter-b in their matter_ids can successfully call /chat."""
        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
        ):
            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(
                return_value={
                    "answer": "The contract was breached.",
                    "citations": [],
                    "intent": "retrieval",
                }
            )
            mock_build.return_value = mock_orchestrator

            token = _make_jwt(matter_ids=["matter-b"])
            response = client.post(
                "/chat",
                json={"query": "What happened?", "matter_id": "matter-b"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert response.status_code == 200

    def test_user_assigned_to_multiple_matters_can_access_each(self, client):
        """User with [matter-a, matter-b] can access both matters."""
        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
        ):
            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(
                return_value={"answer": "OK.", "citations": [], "intent": "general"}
            )
            mock_build.return_value = mock_orchestrator

            token = _make_jwt(matter_ids=["matter-a", "matter-b"])

            for matter_id in ("matter-a", "matter-b"):
                response = client.post(
                    "/chat",
                    json={"query": "Summary?", "matter_id": matter_id},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert response.status_code == 200, (
                    f"Expected 200 for matter {matter_id!r}, got {response.status_code}"
                )

    def test_access_control_applies_before_orchestrator(self, client):
        """The orchestrator is NEVER invoked for unauthorized matter access."""
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
            # _build_orchestrator must NOT have been called
            mock_build.assert_not_called()


# ---------------------------------------------------------------------------
# Retriever-level access control tests
# ---------------------------------------------------------------------------


class TestRetrieverMatterFilter:
    """Task 6.6 — Pinecone retriever scopes queries to the authorized matter."""

    def _make_mock_index(self, chunks: list[dict]) -> MagicMock:
        """Return a mock Pinecone index that yields *chunks* as query results."""
        mock_matches = []
        for chunk in chunks:
            match = MagicMock()
            match.id = chunk["id"]
            match.score = chunk["score"]
            match.metadata = chunk["metadata"]
            mock_matches.append(match)

        mock_response = MagicMock()
        mock_response.matches = mock_matches
        mock_index = MagicMock()
        mock_index.query.return_value = mock_response
        return mock_index

    def _make_mock_embedder(self) -> MagicMock:
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384
        return mock_embedder

    @pytest.mark.asyncio
    async def test_retriever_sends_matter_id_filter_to_pinecone(self):
        """PineconeRetriever passes matter_id as a metadata filter."""
        mock_index = self._make_mock_index([])
        mock_embedder = self._make_mock_embedder()

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        await retriever.query("breach?", matter_id="matter-a", access_level="full")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"]["matter_id"] == {"$eq": "matter-a"}

    @pytest.mark.asyncio
    async def test_retriever_scopes_query_to_requested_matter(self):
        """Querying matter-b sends matter_id=matter-b filter (not matter-a)."""
        mock_index = self._make_mock_index([])
        mock_embedder = self._make_mock_embedder()

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        await retriever.query("facts?", matter_id="matter-b", access_level="full")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"]["matter_id"] == {"$eq": "matter-b"}

    @pytest.mark.asyncio
    async def test_retriever_returns_only_matter_a_chunks_when_querying_matter_a(
        self, sample_chunks_matter_a, sample_chunks_matter_b
    ):
        """When Pinecone returns only matter-a chunks, retriever returns only those."""
        # Pinecone filter is enforced server-side; mock returns only matter-a chunks.
        mock_index = self._make_mock_index(sample_chunks_matter_a)
        mock_embedder = self._make_mock_embedder()

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        results = await retriever.query("breach?", matter_id="matter-a", access_level="full")

        assert len(results) == len(sample_chunks_matter_a)
        for result in results:
            assert result["metadata"]["matter_id"] == "matter-a"

    @pytest.mark.asyncio
    async def test_retriever_returns_empty_when_pinecone_returns_no_matches(self):
        """Empty Pinecone result → empty list from retriever."""
        mock_index = self._make_mock_index([])
        mock_embedder = self._make_mock_embedder()

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        results = await retriever.query("anything?", matter_id="matter-b", access_level="full")

        assert results == []

    @pytest.mark.asyncio
    async def test_retriever_includes_access_level_in_filter(self):
        """PineconeRetriever also sends access_level filter."""
        mock_index = self._make_mock_index([])
        mock_embedder = self._make_mock_embedder()

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        await retriever.query("query", matter_id="matter-a", access_level="restricted")

        call_kwargs = mock_index.query.call_args.kwargs
        assert call_kwargs["filter"]["access_level"] == {"$eq": "restricted"}
