"""HTTP endpoint tests for POST /ingest (task 3.9).

RED: These tests fail until app/routes/ingest.py and its FastAPI wiring exist.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.models import IngestionResult


class TestIngestEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_post_ingest_returns_200(self, client, tmp_path):
        """POST /ingest with valid payload returns 200."""
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF test")

        mock_result = IngestionResult(
            matter_id="matter-001",
            total_files=1,
            processed=1,
            skipped=0,
            failed=0,
            document_ids=["doc-001"],
        )

        with patch("app.routes.ingest.run_ingestion", new_callable=AsyncMock, return_value=mock_result):
            response = client.post(
                "/ingest",
                json={"file_paths": [str(f)], "matter_id": "matter-001"},
            )

        assert response.status_code == 200

    def test_post_ingest_response_schema(self, client, tmp_path):
        """Response must include total_files, processed, skipped, failed, document_ids."""
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF test")

        mock_result = IngestionResult(
            matter_id="matter-001",
            total_files=1,
            processed=1,
            skipped=0,
            failed=0,
            document_ids=["doc-xyz"],
        )

        with patch("app.routes.ingest.run_ingestion", new_callable=AsyncMock, return_value=mock_result):
            response = client.post(
                "/ingest",
                json={"file_paths": [str(f)], "matter_id": "matter-001"},
            )

        body = response.json()
        assert "total_files" in body
        assert "processed" in body
        assert "skipped" in body
        assert "failed" in body
        assert "document_ids" in body

    def test_post_ingest_missing_matter_id_returns_422(self, client, tmp_path):
        """Missing matter_id → 422 Unprocessable Entity (Pydantic validation)."""
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF test")

        response = client.post(
            "/ingest",
            json={"file_paths": [str(f)]},  # missing matter_id
        )

        assert response.status_code == 422

    def test_post_ingest_empty_file_paths_still_valid(self, client):
        """Empty file_paths list is a valid request (returns processed=0)."""
        mock_result = IngestionResult(
            matter_id="matter-001",
            total_files=0,
            processed=0,
            skipped=0,
            failed=0,
            document_ids=[],
        )

        with patch("app.routes.ingest.run_ingestion", new_callable=AsyncMock, return_value=mock_result):
            response = client.post(
                "/ingest",
                json={"file_paths": [], "matter_id": "matter-001"},
            )

        assert response.status_code == 200
        assert response.json()["total_files"] == 0
