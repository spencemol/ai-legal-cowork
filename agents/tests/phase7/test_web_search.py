"""Tests for DuckDuckGo web search tool (task 7.1).

RED: These tests fail until app/research/web_search.py is implemented.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.research.web_search import WebSearchTool


class TestWebSearchToolInit:
    def test_instantiation(self):
        tool = WebSearchTool()
        assert tool is not None

    def test_default_max_results(self):
        tool = WebSearchTool()
        assert tool.default_max_results == 5


class TestWebSearchToolSearch:
    def test_search_returns_list(self):
        mock_results = [
            {
                "title": "Contract Law Overview",
                "href": "https://example.com/contract",
                "body": "Contract law governs agreements...",
            }
        ]
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = mock_results

            tool = WebSearchTool()
            results = tool.search("contract breach law")

        assert isinstance(results, list)

    def test_search_returns_title_url_snippet(self):
        mock_ddgs_results = [
            {
                "title": "Contract Law Overview",
                "href": "https://example.com/contract",
                "body": "Contract law governs agreements between parties.",
            },
            {
                "title": "Breach of Contract",
                "href": "https://example.com/breach",
                "body": "A breach occurs when a party fails to perform.",
            },
        ]
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = mock_ddgs_results

            tool = WebSearchTool()
            results = tool.search("contract breach")

        assert len(results) == 2
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result

    def test_search_maps_href_to_url(self):
        mock_ddgs_results = [
            {
                "title": "Legal Research",
                "href": "https://lawsite.com/research",
                "body": "Legal research involves...",
            }
        ]
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = mock_ddgs_results

            tool = WebSearchTool()
            results = tool.search("legal research")

        assert results[0]["url"] == "https://lawsite.com/research"

    def test_search_maps_body_to_snippet(self):
        mock_ddgs_results = [
            {
                "title": "NDA Guide",
                "href": "https://example.com/nda",
                "body": "An NDA prevents disclosure of confidential information.",
            }
        ]
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = mock_ddgs_results

            tool = WebSearchTool()
            results = tool.search("NDA confidentiality")

        assert results[0]["snippet"] == "An NDA prevents disclosure of confidential information."

    def test_search_respects_max_results(self):
        mock_ddgs_results = [
            {"title": f"Result {i}", "href": f"https://ex.com/{i}", "body": f"Snippet {i}"}
            for i in range(10)
        ]
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = mock_ddgs_results[:3]

            tool = WebSearchTool()
            results = tool.search("contract law", max_results=3)

        # Verify max_results was passed to DDGS
        mock_ddgs.text.assert_called_once_with("contract law", max_results=3)

    def test_search_empty_results(self):
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = []

            tool = WebSearchTool()
            results = tool.search("obscure legal query xyz")

        assert results == []

    def test_search_uses_default_max_results(self):
        with patch("app.research.web_search.DDGS") as mock_ddgs_cls:
            mock_ddgs = MagicMock()
            mock_ddgs_cls.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
            mock_ddgs_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_ddgs.text.return_value = []

            tool = WebSearchTool()
            tool.search("some query")

        mock_ddgs.text.assert_called_once_with("some query", max_results=5)
