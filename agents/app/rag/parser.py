"""LlamaParse document parser wrapper (task 3.2).

The ``DocumentParser`` accepts an injected LlamaParse-compatible client so it
can be tested without an API key or network calls.

Production installation:
    uv sync --extra rag

Production usage:
    from llama_parse import LlamaParse
    llama = LlamaParse(api_key="...", result_type="markdown")
    parser = DocumentParser(llama_client=llama)
    doc = await parser.parse("/path/to/brief.pdf")
"""

from __future__ import annotations

from app.rag.hasher import hash_file
from app.rag.models import PageContent, ParsedDocument


class DocumentParser:
    """Parses a document file into a :class:`~app.rag.models.ParsedDocument`.

    Parameters
    ----------
    llama_client:
        An object with an ``aload_data(file_path: str)`` async method that
        returns a list of document objects with ``.text`` and ``.metadata``
        attributes (matching the LlamaParse interface).  Pass a mock here in
        tests to avoid network calls.
    """

    def __init__(self, llama_client) -> None:  # type: ignore[type-arg]
        self._client = llama_client

    async def parse(self, file_path: str) -> ParsedDocument:
        """Parse *file_path* and return structured page content.

        Computes the SHA-256 hash of the file for deduplication.
        Page numbers are taken from ``metadata["page_label"]`` when present;
        otherwise sequential 1-based numbering is used.
        """
        file_hash = hash_file(file_path)
        raw_docs = await self._client.aload_data(file_path)

        pages: list[PageContent] = []
        for i, doc in enumerate(raw_docs):
            # LlamaParse returns page_label in metadata when available
            page_label = doc.metadata.get("page_label")
            try:
                page_number = int(page_label) if page_label is not None else i + 1
            except (ValueError, TypeError):
                page_number = i + 1

            pages.append(PageContent(page_number=page_number, text=doc.text))

        return ParsedDocument(
            file_path=file_path,
            file_hash=file_hash,
            pages=pages,
        )
