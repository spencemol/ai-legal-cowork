"""LangGraph drafting agent — choose template or freeform → render → export
(tasks 7.13, 7.14).

Graph topology::

    START → classify_drafting_type → render_template  → export → END
                                   → freeform_draft   → export → END

Each node receives and returns a :class:`DraftingState` dict.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class DraftingState(TypedDict):
    """Typed state flowing through the drafting graph."""

    query: str
    matter_id: str
    template_name: str | None
    context_chunks: list[dict]
    rendered_content: str
    export_format: str
    output_path: str | None

    # Runtime fields (not part of the external API but needed within the graph)
    _context: dict
    _access_level: str


class DraftingAgent:
    """LangGraph-based drafting agent.

    Parameters
    ----------
    retriever:
        Object with ``async query(query, matter_id, access_level) -> list[dict]``.
    renderer:
        Object with ``render(template_name, context) -> str``.
    freeform_drafter:
        Object with ``async draft(prompt, context_chunks) -> str``.
    exporter:
        Object with ``export(content, output_path, format) -> str``.
    """

    def __init__(
        self,
        retriever: Any,
        renderer: Any,
        freeform_drafter: Any,
        exporter: Any,
    ) -> None:
        self._retriever = retriever
        self._renderer = renderer
        self._freeform = freeform_drafter
        self._exporter = exporter
        self.graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(
        self,
        query: str,
        matter_id: str,
        access_level: str,
        template_name: str | None = None,
        context: dict | None = None,
        export_format: str = "docx",
        output_path: str | None = None,
    ) -> dict:
        """Run the drafting pipeline and return result.

        Returns
        -------
        dict
            ``{"rendered_content": str, "output_path": str, "citations": list}``
        """
        initial_state: DraftingState = {
            "query": query,
            "matter_id": matter_id,
            "template_name": template_name,
            "context_chunks": [],
            "rendered_content": "",
            "export_format": export_format,
            "output_path": output_path,
            "_context": context or {},
            "_access_level": access_level,
        }
        final_state = await self.graph.ainvoke(initial_state)
        return {
            "rendered_content": final_state.get("rendered_content", ""),
            "output_path": final_state.get("output_path"),
            "answer": final_state.get("rendered_content", ""),
            "citations": [],
        }

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        graph = StateGraph(DraftingState)

        graph.add_node("classify_drafting_type", self._node_classify)
        graph.add_node("render_template", self._node_render_template)
        graph.add_node("freeform_draft", self._node_freeform_draft)
        graph.add_node("export", self._node_export)

        graph.set_entry_point("classify_drafting_type")
        graph.add_conditional_edges(
            "classify_drafting_type",
            self._route,
            {
                "template": "render_template",
                "freeform": "freeform_draft",
            },
        )
        graph.add_edge("render_template", "export")
        graph.add_edge("freeform_draft", "export")
        graph.add_edge("export", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Routing function
    # ------------------------------------------------------------------

    def _route(self, state: DraftingState) -> str:
        if state.get("template_name"):
            return "template"
        return "freeform"

    # ------------------------------------------------------------------
    # Node implementations
    # ------------------------------------------------------------------

    async def _node_classify(self, state: DraftingState) -> dict:
        """No-op classification node — routing is done via template_name."""
        return {}

    async def _node_render_template(self, state: DraftingState) -> dict:
        rendered = self._renderer.render(
            state["template_name"],
            state.get("_context") or {},
        )
        return {"rendered_content": rendered}

    async def _node_freeform_draft(self, state: DraftingState) -> dict:
        # Retrieve firm context first
        chunks = await self._retriever.query(
            query=state["query"],
            matter_id=state["matter_id"],
            access_level=state.get("_access_level", "full"),
        )
        rendered = await self._freeform.draft(
            prompt=state["query"],
            context_chunks=chunks or [],
        )
        return {"rendered_content": rendered, "context_chunks": chunks or []}

    async def _node_export(self, state: DraftingState) -> dict:
        from app.docgen.exporter import ExportFormat  # noqa: PLC0415

        output_path = state.get("output_path") or "/tmp/draft_output.docx"
        fmt = ExportFormat(state.get("export_format", "docx"))
        path = self._exporter.export(
            state["rendered_content"],
            output_path,
            fmt,
        )
        return {"output_path": path}
