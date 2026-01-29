"""Integration tests for agent API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestAgentsAPI:
    """Test agent API endpoints."""

    @pytest.mark.asyncio
    async def test_create_agent_success(self, client, tmp_agents_dir):
        """Test POST /api/v1/agents."""
        unique_id = uuid4().hex[:8]
        response = await client.post(
            "/api/v1/agents",
            json={
                "name": f"Test Agent {unique_id}",
                "tags": ["test", "api"],
                "skills": ["skill-1"],
                "allowed_tools": ["Read", "Write"],
                "allowed_mcps": [],
                "icon_color": "#4A90E2",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "test" in data["tags"]
        assert "skill-1" in data["skills"]
        assert "Read" in data["allowed_tools"]
        assert data["icon_color"] == "#4A90E2"

        # Verify CLAUDE.md was created
        agent_id = data["id"]
        claude_md = tmp_agents_dir / agent_id / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "name:" in content

    @pytest.mark.asyncio
    async def test_get_agent_success(self, client, agent):
        """Test GET /api/v1/agents/{id}."""
        response = await client.get(f"/api/v1/agents/{agent.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(agent.id)

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, client):
        """Test getting non-existent agent."""
        response = await client.get("/api/v1/agents/nonexistent-agent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_agents(self, client, agent):
        """Test GET /api/v1/agents."""
        response = await client.get("/api/v1/agents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_search_agents_by_tags(self, client, agent):
        """Test GET /api/v1/agents/search."""
        response = await client.get("/api/v1/agents/search?tags=python&match_all=false")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_update_agent_success(self, client, agent):
        """Test PATCH /api/v1/agents/{id}."""
        response = await client.patch(
            f"/api/v1/agents/{agent.id}",
            json={"name": f"Updated Agent {uuid4().hex[:8]}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated Agent" in data["name"]

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, client, agent):
        """Test DELETE /api/v1/agents/{id}."""
        response = await client.delete(f"/api/v1/agents/{agent.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_create_agent_without_id(self, client):
        """Test creating agent with auto-generated ID from name."""
        response = await client.post(
            "/api/v1/agents",
            json={
                "name": f"Auto ID Agent {uuid4().hex[:8]}",
                "tags": ["test"],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "auto-id-agent-" in data["id"]
        assert data["file_path"].rstrip("/").endswith(data["id"])

    @pytest.mark.asyncio
    async def test_create_agent_with_custom_id(self, client):
        """Test creating agent with custom ID."""
        custom_id = f"custom-agent-{uuid4().hex[:8]}"
        response = await client.post(
            "/api/v1/agents",
            json={
                "id": custom_id,
                "name": f"Agent With Custom ID {uuid4().hex[:8]}",
                "tags": ["test"],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == custom_id
        assert custom_id in data["file_path"]

    @pytest.mark.asyncio
    async def test_update_agent_with_put(self, client, agent):
        """Test updating agent using PUT method."""
        response = await client.put(
            f"/api/v1/agents/{agent.id}",
            json={"name": f"Updated via PUT {uuid4().hex[:8]}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated via PUT" in data["name"]

    @pytest.mark.asyncio
    async def test_load_agent_content(self, client, agent):
        """Test GET /api/v1/agents/{id}/content - load CLAUDE.md for AI context."""
        response = await client.get(f"/api/v1/agents/{agent.id}/content")

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "# Test Agent" in content or "Test Agent" in content
        assert "---" in content  # YAML frontmatter marker

    @pytest.mark.asyncio
    async def test_load_agent_content_not_found(self, client):
        """Test loading content for non-existent agent."""
        response = await client.get("/api/v1/agents/nonexistent/content")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_load_supporting_doc(self, client, agent, tmp_agents_dir):
        """Test GET /api/v1/agents/{id}/docs/{doc_path} - load supporting docs."""
        # Create a supporting document
        agent_dir = tmp_agents_dir / agent.id
        doc_file = agent_dir / "REFERENCE.md"
        doc_file.write_text("# Reference Documentation\\n\\nThis is a reference doc.")

        response = await client.get(f"/api/v1/agents/{agent.id}/docs/REFERENCE.md")

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Reference Documentation" in content

    @pytest.mark.asyncio
    async def test_load_nested_supporting_doc(self, client, agent, tmp_agents_dir):
        """Test loading nested supporting docs."""
        # Create nested directory structure
        agent_dir = tmp_agents_dir / agent.id
        nested_dir = agent_dir / "docs" / "api"
        nested_dir.mkdir(parents=True, exist_ok=True)
        doc_file = nested_dir / "endpoints.md"
        doc_file.write_text("# API Endpoints\\n\\nEndpoint documentation.")

        response = await client.get(
            f"/api/v1/agents/{agent.id}/docs/docs/api/endpoints.md"
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Endpoint documentation" in content

    @pytest.mark.asyncio
    async def test_load_supporting_doc_path_traversal_blocked(self, client, agent):
        """Test that path traversal attempts are blocked."""
        response = await client.get(
            f"/api/v1/agents/{agent.id}/docs/../../../etc/passwd"
        )

        # FastAPI normalizes the path before reaching our handler, resulting in 404
        assert response.status_code == status.HTTP_404_NOT_FOUND
