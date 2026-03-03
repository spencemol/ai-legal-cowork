"""End-to-end ingestion pipeline (tasks 3.6, 3.7, 3.8).

``ingest_document`` handles a single file:
  file → SHA-256 hash → dedup check → parse → chunk → embed → Pinecone upsert
  → status update (processing → indexed | failed)

``ingest_many`` iterates over a list of file paths and aggregates results
for the POST /ingest endpoint (task 3.9).
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from app.rag.api_client import RestAPIClient
from app.rag.chunker import ChunkConfig, chunk_text
from app.rag.embedder import Embedder
from app.rag.hasher import hash_file
from app.rag.models import IngestionResult, VectorRecord
from app.rag.parser import DocumentParser
from app.rag.pinecone_store import PineconeStore

# Default chunk config for the ingestion pipeline (~512 tokens / ~64 token overlap)
_DEFAULT_CHUNK_CONFIG = ChunkConfig(max_chars=2048, overlap_chars=256)


async def ingest_document(
    file_path: str,
    matter_id: str,
    api_client: RestAPIClient,
    parser: DocumentParser,
    embedder: Embedder,
    pinecone_store: PineconeStore,
    chunk_config: ChunkConfig | None = None,
) -> tuple[str, bool]:
    """Ingest a single document into the RAG pipeline.

    Parameters
    ----------
    file_path:
        Absolute path to the document on the local filesystem.
    matter_id:
        UUID of the matter this document belongs to.
    api_client:
        REST API client used for document registration and status updates.
    parser:
        Document parser (wraps LlamaParse in production).
    embedder:
        Embedding model wrapper.
    pinecone_store:
        Pinecone upsert wrapper.
    chunk_config:
        Chunking parameters.  Uses ``_DEFAULT_CHUNK_CONFIG`` when ``None``.

    Returns
    -------
    (document_id, was_processed)
        *was_processed* is ``False`` when the document was skipped because its
        hash already exists with ``status="indexed"`` (dedup).
    """
    if chunk_config is None:
        chunk_config = _DEFAULT_CHUNK_CONFIG

    path = Path(file_path)
    file_hash = hash_file(path)

    # ------------------------------------------------------------------
    # Dedup check (task 3.6): if the file is already indexed, skip it.
    # ------------------------------------------------------------------
    existing_docs = await api_client.get_documents_for_matter(matter_id)
    for doc in existing_docs:
        if doc.file_hash == file_hash and doc.status == "indexed":
            return (doc.id, False)

    # ------------------------------------------------------------------
    # Register the document (task 3.7)
    # ------------------------------------------------------------------
    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    doc_id = await api_client.register_document(
        matter_id=matter_id,
        file_name=path.name,
        file_path=str(path),
        file_hash=file_hash,
        mime_type=mime_type,
    )

    await api_client.update_document_status(document_id=doc_id, status="processing")

    try:
        # ----------------------------------------------------------------
        # Parse (task 3.2)
        # ----------------------------------------------------------------
        parsed = await parser.parse(str(path))

        # ----------------------------------------------------------------
        # Chunk (task 3.3) — chunk each page separately to preserve page numbers
        # ----------------------------------------------------------------
        all_chunks = []
        for page in parsed.pages:
            page_chunks = chunk_text(page.text, config=chunk_config, page_number=page.page_number)
            all_chunks.extend(page_chunks)

        # ----------------------------------------------------------------
        # Embed (task 3.4)
        # ----------------------------------------------------------------
        texts = [c.text for c in all_chunks]
        vectors = embedder.embed(texts)

        # ----------------------------------------------------------------
        # Build VectorRecords and upsert to Pinecone (task 3.5)
        # ----------------------------------------------------------------
        records = [
            VectorRecord(
                id=f"{doc_id}_{i}",
                values=vectors[i],
                metadata={
                    "document_id": doc_id,
                    "matter_id": matter_id,
                    "chunk_index": chunk.chunk_index,
                    # Truncated to stay within Pinecone's 40 KB metadata limit
                    "chunk_text": chunk.text[:1000],
                    "file_name": path.name,
                    "page_number": chunk.page_number,
                    "access_level": "full",
                    "content_type": _detect_content_type(path),
                },
            )
            for i, chunk in enumerate(all_chunks)
        ]

        if records:
            pinecone_store.upsert(records)

        # ----------------------------------------------------------------
        # Mark as indexed (task 3.7)
        # ----------------------------------------------------------------
        await api_client.update_document_status(document_id=doc_id, status="indexed")
        return (doc_id, True)

    except Exception:
        await api_client.update_document_status(document_id=doc_id, status="failed")
        raise


async def ingest_many(
    file_paths: list[str],
    matter_id: str,
    api_client: RestAPIClient,
    parser: DocumentParser,
    embedder: Embedder,
    pinecone_store: PineconeStore,
    chunk_config: ChunkConfig | None = None,
) -> IngestionResult:
    """Ingest multiple documents and return an aggregated result.

    Failed documents are counted but do not abort the batch.
    """
    result = IngestionResult(
        matter_id=matter_id,
        total_files=len(file_paths),
        processed=0,
        skipped=0,
        failed=0,
        document_ids=[],
    )

    for file_path in file_paths:
        try:
            doc_id, was_processed = await ingest_document(
                file_path=file_path,
                matter_id=matter_id,
                api_client=api_client,
                parser=parser,
                embedder=embedder,
                pinecone_store=pinecone_store,
                chunk_config=chunk_config,
            )
            result.document_ids.append(doc_id)
            if was_processed:
                result.processed += 1
            else:
                result.skipped += 1
        except Exception:
            result.failed += 1

    return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _detect_content_type(path: Path) -> str:
    """Guess legal content type from file name / extension."""
    name_lower = path.stem.lower()
    if "brief" in name_lower:
        return "brief"
    if "transcript" in name_lower:
        return "transcript"
    if "email" in name_lower:
        return "email"
    if "motion" in name_lower:
        return "court_record"
    if "nda" in name_lower or "contract" in name_lower:
        return "contract"
    return "document"
