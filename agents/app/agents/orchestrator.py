"""LangGraph orchestrator agent — classify intent, route to sub-agents
(tasks 4.10, 7.4, 7.14).

Graph topology::

    START → classify_intent → [retrieval | research | drafting | general] → END

The orchestrator uses the LLM gateway to classify intent and then routes to
the appropriate sub-agent or generates a direct response.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class IntentType(StrEnum):
    """Supported intent types for routing."""

    RETRIEVAL = "retrieval"
    RESEARCH = "research"
    DRAFTING = "drafting"
    GENERAL = "general"


class OrchestratorState(TypedDict):
    """Typed state flowing through the orchestrator graph."""

    query: str
    matter_id: str
    access_level: str
    intent: str | None
    result: dict | None


_INTENT_CLASSIFICATION_PROMPT = """\
Classify the following legal query into exactly one category:

- retrieval: Questions that require searching legal documents, case facts, \
  contract terms, or any factual matter-specific information.
- research: Questions asking for legal research, recent precedents, case law, \
  legal analysis, or questions about what the law says on a topic.
- drafting: Requests to draft, write, generate, or create a legal document \
  (e.g. NDA, engagement letter, motion, contract).
- general: Conversational messages, greetings, or very broad conceptual \
  questions that don't require document retrieval or research.

Query: {query}

Respond with just one word: "retrieval", "research", "drafting", or "general".
"""


class OrchestratorAgent:
    """LangGraph-based orchestrator that classifies and routes queries.

    Parameters
    ----------
    retrieval_agent:
        :class:`~app.agents.retrieval_agent.RetrievalAgent` instance.
    gateway:
        LLM gateway for intent classification and direct answers.
    research_agent:
        Optional :class:`~app.agents.research_agent.ResearchAgent` instance.
        Required for routing research-intent queries.
    drafting_agent:
        Optional :class:`~app.agents.drafting_agent.DraftingAgent` instance.
        Required for routing drafting-intent queries.
    """

    def __init__(
        self,
        retrieval_agent: Any,
        gateway: Any,
        research_agent: Any = None,
        drafting_agent: Any = None,
    ) -> None:
        self._retrieval_agent = retrieval_agent
        self._gateway = gateway
        self._research_agent = research_agent
        self._drafting_agent = drafting_agent
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        query: str,
        matter_id: str,
        access_level: str,
    ) -> dict:
        """Classify intent and route to the appropriate handler.

        Returns
        -------
        dict
            ``{"answer": str, "citations": list, "intent": str}``
        """
        initial_state: OrchestratorState = {
            "query": query,
            "matter_id": matter_id,
            "access_level": access_level,
            "intent": None,
            "result": None,
        }
        final_state = await self.graph.ainvoke(initial_state)
        result = final_state.get("result") or {}
        return {
            "answer": result.get("answer", ""),
            "citations": result.get("citations", []),
            "intent": final_state.get("intent"),
        }

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        graph = StateGraph(OrchestratorState)

        graph.add_node("classify_intent", self._node_classify_intent)
        graph.add_node("handle_retrieval", self._node_handle_retrieval)
        graph.add_node("handle_research", self._node_handle_research)
        graph.add_node("handle_drafting", self._node_handle_drafting)
        graph.add_node("handle_general", self._node_handle_general)

        graph.set_entry_point("classify_intent")
        graph.add_conditional_edges(
            "classify_intent",
            self._route,
            {
                IntentType.RETRIEVAL: "handle_retrieval",
                IntentType.RESEARCH: "handle_research",
                IntentType.DRAFTING: "handle_drafting",
                IntentType.GENERAL: "handle_general",
            },
        )
        graph.add_edge("handle_retrieval", END)
        graph.add_edge("handle_research", END)
        graph.add_edge("handle_drafting", END)
        graph.add_edge("handle_general", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Routing function
    # ------------------------------------------------------------------

    def _route(self, state: OrchestratorState) -> IntentType:
        intent_str = (state.get("intent") or "").strip().lower()
        if intent_str == IntentType.RETRIEVAL:
            return IntentType.RETRIEVAL
        if intent_str == IntentType.RESEARCH:
            return IntentType.RESEARCH
        if intent_str == IntentType.DRAFTING:
            return IntentType.DRAFTING
        return IntentType.GENERAL

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_classify_intent(self, state: OrchestratorState) -> dict:
        prompt = _INTENT_CLASSIFICATION_PROMPT.format(query=state["query"])
        raw = await self._gateway.complete(prompt)
        intent_str = raw.strip().lower()

        if "research" in intent_str:
            intent = IntentType.RESEARCH
        elif "drafting" in intent_str or "draft" in intent_str:
            intent = IntentType.DRAFTING
        elif "retrieval" in intent_str:
            intent = IntentType.RETRIEVAL
        else:
            intent = IntentType.GENERAL

        return {"intent": intent}

    async def _node_handle_retrieval(self, state: OrchestratorState) -> dict:
        result = await self._retrieval_agent.run(
            query=state["query"],
            matter_id=state["matter_id"],
            access_level=state["access_level"],
        )
        return {"result": result}

    async def _node_handle_research(self, state: OrchestratorState) -> dict:
        if self._research_agent is None:
            # Fallback to retrieval if research agent not configured
            return await self._node_handle_retrieval(state)
        result = await self._research_agent.run(
            query=state["query"],
            matter_id=state["matter_id"],
            access_level=state["access_level"],
        )
        return {"result": result}

    async def _node_handle_drafting(self, state: OrchestratorState) -> dict:
        if self._drafting_agent is None:
            # Fallback to general if drafting agent not configured
            return await self._node_handle_general(state)
        result = await self._drafting_agent.run(
            query=state["query"],
            matter_id=state["matter_id"],
            access_level=state["access_level"],
        )
        return {"result": result}

    async def _node_handle_general(self, state: OrchestratorState) -> dict:
        prompt = (
            f"Answer the following question helpfully and concisely "
            f"in the context of a legal workspace:\n\n{state['query']}"
        )
        answer = await self._gateway.complete(
            prompt,
            system="You are a helpful legal AI assistant.",
        )
        return {"result": {"answer": answer, "citations": []}}
