"""Integration tests for MCP API endpoints."""

import pytest
from fastapi import status


class TestMcpAPI:
    """Test MCP API endpoints."""

    @pytest.mark.asyncio
    async def test_list_mcp_servers(self, client):
        """Test GET /api/v1/mcp/servers."""
        response = await client.get("/api/v1/mcp/servers")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Returns MCP servers from ~/.claude.json (if configured)
        # Test just validates the endpoint works and returns list structure
        for server in data:
            assert "id" in server
            assert "name" in server
            assert "command" in server
