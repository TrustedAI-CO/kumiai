"""Integration tests for task API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestTasksAPI:
    """Test task API endpoints."""

    @pytest.mark.asyncio
    async def test_create_task_success(self, client, project):
        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Implement auth flow", "description": "Auth description"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Implement auth flow"
        assert data["description"] == "Auth description"
        assert data["status"] == "open"
        assert data["project_id"] == str(project.id)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_task_name_required(self, client, project):
        response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"description": "No name"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_task_project_not_found(self, client):
        response = await client.post(
            f"/api/v1/projects/{uuid4()}/tasks",
            json={"name": "Task"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_tasks_for_project(self, client, project):
        await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Task 1"},
        )
        await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Task 2"},
        )

        response = await client.get(f"/api/v1/projects/{project.id}/tasks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_task_success(self, client, project):
        create_response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Get me"},
        )
        task_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/tasks/{task_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client):
        response = await client.get(f"/api/v1/tasks/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_task_success(self, client, project):
        create_response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Old name"},
        )
        task_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"name": "New name", "status": "in_progress"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New name"
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_delete_task_success(self, client, project):
        create_response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Delete me"},
        )
        task_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/tasks/{task_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        get_response = await client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_session_with_task_id(self, client, project):
        task_response = await client.post(
            f"/api/v1/projects/{project.id}/tasks",
            json={"name": "Task with sessions"},
        )
        task_id = task_response.json()["id"]

        session_response = await client.post(
            "/api/v1/sessions",
            json={
                "agent_id": "test-agent",
                "project_id": str(project.id),
                "session_type": "specialist",
                "task_id": task_id,
            },
        )

        assert session_response.status_code == status.HTTP_201_CREATED
        assert session_response.json()["task_id"] == task_id

    @pytest.mark.asyncio
    async def test_create_session_without_task_id_still_works(self, client, project):
        session_response = await client.post(
            "/api/v1/sessions",
            json={
                "agent_id": "test-agent",
                "project_id": str(project.id),
                "session_type": "specialist",
            },
        )

        assert session_response.status_code == status.HTTP_201_CREATED
        assert session_response.json().get("task_id") is None
