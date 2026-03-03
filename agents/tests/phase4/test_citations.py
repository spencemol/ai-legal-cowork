"""Unit tests for the citation formatter (task 4.7).

Task 4.7: Citation formatter — convert ranked chunks into citation objects

No external dependencies to mock.

RED: These tests fail until app/retrieval/citations.py is implemented.
"""

from __future__ import annotations

import pytest

from app.retrieval.citations import CitationFormatter


@pytest.fixture
def reranked_chunks() -> list[dict]:
    return [
        {
            "id": "doc-001_0",
            "text": "The plaintiff alleges breach of contract dated January 1, 2024.",
            "score": 0.92,
            "rerank_score": 0.97,
            "metadata": {
                "document_id": "doc-001",
                "matter_id": "matter-uuid-001",
                "chunk_index": 0,
                "file_name": "brief.pdf",
                "page_number": 1,
                "access_level": "full",
            },
        },
        {
            "id": "doc-001_1",
            "text": "The defendant denies all allegations and counterclaims damages.",
            "score": 0.85,
            "rerank_score": 0.88,
            "metadata": {
                "document_id": "doc-001",
                "matter_id": "matter-uuid-001",
                "chunk_index": 1,
                "file_name": "brief.pdf",
                "page_number": 2,
                "access_level": "full",
            },
        },
    ]


class TestCitationFormatterFormat:
    def test_format_returns_list(self, reranked_chunks):
        formatter = CitationFormatter()
        result = formatter.format(reranked_chunks)
        assert isinstance(result, list)

    def test_format_correct_count(self, reranked_chunks):
        formatter = CitationFormatter()
        result = formatter.format(reranked_chunks)
        assert len(result) == len(reranked_chunks)

    def test_citation_has_doc_id(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        for citation in citations:
            assert "doc_id" in citation

    def test_citation_has_chunk_id(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        for citation in citations:
            assert "chunk_id" in citation

    def test_citation_has_text_snippet(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        for citation in citations:
            assert "text_snippet" in citation

    def test_citation_has_page(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        for citation in citations:
            assert "page" in citation

    def test_citation_doc_id_matches_document_id(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        assert citations[0]["doc_id"] == "doc-001"

    def test_citation_chunk_id_matches_chunk_record_id(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        assert citations[0]["chunk_id"] == "doc-001_0"

    def test_citation_text_snippet_is_truncated(self, reranked_chunks):
        """Text snippet should be a reasonable length for display."""
        formatter = CitationFormatter(snippet_max_len=50)
        citations = formatter.format(reranked_chunks)
        for citation in citations:
            assert len(citation["text_snippet"]) <= 50 + 3  # allow for "..."

    def test_citation_page_from_metadata(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        assert citations[0]["page"] == 1
        assert citations[1]["page"] == 2

    def test_empty_chunks_returns_empty_list(self):
        formatter = CitationFormatter()
        result = formatter.format([])
        assert result == []

    def test_citation_file_name_present(self, reranked_chunks):
        """Citations should include file_name for display purposes."""
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        for citation in citations:
            assert "file_name" in citation

    def test_citation_file_name_value(self, reranked_chunks):
        formatter = CitationFormatter()
        citations = formatter.format(reranked_chunks)
        assert citations[0]["file_name"] == "brief.pdf"

    def test_chunk_without_page_number_defaults_to_none(self):
        chunks = [
            {
                "id": "doc-002_0",
                "text": "Some text without page info.",
                "score": 0.80,
                "rerank_score": 0.85,
                "metadata": {
                    "document_id": "doc-002",
                    "matter_id": "matter-uuid-001",
                    "chunk_index": 0,
                    "file_name": "unknown.pdf",
                    # No page_number key
                    "access_level": "full",
                },
            }
        ]
        formatter = CitationFormatter()
        citations = formatter.format(chunks)
        assert citations[0]["page"] is None
