"""Pinecone vector upsert module (task 3.5).

``PineconeStore`` wraps a vector index object and batches upserts.
Inject a ``FakeIndex`` in tests to avoid Pinecone API calls.

Production usage:
    from pinecone import Pinecone
    pc = Pinecone(api_key="...")
    index = pc.Index("legal-docs")
    store = PineconeStore(index=index)

Production installation:
    uv sync --extra rag
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.rag.models import VectorRecord


@runtime_checkable
class VectorIndex(Protocol):
    """Minimal interface that both real Pinecone Index and test fakes satisfy."""

    def upsert(self, vectors: list[dict]) -> None:
        ...

    def describe_index_stats(self) -> dict:
        ...


class PineconeStore:
    """Upserts :class:`~app.rag.models.VectorRecord` objects into a Pinecone index.

    Parameters
    ----------
    index:
        An object satisfying the :class:`VectorIndex` protocol.
    batch_size:
        Number of vectors per upsert call.  Pinecone recommends ≤ 100.
    """

    def __init__(self, index: VectorIndex, batch_size: int = 100) -> None:
        self._index = index
        self._batch_size = batch_size

    def upsert(self, records: list[VectorRecord]) -> None:
        """Upsert *records* to Pinecone in batches of ``batch_size``."""
        if not records:
            return
        for i in range(0, len(records), self._batch_size):
            batch = records[i : i + self._batch_size]
            self._index.upsert(
                vectors=[
                    {"id": r.id, "values": r.values, "metadata": r.metadata}
                    for r in batch
                ]
            )

    def describe_stats(self) -> dict:
        """Return index statistics (e.g. total_vector_count)."""
        return self._index.describe_index_stats()
