"""Phase 6 — Task 6.7: PII redaction/re-hydration in the chat flow.

Verifies that:
  - PII in the user query is redacted BEFORE it reaches the LLM
  - The LLM answer with placeholders is re-hydrated based on access level
  - full-access users (attorney/admin) see PII restored in the response
  - read_only users see PII as placeholders in the response
  - LangSmith-visible text (what goes to the LLM) never contains raw PII

All external services are mocked — no real Presidio, Pinecone, or Anthropic API calls.
"""

from __future__ import annotations

import os
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt as jose_jwt

from app.pii.redactor import PIIRedactor, PIIRehydrator, _entity_type_from_placeholder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"
_SECRET = "pii-chat-test-secret-minimum-32chars!!"


def _make_jwt(role: str = "attorney", matter_ids: list[str] | None = None) -> str:
    payload = {
        "sub": "user-001",
        "email": "attorney@firm.com",
        "role": role,
        "matter_ids": matter_ids if matter_ids is not None else ["matter-001"],
        "exp": int(time.time()) + 3600,
    }
    return jose_jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _make_mock_redactor(
    redacted_text: str,
    mapping: dict[str, str],
) -> MagicMock:
    """Create a PIIRedactor mock that returns preset results."""
    mock_redactor = MagicMock(spec=PIIRedactor)
    result = MagicMock()
    result.redacted_text = redacted_text
    result.mapping = mapping
    mock_redactor.redact.return_value = result
    return mock_redactor


# ---------------------------------------------------------------------------
# Unit tests — PIIRedactor
# ---------------------------------------------------------------------------


class TestPIIRedactorBeforeLLM:
    """Verify PII is stripped before LLM sees the text."""

    def test_redactor_returns_redaction_result_with_mapping(self):
        """PIIRedactor.redact() returns RedactionResult with mapping dict."""
        # Use a custom analyzer that detects our test patterns
        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()

        # Simulate no PII detected (avoids spaCy dependency in CI)
        mock_analyzer.analyze.return_value = []
        mock_anonymizer.anonymize.return_value = MagicMock(text="Hello world")

        redactor = PIIRedactor(analyzer=mock_analyzer, anonymizer=mock_anonymizer)
        result = redactor.redact("Hello world")

        assert result.redacted_text == "Hello world"
        assert isinstance(result.mapping, dict)

    def test_redactor_replaces_person_with_placeholder(self):
        """When Presidio detects PERSON, text is replaced with [PERSON_1]."""
        from presidio_analyzer import RecognizerResult  # type: ignore[import]

        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()

        # Simulate detecting "John Smith" as PERSON entity
        mock_result = MagicMock(spec=RecognizerResult)
        mock_result.entity_type = "PERSON"
        mock_result.start = 0
        mock_result.end = 10
        mock_analyzer.analyze.return_value = [mock_result]

        mock_anon_result = MagicMock()
        mock_anon_result.text = "[PERSON_1] signed the contract."
        mock_anonymizer.anonymize.return_value = mock_anon_result

        redactor = PIIRedactor(analyzer=mock_analyzer, anonymizer=mock_anonymizer)
        result = redactor.redact("John Smith signed the contract.")

        assert "[PERSON_1]" in result.redacted_text
        assert "John Smith" not in result.redacted_text

    def test_redactor_mapping_keys_are_placeholders(self):
        """Mapping keys are in [ENTITY_N] format."""
        from presidio_analyzer import RecognizerResult  # type: ignore[import]

        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()

        entity_result = MagicMock(spec=RecognizerResult)
        entity_result.entity_type = "PERSON"
        entity_result.start = 0
        entity_result.end = 10
        mock_analyzer.analyze.return_value = [entity_result]

        mock_anon = MagicMock()
        mock_anon.text = "[PERSON_1] was here."
        mock_anonymizer.anonymize.return_value = mock_anon

        redactor = PIIRedactor(analyzer=mock_analyzer, anonymizer=mock_anonymizer)
        result = redactor.redact("John Smith was here.")

        for key in result.mapping:
            assert key.startswith("[")
            assert key.endswith("]")
            assert "_" in key

    def test_redactor_is_graceful_when_engines_unavailable(self):
        """If Presidio engines fail, original text is returned unchanged."""
        failing_analyzer = MagicMock()
        failing_analyzer.analyze.side_effect = RuntimeError("Model not loaded")

        redactor = PIIRedactor(analyzer=failing_analyzer)
        result = redactor.redact("John Smith")

        # Falls back to original text — no crash
        assert "John Smith" in result.redacted_text

    def test_redactor_empty_text_returns_empty(self):
        """Empty input produces empty output with empty mapping."""
        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()
        mock_analyzer.analyze.return_value = []

        redactor = PIIRedactor(analyzer=mock_analyzer, anonymizer=mock_anonymizer)
        result = redactor.redact("")

        assert result.redacted_text == ""
        assert result.mapping == {}


