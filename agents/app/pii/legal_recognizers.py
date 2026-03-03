"""Custom Presidio recognizers for legal-domain entities (Task 9.6).

Entities recognised:
  - CASE_NUMBER   — court case numbers (2024-CV-001234, 23-CR-456, CV-2024-789, etc.)
  - BAR_ID        — attorney bar IDs (CA#12345, NY-BAR-67890, BAR-12345, etc.)
  - COURT_NAME    — named court references (Superior Court, District Court, etc.)

All recognizers extend PatternRecognizer so they require only regex patterns —
no spaCy NLP model is needed.
"""

from __future__ import annotations

from presidio_analyzer import PatternRecognizer, Pattern  # type: ignore[import]


class CaseNumberRecognizer(PatternRecognizer):
    """Recognise court case number patterns.

    Examples matched:
      2024-CV-001234
      23-CR-456
      CV-2024-789
      Case No. 2024-1234
      No. 22-1234
    """

    PATTERNS = [
        Pattern(
            name="case_number_full",
            regex=r"\b\d{2,4}-[A-Z]{1,4}-\d{3,8}\b",
            score=0.85,
        ),
        Pattern(
            name="case_number_cv",
            regex=r"\b[A-Z]{1,4}-\d{4}-\d{3,8}\b",
            score=0.80,
        ),
        Pattern(
            name="case_number_no_prefix",
            regex=r"\b(?:Case\s+No\.|No\.)\s*\d{4}-\d{3,8}\b",
            score=0.75,
        ),
        Pattern(
            name="case_number_short",
            regex=r"\b\d{2}-\d{4,8}\b",
            score=0.60,
        ),
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CASE_NUMBER",
            patterns=self.PATTERNS,
            name="CaseNumberRecognizer",
        )


class BarIDRecognizer(PatternRecognizer):
    """Recognise attorney bar ID patterns.

    Examples matched:
      CA#12345
      CA-12345
      NY-BAR-67890
      BAR-12345
      SBN 123456  (State Bar Number)
      Bar No. 12345
    """

    PATTERNS = [
        Pattern(
            name="bar_id_state_hash",
            regex=r"\b[A-Z]{2}#\d{4,8}\b",
            score=0.90,
        ),
        Pattern(
            name="bar_id_state_dash",
            regex=r"\b[A-Z]{2}-\d{4,8}\b",
            score=0.75,
        ),
        Pattern(
            name="bar_id_state_bar_prefix",
            regex=r"\b[A-Z]{2}-BAR-\d{4,8}\b",
            score=0.90,
        ),
        Pattern(
            name="bar_id_bar_prefix",
            regex=r"\bBAR-\d{4,8}\b",
            score=0.85,
        ),
        Pattern(
            name="bar_id_sbn",
            regex=r"\bSBN\s*\d{4,8}\b",
            score=0.85,
        ),
        Pattern(
            name="bar_id_bar_no",
            regex=r"\bBar\s+No\.?\s*\d{4,8}\b",
            score=0.80,
        ),
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="BAR_ID",
            patterns=self.PATTERNS,
            name="BarIDRecognizer",
        )


class CourtNameRecognizer(PatternRecognizer):
    """Recognise named court references.

    Examples matched:
      Superior Court
      Superior Court of California
      United States District Court
      U.S. Court of Appeals
      Circuit Court
      Family Court
      Bankruptcy Court
      Supreme Court of the United States
    """

    PATTERNS = [
        Pattern(
            name="court_superior",
            regex=r"\bSuperior Court(?:\s+of\s+[\w\s]+)?\b",
            score=0.85,
        ),
        Pattern(
            name="court_district",
            regex=r"\b(?:United\s+States\s+)?District\s+Court(?:\s+for\s+[\w\s,]+)?\b",
            score=0.85,
        ),
        Pattern(
            name="court_us_prefix",
            regex=r"\bU\.?S\.?\s+(?:District|Circuit|Court\s+of)\s+\w+",
            score=0.80,
        ),
        Pattern(
            name="court_circuit",
            regex=r"\b(?:\w+\s+)?Circuit\s+Court(?:\s+of\s+[\w\s]+)?\b",
            score=0.80,
        ),
        Pattern(
            name="court_family_bankruptcy",
            regex=r"\b(?:Family|Bankruptcy|Probate|Juvenile)\s+Court\b",
            score=0.85,
        ),
        Pattern(
            name="court_supreme",
            regex=r"\bSupreme\s+Court(?:\s+of\s+[\w\s]+)?\b",
            score=0.85,
        ),
        Pattern(
            name="court_appeals",
            regex=r"\bCourt\s+of\s+Appeals(?:\s+for\s+[\w\s,]+)?\b",
            score=0.85,
        ),
    ]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="COURT_NAME",
            patterns=self.PATTERNS,
            name="CourtNameRecognizer",
        )
