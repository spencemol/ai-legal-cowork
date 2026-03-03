"""Pinecone retriever — query by embedding + metadata filter (task 4.5).

Accepts a plain text query, embeds it using the provided embedder, and queries
Pinecone with matter_id + access_level metadata filters.  Returns a list of
chunk dicts that can be passed directly to the reranker.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol


class EmbedderProtocol(Protocol):
    """Minimal interface expected from an embedder."""

    def embed(self, text: str) -> list[float]:
        ...


class PineconeIndexProtocol(Protocol):
    """Minimal interface expected from a Pinecone index."""

    def query(
        self,
        *,
        vector: list[float],
        top_k: int,
        filter: dict,
        include_metadata: bool,
    ) -> Any:
        ...


_DEFAULT_TOP_K = 10


class PineconeRetriever:
    """Query Pinecone for semantically similar chunks filtered by matter.

    Parameters
    ----------
    index:
        A Pinecone ``Index`` instance (or a compatible mock).
    embedder:
        Any object with an ``embed(text: str) -> list[float]`` method.
    top_k:
        Maximum number of results to return from Pinecone.
    """

    def __init__(
        self,
        index: Any,
        embedder: Any,
        top_k: int = _DEFAULT_TOP_K,
    ) -> None:
        self._index = index
        self._embedder = embedder
        self.top_k = top_k

    async def query(
        self,
        query: str,
        matter_id: str,
        access_level: str,
    ) -> list[dict]:
        """Retrieve top-K chunks for *query* within *matter_id*.

        Parameters
        ----------
        query:
            User's search / question text.
        matter_id:
            Restrict results to this matter.
        access_level:
            Restrict results to this access level.

        Returns
        -------
        list[dict]
            Each dict has keys: ``id``, ``text``, ``score``, ``metadata``.
        """
        # Embed in thread pool (sentence-transformers is sync).
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, self._embedder.embed, query)

        metadata_filter: dict = {
            "matter_id": {"$eq": matter_id},
            "access_level": {"$eq": access_level},
        }

        response = self._index.query(
            vector=vector,
            top_k=self.top_k,
            filter=metadata_filter,
            include_metadata=True,
        )

        chunks: list[dict] = []
        for match in response.matches:
            meta = match.metadata or {}
            chunks.append(
                {
                    "id": match.id,
                    "text": meta.get("chunk_text", ""),
                    "score": match.score,
                    "metadata": meta,
                }
            )

        return chunks
