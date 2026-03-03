#!/usr/bin/env python3
"""Seed script for the Legal AI Tool.

Creates a minimal set of test data so developers can exercise the full stack
immediately after `docker compose up`:

  1. Register a test attorney user via POST /auth/register
  2. Authenticate to obtain a JWT via POST /auth/login
  3. Create a test matter via POST /matters
  4. Assign the attorney to the matter via POST /matters/:id/assignments
  5. Register a test document entry via POST /documents
  6. (Optional) Trigger ingestion of a sample PDF via POST /ingest on the
     agents backend when SEED_INGEST=true is set.

Usage
-----
  python infra/scripts/seed.py

Environment variables (all optional — defaults shown):
  SEED_API_URL        http://localhost:3000
  SEED_AGENTS_URL     http://localhost:8000
  SEED_ATTORNEY_EMAIL attorney@firm.com
  SEED_ATTORNEY_PASSWORD SeedPass456!
  SEED_INGEST         false
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx is required: pip install httpx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

API_URL: str = os.getenv("SEED_API_URL", "http://localhost:3000")
AGENTS_URL: str = os.getenv("SEED_AGENTS_URL", "http://localhost:8000")

ATTORNEY_EMAIL: str = os.getenv("SEED_ATTORNEY_EMAIL", "attorney@firm.com")
ATTORNEY_PASSWORD: str = os.getenv("SEED_ATTORNEY_PASSWORD", "SeedPass456!")
ATTORNEY_NAME: str = os.getenv("SEED_ATTORNEY_NAME", "Test Attorney")

DO_INGEST: bool = os.getenv("SEED_INGEST", "false").lower() == "true"

TIMEOUT = httpx.Timeout(30.0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pretty(label: str, data: dict) -> None:
    print(f"  [{label}]", json.dumps(data, indent=2, default=str))


def _check(response: httpx.Response, label: str) -> dict:
    if response.status_code not in (200, 201):
        print(f"ERROR: {label} failed with HTTP {response.status_code}")
        print(response.text)
        sys.exit(1)
    body = response.json()
    _pretty(label, body.get("data", body))
    return body


def _wait_for_health(url: str, service: str, retries: int = 10, delay: float = 3.0) -> None:
    """Poll /health until the service is up."""
    for attempt in range(1, retries + 1):
        try:
            r = httpx.get(f"{url}/health", timeout=5)
            if r.status_code == 200:
                print(f"  {service} is healthy.")
                return
        except httpx.RequestError:
            pass
        print(f"  Waiting for {service}… attempt {attempt}/{retries}")
        time.sleep(delay)
    print(f"ERROR: {service} did not become healthy after {retries} attempts.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Seed steps
# ---------------------------------------------------------------------------


def wait_for_services() -> None:
    print("\n== Step 0: Waiting for services to be healthy ==")
    _wait_for_health(API_URL, "Node API")
    _wait_for_health(AGENTS_URL, "Agents backend")


def register_user(client: httpx.Client) -> dict:
    print("\n== Step 1: Register test attorney ==")
    resp = client.post(
        f"{API_URL}/auth/register",
        json={
            "email": ATTORNEY_EMAIL,
            "password": ATTORNEY_PASSWORD,
            "name": ATTORNEY_NAME,
            "role": "attorney",
        },
    )
    # 409 Conflict means user already exists — that is acceptable for re-runs.
    if resp.status_code == 409:
        print(f"  User {ATTORNEY_EMAIL!r} already exists — skipping registration.")
        return {}
    return _check(resp, "register")


def login(client: httpx.Client) -> str:
    print("\n== Step 2: Authenticate and obtain JWT ==")
    resp = client.post(
        f"{API_URL}/auth/login",
        json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD},
    )
    body = _check(resp, "login")
    token: str = body.get("data", {}).get("token") or body.get("token", "")
    if not token:
        print("ERROR: No token returned from login.")
        sys.exit(1)
    return token


def create_matter(client: httpx.Client, token: str) -> dict:
    print("\n== Step 3: Create test matter ==")
    resp = client.post(
        f"{API_URL}/matters",
        json={
            "title": "Sample Breach of Contract — Seed Matter",
            "caseNumber": "SEED-2024-001",
            "status": "active",
            "clientId": None,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return _check(resp, "create_matter").get("data", {})


def assign_user_to_matter(
    client: httpx.Client,
    token: str,
    matter_id: str,
    user_id: str,
) -> dict:
    print("\n== Step 4: Assign attorney to matter ==")
    resp = client.post(
        f"{API_URL}/matters/{matter_id}/assignments",
        json={"userId": user_id, "accessLevel": "full"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return _check(resp, "assign_user").get("data", {})


def create_document(client: httpx.Client, token: str, matter_id: str) -> dict:
    print("\n== Step 5: Register sample document ==")
    resp = client.post(
        f"{API_URL}/documents",
        json={
            "title": "Sample Contract Brief",
            "mimeType": "application/pdf",
            "matterId": matter_id,
            "storagePath": "seeds/sample-brief.pdf",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return _check(resp, "create_document").get("data", {})


def ingest_sample_pdf(token: str, matter_id: str, document_id: str) -> None:
    """POST a minimal in-memory PDF to the agents /ingest endpoint."""
    print("\n== Step 6: Ingest sample PDF into vector store ==")
    sample_pdf_path = Path(__file__).parent / "sample.pdf"
    if not sample_pdf_path.exists():
        print("  sample.pdf not found — skipping ingest step.")
        print("  To ingest, place a PDF at infra/scripts/sample.pdf and set SEED_INGEST=true.")
        return

    with httpx.Client(timeout=TIMEOUT) as ingest_client:
        with sample_pdf_path.open("rb") as f:
            resp = ingest_client.post(
                f"{AGENTS_URL}/ingest",
                headers={"Authorization": f"Bearer {token}"},
                data={"matter_id": matter_id, "document_id": document_id},
                files={"file": ("sample.pdf", f, "application/pdf")},
            )
        if resp.status_code in (200, 201):
            print("  Ingestion triggered successfully.")
            _pretty("ingest", resp.json())
        else:
            print(f"  Ingestion returned HTTP {resp.status_code}: {resp.text}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("  Legal AI Tool — Database Seed Script")
    print("=" * 60)

    with httpx.Client(timeout=TIMEOUT) as client:
        wait_for_services()

        register_resp = register_user(client)
        token = login(client)

        # Extract user ID from login response if registration already existed
        login_resp = client.post(
            f"{API_URL}/auth/login",
            json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD},
        )
        login_body = login_resp.json()
        user = login_body.get("data", {}).get("user") or login_body.get("user", {})
        user_id: str = user.get("id", "")

        matter = create_matter(client, token)
        matter_id: str = matter.get("id", "")

        if not matter_id:
            print("ERROR: Could not determine matter ID.")
            sys.exit(1)

        if user_id:
            assign_user_to_matter(client, token, matter_id, user_id)
        else:
            print("  WARNING: user_id not found — skipping assignment step.")

        document = create_document(client, token, matter_id)
        document_id: str = document.get("id", "")

        if DO_INGEST and document_id:
            ingest_sample_pdf(token, matter_id, document_id)
        elif DO_INGEST:
            print("  WARNING: document ID not found — skipping ingest.")
        else:
            print("\n== Step 6: Skipped (set SEED_INGEST=true to enable) ==")

    print("\n" + "=" * 60)
    print("  Seed complete.")
    print(f"  Matter ID : {matter_id}")
    print(f"  User ID   : {user_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
