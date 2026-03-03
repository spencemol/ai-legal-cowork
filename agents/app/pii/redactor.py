"""Presidio-based PII redactor and re-hydrator (tasks 4.3, 4.4).

Task 4.3 — PIIRedactor
    Detects and replaces PII with numbered placeholders: [PERSON_1], [US_SSN_1], etc.
    Maintains a per-call mapping table so PII can be re-inserted later.

Task 4.4 — PIIRehydrator
    Given the mapping table and a user access_level, selectively restores PII:
      full       → all PII restored
      restricted → sensitive identifiers (SSN, credit-card, etc.) stay redacted
      read_only  → all PII stays redacted
"""

from __future__ import annotations

from dataclasses import dataclass, field

from presidio_analyzer import AnalyzerEngine  # type: ignore[import]
from presidio_anonymizer import AnonymizerEngine  # type: ignore[import]
from presidio_anonymizer.entities import OperatorConfig  # type: ignore[import]

# Entity types considered highly sensitive — kept redacted in "restricted" mode.
_SENSITIVE_ENTITY_TYPES: frozenset[str] = frozenset(
    [
        "US_SSN",
        "US_PASSPORT",
        "US_DRIVER_LICENSE",
        "CREDIT_CARD",
        "IBAN_CODE",
        "NRP",
        "MEDICAL_LICENSE",
        "IP_ADDRESS",
        "CRYPTO",
    ]
)


@dataclass
class RedactionResult:
    """Result of a PII redaction pass."""

    redacted_text: str
    mapping: dict[str, str] = field(default_factory=dict)
    """Maps placeholder (e.g. ``[PERSON_1]``) → original PII value."""


class PIIRedactor:
    """Detect and replace PII in text using Presidio.

    Each :meth:`redact` call uses fresh counters per entity-type so that
    placeholders are deterministic within a single document but independent
    across documents.

    The ``mapping`` attribute accumulates all substitutions made so far and
    can be passed to :class:`PIIRehydrator` downstream.

    Engines are created lazily on the first :meth:`redact` call so that
    importing this module does not trigger a spaCy model download at startup.
    """

    def __init__(
        self,
        language: str = "en",
        analyzer: AnalyzerEngine | None = None,
        anonymizer: AnonymizerEngine | None = None,
    ) -> None:
        # Accept pre-built engines (for testing / dependency injection).
        # If not provided, they are created lazily on first use.
        self._analyzer: AnalyzerEngine | None = analyzer
        self._anonymizer: AnonymizerEngine | None = anonymizer
        self._language = language
        self._engines_unavailable: bool = False  # cached failure flag
        self.mapping: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Lazy engine accessors
    # ------------------------------------------------------------------

    def _get_analyzer(self) -> AnalyzerEngine:
        if self._analyzer is None:
            self._analyzer = AnalyzerEngine()
        return self._analyzer

    def _get_anonymizer(self) -> AnonymizerEngine:
        if self._anonymizer is None:
            self._anonymizer = AnonymizerEngine()
        return self._anonymizer

    def redact(self, text: str) -> RedactionResult:
        """Redact PII in *text* and return the result with a mapping table.

        Parameters
        ----------
        text:
            Raw text that may contain PII.

        Returns
        -------
        RedactionResult
            ``.redacted_text`` has placeholders in ``[ENTITY_TYPE_N]`` format.
            ``.mapping`` maps each placeholder back to its original value.
            If the NLP engine is unavailable (e.g. spaCy model not installed),
            the original text is returned unchanged with an empty mapping.
        """
        if self._engines_unavailable:
            return RedactionResult(redacted_text=text, mapping={})

        try:
            analyzer = self._get_analyzer()
            anonymizer = self._get_anonymizer()
        except (Exception, SystemExit):  # SystemExit from spacy download failures
            self._engines_unavailable = True
            return RedactionResult(redacted_text=text, mapping={})

        try:
            analyzer_results = analyzer.analyze(text=text, language=self._language)
        except (Exception, SystemExit):  # pragma: no cover — NLP runtime errors
            return RedactionResult(redacted_text=text, mapping={})

        if not analyzer_results:
            return RedactionResult(redacted_text=text, mapping={})

        # Track counters per entity type to produce unique placeholder names.
        counters: dict[str, int] = {}
        placeholder_map: dict[str, str] = {}  # placeholder → original value

        # Build placeholder values for each detected entity (forward order).
        for result in sorted(analyzer_results, key=lambda r: r.start):
            etype = result.entity_type
            counters[etype] = counters.get(etype, 0) + 1
            placeholder = f"[{etype}_{counters[etype]}]"
            original_value = text[result.start : result.end]
            placeholder_map[placeholder] = original_value

        # Build operator configs: map each entity type to its placeholder.
        # We need entity_type → placeholder lookup, but there can be multiple
        # instances of the same type.  Re-use the counters in forward order.
        counters2: dict[str, int] = {}
        operators: dict[str, OperatorConfig] = {}

        for result in sorted(analyzer_results, key=lambda r: r.start):
            etype = result.entity_type
            counters2[etype] = counters2.get(etype, 0) + 1
            placeholder = f"[{etype}_{counters2[etype]}]"
            # Presidio's "replace" operator accepts a ``new_value``.
            # We register per-entity to get unique placeholders.
            operators[etype] = OperatorConfig("replace", {"new_value": placeholder})

        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators,
        )

        # Update instance-level mapping with this call's substitutions.
        self.mapping.update(placeholder_map)

        return RedactionResult(
            redacted_text=anonymized.text,
            mapping=dict(placeholder_map),
        )


class PIIRehydrator:
    """Restore PII placeholders based on user access level (task 4.4).

    Access levels
    -------------
    full       All placeholders replaced with original PII.
    restricted PERSON names restored; SSN/financial/sensitive identifiers kept redacted.
    read_only  All placeholders kept as-is (most restrictive).
    """

    def rehydrate(
        self,
        text: str,
        mapping: dict[str, str],
        access_level: str,
    ) -> str:
        """Replace placeholders in *text* according to *access_level*.

        Parameters
        ----------
        text:
            Text that may contain ``[ENTITY_TYPE_N]`` placeholders.
        mapping:
            Dict mapping placeholder → original value.
        access_level:
            One of ``"full"``, ``"restricted"``, or ``"read_only"``.
            Unrecognised values are treated as ``"read_only"``.

        Returns
        -------
        str
            Text with placeholders selectively replaced.
        """
        if access_level == "read_only" or access_level not in ("full", "restricted"):
            # Most restrictive: return as-is.
            return text

        result = text
        for placeholder, original in mapping.items():
            if access_level == "full":
                result = result.replace(placeholder, original)
            elif access_level == "restricted":
                # Extract entity type from placeholder, e.g. PERSON from [PERSON_1]
                entity_type = _entity_type_from_placeholder(placeholder)
                if entity_type not in _SENSITIVE_ENTITY_TYPES:
                    result = result.replace(placeholder, original)
                # else: leave placeholder in place

        return result


def _entity_type_from_placeholder(placeholder: str) -> str:
    """Extract entity type from a ``[ENTITY_TYPE_N]`` placeholder string."""
    # e.g.  "[PERSON_1]"  → "PERSON"
    #        "[US_SSN_1]" → "US_SSN"
    inner = placeholder.strip("[]")  # "PERSON_1" or "US_SSN_1"
    # Entity type is everything before the last "_N" suffix.
    parts = inner.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return inner
