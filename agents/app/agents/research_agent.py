"""LangGraph research agent — multi-step: firm data + web + legal DB → synthesize
with citations (tasks 7.3, 7.4).

Graph topology::

    START → retrieve_firm_data → search_web → search_legal_db
          → synthesize → format_citations → END

Each node receives and returns a :class:`ResearchState` dict.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class ResearchState(TypedDict):
    """Typed state flowing through the research graph."""

    query: str
    matter_id: str
    firm_chunks: list[dict]
    web_results: list[dict]
    legal_db_results: list[dict]
    answer: str
    citations: list[dict]


_SYNTHESIS_SYSTEM = (
    "You are a senior legal research assistant.  Synthesize information from "
    "multiple sources (firm documents, web articles, case law) into a concise, "
    "accurate answer with proper attribution."
)


class ResearchAgent:
    """LangGraph-based research agent that queries multiple data sources.

    Parameters
    ----------
    retriever:
        Object with ``async query(query, matter_id, access_level) -> list[dict]``.
    web_search:
        Object with ``search(query, max_results=N) -> list[dict]``.
    legal_db:
        Object with ``search(query, max_results=N) -> list[dict]``.
    gateway:
        LLM gateway with ``async complete(prompt, system=None) -> str``.
    max_web_results:
        Maximum DuckDuckGo results to fetch per query.
    max_legal_results:
        Maximum legal DB results to fetch per query.
    """

    def __init__(
        self,
        retriever: Any,
        web_search: Any,
        legal_db: Any,
        gateway: Any,
        max_web_results: int = 5,
        max_legal_results: int = 5,
    ) -> None:
        self._retriever = retriever
        self._web_search = web_search
        self._legal_db = legal_db
        self._gateway = gateway
        self._max_web = max_web_results
        self._max_legal = max_legal_results
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
        """Run the research pipeline and return answer + citations.

        Returns
        -------
        dict
            ``{"answer": str, "citations": list[dict]}``
        """
        initial_state: ResearchState = {
            "query": query,
            "matter_id": matter_id,
            "firm_chunks": [],
            "web_results": [],
            "legal_db_results": [],
            "answer": "",
            "citations": [],
        }
        final_state = await self.graph.ainvoke(initial_state)
        return {
            "answer": final_state["answer"],
            "citations": final_state["citations"],
        }

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        graph = StateGraph(ResearchState)

        graph.add_node("retrieve_firm_data", self._node_retrieve_firm_data)
        graph.add_node("search_web", self._node_search_web)
        graph.add_node("search_legal_db", self._node_search_legal_db)
        graph.add_node("synthesize", self._node_synthesize)

        graph.set_entry_point("retrieve_firm_data")
        graph.add_edge("retrieve_firm_data", "search_web")
        graph.add_edge("search_web", "search_legal_db")
        graph.add_edge("search_legal_db", "synthesize")
        graph.add_edge("synthesize", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_retrieve_firm_data(self, state: ResearchState) -> dict:
        chunks = await self._retriever.query(
            query=state["query"],
            matter_id=state["matter_id"],
            access_level=state.get("access_level", "full"),
        )
        return {"firm_chunks": chunks or []}

    async def _node_search_web(self, state: ResearchState) -> dict:
        results = self._web_search.search(
            state["query"],
            max_results=self._max_web,
        )
        return {"web_results": results or []}

    async def _node_search_legal_db(self, state: ResearchState) -> dict:
        results = self._legal_db.search(
            state["query"],
            max_results=self._max_legal,
        )
        return {"legal_db_results": results or []}

    async def _node_synthesize(self, state: ResearchState) -> dict:
        # Build context sections
        context_parts: list[str] = []

        firm_chunks = state["firm_chunks"]
        if firm_chunks:
            firm_section = "Firm documents:\n" + "\n".join(
                f"  [{i + 1}] {c.get('text', '')}" for i, c in enumerate(firm_chunks)
            )
            context_parts.append(firm_section)

        web_results = state["web_results"]
        if web_results:
            web_section = "Web sources:\n" + "\n".join(
                f"  [{i + 1}] {r.get('title', '')} — {r.get('snippet', '')}"
                for i, r in enumerate(web_results)
            )
            context_parts.append(web_section)

        legal_db_results = state["legal_db_results"]
        if legal_db_results:
            legal_section = "Case law:\n" + "\n".join(
                f"  [{i + 1}] {r.get('citation', '')} — {r.get('snippet', '')}"
                for i, r in enumerate(legal_db_results)
            )
            context_parts.append(legal_section)

        context = "\n\n".join(context_parts) if context_parts else "No context available."
        prompt = (
            f"Research question: {state['query']}\n\n"
            f"Available information:\n{context}\n\n"
            f"Provide a synthesized answer with citations."
        )

        answer = await self._gateway.complete(prompt, system=_SYNTHESIS_SYSTEM)

        # Build mixed citations
        citations: list[dict] = []

        for chunk in firm_chunks:
            citations.append({
                "doc_id": chunk.get("doc_id", ""),
                "chunk_id": chunk.get("chunk_id", ""),
                "text_snippet": chunk.get("text", "")[:200],
                "page": chunk.get("page", 1),
                "source": "firm",
            })

        for result in web_results:
            citations.append({
                "url": result.get("url", ""),
                "title": result.get("title", ""),
                "text_snippet": result.get("snippet", "")[:200],
                "source": "web",
            })

        for result in legal_db_results:
            citations.append({
                "citation": result.get("citation", ""),
                "title": result.get("title", ""),
                "text_snippet": result.get("snippet", "")[:200],
                "source": result.get("source", "westlaw"),
            })

        return {"answer": answer, "citations": citations}
