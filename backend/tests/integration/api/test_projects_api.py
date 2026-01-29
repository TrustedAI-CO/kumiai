"""Integration tests for project API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestProjectsAPI:
    """Test project API endpoints."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, client):
        """Test POST /api/v1/projects - successful creation without explicit path."""
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": f"Test Project {uuid4().hex[:8]}",
                "description": "A test project",
                # No path provided - should use ~/.kumiai/projects/{sanitized-name}
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] == "A test project"
        assert "id" in data
        # Verify path was auto-generated
        assert data["path"]  # Should have a path
        assert "projects/" in data["path"]  # Should be in projects dir
        assert "test-project" in data["path"]  # Should contain sanitized name

    @pytest.mark.asyncio
    async def test_get_project_success(self, client, project):
        """Test GET /api/v1/projects/{id}."""
        response = await client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(project.id)

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client):
        """Test getting non-existent project."""
        response = await client.get(f"/api/v1/projects/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_projects(self, client, project):
        """Test GET /api/v1/projects."""
        response = await client.get("/api/v1/projects")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_update_project_success(self, client, project):
        """Test PATCH /api/v1/projects/{id}."""
        response = await client.patch(
            f"/api/v1/projects/{project.id}",
            json={"name": f"Updated Project {uuid4().hex[:8]}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated Project" in data["name"]

    @pytest.mark.asyncio
    async def test_assign_pm_success(self, client, project, agent):
        """Test POST /api/v1/projects/{id}/assign-pm."""
        response = await client.post(
            f"/api/v1/projects/{project.id}/assign-pm",
            json={"pm_agent_id": agent.id},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pm_agent_id"] == agent.id

    @pytest.mark.asyncio
    async def test_remove_pm_success(self, client, project):
        """Test DELETE /api/v1/projects/{id}/pm."""
        response = await client.delete(f"/api/v1/projects/{project.id}/pm")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pm_agent_id"] is None

    @pytest.mark.asyncio
    async def test_delete_project_success(self, client, project):
        """Test DELETE /api/v1/projects/{id}."""
        response = await client.delete(f"/api/v1/projects/{project.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
