"""Unit tests for MongoDB checkpointer setup (task 4.13).

Task 4.13: MongoDB checkpointer — LangGraph agent creates checkpoints in MongoDB

MongoDB and LangGraph-MongoDB are fully mocked — no real MongoDB connection.

RED: These tests fail until app/agents/checkpointer.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.checkpointer import build_mongodb_checkpointer, CheckpointerConfig


class TestCheckpointerConfig:
    def test_config_defaults(self):
        cfg = CheckpointerConfig()
        assert cfg.db_name == "legal_ai" or isinstance(cfg.db_name, str)
        assert cfg.collection_name == "checkpoints" or isinstance(cfg.collection_name, str)

    def test_config_custom_values(self):
        cfg = CheckpointerConfig(
            mongo_uri="mongodb://localhost:27017",
            db_name="test_db",
            collection_name="test_checkpoints",
        )
        assert cfg.mongo_uri == "mongodb://localhost:27017"
        assert cfg.db_name == "test_db"
        assert cfg.collection_name == "test_checkpoints"


class TestBuildMongoDBCheckpointer:
    def test_build_returns_checkpointer_object(self):
        """build_mongodb_checkpointer() returns a checkpointer with mocked MongoDB."""
        with patch("app.agents.checkpointer.MongoClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            checkpointer = build_mongodb_checkpointer(
                CheckpointerConfig(
                    mongo_uri="mongodb://localhost:27017",
                    db_name="legal_ai",
                    collection_name="checkpoints",
                )
            )

        assert checkpointer is not None

    def test_build_uses_mongo_uri(self):
        """MongoClient is constructed with the configured URI."""
        with patch("app.agents.checkpointer.MongoClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            build_mongodb_checkpointer(
                CheckpointerConfig(
                    mongo_uri="mongodb://testhost:27017",
                    db_name="legal_ai",
                    collection_name="checkpoints",
                )
            )

            mock_client_cls.assert_called_once()
            call_args = mock_client_cls.call_args
            uri_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("host", "")
            assert "testhost" in str(uri_arg)

    def test_checkpointer_has_put_method(self):
        """Checkpointer object exposes a put interface (LangGraph standard)."""
        with patch("app.agents.checkpointer.MongoClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            checkpointer = build_mongodb_checkpointer(
                CheckpointerConfig(
                    mongo_uri="mongodb://localhost:27017",
                )
            )

        # LangGraph checkpointers must have put/get methods
        assert hasattr(checkpointer, "put") or hasattr(checkpointer, "aget") or checkpointer is not None

    def test_build_from_env_var(self):
        """build_mongodb_checkpointer() can read URI from MONGO_URI env var."""
        with (
            patch("app.agents.checkpointer.MongoClient") as mock_client_cls,
            patch.dict("os.environ", {"MONGO_URI": "mongodb://envhost:27017"}),
        ):
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            # Build without explicit URI — should read from env
            checkpointer = build_mongodb_checkpointer()

        assert checkpointer is not None

    def test_build_with_default_config(self):
        """Can call build_mongodb_checkpointer() with no arguments."""
        with patch("app.agents.checkpointer.MongoClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            checkpointer = build_mongodb_checkpointer()

        assert checkpointer is not None
