"""Integration tests for session API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestSessionsAPI:
    """Test session API endpoints."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, client, agent, project):
        """Test POST /api/v1/sessions - successful creation."""
        response = await client.post(
            "/api/v1/sessions",
            json={
                "agent_id": agent.id,
                "project_id": str(project.id),
                "session_type": "pm",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["agent_id"] == agent.id
        assert data["project_id"] == str(project.id)

    @pytest.mark.asyncio
    async def test_get_session_success(self, client, session):
        """Test GET /api/v1/sessions/{id}."""
        response = await client.get(f"/api/v1/sessions/{session.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(session.id)

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        """Test getting non-existent session."""
        response = await client.get(f"/api/v1/sessions/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_sessions(self, client, session):
        """Test GET /api/v1/sessions."""
        response = await client.get("/api/v1/sessions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_project(self, client, session, project):
        """Test listing sessions filtered by project."""
        response = await client.get(f"/api/v1/sessions?project_id={project.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_status(self, client, session):
        """Test listing sessions filtered by status."""
        response = await client.get(f"/api/v1/sessions?status={session.status}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_start_session_success(self, client, session):
        """Test POST /api/v1/sessions/{id}/start."""
        response = await client.post(f"/api/v1/sessions/{session.id}/start")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["thinking", "working"]

    @pytest.mark.asyncio
    async def test_start_session_invalid_state(self, client, session):
        """Test starting session from invalid state."""
        # Start once
        await client.post(f"/api/v1/sessions/{session.id}/start")

        # Try to start again - should fail with 409 Conflict
        response = await client.post(f"/api/v1/sessions/{session.id}/start")

        # InvalidStateTransition should return 409 Conflict
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_complete_session_success(self, client, session):
        """Test POST /api/v1/sessions/{id}/complete."""
        # Start session first
        await client.post(f"/api/v1/sessions/{session.id}/start")

        # Complete it
        response = await client.post(f"/api/v1/sessions/{session.id}/complete")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_interrupt_session_success(self, client, session):
        """Test POST /api/v1/sessions/{id}/interrupt."""
        # Start session first (interrupt only works from working state)
        await client.post(f"/api/v1/sessions/{session.id}/start")

        # Interrupt it
        response = await client.post(f"/api/v1/sessions/{session.id}/interrupt")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "interrupted"

    @pytest.mark.asyncio
    async def test_resume_session_success(self, client, session):
        """Test POST /api/v1/sessions/{id}/resume."""
        # Start and complete session first (resume only works from completed/error states)
        await client.post(f"/api/v1/sessions/{session.id}/start")
        await client.post(f"/api/v1/sessions/{session.id}/complete")

        # Resume it (should transition from completed back to idle)
        response = await client.post(f"/api/v1/sessions/{session.id}/resume")

        # Resume should work from completed state
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "idle"

    @pytest.mark.asyncio
    async def test_resume_interrupted_session_success(self, client, session):
        """Test POST /api/v1/sessions/{id}/resume after interrupt."""
        # Start session and interrupt it
        await client.post(f"/api/v1/sessions/{session.id}/start")
        await client.post(f"/api/v1/sessions/{session.id}/interrupt")

        # Resume it
        response = await client.post(f"/api/v1/sessions/{session.id}/resume")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "idle"

    @pytest.mark.asyncio
    async def test_delete_session_success(self, client, session):
        """Test DELETE /api/v1/sessions/{id}."""
        response = await client.delete(f"/api/v1/sessions/{session.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.skip(
        reason="Requires Claude SDK client and complex executor mocking - needs proper E2E test setup"
    )
    @pytest.mark.asyncio
    async def test_execute_query_sse_streaming(self, client, session):
        """Test POST /api/v1/sessions/{id}/query - SSE streaming."""
        response = await client.post(
            f"/api/v1/sessions/{session.id}/query",
            json={"query": "test query"},
        )

        # SSE endpoint should return 200 OK
        assert response.status_code == status.HTTP_200_OK
