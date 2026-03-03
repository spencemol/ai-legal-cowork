"""Unit tests for the Pinecone retriever (task 4.5).

Task 4.5: Pinecone retriever — query by embedding + metadata filter (matter_id, access_level)

All Pinecone and embedding calls are fully mocked.

RED: These tests fail until app/retrieval/retriever.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.retrieval.retriever import PineconeRetriever


class TestPineconeRetrieverInit:
    def test_instantiation(self):
        mock_index = MagicMock()
        mock_embedder = MagicMock()
        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        assert retriever is not None

    def test_default_top_k(self):
        mock_index = MagicMock()
        mock_embedder = MagicMock()
        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        assert retriever.top_k > 0

    def test_custom_top_k(self):
        mock_index = MagicMock()
        mock_embedder = MagicMock()
        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder, top_k=20)
        assert retriever.top_k == 20


class TestPineconeRetrieverQuery:
    @pytest.fixture
    def mock_pinecone_response(self):
        """Simulate Pinecone query response with 3 matches."""
        match1 = MagicMock()
        match1.id = "doc-001_0"
        match1.score = 0.92
        match1.metadata = {
            "document_id": "doc-001",
            "matter_id": "matter-uuid-001",
            "chunk_text": "The plaintiff alleges breach of contract.",
            "file_name": "brief.pdf",
            "page_number": 1,
            "access_level": "full",
            "chunk_index": 0,
        }

        match2 = MagicMock()
        match2.id = "doc-001_1"
        match2.score = 0.85
        match2.metadata = {
            "document_id": "doc-001",
            "matter_id": "matter-uuid-001",
            "chunk_text": "The defendant denies all allegations.",
            "file_name": "brief.pdf",
            "page_number": 2,
            "access_level": "full",
            "chunk_index": 1,
        }

        response = MagicMock()
        response.matches = [match1, match2]
        return response

    async def test_query_returns_list_of_chunks(self, mock_pinecone_response):
        mock_index = MagicMock()
        mock_index.query.return_value = mock_pinecone_response

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        chunks = await retriever.query(
            query="What happened?",
            matter_id="matter-uuid-001",
            access_level="full",
        )

        assert isinstance(chunks, list)
        assert len(chunks) > 0

    async def test_query_chunk_has_required_fields(self, mock_pinecone_response):
        mock_index = MagicMock()
        mock_index.query.return_value = mock_pinecone_response

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        chunks = await retriever.query(
            query="What happened?",
            matter_id="matter-uuid-001",
            access_level="full",
        )

        for chunk in chunks:
            assert "id" in chunk
            assert "text" in chunk
            assert "score" in chunk
            assert "metadata" in chunk

    async def test_query_passes_matter_id_filter(self, mock_pinecone_response):
        """matter_id must be in the metadata filter passed to Pinecone."""
        mock_index = MagicMock()
        mock_index.query.return_value = mock_pinecone_response

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        await retriever.query(
            query="Contract breach",
            matter_id="matter-uuid-001",
            access_level="full",
        )

        call_kwargs = mock_index.query.call_args
        filter_arg = call_kwargs.kwargs.get("filter") or {}
        assert "matter_id" in filter_arg

    async def test_query_passes_access_level_filter(self, mock_pinecone_response):
        """access_level must be in the metadata filter passed to Pinecone."""
        mock_index = MagicMock()
        mock_index.query.return_value = mock_pinecone_response

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        await retriever.query(
            query="Contract breach",
            matter_id="matter-uuid-001",
            access_level="full",
        )

        call_kwargs = mock_index.query.call_args
        filter_arg = call_kwargs.kwargs.get("filter") or {}
        assert "access_level" in filter_arg

    async def test_query_uses_embedding(self):
        """The query text is embedded and the vector passed to Pinecone."""
        mock_index = MagicMock()
        response = MagicMock()
        response.matches = []
        mock_index.query.return_value = response

        mock_embedder = MagicMock()
        expected_vector = [0.5] * 384
        mock_embedder.embed.return_value = expected_vector

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        await retriever.query(
            query="Test query",
            matter_id="matter-uuid-001",
            access_level="full",
        )

        mock_embedder.embed.assert_called_once_with("Test query")
        call_kwargs = mock_index.query.call_args
        assert call_kwargs.kwargs.get("vector") == expected_vector

    async def test_query_returns_empty_list_when_no_matches(self):
        mock_index = MagicMock()
        response = MagicMock()
        response.matches = []
        mock_index.query.return_value = response

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder)
        chunks = await retriever.query(
            query="Obscure query",
            matter_id="matter-uuid-001",
            access_level="full",
        )

        assert chunks == []

    async def test_query_respects_top_k(self):
        mock_index = MagicMock()
        response = MagicMock()
        response.matches = []
        mock_index.query.return_value = response

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1] * 384

        retriever = PineconeRetriever(index=mock_index, embedder=mock_embedder, top_k=15)
        await retriever.query(
            query="Test",
            matter_id="m001",
            access_level="full",
        )

        call_kwargs = mock_index.query.call_args
        assert call_kwargs.kwargs.get("top_k") == 15
