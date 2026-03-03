"""Unit tests for LangSmith tracing integration (task 4.14).

Task 4.14: LangSmith tracing — all agent runs and LLM calls traced

LangSmith SDK is fully mocked — no real tracing calls.

RED: These tests fail until app/agents/tracing.py is implemented.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.agents.tracing import TracingConfig, configure_tracing, is_tracing_enabled


class TestTracingConfig:
    def test_config_defaults(self):
        cfg = TracingConfig()
        assert isinstance(cfg.enabled, bool)
        assert isinstance(cfg.project_name, str)

    def test_config_custom_values(self):
        cfg = TracingConfig(
            enabled=True,
            project_name="legal-ai-test",
            api_key="test-key",
        )
        assert cfg.enabled is True
        assert cfg.project_name == "legal-ai-test"
        assert cfg.api_key == "test-key"


class TestConfigureTracing:
    def test_configure_tracing_sets_env_vars_when_enabled(self):
        """configure_tracing(enabled=True) sets LANGCHAIN_TRACING_V2=true."""
        import os

        cfg = TracingConfig(enabled=True, project_name="test-project", api_key="test-key")
        with patch.dict("os.environ", {}, clear=False):
            configure_tracing(cfg)
            # After configuration, env var should be set
            assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"

    def test_configure_tracing_disabled_clears_flag(self):
        """configure_tracing(enabled=False) sets LANGCHAIN_TRACING_V2=false."""
        import os

        cfg = TracingConfig(enabled=False)
        with patch.dict("os.environ", {"LANGCHAIN_TRACING_V2": "true"}, clear=False):
            configure_tracing(cfg)
            assert os.environ.get("LANGCHAIN_TRACING_V2") in ("false", "0", "", None)

    def test_configure_tracing_sets_project_name(self):
        """configure_tracing sets LANGCHAIN_PROJECT env var."""
        import os

        cfg = TracingConfig(enabled=True, project_name="my-legal-project", api_key="key")
        with patch.dict("os.environ", {}, clear=False):
            configure_tracing(cfg)
            assert os.environ.get("LANGCHAIN_PROJECT") == "my-legal-project"

    def test_configure_tracing_sets_api_key(self):
        """configure_tracing sets LANGCHAIN_API_KEY env var."""
        import os

        cfg = TracingConfig(enabled=True, project_name="proj", api_key="my-api-key-123")
        with patch.dict("os.environ", {}, clear=False):
            configure_tracing(cfg)
            assert os.environ.get("LANGCHAIN_API_KEY") == "my-api-key-123"


class TestIsTracingEnabled:
    def test_returns_true_when_env_set(self):
        with patch.dict("os.environ", {"LANGCHAIN_TRACING_V2": "true"}):
            assert is_tracing_enabled() is True

    def test_returns_false_when_env_not_set(self):
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("LANGCHAIN_TRACING_V2", None)
            assert is_tracing_enabled() is False

    def test_returns_false_when_env_false(self):
        with patch.dict("os.environ", {"LANGCHAIN_TRACING_V2": "false"}):
            assert is_tracing_enabled() is False

    def test_returns_true_for_value_1(self):
        with patch.dict("os.environ", {"LANGCHAIN_TRACING_V2": "1"}):
            assert is_tracing_enabled() is True


class TestTracingFromEnv:
    def test_configure_from_env_reads_env_vars(self):
        """TracingConfig can be built from environment variables."""
        from app.agents.tracing import TracingConfig

        with patch.dict(
            "os.environ",
            {
                "LANGCHAIN_TRACING_V2": "true",
                "LANGCHAIN_PROJECT": "env-project",
                "LANGCHAIN_API_KEY": "env-api-key",
            },
        ):
            cfg = TracingConfig.from_env()
            assert cfg.enabled is True
            assert cfg.project_name == "env-project"
            assert cfg.api_key == "env-api-key"
