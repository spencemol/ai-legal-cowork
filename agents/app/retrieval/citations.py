"""Citation formatter — convert reranked chunks into citation objects (task 4.7).

Produces a list of citation dicts matching the ``messages.citations`` JSONB
schema used by the Postgres ``messages`` table.

Schema per citation::

    {
        "doc_id":       str,   # document UUID
        "chunk_id":     str,   # "{doc_id}_{chunk_index}"
        "text_snippet": str,   # truncated chunk text for display
        "page":         int | None,
        "file_name":    str,
    }
"""

from __future__ import annotations

_DEFAULT_SNIPPET_MAX_LEN = 200


class CitationFormatter:
    """Convert reranked retrieval chunks to citation objects.

    Parameters
    ----------
    snippet_max_len:
        Maximum character length of ``text_snippet``.  If the chunk text
        exceeds this length, it is truncated with an ellipsis (``"..."``).
    """

    def __init__(self, snippet_max_len: int = _DEFAULT_SNIPPET_MAX_LEN) -> None:
        self.snippet_max_len = snippet_max_len

    def format(self, chunks: list[dict]) -> list[dict]:  # noqa: A003
        """Convert *chunks* to citation dicts.

        Parameters
        ----------
        chunks:
            List of chunk dicts as returned by the retriever / reranker.
            Each must have: ``id``, ``text``, ``metadata``.

        Returns
        -------
        list[dict]
            One citation dict per input chunk, in the same order.
        """
        citations: list[dict] = []
        for chunk in chunks:
            meta = chunk.get("metadata") or {}
            text = chunk.get("text", "")
            snippet = self._truncate(text)

            citation: dict = {
                "doc_id": meta.get("document_id", ""),
                "chunk_id": chunk.get("id", ""),
                "text_snippet": snippet,
                "page": meta.get("page_number"),  # None if not present
                "file_name": meta.get("file_name", ""),
            }
            citations.append(citation)

        return citations

    def _truncate(self, text: str) -> str:
        """Truncate *text* to ``snippet_max_len`` chars, appending ``"..."``."""
        if len(text) <= self.snippet_max_len:
            return text
        return text[: self.snippet_max_len] + "..."
