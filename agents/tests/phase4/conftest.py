"""Shared fixtures for Phase 4 test suite."""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_matter_id() -> str:
    return "matter-uuid-001"


@pytest.fixture
def sample_user_id() -> str:
    return "user-uuid-001"


@pytest.fixture
def sample_query() -> str:
    return "What are the key facts in this breach of contract matter?"


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Sample retrieval chunks with metadata."""
    return [
        {
            "id": "doc-001_0",
            "text": "The plaintiff alleges breach of contract dated January 1, 2024.",
            "score": 0.92,
            "metadata": {
                "document_id": "doc-001",
                "matter_id": "matter-uuid-001",
                "chunk_index": 0,
                "file_name": "brief.pdf",
                "page_number": 1,
                "access_level": "full",
            },
        },
        {
            "id": "doc-001_1",
            "text": "The defendant denies all allegations and counterclaims damages.",
            "score": 0.85,
            "metadata": {
                "document_id": "doc-001",
                "matter_id": "matter-uuid-001",
                "chunk_index": 1,
                "file_name": "brief.pdf",
                "page_number": 2,
                "access_level": "full",
            },
        },
        {
            "id": "doc-002_0",
            "text": "Discovery is scheduled for March 15, 2024.",
            "score": 0.78,
            "metadata": {
                "document_id": "doc-002",
                "matter_id": "matter-uuid-001",
                "chunk_index": 0,
                "file_name": "schedule.pdf",
                "page_number": 1,
                "access_level": "full",
            },
        },
    ]


@pytest.fixture
def sample_jwt_payload() -> dict:
    return {
        "sub": "user-uuid-001",
        "email": "attorney@firm.com",
        "role": "attorney",
        "matter_ids": ["matter-uuid-001", "matter-uuid-002"],
        "exp": 9999999999,
    }
