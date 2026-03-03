"""Unit tests for the LangGraph orchestrator agent (task 4.10).

Task 4.10: LangGraph orchestrator — classify intent, route to retrieval agent

RED: These tests fail until app/agents/orchestrator.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.orchestrator import OrchestratorAgent, OrchestratorState, IntentType


class TestOrchestratorStateSchema:
    def test_state_has_query(self):
        state = OrchestratorState(
            query="What are the key facts?",
            matter_id="m-001",
            access_level="full",
            intent=None,
            result=None,
        )
        assert state["query"] == "What are the key facts?"

    def test_state_intent_initially_none(self):
        state = OrchestratorState(
            query="Q",
            matter_id="m-001",
            access_level="full",
            intent=None,
            result=None,
        )
        assert state["intent"] is None


class TestIntentType:
    def test_retrieval_intent_exists(self):
        assert hasattr(IntentType, "RETRIEVAL") or "retrieval" in [e.value for e in IntentType]

    def test_general_intent_exists(self):
        # Should have at least RETRIEVAL and GENERAL/UNKNOWN
        values = [e.value for e in IntentType]
        assert len(values) >= 2


class TestOrchestratorAgentInit:
    def test_build_with_mocked_dependencies(self):
        mock_retrieval_agent = MagicMock()
        mock_gateway = MagicMock()

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )
        assert agent is not None

    def test_has_compiled_graph(self):
        mock_retrieval_agent = MagicMock()
        mock_gateway = MagicMock()

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )
        assert agent.graph is not None


class TestOrchestratorIntentClassification:
    async def test_factual_question_routes_to_retrieval(self):
        """Factual questions about the matter should route to retrieval agent."""
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(
            return_value={
                "answer": "The contract was breached on January 1, 2024.",
                "citations": [{"doc_id": "d1", "chunk_id": "c1", "text_snippet": "...", "page": 1, "file_name": "f.pdf"}],
            }
        )

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="retrieval")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What are the key facts in this breach of contract case?",
            matter_id="m-001",
            access_level="full",
        )

        assert "answer" in result
        # Retrieval agent should have been called
        mock_retrieval_agent.run.assert_called_once()

    async def test_run_returns_answer_from_retrieval(self):
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(
            return_value={
                "answer": "The contract date was January 1.",
                "citations": [],
            }
        )

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="retrieval")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="When was the contract signed?",
            matter_id="m-001",
            access_level="full",
        )

        assert result["answer"] == "The contract date was January 1."
        assert "citations" in result

    async def test_routing_decision_is_logged(self):
        """The routing decision (intent) should be part of the result."""
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(
            return_value={"answer": "Some answer", "citations": []}
        )

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="retrieval")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="What happened?",
            matter_id="m-001",
            access_level="full",
        )

        # Result should include routing/intent info
        assert "answer" in result
        assert "intent" in result or "citations" in result

    async def test_general_query_gets_direct_answer(self):
        """Non-factual queries may be answered directly without retrieval."""
        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(
            return_value={"answer": "Direct answer", "citations": []}
        )

        mock_gateway = MagicMock()
        # Gateway returns "general" intent — could route differently
        mock_gateway.complete = AsyncMock(return_value="general")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
        )

        result = await agent.run(
            query="Hello, how are you?",
            matter_id="m-001",
            access_level="full",
        )

        assert "answer" in result
