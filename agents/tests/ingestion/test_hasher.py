"""Unit tests for the SHA-256 file hasher (task 3.1).

RED: These tests fail until app/rag/hasher.py is implemented.
"""



from app.rag.hasher import hash_file


class TestHashFile:
    def test_returns_hex_string(self, sample_text_file):
        result = hash_file(sample_text_file)
        assert isinstance(result, str)
        # SHA-256 hex digest is always 64 characters
        assert len(result) == 64

    def test_hex_characters_only(self, sample_text_file):
        result = hash_file(sample_text_file)
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_file_same_hash(self, sample_text_file):
        hash1 = hash_file(sample_text_file)
        hash2 = hash_file(sample_text_file)
        assert hash1 == hash2

    def test_different_files_different_hash(self, sample_text_file, another_text_file):
        hash1 = hash_file(sample_text_file)
        hash2 = hash_file(another_text_file)
        assert hash1 != hash2

    def test_modified_file_changes_hash(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("original content")
        original_hash = hash_file(str(f))

        f.write_text("modified content")
        modified_hash = hash_file(str(f))

        assert original_hash != modified_hash

    def test_accepts_path_object(self, tmp_path):

        f = tmp_path / "doc.txt"
        f.write_text("test")
        # Should accept both str and Path
        assert hash_file(f) == hash_file(str(f))

    def test_empty_file_has_known_hash(self, tmp_path):
        """Empty file has a deterministic SHA-256 hash."""
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        result = hash_file(str(f))
        # SHA-256 of empty input
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
