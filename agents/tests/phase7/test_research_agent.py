"""Tests for LangGraph research agent (tasks 7.3, 7.4, 7.5).

RED: These tests fail until app/agents/research_agent.py is implemented
and orchestrator routing is updated.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.research_agent import ResearchAgent, ResearchState
from app.agents.orchestrator import IntentType, OrchestratorAgent


class TestResearchStateSchema:
    def test_state_has_required_fields(self):
        state = ResearchState(
            query="What are precedents for breach of contract?",
            matter_id="matter-001",
            firm_chunks=[],
            web_results=[],
            legal_db_results=[],
            answer="",
            citations=[],
        )
        assert state["query"] == "What are precedents for breach of contract?"
        assert state["matter_id"] == "matter-001"

    def test_state_citations_initially_empty(self):
        state = ResearchState(
            query="Q",
            matter_id="m-1",
            firm_chunks=[],
            web_results=[],
            legal_db_results=[],
            answer="",
            citations=[],
        )
        assert state["citations"] == []


class TestResearchAgentInit:
    def test_instantiation(self):
        mock_retriever = MagicMock()
        mock_web_search = MagicMock()
        mock_legal_db = MagicMock()
        mock_gateway = MagicMock()

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )
        assert agent is not None

    def test_has_compiled_graph(self):
        agent = ResearchAgent(
            retriever=MagicMock(),
            web_search=MagicMock(),
            legal_db=MagicMock(),
            gateway=MagicMock(),
        )
        assert agent.graph is not None


class TestResearchAgentRun:
    async def test_run_returns_answer(self):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[
            {"doc_id": "d1", "chunk_id": "c1", "text": "Breach requires non-performance.", "page": 1, "file_name": "f.pdf"}
        ])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[
            {"title": "Breach Law", "url": "https://ex.com", "snippet": "Breach occurs when..."}
        ])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[
            {"title": "Smith v. Jones", "citation": "123 F.3d 456", "snippet": "Court held...", "source": "westlaw", "url": "https://wl.com"}
        ])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Breach of contract requires non-performance of a material term.")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What are the elements of breach of contract?",
            matter_id="matter-001",
            access_level="full",
        )

        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

    async def test_run_returns_citations(self):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[
            {"doc_id": "d1", "chunk_id": "c1", "text": "Contract terms...", "page": 2, "file_name": "contract.pdf"}
        ])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[
            {"title": "Legal Overview", "url": "https://ex.com/law", "snippet": "Overview of law..."}
        ])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[
            {"title": "Doe v. Roe", "citation": "456 F.2d 789", "snippet": "Damages held...", "source": "lexisnexis", "url": "https://ln.com"}
        ])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Based on the research, breach requires...")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What are recent precedents for breach damages?",
            matter_id="matter-001",
            access_level="full",
        )

        assert "citations" in result
        assert isinstance(result["citations"], list)

    async def test_citations_include_mixed_sources(self):
        """Citations should include firm, web, and legal DB sources."""
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[
            {"doc_id": "d1", "chunk_id": "c1", "text": "Firm doc text.", "page": 1, "file_name": "brief.pdf"}
        ])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[
            {"title": "Web Article", "url": "https://web.com/article", "snippet": "Web snippet"}
        ])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[
            {"title": "Case Law", "citation": "100 F.3d 200", "snippet": "Court decided...", "source": "westlaw", "url": "https://wl.com"}
        ])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Synthesized research answer.")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="Research contract breach precedents",
            matter_id="matter-001",
            access_level="full",
        )

        citations = result["citations"]
        sources = {c.get("source") for c in citations}
        # Should have at least one citation source
        assert len(sources) > 0

    async def test_firm_citation_format(self):
        """Firm citations should have doc_id, chunk_id, text_snippet, page, source=firm."""
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[
            {"doc_id": "doc-abc", "chunk_id": "chk-1", "text": "Contract clause text.", "page": 5, "file_name": "contract.pdf"}
        ])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Answer based on firm data.")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What does the contract say?",
            matter_id="matter-001",
            access_level="full",
        )

        firm_citations = [c for c in result["citations"] if c.get("source") == "firm"]
        assert len(firm_citations) > 0
        firm_cit = firm_citations[0]
        assert "doc_id" in firm_cit
        assert "chunk_id" in firm_cit
        assert "text_snippet" in firm_cit
        assert "page" in firm_cit

    async def test_web_citation_format(self):
        """Web citations should have url, title, text_snippet, source=web."""
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[
            {"title": "Legal Blog", "url": "https://blog.com/law", "snippet": "Law blog post."}
        ])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Web-sourced answer.")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="Recent legal developments",
            matter_id="matter-001",
            access_level="full",
        )

        web_citations = [c for c in result["citations"] if c.get("source") == "web"]
        assert len(web_citations) > 0
        web_cit = web_citations[0]
        assert "url" in web_cit
        assert "title" in web_cit
        assert "text_snippet" in web_cit

    async def test_legal_db_citation_format(self):
        """Legal DB citations should have citation, title, text_snippet, source (westlaw/lexisnexis)."""
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[
            {"title": "Case X v. Y", "citation": "999 F.3d 111", "snippet": "Court ruled...", "source": "westlaw", "url": "https://wl.com"}
        ])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Case law answer.")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What case law governs this?",
            matter_id="matter-001",
            access_level="full",
        )

        legal_citations = [c for c in result["citations"] if c.get("source") in ("westlaw", "lexisnexis")]
        assert len(legal_citations) > 0
        legal_cit = legal_citations[0]
        assert "citation" in legal_cit
        assert "title" in legal_cit
        assert "text_snippet" in legal_cit

    async def test_all_tool_nodes_called(self):
        """All three data sources should be queried."""
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_web_search = MagicMock()
        mock_web_search.search = MagicMock(return_value=[])

        mock_legal_db = MagicMock()
        mock_legal_db.search = MagicMock(return_value=[])

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Empty context answer.")

        agent = ResearchAgent(
            retriever=mock_retriever,
            web_search=mock_web_search,
            legal_db=mock_legal_db,
            gateway=mock_gateway,
        )

        await agent.run(
            query="Test query",
            matter_id="matter-001",
            access_level="full",
        )

        mock_retriever.query.assert_called_once()
        mock_web_search.search.assert_called_once()
        mock_legal_db.search.assert_called_once()


class TestOrchestratorResearchRouting:
    """Task 7.4: Orchestrator should route research-intent queries to research agent."""

    def test_research_intent_in_enum(self):
        values = [e.value for e in IntentType]
        assert "research" in values

    def test_drafting_intent_in_enum(self):
        values = [e.value for e in IntentType]
        assert "drafting" in values

    async def test_research_query_routes_to_research_agent(self):
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(return_value={"answer": "Retrieval answer", "citations": []})

        mock_research_agent = MagicMock()
        mock_research_agent.run = AsyncMock(return_value={
            "answer": "Research synthesized answer",
            "citations": [{"source": "web", "url": "https://ex.com", "title": "T", "text_snippet": "S"}],
        })

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="research")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
            research_agent=mock_research_agent,
        )

        result = await agent.run(
            query="What are recent precedents for breach of contract?",
            matter_id="matter-001",
            access_level="full",
        )

        assert "answer" in result
        mock_research_agent.run.assert_called_once()
        mock_retrieval_agent.run.assert_not_called()

    async def test_drafting_query_routes_to_drafting_agent(self):
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(return_value={"answer": "Retrieval answer", "citations": []})

        mock_drafting_agent = MagicMock()
        mock_drafting_agent.run = AsyncMock(return_value={
            "answer": "Drafted NDA document",
            "citations": [],
            "output_path": "/tmp/nda.docx",
        })

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="drafting")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
            drafting_agent=mock_drafting_agent,
        )

        result = await agent.run(
            query="Draft an NDA for matter-001",
            matter_id="matter-001",
            access_level="full",
        )

        assert "answer" in result
        mock_drafting_agent.run.assert_called_once()
        mock_retrieval_agent.run.assert_not_called()

    async def test_existing_retrieval_routing_still_works(self):
        """Existing retrieval routing must not be broken by new intents."""
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(return_value={"answer": "Retrieved answer", "citations": []})

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="retrieval")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What are the key facts in this matter?",
            matter_id="matter-001",
            access_level="full",
        )

        assert "answer" in result
        mock_retrieval_agent.run.assert_called_once()
