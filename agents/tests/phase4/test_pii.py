"""Unit tests for PII redaction and re-hydration (tasks 4.3, 4.4).

Task 4.3: Presidio PII redactor — detect and replace PII with placeholders
Task 4.4: PII re-hydrator — selectively restore based on access level

All Presidio calls are fully mocked — no real NLP models loaded.

RED: These tests fail until app/pii/redactor.py is implemented.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.pii.redactor import PIIRedactor, PIIRehydrator, RedactionResult


# ---------------------------------------------------------------------------
# Task 4.3 — PIIRedactor
# ---------------------------------------------------------------------------


class TestPIIRedactorInit:
    def test_instantiation(self):
        with (
            patch("app.pii.redactor.AnalyzerEngine"),
            patch("app.pii.redactor.AnonymizerEngine"),
        ):
            redactor = PIIRedactor()
            assert redactor is not None

    def test_has_empty_mapping_initially(self):
        with (
            patch("app.pii.redactor.AnalyzerEngine"),
            patch("app.pii.redactor.AnonymizerEngine"),
        ):
            redactor = PIIRedactor()
            assert redactor.mapping == {}


class TestPIIRedactorRedact:
    def _make_mock_redactor(self, mocker):
        """Build a PIIRedactor with fully mocked Presidio engines."""
        mock_analyzer = MagicMock()
        mock_anonymizer = MagicMock()

        mocker.patch("app.pii.redactor.AnalyzerEngine", return_value=mock_analyzer)
        mocker.patch("app.pii.redactor.AnonymizerEngine", return_value=mock_anonymizer)

        return PIIRedactor(), mock_analyzer, mock_anonymizer

    def test_redact_returns_redaction_result(self, mocker):
        redactor, mock_analyzer, mock_anonymizer = self._make_mock_redactor(mocker)

        # Simulate Presidio finding a PERSON entity
        mock_entity = MagicMock()
        mock_entity.entity_type = "PERSON"
        mock_entity.start = 4
        mock_entity.end = 14
        mock_entity.score = 0.95
        mock_analyzer.analyze.return_value = [mock_entity]

        mock_result = MagicMock()
        mock_result.text = "The [PERSON_1] filed the complaint."
        mock_anonymizer.anonymize.return_value = mock_result

        result = redactor.redact("The John Smith filed the complaint.")

        assert isinstance(result, RedactionResult)

    def test_redact_result_has_redacted_text(self, mocker):
        redactor, mock_analyzer, mock_anonymizer = self._make_mock_redactor(mocker)

        mock_entity = MagicMock()
        mock_entity.entity_type = "PERSON"
        mock_entity.start = 4
        mock_entity.end = 14
        mock_entity.score = 0.95
        mock_analyzer.analyze.return_value = [mock_entity]

        mock_result = MagicMock()
        mock_result.text = "The [PERSON_1] filed the complaint."
        mock_anonymizer.anonymize.return_value = mock_result

        result = redactor.redact("The John Smith filed the complaint.")
        assert "John Smith" not in result.redacted_text or result.redacted_text == "The [PERSON_1] filed the complaint."

    def test_redact_builds_mapping_table(self, mocker):
        redactor, mock_analyzer, mock_anonymizer = self._make_mock_redactor(mocker)

        mock_entity = MagicMock()
        mock_entity.entity_type = "PERSON"
        mock_entity.start = 4
        mock_entity.end = 14
        mock_entity.score = 0.95
        mock_analyzer.analyze.return_value = [mock_entity]

        mock_result = MagicMock()
        mock_result.text = "The [PERSON_1] filed the complaint."
        # items() used in redactor to extract mappings
        mock_result.items = MagicMock(return_value=[
            MagicMock(
                operator="replace",
                entity_type="PERSON",
                start=4,
                end=14,
                text="[PERSON_1]",
                new_value="John Smith",
            )
        ])
        mock_anonymizer.anonymize.return_value = mock_result

        result = redactor.redact("The John Smith filed the complaint.")
        # The mapping should be accessible via result.mapping
        assert isinstance(result.mapping, dict)

    def test_clean_text_no_pii_detected(self, mocker):
        redactor, mock_analyzer, mock_anonymizer = self._make_mock_redactor(mocker)

        mock_analyzer.analyze.return_value = []  # No PII found

        mock_result = MagicMock()
        mock_result.text = "The contract was signed on January 1."
        mock_result.items = MagicMock(return_value=[])
        mock_anonymizer.anonymize.return_value = mock_result

        result = redactor.redact("The contract was signed on January 1.")
        assert result.redacted_text == "The contract was signed on January 1."
        assert result.mapping == {}

    def test_placeholder_format_person(self, mocker):
        """Placeholder format must match [ENTITY_TYPE_N]."""
        redactor, mock_analyzer, mock_anonymizer = self._make_mock_redactor(mocker)

        mock_entity = MagicMock()
        mock_entity.entity_type = "PERSON"
        mock_entity.start = 0
        mock_entity.end = 8
        mock_entity.score = 0.99
        mock_analyzer.analyze.return_value = [mock_entity]

        mock_result = MagicMock()
        mock_result.text = "[PERSON_1] filed the lawsuit."
        mock_result.items = MagicMock(return_value=[])
        mock_anonymizer.anonymize.return_value = mock_result

        result = redactor.redact("Jane Doe filed the lawsuit.")
        assert "[PERSON_1]" in result.redacted_text

    def test_redact_multiple_entity_types(self, mocker):
        redactor, mock_analyzer, mock_anonymizer = self._make_mock_redactor(mocker)

        mock_person = MagicMock()
        mock_person.entity_type = "PERSON"
        mock_person.start = 0
        mock_person.end = 8
        mock_person.score = 0.99

        mock_ssn = MagicMock()
        mock_ssn.entity_type = "US_SSN"
        mock_ssn.start = 20
        mock_ssn.end = 31
        mock_ssn.score = 0.99

        mock_analyzer.analyze.return_value = [mock_person, mock_ssn]

        mock_result = MagicMock()
        mock_result.text = "[PERSON_1] SSN is [US_SSN_1]."
        mock_result.items = MagicMock(return_value=[])
        mock_anonymizer.anonymize.return_value = mock_result

        result = redactor.redact("John Doe SSN is 123-45-6789.")
        assert isinstance(result, RedactionResult)


# ---------------------------------------------------------------------------
# Task 4.4 — PIIRehydrator
# ---------------------------------------------------------------------------


class TestPIIRehydratorFullAccess:
    def test_full_access_restores_all_pii(self):
        """full access level → all PII placeholders restored."""
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "John Smith", "[US_SSN_1]": "123-45-6789"}
        text = "The plaintiff [PERSON_1] has SSN [US_SSN_1]."

        result = rehydrator.rehydrate(text, mapping, access_level="full")
        assert "John Smith" in result
        assert "123-45-6789" in result

    def test_full_access_replaces_all_placeholders(self):
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "Alice Johnson", "[PERSON_2]": "Bob Williams"}
        text = "Between [PERSON_1] and [PERSON_2]."

        result = rehydrator.rehydrate(text, mapping, access_level="full")
        assert "[PERSON_1]" not in result
        assert "[PERSON_2]" not in result
        assert "Alice Johnson" in result
        assert "Bob Williams" in result


class TestPIIRehydratorRestrictedAccess:
    def test_restricted_access_keeps_sensitive_pii_redacted(self):
        """restricted access → SSN and financial identifiers stay redacted."""
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "John Smith", "[US_SSN_1]": "123-45-6789"}
        text = "The plaintiff [PERSON_1] has SSN [US_SSN_1]."

        result = rehydrator.rehydrate(text, mapping, access_level="restricted")
        # SSN should remain redacted
        assert "123-45-6789" not in result
        assert "[US_SSN_1]" in result

    def test_restricted_access_may_restore_names(self):
        """restricted access may restore PERSON names."""
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "John Smith", "[US_SSN_1]": "123-45-6789"}
        text = "[PERSON_1] SSN: [US_SSN_1]"

        result = rehydrator.rehydrate(text, mapping, access_level="restricted")
        # Person names can be restored in restricted mode
        assert "John Smith" in result


class TestPIIRehydratorReadOnlyAccess:
    def test_read_only_keeps_all_pii_redacted(self):
        """read_only access → all PII placeholders remain."""
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "John Smith", "[US_SSN_1]": "123-45-6789"}
        text = "The plaintiff [PERSON_1] has SSN [US_SSN_1]."

        result = rehydrator.rehydrate(text, mapping, access_level="read_only")
        assert "John Smith" not in result
        assert "123-45-6789" not in result
        assert "[PERSON_1]" in result
        assert "[US_SSN_1]" in result

    def test_read_only_returns_text_unchanged(self):
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "Jane Doe"}
        text = "Counsel [PERSON_1] appeared."

        result = rehydrator.rehydrate(text, mapping, access_level="read_only")
        assert result == text


class TestPIIRehydratorEdgeCases:
    def test_empty_mapping_returns_text_unchanged(self):
        rehydrator = PIIRehydrator()
        text = "No PII in this text."
        result = rehydrator.rehydrate(text, {}, access_level="full")
        assert result == text

    def test_placeholder_not_in_text_ignored(self):
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "John Smith"}
        text = "No placeholders here."
        result = rehydrator.rehydrate(text, mapping, access_level="full")
        assert result == text

    def test_invalid_access_level_defaults_to_read_only(self):
        rehydrator = PIIRehydrator()
        mapping = {"[PERSON_1]": "John Smith"}
        text = "Plaintiff [PERSON_1]."
        # Unknown access level defaults to most restrictive
        result = rehydrator.rehydrate(text, mapping, access_level="unknown_level")
        assert "John Smith" not in result
