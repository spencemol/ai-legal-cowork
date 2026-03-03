"""Phase 9 — Task 9.5: Airflow re-indexing DAG tests.

Verifies the DAG file without running Airflow:
  - File exists and has valid Python syntax
  - DAG object is importable with a mocked Airflow
  - Schedule interval is set (nightly cron)
  - Required tasks (reindex_all_matters) are defined
  - DAG metadata (owner, tags, catchup=False) is correct
  - Task callables reference the ingestion endpoint

Airflow itself is NOT running in CI — we validate structure only.
"""

from __future__ import annotations

import ast
import re
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


class TestAirflowDagFile:
    """Task 9.5 — reindex_dag.py structural checks."""

    def test_dag_file_exists(self, airflow_dag_path: Path) -> None:
        assert airflow_dag_path.exists(), (
            f"reindex_dag.py not found at {airflow_dag_path}"
        )

    def test_dag_file_has_valid_python_syntax(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"reindex_dag.py has a syntax error: {e}")

    def test_dag_file_has_schedule_interval(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "schedule_interval" in source or "schedule" in source, (
            "reindex_dag.py must define a schedule_interval"
        )

    def test_dag_file_uses_nightly_cron(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        # Look for a cron expression in the file — any hourly/daily pattern
        # Acceptable: "0 2 * * *", "@daily", "0 0 * * *", etc.
        has_cron = bool(
            re.search(r'"@daily"|"@hourly"|\d+ \d+ \* \* \*', source)
        )
        assert has_cron, (
            "reindex_dag.py should use a cron schedule (e.g. '0 2 * * *')"
        )

    def test_dag_file_has_dag_id(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "dag_id" in source, (
            "reindex_dag.py must specify a dag_id"
        )

    def test_dag_id_is_legal_ai_reindex(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "legal_ai_reindex" in source, (
            "dag_id should be 'legal_ai_reindex'"
        )

    def test_dag_file_references_ingest_endpoint(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "/ingest" in source, (
            "reindex_dag.py should call the /ingest endpoint on the agent backend"
        )

    def test_dag_file_references_matters_endpoint(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "/matters" in source, (
            "reindex_dag.py should fetch matters from the Node API"
        )

    def test_dag_file_has_catchup_false(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "catchup=False" in source or "catchup = False" in source, (
            "reindex_dag.py should set catchup=False to prevent backfill runs"
        )

    def test_dag_file_has_retries_configured(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert '"retries"' in source or "'retries'" in source, (
            "reindex_dag.py DEFAULT_ARGS should configure retries"
        )

    def test_dag_file_has_owner(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert '"owner"' in source or "'owner'" in source, (
            "reindex_dag.py DEFAULT_ARGS should specify an owner"
        )

    def test_dag_file_uses_python_operator(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "PythonOperator" in source, (
            "reindex_dag.py should use PythonOperator for the reindex task"
        )


class TestAirflowDagImportable:
    """Task 9.5 — DAG can be imported when Airflow is mocked."""

    def test_dag_importable_with_mocked_airflow(self, airflow_dag_path: Path) -> None:
        """Import the DAG module with Airflow mocked to avoid real Airflow dependency."""
        # Stub out airflow modules
        airflow_mock = types.ModuleType("airflow")
        dag_class = MagicMock()
        dag_instance = MagicMock()
        dag_instance.__enter__ = MagicMock(return_value=dag_instance)
        dag_instance.__exit__ = MagicMock(return_value=False)
        dag_class.return_value = dag_instance
        airflow_mock.DAG = dag_class  # type: ignore[attr-defined]

        operators_mock = types.ModuleType("airflow.operators")
        python_mock = types.ModuleType("airflow.operators.python")
        python_mock.PythonOperator = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]

        sys.modules.setdefault("airflow", airflow_mock)
        sys.modules.setdefault("airflow.operators", operators_mock)
        sys.modules.setdefault("airflow.operators.python", python_mock)

        import importlib.util

        spec = importlib.util.spec_from_file_location("reindex_dag", airflow_dag_path)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        try:
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        except Exception as e:
            pytest.fail(f"reindex_dag.py failed to import with mocked Airflow: {e}")

    def test_dag_callable_trigger_all_matters_reindex_exists(self, airflow_dag_path: Path) -> None:
        source = airflow_dag_path.read_text()
        assert "trigger_all_matters_reindex" in source or "reindex_all_matters" in source, (
            "reindex_dag.py should define a reindex callable function"
        )
