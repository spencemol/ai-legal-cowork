"""PII audit logging — record redaction events for compliance (referenced in spec)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


@dataclass
class PIIAuditEvent:
    """Represents a single PII redaction audit event."""

    timestamp: str
    user_id: str
    matter_id: str
    entity_types_detected: list[str]
    placeholder_count: int


def log_pii_audit_event(
    user_id: str,
    matter_id: str,
    entity_types_detected: list[str],
    placeholder_count: int,
) -> PIIAuditEvent:
    """Log a PII redaction event.

    Parameters
    ----------
    user_id:
        ID of the user whose input was redacted.
    matter_id:
        Matter context for the operation.
    entity_types_detected:
        List of PII entity types found (e.g. ``["PERSON", "US_SSN"]``).
    placeholder_count:
        Total number of PII instances replaced.

    Returns
    -------
    PIIAuditEvent
        The logged event record.
    """
    event = PIIAuditEvent(
        timestamp=datetime.now(tz=UTC).isoformat(),
        user_id=user_id,
        matter_id=matter_id,
        entity_types_detected=entity_types_detected,
        placeholder_count=placeholder_count,
    )
    logger.info(
        "PII redaction: user=%s matter=%s types=%s count=%d",
        user_id,
        matter_id,
        entity_types_detected,
        placeholder_count,
    )
    return event
