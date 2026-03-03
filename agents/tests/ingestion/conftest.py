"""Shared fixtures for ingestion unit and integration tests."""


import pytest

from app.rag.models import (
    DocumentInfo,
    PageContent,
    ParsedDocument,
    TextChunk,
    VectorRecord,
)

# ---------------------------------------------------------------------------
# File fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_text_file(tmp_path):
    """A real file on disk for hashing / chunking tests."""
    content = (
        "The plaintiff alleges breach of contract dated January 1, 2024. "
        "The defendant denies all allegations. "
        "Discovery is scheduled for March 15, 2024. "
        "The parties have agreed to mediation before trial. "
        "Counsel for both parties must submit briefs by April 30, 2024."
    )
    f = tmp_path / "sample.txt"
    f.write_text(content)
    return str(f)


@pytest.fixture
def another_text_file(tmp_path):
    """A second file with different content (different hash)."""
    f = tmp_path / "other.txt"
    f.write_text("Completely different legal document content here.")
    return str(f)


# ---------------------------------------------------------------------------
# Model fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_parsed_document(sample_text_file):
    return ParsedDocument(
        file_path=sample_text_file,
        file_hash="abc123deadbeef",
        pages=[
            PageContent(
                page_number=1,
                text=(
                    "The plaintiff alleges breach of contract dated January 1, 2024. "
                    "The defendant denies all allegations. "
                    "Discovery is scheduled for March 15, 2024."
                ),
            ),
            PageContent(
                page_number=2,
                text=(
                    "The parties have agreed to mediation before trial. "
                    "Counsel for both parties must submit briefs by April 30, 2024."
                ),
            ),
        ],
    )


@pytest.fixture
def sample_chunks():
    return [
        TextChunk(text="The plaintiff alleges breach of contract.", chunk_index=0, page_number=1, char_count=42),
        TextChunk(text="The defendant denies all allegations.", chunk_index=1, page_number=1, char_count=37),
        TextChunk(text="The parties agreed to mediation.", chunk_index=2, page_number=2, char_count=31),
    ]


@pytest.fixture
def sample_vectors():
    """384-dim float vectors simulating all-MiniLM-L6-v2 output."""
    import random

    random.seed(42)
    return [[random.uniform(-1, 1) for _ in range(384)] for _ in range(3)]


@pytest.fixture
def sample_vector_records(sample_vectors):
    doc_id = "doc-uuid-001"
    return [
        VectorRecord(
            id=f"{doc_id}_{i}",
            values=sample_vectors[i],
            metadata={
                "document_id": doc_id,
                "matter_id": "matter-uuid-001",
                "chunk_index": i,
                "chunk_text": f"chunk text {i}",
                "file_name": "sample.pdf",
                "page_number": 1,
                "access_level": "full",
                "content_type": "brief",
            },
        )
        for i in range(3)
    ]


@pytest.fixture
def existing_document_info(sample_text_file):
    """Simulates a document already registered in the Node REST API."""
    return DocumentInfo(
        id="doc-existing-001",
        file_name="sample.pdf",
        file_path=sample_text_file,
        file_hash="abc123deadbeef",
        status="indexed",
        matter_id="matter-uuid-001",
    )
