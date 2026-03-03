"""Tests for legal database search stub (task 7.2).

RED: These tests fail until app/research/legal_db.py is implemented.
"""

from __future__ import annotations

import pytest

from app.research.legal_db import LegalDBSearchTool


class TestLegalDBSearchToolInit:
    def test_instantiation(self):
        tool = LegalDBSearchTool()
        assert tool is not None


class TestLegalDBSearchToolSearch:
    def test_search_returns_list(self):
        tool = LegalDBSearchTool()
        results = tool.search("contract breach")
        assert isinstance(results, list)

    def test_search_returns_results(self):
        tool = LegalDBSearchTool()
        results = tool.search("breach of contract damages")
        assert len(results) > 0

    def test_results_have_required_fields(self):
        tool = LegalDBSearchTool()
        results = tool.search("negligence tort law")
        for result in results:
            assert "title" in result
            assert "citation" in result
            assert "snippet" in result
            assert "source" in result
            assert "url" in result

    def test_source_is_westlaw_or_lexisnexis(self):
        tool = LegalDBSearchTool()
        results = tool.search("contract breach")
        for result in results:
            assert result["source"] in ("westlaw", "lexisnexis")

    def test_max_results_respected(self):
        tool = LegalDBSearchTool()
        results = tool.search("contract law", max_results=2)
        assert len(results) <= 2

    def test_max_results_default(self):
        tool = LegalDBSearchTool()
        results = tool.search("legal precedent")
        assert len(results) <= 5

    def test_citation_is_nonempty_string(self):
        tool = LegalDBSearchTool()
        results = tool.search("court ruling")
        for result in results:
            assert isinstance(result["citation"], str)
            assert len(result["citation"]) > 0

    def test_title_is_nonempty_string(self):
        tool = LegalDBSearchTool()
        results = tool.search("court ruling")
        for result in results:
            assert isinstance(result["title"], str)
            assert len(result["title"]) > 0

    def test_different_queries_return_results(self):
        """Stub should return results regardless of query content."""
        tool = LegalDBSearchTool()
        r1 = tool.search("NDA confidentiality")
        r2 = tool.search("employment discrimination")
        assert len(r1) > 0
        assert len(r2) > 0
