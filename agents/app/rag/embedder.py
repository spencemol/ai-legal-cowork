"""Sentence-transformer embedding module (task 3.4).

Uses ``all-MiniLM-L6-v2`` by default, which produces 384-dimensional vectors.
The real ``SentenceTransformer`` model is loaded lazily so the module can be
imported (and tested with a mock) without PyTorch installed.

Production installation:
    uv sync --extra ml
"""

from __future__ import annotations

from typing import Any, Protocol


class _EncoderProtocol(Protocol):
    """Minimal interface that SentenceTransformer satisfies."""

    def encode(self, texts: list[str], **kwargs) -> Any:
        ...


class Embedder:
    """Wraps a sentence-transformers model to embed lists of strings.

    Parameters
    ----------
    model:
        An object with an ``encode(texts, **kwargs) -> np.ndarray`` method.
        When *None*, the real ``SentenceTransformer`` is loaded lazily on
        first use.  Pass a mock here in tests to avoid loading PyTorch.
    model_name:
        Hugging-Face model name used when loading the real model.
    """

    def __init__(
        self,
        model: _EncoderProtocol | None = None,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self._model = model
        self.model_name = model_name

    def _get_model(self) -> _EncoderProtocol:
        if self._model is None:
            # Lazy import — requires ``sentence-transformers`` extra
            try:
                from sentence_transformers import (
                    SentenceTransformer,  # type: ignore[import]
                )
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required for embedding. "
                    "Install it with: uv sync --extra ml"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings and return 384-dim float vectors.

        Parameters
        ----------
        texts:
            List of strings to embed.

        Returns
        -------
        list[list[float]]
            One 384-element float list per input string.
        """
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(texts)
        # SentenceTransformer returns a numpy ndarray; plain list-of-lists is
        # also accepted (used by test fakes that don't depend on numpy).
        if hasattr(embeddings, "tolist"):
            return embeddings.tolist()
        return [list(row) for row in embeddings]