# ---------------------------------------------------------------------------
# Unit tests — PIIRehydrator
# ---------------------------------------------------------------------------


class TestPIIRehydratorAccessLevels:
    """Verify PII is restored or suppressed based on access level."""

    @pytest.fixture
    def rehydrator(self):
        return PIIRehydrator()

    @pytest.fixture
    def pii_mapping(self):
        return {
            "[PERSON_1]": "John Smith",
            "[US_SSN_1]": "123-45-6789",
            "[EMAIL_ADDRESS_1]": "john@example.com",
        }

    @pytest.fixture
    def redacted_answer(self):
        return (
            "[PERSON_1] filed a claim. "
            "The SSN on file is [US_SSN_1]. "
            "Contact via [EMAIL_ADDRESS_1]."
        )

    def test_full_access_restores_all_pii(self, rehydrator, pii_mapping, redacted_answer):
        """full access level → all PII placeholders replaced with original values."""
        result = rehydrator.rehydrate(redacted_answer, pii_mapping, access_level="full")

        assert "John Smith" in result
        assert "123-45-6789" in result
        assert "john@example.com" in result
        assert "[PERSON_1]" not in result
        assert "[US_SSN_1]" not in result
        assert "[EMAIL_ADDRESS_1]" not in result

    def test_read_only_keeps_all_placeholders(self, rehydrator, pii_mapping, redacted_answer):
        """read_only access level → all placeholders remain (no PII exposed)."""
        result = rehydrator.rehydrate(redacted_answer, pii_mapping, access_level="read_only")

        assert "[PERSON_1]" in result
        assert "[US_SSN_1]" in result
        assert "[EMAIL_ADDRESS_1]" in result
        assert "John Smith" not in result
        assert "123-45-6789" not in result
        assert "john@example.com" not in result

    def test_restricted_restores_person_but_keeps_ssn(self, rehydrator, pii_mapping, redacted_answer):
        """restricted access level → PERSON names restored, SSN kept redacted."""
        result = rehydrator.rehydrate(redacted_answer, pii_mapping, access_level="restricted")

        # PERSON should be restored
        assert "John Smith" in result
        # SSN is a sensitive entity — must stay redacted
        assert "[US_SSN_1]" in result
        assert "123-45-6789" not in result

    def test_unknown_access_level_treated_as_read_only(self, rehydrator, pii_mapping, redacted_answer):
        """Unknown access level is treated as read_only (most restrictive)."""
        result = rehydrator.rehydrate(redacted_answer, pii_mapping, access_level="unknown_level")

        assert "[PERSON_1]" in result
        assert "[US_SSN_1]" in result

    def test_empty_mapping_returns_text_unchanged(self, rehydrator, redacted_answer):
        """Empty mapping → text returned as-is for any access level."""
        result = rehydrator.rehydrate(redacted_answer, {}, access_level="full")
        assert result == redacted_answer

    def test_entity_type_extraction_from_placeholder(self):
        """_entity_type_from_placeholder correctly extracts entity type."""
        assert _entity_type_from_placeholder("[PERSON_1]") == "PERSON"
        assert _entity_type_from_placeholder("[US_SSN_1]") == "US_SSN"
        assert _entity_type_from_placeholder("[EMAIL_ADDRESS_1]") == "EMAIL_ADDRESS"
        assert _entity_type_from_placeholder("[CREDIT_CARD_2]") == "CREDIT_CARD"


# ---------------------------------------------------------------------------
# Integration tests — /chat endpoint PII flow
# ---------------------------------------------------------------------------


