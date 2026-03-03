"""LangGraph orchestrator agent — classify intent, route to retrieval agent (task 4.10).

Graph topology::

    START → classify_intent → [retrieval | direct_answer] → END

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
- general: Conversational messages, greetings, or very broad conceptual \
  questions that don't require document retrieval.

Query: {query}

Respond with just one word: either "retrieval" or "general".
"""


class OrchestratorAgent:
    """LangGraph-based orchestrator that classifies and routes queries.

    Parameters
    ----------
    retrieval_agent:
        :class:`~app.agents.retrieval_agent.RetrievalAgent` instance.
    gateway:
        LLM gateway for intent classification and direct answers.
    """

    def __init__(self, retrieval_agent: Any, gateway: Any) -> None:
        self._retrieval_agent = retrieval_agent
        self._gateway = gateway
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
        graph.add_node("handle_general", self._node_handle_general)

        graph.set_entry_point("classify_intent")
        graph.add_conditional_edges(
            "classify_intent",
            self._route,
            {
                IntentType.RETRIEVAL: "handle_retrieval",
                IntentType.GENERAL: "handle_general",
            },
        )
        graph.add_edge("handle_retrieval", END)
        graph.add_edge("handle_general", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Routing function
    # ------------------------------------------------------------------

    def _route(self, state: OrchestratorState) -> IntentType:
        intent_str = (state.get("intent") or "").strip().lower()
        if intent_str == IntentType.RETRIEVAL:
            return IntentType.RETRIEVAL
        return IntentType.GENERAL

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_classify_intent(self, state: OrchestratorState) -> dict:
        prompt = _INTENT_CLASSIFICATION_PROMPT.format(query=state["query"])
        raw = await self._gateway.complete(prompt)
        intent_str = raw.strip().lower()

        if "retrieval" in intent_str:
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
