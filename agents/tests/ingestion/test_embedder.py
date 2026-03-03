"""Unit tests for the sentence-transformer embedding module (task 3.4).

The Embedder accepts an injected model so tests never load PyTorch or numpy.

RED: These tests fail until app/rag/embedder.py is implemented.
"""

import pytest

from app.rag.embedder import Embedder


class FakeModel:
    """Minimal stand-in for SentenceTransformer that returns deterministic 384-dim vectors.

    Returns plain Python lists so numpy is not required at test time.
    Embedder.embed() handles both numpy arrays and plain list-of-lists.
    """

    def encode(self, texts, **kwargs):
        # Deterministic 384-dim vectors as plain floats, no numpy required.
        return [[float(i % 384) / 384.0 for i in range(384)] for _ in texts]


class TestEmbedder:
    @pytest.fixture
    def embedder(self):
        return Embedder(model=FakeModel())

    def test_embed_returns_list(self, embedder):
        result = embedder.embed(["some legal text"])
        assert isinstance(result, list)

    def test_embed_returns_correct_count(self, embedder):
        texts = ["text one", "text two", "text three"]
        result = embedder.embed(texts)
        assert len(result) == 3

    def test_embed_returns_384_dim_vectors(self, embedder):
        result = embedder.embed(["legal brief contents"])
        assert len(result[0]) == 384

    def test_each_vector_is_list_of_floats(self, embedder):
        result = embedder.embed(["contract clause"])
        assert all(isinstance(v, float) for v in result[0])

    def test_batch_embed(self, embedder):
        texts = [f"document chunk {i}" for i in range(10)]
        result = embedder.embed(texts)
        assert len(result) == 10
        assert all(len(v) == 384 for v in result)

    def test_empty_list_returns_empty(self, embedder):
        result = embedder.embed([])
        assert result == []

    def test_model_used_for_encoding(self):
        """Embedder must delegate encoding to the injected model."""
        call_log = []

        class SpyModel:
            def encode(self, texts, **kwargs):
                call_log.append(list(texts))
                return [[0.0] * 384 for _ in texts]

        embedder = Embedder(model=SpyModel())
        embedder.embed(["hello", "world"])
        assert call_log == [["hello", "world"]]

    def test_default_model_name(self):
        """Default model name is all-MiniLM-L6-v2 (no model loaded in unit test)."""
        embedder = Embedder()
        assert embedder.model_name == "all-MiniLM-L6-v2"
