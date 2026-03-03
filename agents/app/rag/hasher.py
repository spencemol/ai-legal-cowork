"""SHA-256 file hasher for ingestion deduplication (task 3.1)."""

import hashlib
from pathlib import Path


def hash_file(file_path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file.

    Reads in 64 KiB chunks so large documents don't consume excess memory.
    Accepts both ``str`` and :class:`pathlib.Path` arguments.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
