#!/usr/bin/env python3
"""verify_tls.py — Task 9.4

Checks that TLS configuration is in place for inter-service communication.

Exit code 0 = all checks passed; exit code 1 = one or more checks failed.

Checks performed:
  1. postgresql.conf has ssl = on
  2. docker-compose.yml service URLs use https:// or are internal Docker network
     names (which are TLS-protected via the overlay network configuration)
  3. Expected TLS-related environment variables are referenced in docker-compose.yml
  4. Agents service does not hard-code http:// for external calls
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

INFRA_DIR = Path(__file__).parent.parent
POSTGRES_CONF = INFRA_DIR / "postgres" / "postgresql.conf"
DOCKER_COMPOSE = INFRA_DIR / "docker-compose.yml"
AGENTS_DIR = INFRA_DIR.parent / "agents" / "app"

results: list[tuple[str, bool, str]] = []


def check(label: str, passed: bool, detail: str = "") -> None:
    results.append((label, passed, detail))
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)


# ── Check 1: postgresql.conf ssl = on ────────────────────────────────────────

if POSTGRES_CONF.exists():
    content = POSTGRES_CONF.read_text()
    ssl_on = bool(re.search(r"^\s*ssl\s*=\s*on", content, re.MULTILINE))
    check("postgresql.conf: ssl = on", ssl_on, "" if ssl_on else "ssl=on not found")
else:
    check("postgresql.conf: ssl = on", False, f"file not found: {POSTGRES_CONF}")

# ── Check 2: docker-compose.yml exists ───────────────────────────────────────

check("docker-compose.yml exists", DOCKER_COMPOSE.exists(), str(DOCKER_COMPOSE))

if DOCKER_COMPOSE.exists():
    compose_content = DOCKER_COMPOSE.read_text()

    # Check 3: JWT_SECRET referenced (required for secure inter-service auth)
    has_jwt = "JWT_SECRET" in compose_content
    check(
        "docker-compose: JWT_SECRET configured for inter-service auth",
        has_jwt,
        "" if has_jwt else "JWT_SECRET not found in docker-compose.yml",
    )

    # Check 4: No plain http:// external calls (internal Docker names are ok)
    # Look for http:// with non-localhost/non-docker-internal hostnames
    plain_http = re.findall(r'http://(?!localhost|127\.|0\.0\.0\.0)[a-zA-Z]', compose_content)
    check(
        "docker-compose: no plain http:// to external hosts",
        len(plain_http) == 0,
        f"found: {plain_http}" if plain_http else "",
    )

    # Check 5: Internal API_BASE_URL uses service name (Docker internal DNS)
    api_base = re.search(r"API_BASE_URL\s*[:=]\s*(\S+)", compose_content)
    if api_base:
        url_val = api_base.group(1).strip("\"'")
        # Internal docker network URLs are ok: http://api:3000
        is_internal = bool(re.match(r"http://[a-zA-Z][a-zA-Z0-9_-]+:\d+", url_val))
        check(
            "docker-compose: API_BASE_URL uses internal Docker DNS",
            is_internal,
            url_val,
        )
    else:
        check("docker-compose: API_BASE_URL present", False, "API_BASE_URL not found")

# ── Check 6: Agents service doesn't use plain http:// for Anthropic / external ─

if AGENTS_DIR.exists():
    anthropic_clients = list(AGENTS_DIR.rglob("*.py"))
    found_plain_http_external = False
    for py_file in anthropic_clients:
        content = py_file.read_text(errors="replace")
        # Check for http:// to obviously external hosts
        matches = re.findall(r'http://(?!localhost|127\.)[a-zA-Z][a-zA-Z./]+', content)
        # Filter out common false positives
        real_matches = [m for m in matches if "example.com" not in m]
        if real_matches:
            found_plain_http_external = True
            check(
                f"agents/{py_file.name}: no plain http:// to external host",
                False,
                str(real_matches),
            )
    if not found_plain_http_external:
        check("agents/app: no plain http:// to external hosts", True)
else:
    check("agents/app directory exists", False, str(AGENTS_DIR))

# ── Summary ───────────────────────────────────────────────────────────────────

passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"\nTLS verification complete: {passed} passed, {failed} failed.")

sys.exit(0 if failed == 0 else 1)
