"""reindex_dag.py — Task 9.5

Airflow DAG for scheduled re-indexing of all matter documents.

Schedule: nightly at 02:00 UTC (cron: '0 2 * * *')
Owner:    legal-ai-ops

The DAG:
  1. Fetches the list of all active matters from the Node REST API.
  2. For each matter, calls POST /ingest on the Python agent backend to
     re-index new or changed documents.
  3. Logs the number of documents upserted per matter.

No real infrastructure is started in CI — this file is syntax-checked and
structurally validated by tests/phase9/test_airflow_dag.py.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG  # type: ignore[import]
from airflow.operators.python import PythonOperator  # type: ignore[import]

# ── DAG default arguments ─────────────────────────────────────────────────────

DEFAULT_ARGS = {
    "owner": "legal-ai-ops",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ── Environment ───────────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:3000")
AGENTS_BASE_URL = os.getenv("AGENTS_BASE_URL", "http://agents:8000")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")

# ── Task functions ─────────────────────────────────────────────────────────────


def fetch_active_matters(**context: object) -> list[dict]:
    """Fetch all active matters from the Node REST API.

    Returns a list of matter dicts with at minimum: { 'id': str, 'title': str }.
    Uses the internal service JWT for authentication.
    """
    import requests  # type: ignore[import]

    headers = {"Authorization": f"Bearer {_get_service_token()}"}
    response = requests.get(f"{API_BASE_URL}/matters", headers=headers, timeout=30)
    response.raise_for_status()
    matters: list[dict] = response.json()
    active = [m for m in matters if m.get("status") == "active"]

    # Push to XCom so downstream tasks can consume it
    context["ti"].xcom_push(key="active_matter_ids", value=[m["id"] for m in active])  # type: ignore[index]
    return active


def reindex_matter(matter_id: str, **context: object) -> dict:
    """Call POST /ingest on the agent backend for a single matter.

    The ingestion endpoint re-processes all documents in the matter that have
    been added or modified since the last indexing run.
    """
    import requests  # type: ignore[import]

    headers = {
        "Authorization": f"Bearer {_get_service_token()}",
        "Content-Type": "application/json",
    }
    payload = {
        "matter_id": matter_id,
        "reindex": True,  # signal to the ingestion endpoint to re-check all docs
    }
    response = requests.post(
        f"{AGENTS_BASE_URL}/ingest",
        json=payload,
        headers=headers,
        timeout=300,  # 5 minutes per matter
    )
    response.raise_for_status()
    result: dict = response.json()
    return result


def trigger_all_matters_reindex(**context: object) -> None:
    """Orchestrate per-matter re-indexing as a single serial loop.

    For large deployments with many matters, this can be parallelised by
    emitting dynamic tasks (Airflow 2.3+ TaskGroup / dynamic task mapping).
    """
    import requests  # type: ignore[import]

    headers = {"Authorization": f"Bearer {_get_service_token()}"}
    response = requests.get(f"{API_BASE_URL}/matters", headers=headers, timeout=30)
    response.raise_for_status()
    matters: list[dict] = response.json()

    total_upserted = 0
    for matter in matters:
        if matter.get("status") != "active":
            continue
        result = reindex_matter(matter["id"])
        upserted = result.get("upserted", 0)
        total_upserted += upserted
        print(f"Matter {matter['id']!r}: {upserted} vectors upserted")

    print(f"Re-indexing complete. Total vectors upserted: {total_upserted}")


def _get_service_token() -> str:
    """Create a minimal service-to-service JWT.

    In production this should be replaced by a dedicated service account
    token issued by the auth service, not derived from the shared secret.
    """
    import jwt  # type: ignore[import]

    payload = {
        "sub": "airflow-reindex-service",
        "role": "service",
        "matter_ids": ["*"],  # service account has global access
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# ── DAG definition ────────────────────────────────────────────────────────────

with DAG(
    dag_id="legal_ai_reindex",
    default_args=DEFAULT_ARGS,
    description="Nightly re-indexing of all active matter documents into Pinecone",
    schedule_interval="0 2 * * *",  # 02:00 UTC every day
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["legal-ai", "ingestion", "pinecone"],
    max_active_runs=1,  # prevent overlapping runs
) as dag:

    reindex_task = PythonOperator(
        task_id="reindex_all_matters",
        python_callable=trigger_all_matters_reindex,
        doc_md="""
        ## Re-index all active matters

        Fetches the list of active matters from the API, then calls the agent
        backend's `/ingest` endpoint for each matter to ensure new and modified
        documents are indexed in Pinecone.
        """,
    )

    reindex_task
