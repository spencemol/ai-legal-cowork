"""HTTP client for the Node REST API (tasks 3.6, 3.7).

Handles document registration, hash-based dedup checks, and status updates.
All methods use httpx async so the ingestion pipeline can run without blocking.
"""

from __future__ import annotations

import httpx

from app.rag.models import DocumentInfo


class RestAPIClient:
    """Async HTTP client for the Node REST API.

    Parameters
    ----------
    base_url:
        Base URL of the Node REST API (e.g. ``http://localhost:3000``).
    jwt_token:
        Optional JWT bearer token.  When provided it is sent as the
        ``Authorization: Bearer <token>`` header on every request.
    """

    def __init__(self, base_url: str, jwt_token: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers: dict[str, str] = {}
        if jwt_token:
            self._headers["Authorization"] = f"Bearer {jwt_token}"

    async def get_documents_for_matter(self, matter_id: str) -> list[DocumentInfo]:
        """Return all documents registered under *matter_id*.

        Used for deduplication: caller compares ``file_hash`` to decide
        whether a file needs re-embedding.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/matters/{matter_id}/documents",
                headers=self._headers,
            )
            response.raise_for_status()
            return [_doc_from_api(d) for d in response.json()]

    async def register_document(
        self,
        matter_id: str,
        file_name: str,
        file_path: str,
        file_hash: str,
        mime_type: str,
    ) -> str:
        """Register a new document record and return its UUID."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/matters/{matter_id}/documents",
                json={
                    "fileName": file_name,
                    "filePath": file_path,
                    "fileHash": file_hash,
                    "mimeType": mime_type,
                },
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json()["id"]

    async def update_document_status(self, document_id: str, status: str) -> None:
        """Set the ingestion status of *document_id* (pending/processing/indexed/failed)."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self._base_url}/documents/{document_id}/status",
                json={"status": status},
                headers=self._headers,
            )
            response.raise_for_status()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc_from_api(raw: dict) -> DocumentInfo:
    """Map Node API camelCase keys to DocumentInfo fields."""
    return DocumentInfo(
        id=raw["id"],
        file_name=raw.get("fileName", raw.get("file_name", "")),
        file_path=raw.get("filePath", raw.get("file_path", "")),
        file_hash=raw.get("fileHash", raw.get("file_hash", "")),
        status=raw.get("status", ""),
        matter_id=raw.get("matterId", raw.get("matter_id", "")),
    )
