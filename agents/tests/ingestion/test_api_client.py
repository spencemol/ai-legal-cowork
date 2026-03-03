"""Unit tests for the REST API client (tasks 3.6, 3.7).

Uses pytest-mock / respx to intercept httpx calls without a real Node API.

RED: These tests fail until app/rag/api_client.py is implemented.
"""

import pytest

from app.rag.api_client import RestAPIClient
from app.rag.models import DocumentInfo


@pytest.fixture
def base_url():
    return "http://localhost:3000"


@pytest.fixture
def auth_token():
    return "test-jwt-token"


class TestRestAPIClientGetDocuments:
    async def test_returns_list_of_document_info(self, base_url, auth_token, mocker):
        mock_response = mocker.MagicMock()
        mock_response.json.return_value = [
            {
                "id": "doc-001",
                "fileName": "brief.pdf",
                "filePath": "/docs/brief.pdf",
                "fileHash": "abc123",
                "status": "indexed",
                "matterId": "matter-001",
            }
        ]
        mock_response.raise_for_status = mocker.MagicMock()

        mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

        client = RestAPIClient(base_url=base_url, jwt_token=auth_token)
        docs = await client.get_documents_for_matter("matter-001")

        assert len(docs) == 1
        assert isinstance(docs[0], DocumentInfo)
        assert docs[0].id == "doc-001"
        assert docs[0].file_hash == "abc123"

    async def test_returns_empty_list_when_no_documents(self, base_url, mocker):
        mock_response = mocker.MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = mocker.MagicMock()

        mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

        client = RestAPIClient(base_url=base_url)
        docs = await client.get_documents_for_matter("matter-empty")
        assert docs == []


class TestRestAPIClientRegisterDocument:
    async def test_returns_document_id(self, base_url, auth_token, mocker):
        mock_response = mocker.MagicMock()
        mock_response.json.return_value = {"id": "new-doc-id"}
        mock_response.raise_for_status = mocker.MagicMock()

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = RestAPIClient(base_url=base_url, jwt_token=auth_token)
        doc_id = await client.register_document(
            matter_id="matter-001",
            file_name="contract.pdf",
            file_path="/legal/contract.pdf",
            file_hash="deadbeef",
            mime_type="application/pdf",
        )

        assert doc_id == "new-doc-id"

    async def test_sends_correct_payload(self, base_url, mocker):
        mock_response = mocker.MagicMock()
        mock_response.json.return_value = {"id": "doc-xyz"}
        mock_response.raise_for_status = mocker.MagicMock()

        post_mock = mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = RestAPIClient(base_url=base_url)
        await client.register_document(
            matter_id="m-001",
            file_name="motion.pdf",
            file_path="/legal/motion.pdf",
            file_hash="hash123",
            mime_type="application/pdf",
        )

        call_kwargs = post_mock.call_args
        sent_json = call_kwargs.kwargs.get("json", {})
        # Verify required fields are present (field names are camelCase for the Node API)
        assert "fileName" in sent_json or "file_name" in sent_json
        assert "fileHash" in sent_json or "file_hash" in sent_json


class TestRestAPIClientUpdateStatus:
    async def test_update_status_to_indexed(self, base_url, mocker):
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status = mocker.MagicMock()

        patch_mock = mocker.patch("httpx.AsyncClient.patch", return_value=mock_response)

        client = RestAPIClient(base_url=base_url)
        await client.update_document_status("doc-001", "indexed")

        patch_mock.assert_called_once()

    async def test_update_status_to_failed(self, base_url, mocker):
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status = mocker.MagicMock()

        mocker.patch("httpx.AsyncClient.patch", return_value=mock_response)

        client = RestAPIClient(base_url=base_url)
        # Should not raise
        await client.update_document_status("doc-001", "failed")

    async def test_sends_status_in_payload(self, base_url, mocker):
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status = mocker.MagicMock()

        patch_mock = mocker.patch("httpx.AsyncClient.patch", return_value=mock_response)

        client = RestAPIClient(base_url=base_url)
        await client.update_document_status("doc-001", "processing")

        call_kwargs = patch_mock.call_args
        sent_json = call_kwargs.kwargs.get("json") or {}
        assert "status" in sent_json
        assert sent_json["status"] == "processing"
