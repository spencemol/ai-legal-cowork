"""Shared fixtures for Phase 9 tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# Repository root (3 levels up from this file)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INFRA_DIR = REPO_ROOT / "infra"
AGENTS_DIR = REPO_ROOT / "agents"


@pytest.fixture
def infra_dir() -> Path:
    return INFRA_DIR


@pytest.fixture
def agents_dir() -> Path:
    return AGENTS_DIR


@pytest.fixture
def postgres_conf_path() -> Path:
    return INFRA_DIR / "postgres" / "postgresql.conf"


@pytest.fixture
def docker_compose_path() -> Path:
    return INFRA_DIR / "docker-compose.yml"


@pytest.fixture
def verify_encryption_script() -> Path:
    return INFRA_DIR / "scripts" / "verify_encryption.sh"


@pytest.fixture
def verify_tls_script() -> Path:
    return INFRA_DIR / "scripts" / "verify_tls.py"


@pytest.fixture
def airflow_dag_path() -> Path:
    return INFRA_DIR / "airflow" / "dags" / "reindex_dag.py"
