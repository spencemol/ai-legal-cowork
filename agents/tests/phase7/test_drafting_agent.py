"""Tests for LangGraph drafting agent (tasks 7.13, 7.14, 7.15).

RED: These tests fail until app/agents/drafting_agent.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.drafting_agent import DraftingAgent, DraftingState


class TestDraftingStateSchema:
    def test_state_has_required_fields(self):
        state = DraftingState(
            query="Draft an NDA for matter-001",
            matter_id="matter-001",
            template_name=None,
            context_chunks=[],
            rendered_content="",
            export_format="docx",
            output_path=None,
        )
        assert state["query"] == "Draft an NDA for matter-001"
        assert state["template_name"] is None
        assert state["output_path"] is None

    def test_state_template_name_can_be_set(self):
        state = DraftingState(
            query="Draft using template",
            matter_id="matter-001",
            template_name="nda.j2",
            context_chunks=[],
            rendered_content="",
            export_format="docx",
            output_path=None,
        )
        assert state["template_name"] == "nda.j2"


class TestDraftingAgentInit:
    def test_instantiation(self):
        mock_retriever = MagicMock()
        mock_renderer = MagicMock()
        mock_freeform = MagicMock()
        mock_exporter = MagicMock()

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=mock_renderer,
            freeform_drafter=mock_freeform,
            exporter=mock_exporter,
        )
        assert agent is not None

    def test_has_compiled_graph(self):
        agent = DraftingAgent(
            retriever=MagicMock(),
            renderer=MagicMock(),
            freeform_drafter=MagicMock(),
            exporter=MagicMock(),
        )
        assert agent.graph is not None


class TestDraftingAgentTemplatePath:
    """Task 7.13: Template-based drafting path."""

    async def test_template_path_renders_and_exports(self, tmp_path):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_renderer = MagicMock()
        mock_renderer.render = MagicMock(return_value="RENDERED NDA CONTENT")

        mock_freeform = MagicMock()

        mock_exporter = MagicMock()
        expected_path = str(tmp_path / "nda.docx")
        mock_exporter.export = MagicMock(return_value=expected_path)

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=mock_renderer,
            freeform_drafter=mock_freeform,
            exporter=mock_exporter,
        )

        result = await agent.run(
            query="Draft an NDA for Acme Corp and Beta LLC",
            matter_id="matter-001",
            access_level="full",
            template_name="nda.j2",
            context={"party_a": "Acme Corp", "party_b": "Beta LLC",
                     "effective_date": "March 1, 2026", "duration": "2 years",
                     "governing_law": "California"},
            export_format="docx",
            output_path=expected_path,
        )

        assert "output_path" in result
        mock_renderer.render.assert_called_once()
        mock_exporter.export.assert_called_once()
        # Freeform should NOT be called in template path
        mock_freeform.draft.assert_not_called()

    async def test_template_path_result_has_rendered_content(self, tmp_path):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_renderer = MagicMock()
        mock_renderer.render = MagicMock(return_value="TEMPLATE RENDERED TEXT")

        mock_exporter = MagicMock()
        mock_exporter.export = MagicMock(return_value=str(tmp_path / "doc.docx"))

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=mock_renderer,
            freeform_drafter=MagicMock(),
            exporter=mock_exporter,
        )

        result = await agent.run(
            query="Draft NDA",
            matter_id="matter-001",
            access_level="full",
            template_name="nda.j2",
            context={},
            export_format="docx",
            output_path=str(tmp_path / "doc.docx"),
        )

        assert "rendered_content" in result
        assert result["rendered_content"] == "TEMPLATE RENDERED TEXT"


class TestDraftingAgentFreeformPath:
    """Task 7.13: Freeform drafting path."""

    async def test_freeform_path_calls_drafter(self, tmp_path):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[
            {"doc_id": "d1", "chunk_id": "c1", "text": "Matter context.", "page": 1, "file_name": "file.pdf"}
        ])

        mock_renderer = MagicMock()

        mock_freeform = MagicMock()
        mock_freeform.draft = AsyncMock(return_value="FREEFORM DRAFTED NDA CONTENT")

        mock_exporter = MagicMock()
        expected_path = str(tmp_path / "nda_freeform.docx")
        mock_exporter.export = MagicMock(return_value=expected_path)

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=mock_renderer,
            freeform_drafter=mock_freeform,
            exporter=mock_exporter,
        )

        result = await agent.run(
            query="Draft an NDA for matter-001",
            matter_id="matter-001",
            access_level="full",
            template_name=None,  # No template — use freeform
            context={},
            export_format="docx",
            output_path=expected_path,
        )

        assert "output_path" in result
        mock_freeform.draft.assert_called_once()
        mock_exporter.export.assert_called_once()
        # Renderer should NOT be called in freeform path
        mock_renderer.render.assert_not_called()

    async def test_freeform_path_retrieves_context(self, tmp_path):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[
            {"doc_id": "d1", "chunk_id": "c1", "text": "Context text.", "page": 1, "file_name": "doc.pdf"}
        ])

        mock_freeform = MagicMock()
        mock_freeform.draft = AsyncMock(return_value="Drafted content.")

        mock_exporter = MagicMock()
        mock_exporter.export = MagicMock(return_value=str(tmp_path / "doc.md"))

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=MagicMock(),
            freeform_drafter=mock_freeform,
            exporter=mock_exporter,
        )

        await agent.run(
            query="Draft a summary",
            matter_id="matter-001",
            access_level="full",
            template_name=None,
            context={},
            export_format="md",
            output_path=str(tmp_path / "doc.md"),
        )

        mock_retriever.query.assert_called_once()

    async def test_freeform_result_has_content(self, tmp_path):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_freeform = MagicMock()
        mock_freeform.draft = AsyncMock(return_value="FREEFORM CONTENT HERE")

        mock_exporter = MagicMock()
        mock_exporter.export = MagicMock(return_value=str(tmp_path / "doc.md"))

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=MagicMock(),
            freeform_drafter=mock_freeform,
            exporter=mock_exporter,
        )

        result = await agent.run(
            query="Draft a motion",
            matter_id="matter-001",
            access_level="full",
            template_name=None,
            context={},
            export_format="md",
            output_path=str(tmp_path / "doc.md"),
        )

        assert "rendered_content" in result
        assert result["rendered_content"] == "FREEFORM CONTENT HERE"


class TestDraftingAgentExport:
    """Task 7.13: Export in all supported formats."""

    async def test_export_format_docx_passed_to_exporter(self, tmp_path):
        from app.docgen.exporter import ExportFormat

        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_renderer = MagicMock()
        mock_renderer.render = MagicMock(return_value="Content")

        mock_exporter = MagicMock()
        mock_exporter.export = MagicMock(return_value=str(tmp_path / "doc.docx"))

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=mock_renderer,
            freeform_drafter=MagicMock(),
            exporter=mock_exporter,
        )

        await agent.run(
            query="Draft NDA",
            matter_id="matter-001",
            access_level="full",
            template_name="nda.j2",
            context={},
            export_format="docx",
            output_path=str(tmp_path / "doc.docx"),
        )

        call_args = mock_exporter.export.call_args
        # Verify format arg was passed
        assert "docx" in str(call_args)

    async def test_export_format_md_passed_to_exporter(self, tmp_path):
        mock_retriever = MagicMock()
        mock_retriever.query = AsyncMock(return_value=[])

        mock_renderer = MagicMock()
        mock_renderer.render = MagicMock(return_value="Markdown content")

        mock_exporter = MagicMock()
        mock_exporter.export = MagicMock(return_value=str(tmp_path / "doc.md"))

        agent = DraftingAgent(
            retriever=mock_retriever,
            renderer=mock_renderer,
            freeform_drafter=MagicMock(),
            exporter=mock_exporter,
        )

        await agent.run(
            query="Draft NDA as markdown",
            matter_id="matter-001",
            access_level="full",
            template_name="nda.j2",
            context={},
            export_format="md",
            output_path=str(tmp_path / "doc.md"),
        )

        call_args = mock_exporter.export.call_args
        assert "md" in str(call_args)


class TestOrchestratorDraftingRouting:
    """Task 7.14: Orchestrator should route drafting-intent queries to drafting agent."""

    async def test_drafting_query_routes_to_drafting_agent(self):
        from app.agents.orchestrator import OrchestratorAgent

        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(return_value={"answer": "Retrieved", "citations": []})

        mock_drafting_agent = MagicMock()
        mock_drafting_agent.run = AsyncMock(return_value={
            "answer": "Drafted document content.",
            "rendered_content": "NDA CONTENT",
            "output_path": "/tmp/nda.docx",
            "citations": [],
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

    async def test_non_drafting_query_does_not_route_to_drafting(self):
        from app.agents.orchestrator import OrchestratorAgent

        mock_retrieval_agent = MagicMock()
        mock_retrieval_agent.run = AsyncMock(return_value={"answer": "Retrieved", "citations": []})

        mock_drafting_agent = MagicMock()
        mock_drafting_agent.run = AsyncMock(return_value={"answer": "Drafted", "citations": []})

        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="retrieval")

        agent = OrchestratorAgent(
            retrieval_agent=mock_retrieval_agent,
            gateway=mock_gateway,
            drafting_agent=mock_drafting_agent,
        )

        await agent.run(
            query="What are the facts of this case?",
            matter_id="matter-001",
            access_level="full",
        )

        mock_drafting_agent.run.assert_not_called()
        mock_retrieval_agent.run.assert_called_once()
