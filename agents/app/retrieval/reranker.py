"""bge-reranker module — rerank retrieved chunks by relevance (task 4.6).

Uses ``FlagEmbedding.FlagReranker`` to score each (query, chunk_text) pair and
returns the top-K chunks sorted by descending rerank score.
"""

from __future__ import annotations

try:
    from FlagEmbedding import FlagReranker  # type: ignore[import]
except ImportError:  # pragma: no cover
    FlagReranker = None  # type: ignore[assignment,misc]


_DEFAULT_MODEL = "BAAI/bge-reranker-base"
_DEFAULT_TOP_K = 5


class BGEReranker:
    """Rerank retrieved chunks using a cross-encoder bge model.

    Parameters
    ----------
    model_name:
        HuggingFace model ID for the FlagReranker.  Defaults to
        ``BAAI/bge-reranker-base``.
    top_k:
        Maximum number of chunks to return after reranking.
    use_fp16:
        Use half-precision inference (requires CUDA).  Defaults to ``False``
        for CPU compatibility in tests.
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        top_k: int = _DEFAULT_TOP_K,
        use_fp16: bool = False,
    ) -> None:
        if FlagReranker is None:  # pragma: no cover
            raise ImportError(
                "FlagEmbedding is not installed. "
                "Run: uv sync --extra agents"
            )
        self._reranker = FlagReranker(model_name, use_fp16=use_fp16)
        self.top_k = top_k

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        """Rerank *chunks* by relevance to *query*.

        Parameters
        ----------
        query:
            The search query / question text.
        chunks:
            List of chunk dicts with at least a ``"text"`` key.

        Returns
        -------
        list[dict]
            Top-K chunks (at most ``self.top_k``) sorted by descending
            ``rerank_score``.  Each dict has all original fields plus a new
            ``rerank_score`` (float) key.
        """
        if not chunks:
            return []

        sentence_pairs = [[query, chunk["text"]] for chunk in chunks]
        scores: list[float] = self._reranker.compute_score(sentence_pairs)

        # Attach rerank scores and sort descending.
        scored: list[dict] = []
        for chunk, score in zip(chunks, scores):
            entry = dict(chunk)
            entry["rerank_score"] = float(score)
            scored.append(entry)

        scored.sort(key=lambda c: c["rerank_score"], reverse=True)
        return scored[: self.top_k]
