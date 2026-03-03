"""POST /ingest — manual document ingestion trigger (task 3.9).

The route delegates to ``run_ingestion`` which is a thin wrapper around
``ingest_many``.  Tests patch ``run_ingestion`` directly so that the endpoint
can be exercised without a running Node API, Pinecone, or LlamaParse instance.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from app.rag.api_client import RestAPIClient
from app.rag.embedder import Embedder
from app.rag.ingestion import ingest_many
from app.rag.models import IngestionRequest, IngestionResult
from app.rag.parser import DocumentParser
from app.rag.pinecone_store import PineconeStore

router = APIRouter()


async def run_ingestion(request: IngestionRequest) -> IngestionResult:
    """Build pipeline dependencies from environment and run ``ingest_many``.

    Separated from the route handler so tests can patch it in isolation.
    Required environment variables (all optional with safe defaults for dev):
      - ``NODE_API_URL``      — Node REST API base URL (default: http://localhost:3000)
      - ``NODE_API_JWT``      — JWT token for the Node REST API (default: empty)
      - ``PINECONE_API_KEY``  — Pinecone API key
      - ``PINECONE_INDEX``    — Pinecone index name (default: legal-docs)
      - ``EMBEDDING_MODEL``   — sentence-transformers model name
    """
    node_url = os.getenv("NODE_API_URL", "http://localhost:3000")
    node_jwt = os.getenv("NODE_API_JWT")
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
    pinecone_index_name = os.getenv("PINECONE_INDEX", "legal-docs")
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    api_client = RestAPIClient(base_url=node_url, jwt_token=node_jwt)
    embedder = Embedder(model_name=embedding_model)

    # Build Pinecone index lazily so the import only fails at request time
    # (not at startup) when the optional `rag` extra isn't installed.
    try:
        from pinecone import Pinecone  # type: ignore[import]

        pc = Pinecone(api_key=pinecone_api_key)
        pinecone_index = pc.Index(pinecone_index_name)
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Pinecone is not installed. Run: uv sync --extra rag",
        ) from exc

    try:
        from llama_parse import LlamaParse  # type: ignore[import]

        llama_client = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY", ""),
            result_type="markdown",
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="llama-parse is not installed. Run: uv sync --extra rag",
        ) from exc

    parser = DocumentParser(llama_client=llama_client)
    pinecone_store = PineconeStore(index=pinecone_index)

    return await ingest_many(
        file_paths=request.file_paths,
        matter_id=request.matter_id,
        api_client=api_client,
        parser=parser,
        embedder=embedder,
        pinecone_store=pinecone_store,
    )


@router.post("/ingest", response_model=IngestionResult)
async def ingest_endpoint(request: IngestionRequest) -> IngestionResult:
    """Ingest one or more document files into the RAG pipeline.

    Accepts a JSON body with ``file_paths`` (list of absolute paths on the
    server's filesystem) and ``matter_id`` (UUID).  Returns counts of
    processed, skipped (dedup), and failed files along with document IDs.
    """
    return await run_ingestion(request)
