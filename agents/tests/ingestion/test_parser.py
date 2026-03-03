"""Unit tests for the LlamaParse document parser wrapper (task 3.2).

The DocumentParser accepts an injected LlamaParse client so no API key
or network calls are needed during testing.

RED: These tests fail until app/rag/parser.py is implemented.
"""

import pytest

from app.rag.models import ParsedDocument
from app.rag.parser import DocumentParser


class FakeLlamaDocument:
    """Mimics a single LlamaIndex / LlamaParse Document object."""

    def __init__(self, text: str, metadata: dict):
        self.text = text
        self.metadata = metadata


class FakeLlamaParser:
    """Mimics llama_parse.LlamaParse.load_data()."""

    def __init__(self, pages: list[tuple[int, str]]):
        self._pages = pages

    async def aload_data(self, file_path: str):
        return [
            FakeLlamaDocument(
                text=text,
                metadata={"page_label": str(page_num)},
            )
            for page_num, text in self._pages
        ]


class TestDocumentParser:
    @pytest.fixture
    def two_page_parser(self):
        return FakeLlamaParser(
            pages=[
                (1, "Page one discusses the contract terms and obligations."),
                (2, "Page two outlines the dispute resolution mechanism."),
            ]
        )

    @pytest.fixture
    def file_path(self, tmp_path):
        f = tmp_path / "brief.pdf"
        f.write_bytes(b"%PDF-1.4 fake pdf content")
        return str(f)

    async def test_parse_returns_parsed_document(self, two_page_parser, file_path, sample_text_file):
        parser = DocumentParser(llama_client=two_page_parser)
        result = await parser.parse(file_path)
        assert isinstance(result, ParsedDocument)

    async def test_parse_includes_pages(self, two_page_parser, file_path):
        parser = DocumentParser(llama_client=two_page_parser)
        result = await parser.parse(file_path)
        assert len(result.pages) == 2

    async def test_parse_page_content_correct(self, two_page_parser, file_path):
        parser = DocumentParser(llama_client=two_page_parser)
        result = await parser.parse(file_path)
        assert result.pages[0].page_number == 1
        assert "contract terms" in result.pages[0].text
        assert result.pages[1].page_number == 2
        assert "dispute resolution" in result.pages[1].text

    async def test_parse_sets_file_path(self, two_page_parser, file_path):
        parser = DocumentParser(llama_client=two_page_parser)
        result = await parser.parse(file_path)
        assert result.file_path == file_path

    async def test_parse_computes_file_hash(self, two_page_parser, file_path):
        parser = DocumentParser(llama_client=two_page_parser)
        result = await parser.parse(file_path)
        # Hash should be a 64-char hex string
        assert isinstance(result.file_hash, str)
        assert len(result.file_hash) == 64

    async def test_parse_empty_document(self, file_path):
        empty_parser = FakeLlamaParser(pages=[])
        parser = DocumentParser(llama_client=empty_parser)
        result = await parser.parse(file_path)
        assert isinstance(result, ParsedDocument)
        assert result.pages == []

    async def test_missing_page_label_defaults_to_sequential(self, file_path):
        """If LlamaParse doesn't provide page_label, fall back to sequential numbering."""

        class NoLabelParser:
            async def aload_data(self, fp):
                return [
                    FakeLlamaDocument(text="text", metadata={}),
                    FakeLlamaDocument(text="more text", metadata={}),
                ]

        parser = DocumentParser(llama_client=NoLabelParser())
        result = await parser.parse(file_path)
        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2
