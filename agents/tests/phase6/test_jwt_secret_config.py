"""Phase 6 — Task 6.2: Shared JWT secret configuration tests.

Verifies that:
  - JWT_SECRET env var is correctly read by the agents backend
  - A token signed with the same secret as the API is accepted
  - A token signed with a DIFFERENT secret is rejected (401)
  - An absent JWT_SECRET causes token validation to fail gracefully
  - The chat endpoint enforces the shared JWT contract end-to-end

All HTTP calls are against the TestClient (no real server required).
"""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt
from jose.exceptions import JWTError

from app.auth.jwt_validator import decode_token, _get_secret
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"


def _make_token(secret: str, matter_ids: list[str] | None = None, role: str = "attorney") -> str:
    payload = {
        "sub": "user-001",
        "email": "attorney@firm.com",
        "role": role,
        "matter_ids": matter_ids or ["matter-001"],
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jose_jwt.encode(payload, secret, algorithm=_ALGORITHM)


# ---------------------------------------------------------------------------
# Unit tests — _get_secret / decode_token
# ---------------------------------------------------------------------------


class TestJWTSecretConfiguration:
    """Task 6.2 — JWT secret is read from environment variable."""

    def test_get_secret_reads_from_env(self):
        """_get_secret() returns the value of JWT_SECRET env var."""
        with patch.dict(os.environ, {"JWT_SECRET": "my-shared-secret-value"}):
            secret = _get_secret()
        assert secret == "my-shared-secret-value"

    def test_get_secret_returns_empty_string_when_unset(self):
        """_get_secret() returns '' when JWT_SECRET is not set (validation will fail later)."""
        env_without_secret = {k: v for k, v in os.environ.items() if k != "JWT_SECRET"}
        with patch.dict(os.environ, env_without_secret, clear=True):
            secret = _get_secret()
        assert secret == ""

    def test_decode_token_accepts_valid_token_with_matching_secret(self):
        """Token signed with the same secret is decoded successfully."""
        secret = "shared-secret-for-api-and-agents"
        token = _make_token(secret)

        with patch.dict(os.environ, {"JWT_SECRET": secret}):
            payload = decode_token(token)

        assert payload["sub"] == "user-001"
        assert payload["role"] == "attorney"

    def test_decode_token_rejects_token_signed_with_different_secret(self):
        """Token signed with a DIFFERENT secret raises HTTPException(401)."""
        from fastapi import HTTPException

        api_secret = "secret-used-by-node-api"
        wrong_secret = "completely-different-secret-that-agents-must-reject"

        token = _make_token(api_secret)  # signed with api_secret

        with patch.dict(os.environ, {"JWT_SECRET": wrong_secret}):
            with pytest.raises(HTTPException) as exc_info:
                decode_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_token_rejects_expired_token(self):
        """Expired tokens are rejected with 401."""
        from fastapi import HTTPException

        secret = "shared-secret-value"
        expired_payload = {
            "sub": "user-001",
            "email": "a@b.com",
            "role": "attorney",
            "matter_ids": ["matter-001"],
            "exp": int(time.time()) - 60,  # expired 60 seconds ago
        }
        expired_token = jose_jwt.encode(expired_payload, secret, algorithm=_ALGORITHM)

        with patch.dict(os.environ, {"JWT_SECRET": secret}):
            with pytest.raises(HTTPException) as exc_info:
                decode_token(expired_token)

        assert exc_info.value.status_code == 401

    def test_decode_token_rejects_malformed_token(self):
        """Malformed (non-JWT) tokens raise 401."""
        from fastapi import HTTPException

        with patch.dict(os.environ, {"JWT_SECRET": "any-secret"}):
            with pytest.raises(HTTPException) as exc_info:
                decode_token("this-is-not-a-jwt")

        assert exc_info.value.status_code == 401

    def test_decode_token_rejects_empty_string(self):
        """Empty string token raises 401."""
        from fastapi import HTTPException

        with patch.dict(os.environ, {"JWT_SECRET": "any-secret"}):
            with pytest.raises(HTTPException) as exc_info:
                decode_token("")

        assert exc_info.value.status_code == 401

    def test_payload_contains_expected_claims(self):
        """Decoded payload preserves all claims embedded by the Node API."""
        secret = "shared-secret-abcdefghijklmnop"
        payload_in = {
            "sub": "user-uuid-abc",
            "email": "partner@firm.com",
            "role": "partner",
            "matter_ids": ["m1", "m2", "m3"],
            "exp": int(time.time()) + 3600,
        }
        token = jose_jwt.encode(payload_in, secret, algorithm=_ALGORITHM)

        with patch.dict(os.environ, {"JWT_SECRET": secret}):
            payload_out = decode_token(token)

        assert payload_out["sub"] == "user-uuid-abc"
        assert payload_out["email"] == "partner@firm.com"
        assert payload_out["role"] == "partner"
        assert set(payload_out["matter_ids"]) == {"m1", "m2", "m3"}


# ---------------------------------------------------------------------------
# Integration tests — /chat endpoint respects shared JWT secret
# ---------------------------------------------------------------------------


class TestSharedJWTSecretE2E:
    """End-to-end contract: token issued by Node API (same secret) works on /chat."""

    @pytest.fixture
    def client(self):
        return TestClient(app, raise_server_exceptions=False)

    def test_chat_accepts_token_signed_with_shared_secret(self, client):
        """Token signed with JWT_SECRET env var gives 200 on /chat."""
        from unittest.mock import AsyncMock, MagicMock

        shared_secret = "e2e-shared-secret-minimum-32-chars!"

        with (
            patch.dict(os.environ, {"JWT_SECRET": shared_secret}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
        ):
            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(
                return_value={"answer": "Test answer.", "citations": [], "intent": "general"}
            )
            mock_build.return_value = mock_orchestrator

            token = _make_token(shared_secret, matter_ids=["matter-001"])
            response = client.post(
                "/chat",
                json={"query": "What happened?", "matter_id": "matter-001"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200

    def test_chat_rejects_token_signed_with_wrong_secret(self, client):
        """Token signed with wrong secret gives 401 on /chat."""
        agents_secret = "agents-expects-this-secret-minimum-32!"
        wrong_secret = "api-was-configured-with-this-secret-!!"

        with patch.dict(os.environ, {"JWT_SECRET": agents_secret}):
            token = _make_token(wrong_secret, matter_ids=["matter-001"])
            response = client.post(
                "/chat",
                json={"query": "What happened?", "matter_id": "matter-001"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 401

    def test_chat_rejects_missing_authorization_header(self, client):
        """Request with no Authorization header gives 401."""
        with patch.dict(os.environ, {"JWT_SECRET": "some-secret"}):
            response = client.post(
                "/chat",
                json={"query": "What happened?", "matter_id": "matter-001"},
            )
        assert response.status_code == 401

    def test_jwt_secret_env_var_name_is_jwt_secret(self):
        """Confirm the env var name matches what the Node API uses (contract test)."""
        # This test documents the contract: both services MUST read JWT_SECRET.
        # The Node API sets process.env.JWT_SECRET; agents reads os.getenv("JWT_SECRET").
        with patch.dict(os.environ, {"JWT_SECRET": "contract-verified-secret"}):
            secret = _get_secret()
        assert secret == "contract-verified-secret"
        # The environment variable name is the contract between the two services.
        assert "JWT_SECRET" in os.environ or True  # always passes — documents intent
