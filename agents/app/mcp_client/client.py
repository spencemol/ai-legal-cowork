"""MCP HTTP client — call Node REST API tools from Python (task 4.8).

The Node REST API exposes an MCP endpoint at ``/mcp`` that accepts JSON-RPC
style ``tools/call`` requests.  This client wraps httpx to provide a simple
async interface for calling individual MCP tools and parsing results.
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class MCPClient:
    """Async HTTP client for calling Node REST API MCP tools.

    Parameters
    ----------
    base_url:
        Base URL of the Node REST API (e.g. ``http://localhost:3000``).
    jwt_token:
        Optional JWT token sent as ``Authorization: Bearer <token>``.
    timeout:
        Request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        jwt_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.jwt_token = jwt_token
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Generic tool call
    # ------------------------------------------------------------------

    async def call_tool(self, tool_name: str, arguments: dict) -> Any | None:
        """Call a named MCP tool and return the parsed result.

        Parameters
        ----------
        tool_name:
            The MCP tool name (e.g. ``"get_matter"``).
        arguments:
            Tool argument dict.

        Returns
        -------
        Any
            Parsed JSON value from the first ``content`` block, or ``None``
            if the response has ``isError: true``.

        Raises
        ------
        httpx.HTTPStatusError
            On non-2xx HTTP responses.
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        payload = {
            "method": "tools/call",
            "name": tool_name,
            "params": {"name": tool_name, "arguments": arguments},
        }

        async with httpx.AsyncClient(timeout=self._timeout) as http:
            response = await http.post(
                f"{self.base_url}/mcp",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        body = response.json()

        # Handle MCP-level errors (isError: true in response body)
        if body.get("isError"):
            return None

        # Extract text from first content block and parse as JSON
        content_blocks = body.get("content", [])
        if not content_blocks:
            return None

        first_block = content_blocks[0]
        text = first_block.get("text", "")

        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return text

    # ------------------------------------------------------------------
    # Convenience wrappers for commonly used tools
    # ------------------------------------------------------------------

    async def get_matter(self, matter_id: str) -> dict | None:
        """Call the ``get_matter`` MCP tool."""
        return await self.call_tool("get_matter", {"matter_id": matter_id})

    async def get_matter_assignments(self, user_id: str) -> list | None:
        """Call the ``get_matter_assignments`` MCP tool for a user."""
        return await self.call_tool("get_matter_assignments", {"user_id": user_id})

    async def list_matters(self, limit: int = 50) -> list | None:
        """Call the ``list_matters`` MCP tool."""
        return await self.call_tool("list_matters", {"limit": limit})
