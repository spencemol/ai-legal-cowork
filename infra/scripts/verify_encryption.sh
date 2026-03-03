#!/usr/bin/env bash
# verify_encryption.sh — Task 9.3
#
# Verifies that the Legal AI Tool encryption configuration is in place.
# Exit code 0 = all checks passed; exit code 1 = one or more checks failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
POSTGRES_CONF="$INFRA_DIR/postgres/postgresql.conf"
ENCRYPTION_README="$INFRA_DIR/encryption/README.md"

PASS=0
FAIL=0

check() {
  local label="$1"
  local result="$2"
  if [ "$result" = "ok" ]; then
    echo "[PASS] $label"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $label — $result"
    FAIL=$((FAIL + 1))
  fi
}

# ── Check 1: postgresql.conf exists ──────────────────────────────────────────
if [ -f "$POSTGRES_CONF" ]; then
  check "postgresql.conf file exists" "ok"
else
  check "postgresql.conf file exists" "not found at $POSTGRES_CONF"
fi

# ── Check 2: ssl = on is set ──────────────────────────────────────────────────
if grep -qE "^\s*ssl\s*=\s*on" "$POSTGRES_CONF" 2>/dev/null; then
  check "postgresql.conf: ssl = on" "ok"
else
  check "postgresql.conf: ssl = on" "ssl=on not found in $POSTGRES_CONF"
fi

# ── Check 3: TLS minimum version is set ──────────────────────────────────────
if grep -qE "ssl_min_protocol_version" "$POSTGRES_CONF" 2>/dev/null; then
  check "postgresql.conf: ssl_min_protocol_version set" "ok"
else
  check "postgresql.conf: ssl_min_protocol_version set" "missing from $POSTGRES_CONF"
fi

# ── Check 4: password_encryption = scram-sha-256 ─────────────────────────────
if grep -qE "password_encryption\s*=\s*scram-sha-256" "$POSTGRES_CONF" 2>/dev/null; then
  check "postgresql.conf: password_encryption = scram-sha-256" "ok"
else
  check "postgresql.conf: password_encryption = scram-sha-256" "not configured"
fi

# ── Check 5: Encryption README exists ────────────────────────────────────────
if [ -f "$ENCRYPTION_README" ]; then
  check "Encryption README exists" "ok"
else
  check "Encryption README exists" "not found at $ENCRYPTION_README"
fi

# ── Check 6: docker-compose uses named volume for postgres data ───────────────
COMPOSE_FILE="$INFRA_DIR/docker-compose.yml"
if grep -qE "postgres_data" "$COMPOSE_FILE" 2>/dev/null; then
  check "docker-compose: postgres_data named volume configured" "ok"
else
  check "docker-compose: postgres_data named volume configured" "not found in $COMPOSE_FILE"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "Encryption verification complete: $PASS passed, $FAIL failed."

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
