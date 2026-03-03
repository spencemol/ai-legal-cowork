"""Unit tests for the MCP HTTP client (task 4.8).

Task 4.8: MCP client module — call Node REST API tools from Python (HTTP transport)

All httpx calls are fully mocked.

RED: These tests fail until app/mcp_client/client.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.mcp_client.client import MCPClient


class TestMCPClientInit:
    def test_instantiation(self):
        client = MCPClient(base_url="http://localhost:3000")
        assert client is not None

    def test_base_url_stored(self):
        client = MCPClient(base_url="http://api:3000")
        assert "api" in client.base_url or "3000" in client.base_url

    def test_jwt_token_stored(self):
        client = MCPClient(base_url="http://localhost:3000", jwt_token="tok123")
        assert client.jwt_token == "tok123"

    def test_no_token_by_default(self):
        client = MCPClient(base_url="http://localhost:3000")
        assert client.jwt_token is None


class TestMCPClientCallTool:
    async def test_call_tool_returns_dict(self, mocker):
        """call_tool() returns a parsed dict from the MCP response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"id": "matter-001", "name": "Smith v. Jones"}'}]
        }
        mock_response.raise_for_status = MagicMock()

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        result = await client.call_tool("get_matter", {"matter_id": "matter-001"})

        assert isinstance(result, dict)

    async def test_call_tool_get_matter(self, mocker):
        """call_tool with get_matter returns matter data."""
        matter_data = {"id": "matter-001", "name": "Smith v. Jones", "status": "active"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"id": "matter-001", "name": "Smith v. Jones", "status": "active"}'}]
        }
        mock_response.raise_for_status = MagicMock()

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        result = await client.call_tool("get_matter", {"matter_id": "matter-001"})

        assert result.get("id") == "matter-001"

    async def test_call_tool_sends_correct_payload(self, mocker):
        """Payload sent to MCP endpoint contains tool name and arguments."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "{}"}]
        }
        mock_response.raise_for_status = MagicMock()

        post_mock = mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        await client.call_tool("list_matters", {"limit": 10})

        call_kwargs = post_mock.call_args
        sent_json = call_kwargs.kwargs.get("json") or {}
        assert "name" in sent_json or "tool" in sent_json or "method" in sent_json

    async def test_call_tool_includes_auth_header(self, mocker):
        """JWT token is included in the Authorization header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "{}"}]
        }
        mock_response.raise_for_status = MagicMock()

        post_mock = mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000", jwt_token="my-jwt-token")
        await client.call_tool("get_matter", {"matter_id": "m-001"})

        call_kwargs = post_mock.call_args
        headers = call_kwargs.kwargs.get("headers") or {}
        assert any("bearer" in str(v).lower() or "my-jwt-token" in str(v) for v in headers.values())

    async def test_call_tool_raises_on_error_response(self, mocker):
        """call_tool raises an exception on non-200 response."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=mock_response,
        )

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        with pytest.raises(Exception):
            await client.call_tool("get_matter", {"matter_id": "bad-id"})

    async def test_call_tool_not_found_returns_none_or_raises(self, mocker):
        """Tool returning isError=true is handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isError": True,
            "content": [{"type": "text", "text": "Matter not found"}],
        }
        mock_response.raise_for_status = MagicMock()

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        result = await client.call_tool("get_matter", {"matter_id": "nonexistent"})
        # Should return None or raise a specific exception
        assert result is None or isinstance(result, dict)


class TestMCPClientGetMatter:
    async def test_get_matter_convenience_method(self, mocker):
        """get_matter() wraps call_tool('get_matter', ...)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '{"id": "matter-001", "name": "Smith"}'}]
        }
        mock_response.raise_for_status = MagicMock()

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        result = await client.get_matter("matter-001")

        assert result is not None
        assert result.get("id") == "matter-001"

    async def test_get_matter_assignments_convenience_method(self, mocker):
        """get_matter_assignments() wraps call_tool(...)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": '[{"matter_id": "matter-001", "user_id": "user-001"}]'}]
        }
        mock_response.raise_for_status = MagicMock()

        mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

        client = MCPClient(base_url="http://localhost:3000")
        result = await client.get_matter_assignments("user-001")

        assert result is not None
