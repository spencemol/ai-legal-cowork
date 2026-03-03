"""Phase 9 — Task 9.3: Encryption at rest configuration tests.

Verifies that:
  - infra/postgres/postgresql.conf exists and has ssl = on
  - ssl_min_protocol_version is set (TLS 1.2+)
  - password_encryption = scram-sha-256
  - infra/encryption/README.md documents TDE options
  - infra/scripts/verify_encryption.sh exists and is executable
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

import pytest


class TestPostgresqlConf:
    """Task 9.3 — postgresql.conf encryption / TLS settings."""

    def test_postgresql_conf_exists(self, postgres_conf_path: Path) -> None:
        assert postgres_conf_path.exists(), (
            f"postgresql.conf not found at {postgres_conf_path}"
        )

    def test_ssl_is_enabled(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        # Must have an uncommented 'ssl = on' line
        assert re.search(r"^\s*ssl\s*=\s*on", content, re.MULTILINE), (
            "ssl = on not found in postgresql.conf"
        )

    def test_ssl_min_protocol_version_is_set(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        assert "ssl_min_protocol_version" in content, (
            "ssl_min_protocol_version not set in postgresql.conf"
        )

    def test_ssl_min_protocol_version_is_tls12_or_higher(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        match = re.search(r"ssl_min_protocol_version\s*=\s*'?(TLSv[\d.]+)'?", content)
        assert match is not None, "ssl_min_protocol_version value not parseable"
        version_str = match.group(1)  # e.g. 'TLSv1.2'
        # Accept TLSv1.2 or higher (TLSv1.3)
        assert version_str in ("TLSv1.2", "TLSv1.3"), (
            f"ssl_min_protocol_version should be TLSv1.2 or TLSv1.3, got {version_str!r}"
        )

    def test_password_encryption_uses_scram(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        assert re.search(r"password_encryption\s*=\s*scram-sha-256", content), (
            "password_encryption = scram-sha-256 not set in postgresql.conf"
        )

    def test_ssl_cert_file_is_referenced(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        assert "ssl_cert_file" in content, (
            "ssl_cert_file not referenced in postgresql.conf"
        )

    def test_ssl_key_file_is_referenced(self, postgres_conf_path: Path) -> None:
        content = postgres_conf_path.read_text()
        assert "ssl_key_file" in content, (
            "ssl_key_file not referenced in postgresql.conf"
        )


class TestEncryptionDocumentation:
    """Task 9.3 — Encryption documentation exists."""

    def test_encryption_readme_exists(self, infra_dir: Path) -> None:
        readme = infra_dir / "encryption" / "README.md"
        assert readme.exists(), f"Encryption README not found at {readme}"

    def test_encryption_readme_mentions_tde(self, infra_dir: Path) -> None:
        readme = infra_dir / "encryption" / "README.md"
        content = readme.read_text()
        assert "TDE" in content or "Transparent Data Encryption" in content, (
            "Encryption README does not mention TDE options"
        )

    def test_encryption_readme_mentions_ssl(self, infra_dir: Path) -> None:
        readme = infra_dir / "encryption" / "README.md"
        content = readme.read_text()
        assert "ssl" in content.lower() or "tls" in content.lower(), (
            "Encryption README does not mention SSL/TLS"
        )

    def test_encryption_readme_mentions_pgcrypto(self, infra_dir: Path) -> None:
        readme = infra_dir / "encryption" / "README.md"
        content = readme.read_text()
        assert "pgcrypto" in content.lower(), (
            "Encryption README should document pgcrypto column-level encryption"
        )


class TestVerifyEncryptionScript:
    """Task 9.3 — verify_encryption.sh script checks."""

    def test_verify_encryption_script_exists(self, verify_encryption_script: Path) -> None:
        assert verify_encryption_script.exists(), (
            f"verify_encryption.sh not found at {verify_encryption_script}"
        )

    def test_verify_encryption_script_is_executable(
        self, verify_encryption_script: Path
    ) -> None:
        mode = os.stat(verify_encryption_script).st_mode
        assert mode & stat.S_IXUSR, (
            "verify_encryption.sh is not executable (chmod +x required)"
        )

    def test_verify_encryption_script_checks_ssl_on(
        self, verify_encryption_script: Path
    ) -> None:
        content = verify_encryption_script.read_text()
        assert "ssl" in content.lower(), (
            "verify_encryption.sh should check for ssl configuration"
        )

    def test_verify_encryption_script_has_pass_fail_output(
        self, verify_encryption_script: Path
    ) -> None:
        content = verify_encryption_script.read_text()
        assert "PASS" in content and "FAIL" in content, (
            "verify_encryption.sh should print PASS/FAIL status for each check"
        )
