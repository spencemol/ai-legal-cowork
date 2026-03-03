"""Unit tests for the Pinecone upsert module (task 3.5).

PineconeStore wraps a VectorIndex Protocol so the real Pinecone client
is never instantiated during tests.

RED: These tests fail until app/rag/pinecone_store.py is implemented.
"""

import pytest

from app.rag.models import VectorRecord
from app.rag.pinecone_store import PineconeStore


class FakeIndex:
    """Tracks upsert calls and simulates Pinecone index stats."""

    def __init__(self):
        self.upserted: list[list[dict]] = []

    def upsert(self, vectors: list[dict]) -> None:
        self.upserted.append(vectors)

    def describe_index_stats(self) -> dict:
        total = sum(len(batch) for batch in self.upserted)
        return {"total_vector_count": total, "dimension": 384}


class TestPineconeStore:
    @pytest.fixture
    def fake_index(self):
        return FakeIndex()

    @pytest.fixture
    def store(self, fake_index):
        return PineconeStore(index=fake_index)

    def test_upsert_calls_index(self, store, fake_index, sample_vector_records):
        store.upsert(sample_vector_records)
        assert len(fake_index.upserted) == 1

    def test_upsert_passes_correct_ids(self, store, fake_index, sample_vector_records):
        store.upsert(sample_vector_records)
        upserted_ids = {v["id"] for v in fake_index.upserted[0]}
        expected_ids = {r.id for r in sample_vector_records}
        assert upserted_ids == expected_ids

    def test_upsert_passes_correct_values(self, store, fake_index, sample_vector_records):
        store.upsert(sample_vector_records)
        batch = fake_index.upserted[0]
        for item, record in zip(batch, sample_vector_records):
            assert item["values"] == record.values

    def test_upsert_includes_metadata(self, store, fake_index, sample_vector_records):
        store.upsert(sample_vector_records)
        for item in fake_index.upserted[0]:
            assert "metadata" in item
            assert "document_id" in item["metadata"]
            assert "matter_id" in item["metadata"]

    def test_upsert_batches_large_input(self, fake_index):
        """Vectors over the batch_size must be upserted in multiple batches."""
        store = PineconeStore(index=fake_index, batch_size=2)
        records = [
            VectorRecord(
                id=f"doc_{i}",
                values=[0.1] * 384,
                metadata={"document_id": f"doc_{i}", "matter_id": "m1"},
            )
            for i in range(5)
        ]
        store.upsert(records)
        # 5 vectors with batch_size=2 → 3 batches (2 + 2 + 1)
        assert len(fake_index.upserted) == 3

    def test_describe_stats(self, store, fake_index, sample_vector_records):
        store.upsert(sample_vector_records)
        stats = store.describe_stats()
        assert "total_vector_count" in stats
        assert stats["total_vector_count"] == len(sample_vector_records)

    def test_upsert_empty_list_does_nothing(self, store, fake_index):
        store.upsert([])
        assert fake_index.upserted == []
