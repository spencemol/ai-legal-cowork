"""LangSmith tracing configuration for agent runs and LLM calls (task 4.14).

LangSmith tracing is enabled by setting LANGCHAIN_TRACING_V2=true in the
environment.  This module provides a structured :class:`TracingConfig` dataclass
and helper functions for configuring tracing programmatically.

When ``LANGCHAIN_TRACING_V2=true`` (or ``"1"``), all LangChain/LangGraph
calls automatically send traces to LangSmith without requiring any additional
instrumentation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class TracingConfig:
    """Configuration for LangSmith tracing.

    Parameters
    ----------
    enabled:
        Whether tracing is active.  Defaults to reading ``LANGCHAIN_TRACING_V2``
        from the environment (``"true"`` or ``"1"`` → True).
    project_name:
        LangSmith project name.  Defaults to reading ``LANGCHAIN_PROJECT``.
    api_key:
        LangSmith API key.  Defaults to reading ``LANGCHAIN_API_KEY``.
    """

    enabled: bool = field(
        default_factory=lambda: os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1")
    )
    project_name: str = field(
        default_factory=lambda: os.getenv("LANGCHAIN_PROJECT", "legal-ai-tool")
    )
    api_key: str | None = field(
        default_factory=lambda: os.getenv("LANGCHAIN_API_KEY") or None
    )

    @classmethod
    def from_env(cls) -> TracingConfig:
        """Build a :class:`TracingConfig` from the current environment."""
        return cls(
            enabled=os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1"),
            project_name=os.getenv("LANGCHAIN_PROJECT", "legal-ai-tool"),
            api_key=os.getenv("LANGCHAIN_API_KEY") or None,
        )


def configure_tracing(config: TracingConfig) -> None:
    """Apply *config* to the process environment for LangSmith tracing.

    LangChain/LangGraph reads these env-vars at call time, so setting them
    here is sufficient to enable or disable tracing for all subsequent calls.

    Parameters
    ----------
    config:
        :class:`TracingConfig` instance describing the desired tracing state.
    """
    if config.enabled:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    os.environ["LANGCHAIN_PROJECT"] = config.project_name

    if config.api_key:
        os.environ["LANGCHAIN_API_KEY"] = config.api_key


def is_tracing_enabled() -> bool:
    """Return ``True`` if LangSmith tracing is currently enabled.

    Reads ``LANGCHAIN_TRACING_V2`` from the environment.  Returns ``True``
    when the value is ``"true"`` or ``"1"`` (case-insensitive).
    """
    value = os.getenv("LANGCHAIN_TRACING_V2", "").lower()
    return value in ("true", "1")
