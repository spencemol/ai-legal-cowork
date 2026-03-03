"""Shared fixtures for Phase 6 E2E / integration tests.

All external services are fully mocked — no real Pinecone, Postgres, MongoDB,
or Anthropic API calls are made.  Tests are self-contained and can run in CI
without any running Docker services.
"""

from __future__ import annotations

import time

import pytest
from jose import jwt as jose_jwt


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

TEST_SECRET = "test-phase6-jwt-secret-minimum-32-chars"
ALGORITHM = "HS256"


def make_jwt(
    user_id: str = "user-p6-001",
    email: str = "attorney@firm.com",
    role: str = "attorney",
    matter_ids: list[str] | None = None,
    secret: str = TEST_SECRET,
    expires_in: int = 3600,
) -> str:
    """Create a signed HS256 JWT for test use."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "matter_ids": matter_ids if matter_ids is not None else ["matter-a"],
        "exp": int(time.time()) + expires_in,
        "iat": int(time.time()),
    }
    return jose_jwt.encode(payload, secret, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def jwt_secret() -> str:
    return TEST_SECRET


@pytest.fixture
def attorney_token(jwt_secret: str) -> str:
    return make_jwt(
        user_id="user-attorney-001",
        role="attorney",
        matter_ids=["matter-a", "matter-b"],
        secret=jwt_secret,
    )


@pytest.fixture
def paralegal_token(jwt_secret: str) -> str:
    return make_jwt(
        user_id="user-paralegal-001",
        role="paralegal",
        matter_ids=["matter-a"],
        secret=jwt_secret,
    )


@pytest.fixture
def viewer_token(jwt_secret: str) -> str:
    return make_jwt(
        user_id="user-viewer-001",
        role="viewer",
        matter_ids=["matter-a"],
        secret=jwt_secret,
    )


@pytest.fixture
def matter_a_id() -> str:
    return "matter-a"


@pytest.fixture
def matter_b_id() -> str:
    return "matter-b"


@pytest.fixture
def sample_chunks_matter_a() -> list[dict]:
    """Chunks that belong exclusively to matter-a."""
    return [
        {
            "id": "doc-a1_0",
            "text": "John Smith signed the contract on 2024-01-15.",
            "score": 0.93,
            "metadata": {
                "document_id": "doc-a1",
                "matter_id": "matter-a",
                "chunk_index": 0,
                "file_name": "contract-a.pdf",
                "page_number": 1,
                "access_level": "full",
                "chunk_text": "John Smith signed the contract on 2024-01-15.",
            },
        },
        {
            "id": "doc-a1_1",
            "text": "The SSN of the plaintiff is 123-45-6789.",
            "score": 0.88,
            "metadata": {
                "document_id": "doc-a1",
                "matter_id": "matter-a",
                "chunk_index": 1,
                "file_name": "contract-a.pdf",
                "page_number": 2,
                "access_level": "full",
                "chunk_text": "The SSN of the plaintiff is 123-45-6789.",
            },
        },
    ]


@pytest.fixture
def sample_chunks_matter_b() -> list[dict]:
    """Chunks that belong exclusively to matter-b."""
    return [
        {
            "id": "doc-b1_0",
            "text": "Confidential matter-b document content.",
            "score": 0.90,
            "metadata": {
                "document_id": "doc-b1",
                "matter_id": "matter-b",
                "chunk_index": 0,
                "file_name": "matter-b-brief.pdf",
                "page_number": 1,
                "access_level": "full",
                "chunk_text": "Confidential matter-b document content.",
            },
        },
    ]
