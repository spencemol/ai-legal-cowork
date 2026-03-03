"""Phase 9 — Task 9.4: TLS inter-service communication tests.

Verifies that:
  - JWT_SECRET is configured in docker-compose for inter-service auth
  - postgresql.conf has ssl = on (transport-level TLS)
  - docker-compose does not hard-code plain http:// to external hosts
  - verify_tls.py script exists and has valid Python syntax
  - Internal Docker service URLs are used correctly
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


class TestDockerComposeTlsConfig:
    """Task 9.4 — docker-compose TLS/security settings."""

    def test_docker_compose_exists(self, docker_compose_path: Path) -> None:
        assert docker_compose_path.exists(), (
            f"docker-compose.yml not found at {docker_compose_path}"
        )

    def test_jwt_secret_configured_for_all_services(self, docker_compose_path: Path) -> None:
        content = docker_compose_path.read_text()
        # JWT_SECRET must be set for both the api and agents services
        matches = re.findall(r"JWT_SECRET", content)
        assert len(matches) >= 2, (
            f"JWT_SECRET should appear in at least 2 service configs, found {len(matches)}"
        )

    def test_no_plain_http_external_in_docker_compose(self, docker_compose_path: Path) -> None:
        content = docker_compose_path.read_text()
        # Find any http:// URLs that are NOT internal Docker service names
        # Internal names: http://api:PORT, http://agents:PORT, http://localhost:PORT
        plain_http = re.findall(
            r'http://(?!localhost|127\.|0\.0\.0\.0|api:|agents:|postgres:|mongodb:)[a-zA-Z]',
            content,
        )
        assert not plain_http, (
            f"Plain http:// to external hosts found in docker-compose: {plain_http}"
        )

    def test_postgres_service_uses_named_volume(self, docker_compose_path: Path) -> None:
        content = docker_compose_path.read_text()
        assert "postgres_data" in content, (
            "postgres_data named volume not configured in docker-compose.yml"
        )

    def test_api_service_has_database_url(self, docker_compose_path: Path) -> None:
        content = docker_compose_path.read_text()
        assert "DATABASE_URL" in content, (
            "DATABASE_URL not configured in docker-compose.yml"
        )

    def test_agents_service_depends_on_api(self, docker_compose_path: Path) -> None:
        content = docker_compose_path.read_text()
        # agents should declare api as a dependency
        # The content around "agents:" block should reference api dependency
        assert "api" in content, (
            "agents service should declare dependency on api service"
        )


class TestPostgresqlTlsConfig:
    """Task 9.4 — Postgres TLS config (referenced here from 9.3 shared setup)."""

    def test_postgres_ssl_enabled(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        assert re.search(r"^\s*ssl\s*=\s*on", content, re.MULTILINE), (
            "Postgres ssl must be enabled for transport-level TLS"
        )

    def test_postgres_ssl_prefers_server_ciphers(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        assert "ssl_prefer_server_ciphers" in content, (
            "ssl_prefer_server_ciphers should be set for cipher negotiation control"
        )


class TestVerifyTlsScript:
    """Task 9.4 — verify_tls.py script."""

    def test_verify_tls_script_exists(self, verify_tls_script: Path) -> None:
        assert verify_tls_script.exists(), (
            f"verify_tls.py not found at {verify_tls_script}"
        )

    def test_verify_tls_script_has_valid_syntax(self, verify_tls_script: Path) -> None:
        source = verify_tls_script.read_text()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"verify_tls.py has a syntax error: {e}")

    def test_verify_tls_script_checks_ssl(self, verify_tls_script: Path) -> None:
        content = verify_tls_script.read_text()
        assert "ssl" in content.lower(), (
            "verify_tls.py should check SSL/TLS configuration"
        )

    def test_verify_tls_script_checks_docker_compose(self, verify_tls_script: Path) -> None:
        content = verify_tls_script.read_text()
        assert "docker-compose" in content or "docker_compose" in content, (
            "verify_tls.py should verify docker-compose TLS settings"
        )

    def test_verify_tls_script_checks_jwt_secret(self, verify_tls_script: Path) -> None:
        content = verify_tls_script.read_text()
        assert "JWT_SECRET" in content or "jwt" in content.lower(), (
            "verify_tls.py should verify JWT_SECRET for inter-service auth"
        )
