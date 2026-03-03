"""Tests for freeform LLM drafting module (task 7.9).

RED: These tests fail until app/docgen/freeform.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.docgen.freeform import FreeformDrafter


class TestFreeformDrafterInit:
    def test_instantiation(self):
        mock_gateway = MagicMock()
        drafter = FreeformDrafter(llm_gateway=mock_gateway)
        assert drafter is not None

    def test_gateway_stored(self):
        mock_gateway = MagicMock()
        drafter = FreeformDrafter(llm_gateway=mock_gateway)
        assert drafter.gateway is mock_gateway


class TestFreeformDrafterDraft:
    async def test_draft_returns_string(self, sample_chunks):
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(
            return_value="MUTUAL NON-DISCLOSURE AGREEMENT\n\nThis Agreement is entered into..."
        )
        drafter = FreeformDrafter(llm_gateway=mock_gateway)
        result = await drafter.draft(
            prompt="Draft an NDA for Acme Corp and Beta LLC",
            context_chunks=sample_chunks,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_draft_calls_gateway(self, sample_chunks):
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Generated legal document content.")
        drafter = FreeformDrafter(llm_gateway=mock_gateway)

        await drafter.draft(
            prompt="Draft a motion for summary judgment",
            context_chunks=sample_chunks,
        )

        mock_gateway.complete.assert_called_once()

    async def test_draft_includes_prompt_in_gateway_call(self):
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Document text.")
        drafter = FreeformDrafter(llm_gateway=mock_gateway)

        prompt = "Draft an engagement letter for new client"
        await drafter.draft(prompt=prompt, context_chunks=[])

        # The prompt should be included in the call to gateway
        call_args = mock_gateway.complete.call_args
        # First positional arg or keyword arg should contain the prompt
        all_args = str(call_args)
        assert prompt in all_args

    async def test_draft_includes_context_chunks_in_call(self, sample_chunks):
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Document with context.")
        drafter = FreeformDrafter(llm_gateway=mock_gateway)

        await drafter.draft(
            prompt="Draft a summary",
            context_chunks=sample_chunks,
        )

        # The gateway should be called with something that includes chunk text
        call_args = mock_gateway.complete.call_args
        call_str = str(call_args)
        # At least one chunk's text content should be included
        assert any(chunk["text"] in call_str for chunk in sample_chunks)

    async def test_draft_returns_gateway_response(self):
        expected_text = "ENGAGEMENT LETTER\n\nDear Client,\n\nWe are pleased..."
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value=expected_text)
        drafter = FreeformDrafter(llm_gateway=mock_gateway)

        result = await drafter.draft(
            prompt="Draft an engagement letter",
            context_chunks=[],
        )

        assert result == expected_text

    async def test_draft_with_empty_chunks(self):
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Document without context.")
        drafter = FreeformDrafter(llm_gateway=mock_gateway)

        result = await drafter.draft(
            prompt="Draft a document",
            context_chunks=[],
        )

        assert isinstance(result, str)
        mock_gateway.complete.assert_called_once()

    async def test_draft_passes_system_prompt(self):
        mock_gateway = MagicMock()
        mock_gateway.complete = AsyncMock(return_value="Generated text.")
        drafter = FreeformDrafter(llm_gateway=mock_gateway)

        await drafter.draft(prompt="Draft an NDA", context_chunks=[])

        # Should call complete with a system keyword arg
        call_kwargs = mock_gateway.complete.call_args.kwargs
        assert "system" in call_kwargs
