"""Input sanitizer — detect and flag common prompt injection patterns (task 4.2)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SanitizationResult:
    """Result of an input sanitization check."""

    sanitized_text: str
    is_safe: bool
    flagged_patterns: list[str] = field(default_factory=list)


# Prompt injection patterns: (name, compiled_regex)
_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignore_previous_instructions",
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules?|prompts?)", re.IGNORECASE),
    ),
    (
        "system_prompt_override",
        re.compile(r"\bSYSTEM\s*:\s*(you\s+(are|have)|forget|disregard|override)", re.IGNORECASE),
    ),
    (
        "role_playing_attack",
        re.compile(r"\b(pretend|act\s+as\s+if|roleplay|role-play|you\s+are\s+now)\b.{0,60}(no\s+restrictions?|unrestricted|DAN|jailbreak)", re.IGNORECASE),
    ),
    (
        "prompt_leak_attempt",
        re.compile(r"repeat\s+(all\s+)?(text|instructions?|prompt)\s+(above|before|prior)", re.IGNORECASE),
    ),
    (
        "jailbreak_no_guidelines",
        re.compile(r"(no\s+ethical\s+guidelines?|no\s+restrictions?|act\s+as\s+if.{0,40}guidelines?)", re.IGNORECASE),
    ),
    (
        "forget_instructions",
        re.compile(r"\b(forget|disregard|override)\s+(all\s+)?(previous|prior|your)\s+(instructions?|rules?|training|guidelines?)", re.IGNORECASE),
    ),
    (
        "reveal_system_prompt",
        re.compile(r"(reveal|show|print|output|repeat)\s+(your\s+)?(system\s+prompt|instructions?|training\s+data)", re.IGNORECASE),
    ),
]


class InputSanitizer:
    """Checks user input for common prompt injection patterns.

    Usage::

        sanitizer = InputSanitizer()
        result = sanitizer.check(user_text)
        if not result.is_safe:
            raise ValueError(f"Injection detected: {result.flagged_patterns}")
    """

    def check(self, text: str) -> SanitizationResult:
        """Scan *text* for injection patterns.

        Returns a :class:`SanitizationResult` with:
        - ``is_safe`` — False if any pattern matched.
        - ``flagged_patterns`` — list of pattern names that matched.
        - ``sanitized_text`` — the original text (sanitizer flags but does not
          alter content; the caller decides how to handle flagged input).
        """
        flagged: list[str] = []
        for name, pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                flagged.append(name)

        return SanitizationResult(
            sanitized_text=text,
            is_safe=len(flagged) == 0,
            flagged_patterns=flagged,
        )