class TestPIIChatEndpointFlow:
    """Task 6.7 — Chat endpoint PII redaction/re-hydration contract."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_full_access_user_sees_pii_in_response(self, client):
        """Attorney (full access) gets PII re-hydrated in their chat response."""
        # Mock the redactor to return known mapping
        mock_mapping = {"[PERSON_1]": "Jane Doe"}
        mock_redaction_result = MagicMock()
        mock_redaction_result.redacted_text = "What did [PERSON_1] sign?"
        mock_redaction_result.mapping = mock_mapping

        mock_orchestrator_result = {
            "answer": "[PERSON_1] signed the contract.",
            "citations": [],
            "intent": "retrieval",
        }

        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
            patch("app.routes.chat.PIIRedactor") as MockRedactor,
        ):
            mock_redactor_instance = MagicMock()
            mock_redactor_instance.redact.return_value = mock_redaction_result
            MockRedactor.return_value = mock_redactor_instance

            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(return_value=mock_orchestrator_result)
            mock_build.return_value = mock_orchestrator

            token = _make_jwt(role="attorney", matter_ids=["matter-001"])
            response = client.post(
                "/chat",
                json={"query": "What did Jane Doe sign?", "matter_id": "matter-001"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        # Full access → "Jane Doe" is re-hydrated; tokens are split word-by-word in SSE
        # so check that both parts appear in the response body
        assert "Jane" in response.text
        assert "Doe" in response.text

    def test_read_only_user_sees_placeholder_not_pii(self, client):
        """Viewer (read_only) sees [PERSON_1] placeholder instead of real name."""
        mock_mapping = {"[PERSON_1]": "Jane Doe"}
        mock_redaction_result = MagicMock()
        mock_redaction_result.redacted_text = "What did [PERSON_1] sign?"
        mock_redaction_result.mapping = mock_mapping

        mock_orchestrator_result = {
            "answer": "[PERSON_1] signed the contract.",
            "citations": [],
            "intent": "retrieval",
        }

        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
            patch("app.routes.chat.PIIRedactor") as MockRedactor,
        ):
            mock_redactor_instance = MagicMock()
            mock_redactor_instance.redact.return_value = mock_redaction_result
            MockRedactor.return_value = mock_redactor_instance

            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(return_value=mock_orchestrator_result)
            mock_build.return_value = mock_orchestrator

            # Viewer role → read_only access level
            token = _make_jwt(role="viewer", matter_ids=["matter-001"])
            response = client.post(
                "/chat",
                json={"query": "What did Jane Doe sign?", "matter_id": "matter-001"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert response.status_code == 200
        # read_only → placeholder stays, real name must NOT appear
        assert "[PERSON_1]" in response.text
        assert "Jane Doe" not in response.text

    def test_query_is_redacted_before_reaching_orchestrator(self, client):
        """The orchestrator receives the redacted query, not the raw query."""
        raw_query = "What did Jane Doe sign?"
        redacted_query = "What did [PERSON_1] sign?"

        mock_redaction_result = MagicMock()
        mock_redaction_result.redacted_text = redacted_query
        mock_redaction_result.mapping = {"[PERSON_1]": "Jane Doe"}

        orchestrator_received_query = []

        async def capture_run(query: str, **kwargs):
            orchestrator_received_query.append(query)
            return {"answer": "The answer.", "citations": [], "intent": "general"}

        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
            patch("app.routes.chat.PIIRedactor") as MockRedactor,
        ):
            mock_redactor_instance = MagicMock()
            mock_redactor_instance.redact.return_value = mock_redaction_result
            MockRedactor.return_value = mock_redactor_instance

            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(side_effect=capture_run)
            mock_build.return_value = mock_orchestrator

            token = _make_jwt(role="attorney", matter_ids=["matter-001"])
            client.post(
                "/chat",
                json={"query": raw_query, "matter_id": "matter-001"},
                headers={"Authorization": f"Bearer {token}"},
            )

        # The orchestrator must have received the redacted version, not the raw
        assert len(orchestrator_received_query) == 1
        assert orchestrator_received_query[0] == redacted_query
        assert "Jane Doe" not in orchestrator_received_query[0]

    def test_pii_redaction_called_exactly_once_per_request(self, client):
        """PIIRedactor.redact() is called exactly once per chat request."""
        mock_redaction_result = MagicMock()
        mock_redaction_result.redacted_text = "Hello world."
        mock_redaction_result.mapping = {}

        with (
            patch.dict(os.environ, {"JWT_SECRET": _SECRET}),
            patch("app.routes.chat._build_orchestrator") as mock_build,
            patch("app.routes.chat.PIIRedactor") as MockRedactor,
        ):
            mock_redactor_instance = MagicMock()
            mock_redactor_instance.redact.return_value = mock_redaction_result
            MockRedactor.return_value = mock_redactor_instance

            mock_orchestrator = MagicMock()
            mock_orchestrator.run = AsyncMock(
                return_value={"answer": "OK.", "citations": [], "intent": "general"}
            )
            mock_build.return_value = mock_orchestrator

            token = _make_jwt(role="attorney", matter_ids=["matter-001"])
            client.post(
                "/chat",
                json={"query": "Tell me about the case.", "matter_id": "matter-001"},
                headers={"Authorization": f"Bearer {token}"},
            )

        mock_redactor_instance.redact.assert_called_once()
