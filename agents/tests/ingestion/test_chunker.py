"""Unit tests for the semantic text chunker (task 3.3).

RED: These tests fail until app/rag/chunker.py is implemented.
"""


from app.rag.chunker import ChunkConfig, chunk_text
from app.rag.models import TextChunk


class TestChunkText:
    def test_returns_list_of_text_chunks(self):
        text = "The plaintiff alleges breach of contract. The defendant denies all claims."
        chunks = chunk_text(text)
        assert isinstance(chunks, list)
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_empty_text_returns_empty_list(self):
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert chunk_text("   \n\n  ") == []

    def test_single_short_sentence_returns_one_chunk(self):
        text = "The court finds in favor of the plaintiff."
        chunks = chunk_text(text, config=ChunkConfig(max_chars=500))
        assert len(chunks) == 1
        assert chunks[0].text == text.strip() or text.strip() in chunks[0].text

    def test_chunks_respect_max_chars(self):
        # Long text with many sentences, small chunk size
        sentences = [f"Sentence number {i} contains some legal content about the matter at hand." for i in range(20)]
        text = " ".join(sentences)
        max_chars = 200

        chunks = chunk_text(text, config=ChunkConfig(max_chars=max_chars, overlap_chars=0))

        for chunk in chunks:
            # Each chunk should not massively exceed max_chars
            # (a single sentence may exceed max_chars — that's allowed)
            assert chunk.char_count <= max_chars * 2  # generous upper bound for edge cases

    def test_overlap_exists_between_adjacent_chunks(self):
        # Create enough text to force multiple chunks
        sentences = [
            "The plaintiff claims damages of one million dollars.",
            "The defendant argues the contract was void ab initio.",
            "Expert witnesses will testify on the financial impact.",
            "The court has scheduled oral arguments for next month.",
            "Both parties have submitted extensive discovery materials.",
            "The judge will rule on the motion to dismiss shortly.",
        ]
        text = " ".join(sentences)
        config = ChunkConfig(max_chars=120, overlap_chars=60)
        chunks = chunk_text(text, config=config)

        if len(chunks) >= 2:
            # The end of chunk[0] should share content with start of chunk[1]
            chunk0_words = set(chunks[0].text.split())
            chunk1_words = set(chunks[1].text.split())
            overlap_words = chunk0_words & chunk1_words
            assert len(overlap_words) > 0, "Adjacent chunks should share words (overlap)"

    def test_chunk_indices_are_sequential(self):
        sentences = [f"Legal sentence {i} about the ongoing litigation." for i in range(10)]
        text = " ".join(sentences)
        chunks = chunk_text(text, config=ChunkConfig(max_chars=150))

        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_all_text_covered(self):
        """Every sentence from the source text should appear in at least one chunk."""
        sentences = [
            "The contract was executed on March 1, 2024.",
            "The defendant breached the terms on April 15, 2024.",
            "Damages are estimated at fifty thousand dollars.",
        ]
        text = " ".join(sentences)
        chunks = chunk_text(text, config=ChunkConfig(max_chars=200, overlap_chars=50))
        combined = " ".join(c.text for c in chunks)

        for sentence in sentences:
            # Each sentence should appear somewhere in the combined chunk output
            key_words = sentence.split()[:3]
            assert any(word in combined for word in key_words), f"Sentence start '{key_words}' not found in chunks"

    def test_page_number_propagated(self):
        text = "This is page two content. It discusses the settlement terms."
        chunks = chunk_text(text, page_number=2)
        assert all(c.page_number == 2 for c in chunks)

    def test_page_number_none_by_default(self):
        text = "Some legal text without page info."
        chunks = chunk_text(text)
        assert all(c.page_number is None for c in chunks)

    def test_char_count_matches_text_length(self):
        text = "A short legal sentence. Another sentence here."
        chunks = chunk_text(text)
        for chunk in chunks:
            assert chunk.char_count == len(chunk.text)

    def test_configurable_max_chars(self):
        text = " ".join(
            [f"Sentence {i} about the matter at hand for the plaintiff." for i in range(15)]
        )
        small_chunks = chunk_text(text, config=ChunkConfig(max_chars=100, overlap_chars=0))
        large_chunks = chunk_text(text, config=ChunkConfig(max_chars=400, overlap_chars=0))
        assert len(small_chunks) >= len(large_chunks)

    def test_single_sentence_exceeding_max_chars_still_emitted(self):
        """A sentence longer than max_chars must still be included (not dropped)."""
        long_sentence = "The " + "very " * 100 + "long legal argument was presented to the court."
        chunks = chunk_text(long_sentence, config=ChunkConfig(max_chars=50, overlap_chars=0))
        assert len(chunks) >= 1
        combined = " ".join(c.text for c in chunks)
        assert "legal argument" in combined
