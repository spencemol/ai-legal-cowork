"""Sentence-boundary-aware text chunker with configurable size and overlap (task 3.3)."""

import re
from dataclasses import dataclass

from app.rag.models import TextChunk


@dataclass
class ChunkConfig:
    """Configuration for the text chunker.

    Parameters
    ----------
    max_chars:
        Maximum characters per chunk (~4 chars ≈ 1 token, so the default
        2048 chars ≈ 512 tokens).
    overlap_chars:
        Approximate characters of overlap between adjacent chunks.
        The algorithm includes enough trailing sentences from the previous
        chunk to cover at least ``overlap_chars`` characters.
    """

    max_chars: int = 2048
    overlap_chars: int = 256


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on terminal punctuation followed by whitespace."""
    parts = _SENTENCE_SPLIT.split(text.strip())
    return [s.strip() for s in parts if s.strip()]


def chunk_text(
    text: str,
    config: ChunkConfig | None = None,
    page_number: int | None = None,
) -> list[TextChunk]:
    """Split *text* into overlapping :class:`~app.rag.models.TextChunk` objects.

    Algorithm
    ---------
    1. Split into sentences at terminal-punctuation boundaries.
    2. Greedily accumulate sentences into a chunk until ``max_chars`` would
       be exceeded.
    3. A single sentence that by itself exceeds ``max_chars`` is emitted as
       its own chunk (never dropped).
    4. For the next chunk, back up enough trailing sentences to achieve
       approximately ``overlap_chars`` of shared context.
    """
    if config is None:
        config = ChunkConfig()

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[TextChunk] = []
    chunk_start = 0  # index into *sentences* where the current chunk begins

    while chunk_start < len(sentences):
        group: list[str] = []
        group_len = 0
        idx = chunk_start

        # Accumulate sentences until max_chars would be exceeded
        while idx < len(sentences):
            sep = 1 if group else 0  # space between sentences
            candidate_len = group_len + sep + len(sentences[idx])
            if candidate_len > config.max_chars and group:
                break
            group.append(sentences[idx])
            group_len = group_len + sep + len(sentences[idx])
            idx += 1

        # Pathological: single sentence bigger than max_chars — emit anyway
        if not group:
            group = [sentences[chunk_start]]
            idx = chunk_start + 1

        chunk_str = " ".join(group)
        chunks.append(
            TextChunk(
                text=chunk_str,
                chunk_index=len(chunks),
                page_number=page_number,
                char_count=len(chunk_str),
            )
        )

        if idx >= len(sentences):
            break

        # Calculate next chunk_start so that the last portion of *group*
        # (approximately overlap_chars worth) is repeated at the beginning
        # of the next chunk.
        if config.overlap_chars > 0 and len(group) > 1:
            overlap_accumulated = 0
            new_start = idx - 1  # start from the sentence just before idx
            while new_start > chunk_start:
                overlap_accumulated += len(sentences[new_start]) + 1
                if overlap_accumulated >= config.overlap_chars:
                    break
                new_start -= 1
            # Always advance by at least 1 sentence to prevent infinite loops
            # when overlap cannot retreat past chunk_start.
            chunk_start = max(chunk_start + 1, new_start)
        else:
            chunk_start = idx

    return chunks
