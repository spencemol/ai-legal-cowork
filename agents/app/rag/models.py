"""Pydantic models shared across the RAG / ingestion pipeline."""

from pydantic import BaseModel


class PageContent(BaseModel):
    """Parsed content of a single document page."""

    page_number: int
    text: str


class ParsedDocument(BaseModel):
    """Output of the document parser."""

    file_path: str
    file_hash: str
    pages: list[PageContent]


class TextChunk(BaseModel):
    """A single text chunk produced by the chunker."""

    text: str
    chunk_index: int
    page_number: int | None = None
    char_count: int


class VectorRecord(BaseModel):
    """A vector record ready to upsert into Pinecone."""

    id: str  # "{document_id}_{chunk_index}"
    values: list[float]  # 384-dim for all-MiniLM-L6-v2
    metadata: dict


class IngestionRequest(BaseModel):
    """Request body for the POST /ingest endpoint."""

    file_paths: list[str]
    matter_id: str


class IngestionResult(BaseModel):
    """Response from the POST /ingest endpoint."""

    matter_id: str
    total_files: int
    processed: int
    skipped: int  # dedup skip — file hash unchanged and already indexed
    failed: int
    document_ids: list[str]


class DocumentInfo(BaseModel):
    """Document metadata returned by the Node REST API."""

    id: str
    file_name: str
    file_path: str
    file_hash: str
    status: str
    matter_id: str
