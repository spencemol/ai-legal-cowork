"""Unit tests for the LangGraph retrieval agent (task 4.9).

Task 4.9: LangGraph retrieval agent — search → rerank → format citations → return

All external calls (LLM gateway, retriever, reranker) are fully mocked.

RED: These tests fail until app/agents/retrieval_agent.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.retrieval_agent import RetrievalAgent, RetrievalState


class TestRetrievalStateSchema:
    def test_state_has_query(self):
        state = RetrievalState(
            query="What happened?",
            matter_id="m-001",
            access_level="full",
            chunks=[],
            answer="",
            citations=[],
        )
        assert state["query"] == "What happened?"

    def test_state_has_matter_id(self):
        state = RetrievalState(
            query="Q",
            matter_id="matter-001",
            access_level="full",
            chunks=[],
            answer="",
            citations=[],
        )
        assert state["matter_id"] == "matter-001"

    def test_state_has_citations(self):
        state = RetrievalState(
            query="Q",
            matter_id="m",
            access_level="full",
            chunks=[],
            answer="",
            citations=[{"doc_id": "d1", "chunk_id": "c1", "text_snippet": "...", "page": 1, "file_name": "a.pdf"}],
        )
        assert len(state["citations"]) == 1


class TestRetrievalAgentInit:
    def test_build_with_mocked_dependencies(self):
        mock_retriever = MagicMock()
        mock_reranker = MagicMock()
        mock_gateway = MagicMock()

        agent = RetrievalAgent(
            retriever=mock_retriever,
            reranker=mock_reranker,
            gateway=mock_gateway,
        )
        assert agent is not None

    def test_has_compiled_graph(self):
        mock_retriever = MagicMock()
        mock_reranker = MagicMock()
        mock_gateway = MagicMock()

        agent = RetrievalAgent(
            retriever=mock_retriever,
            reranker=mock_reranker,
            gateway=mock_gateway,
        )
        assert agent.graph is not None


class TestRetrievalAgentRun:
    async def test_run_returns_answer_and_citations(self):
        """Full agent run returns answer string and citations list."""
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(
            return_value=[
                {
                    "id": "doc-001_0",
                    "text": "Contract breached on Jan 1.",
                    "score": 0.92,
                    "metadata": {
                        "document_id": "doc-001",
                        "matter_id": "m-001",
                        "chunk_index": 0,
                        "file_name": "brief.pdf",
                        "page_number": 1,
                        "access_level": "full",
                    },
                }
            ]
        )

        mock_reranker = MagicMock()
        mock_reranker.rerank = MagicMock(
            return_value=[
                {
                    "id": "doc-001_0",
                    "text": "Contract breached on Jan 1.",
                    "score": 0.92,
                    "rerank_score": 0.97,
                    "metadata": {
                        "document_id": "doc-001",
                        "matter_id": "m-001",
                        "chunk_index": 0,
                        "file_name": "brief.pdf",
                        "page_number": 1,
                        "access_level": "full",
                    },
                }
            ]
        )

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(
            return_value="Based on the documents, the contract was breached."
        )

        agent = RetrievalAgent(
            retriever=mock_retriever,
            reranker=mock_reranker,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What happened with the contract?",
            matter_id="m-001",
            access_level="full",
        )

        assert "answer" in result
        assert "citations" in result
        assert isinstance(result["answer"], str)
        assert isinstance(result["citations"], list)

    async def test_run_calls_retriever_with_matter_id(self):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_reranker = MagicMock()
        mock_reranker.rerank = MagicMock(return_value=[])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="No results found.")

        agent = RetrievalAgent(
            retriever=mock_retriever,
            reranker=mock_reranker,
            gateway=mock_gateway,
        )

        await agent.run(
            query="Contract details",
            matter_id="specific-matter-001",
            access_level="full",
        )

        mock_retriever.query.assert_called_once()
        call_kwargs = mock_retriever.query.call_args
        # matter_id should be passed to retriever
        assert "specific-matter-001" in str(call_kwargs)

    async def test_run_returns_citations_for_retrieved_chunks(self):
        chunk = {
            "id": "doc-001_0",
            "text": "Breach occurred.",
            "score": 0.92,
            "rerank_score": 0.97,
            "metadata": {
                "document_id": "doc-001",
                "matter_id": "m-001",
                "chunk_index": 0,
                "file_name": "brief.pdf",
                "page_number": 1,
                "access_level": "full",
            },
        }

        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[chunk])

        mock_reranker = MagicMock()
        mock_reranker.rerank = MagicMock(return_value=[chunk])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="The contract was breached.")

        agent = RetrievalAgent(
            retriever=mock_retriever,
            reranker=mock_reranker,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What happened?",
            matter_id="m-001",
            access_level="full",
        )

        assert len(result["citations"]) == 1
        assert result["citations"][0]["doc_id"] == "doc-001"

    async def test_run_empty_retrieval_gives_answer_without_citations(self):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_reranker = MagicMock()
        mock_reranker.rerank = MagicMock(return_value=[])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="I could not find relevant information.")

        agent = RetrievalAgent(
            retriever=mock_retriever,
            reranker=mock_reranker,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="obscure query",
            matter_id="m-001",
            access_level="full",
        )

        assert result["citations"] == []
        assert isinstance(result["answer"], str)
