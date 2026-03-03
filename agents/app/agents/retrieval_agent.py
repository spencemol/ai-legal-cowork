"""LangGraph retrieval agent — search → rerank → format citations → return (task 4.9).

Graph topology::

    START → retrieve → rerank → generate → END

Each node receives and returns a ``RetrievalState`` dict.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.retrieval.citations import CitationFormatter


class RetrievalState(TypedDict):
    """Typed state flowing through the retrieval graph."""

    query: str
    matter_id: str
    access_level: str
    chunks: list[dict]
    answer: str
    citations: list[dict]


class RetrievalAgent:
    """LangGraph-based retrieval agent.

    Parameters
    ----------
    retriever:
        Object with ``async query(query, matter_id, access_level) -> list[dict]``.
    reranker:
        Object with ``rerank(query, chunks) -> list[dict]``.
    gateway:
        :class:`~app.gateway.client.LLMGateway` (or compatible mock) with
        ``async complete(prompt, system=None) -> str``.
    citation_formatter:
        Optional :class:`~app.retrieval.citations.CitationFormatter`.  A
        default instance is created if not provided.
    top_rerank:
        Maximum number of reranked chunks to pass to the LLM for answer
        generation.
    """

    def __init__(
        self,
        retriever: Any,
        reranker: Any,
        gateway: Any,
        citation_formatter: Any = None,
        top_rerank: int = 5,
    ) -> None:
        self._retriever = retriever
        self._reranker = reranker
        self._gateway = gateway
        self._formatter = citation_formatter or CitationFormatter()
        self._top_rerank = top_rerank
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
        """Run the retrieval pipeline and return answer + citations.

        Returns
        -------
        dict
            ``{"answer": str, "citations": list[dict]}``
        """
        initial_state: RetrievalState = {
            "query": query,
            "matter_id": matter_id,
            "access_level": access_level,
            "chunks": [],
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
        graph = StateGraph(RetrievalState)

        graph.add_node("retrieve", self._node_retrieve)
        graph.add_node("rerank", self._node_rerank)
        graph.add_node("generate", self._node_generate)

        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "rerank")
        graph.add_edge("rerank", "generate")
        graph.add_edge("generate", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_retrieve(self, state: RetrievalState) -> dict:
        chunks = await self._retriever.query(
            query=state["query"],
            matter_id=state["matter_id"],
            access_level=state["access_level"],
        )
        return {"chunks": chunks}

    async def _node_rerank(self, state: RetrievalState) -> dict:
        chunks = state["chunks"]
        if not chunks:
            return {"chunks": []}

        reranked = self._reranker.rerank(
            query=state["query"],
            chunks=chunks,
        )
        return {"chunks": reranked[: self._top_rerank]}

    async def _node_generate(self, state: RetrievalState) -> dict:
        chunks = state["chunks"]
        citations = self._formatter.format(chunks)

        if chunks:
            context = "\n\n".join(
                f"[{i + 1}] {c['text']}" for i, c in enumerate(chunks)
            )
            prompt = (
                f"Using the following retrieved legal document excerpts, "
                f"answer the question concisely.\n\n"
                f"Question: {state['query']}\n\n"
                f"Context:\n{context}\n\n"
                f"Answer:"
            )
        else:
            prompt = (
                f"Answer the following legal question. "
                f"No relevant documents were found.\n\n"
                f"Question: {state['query']}\n\nAnswer:"
            )

        answer = await self._gateway.complete(
            prompt,
            system="You are a legal research assistant. Be concise and accurate.",
        )

        return {"answer": answer, "citations": citations}
