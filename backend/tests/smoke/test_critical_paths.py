"""
Smoke Tests - Critical User Paths

Tests that verify the most important user workflows don't crash.
These are end-to-end smoke tests for critical functionality.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestProjectWorkflow:
    """Test basic project operations don't crash."""

    def test_can_list_projects(self, client):
        """Verify listing projects works."""
        response = client.get("/api/v1/projects")

        # Should either succeed or fail gracefully
        assert response.status_code in [
            200,
            401,
            403,
            404,
        ], "List projects should not crash"

        if response.status_code == 200:
            # If it succeeds, should return a list
            data = response.json()
            assert isinstance(data, list), "Should return a list of projects"

    def test_can_access_project_by_id(self, client):
        """Verify accessing a project by ID works."""
        # First get list of projects
        response = client.get("/api/v1/projects")

        if response.status_code == 200 and response.json():
            # If we have projects, try to get one
            projects = response.json()
            if projects:
                project_id = projects[0].get("id") or projects[0].get("name")
                detail_response = client.get(f"/api/v1/projects/{project_id}")

                assert detail_response.status_code in [
                    200,
                    404,
                ], "Get project detail should not crash"


class TestAgentWorkflow:
    """Test basic agent operations don't crash."""

    def test_can_list_agents(self, client):
        """Verify listing agents works."""
        response = client.get("/api/v1/agents")

        assert response.status_code in [
            200,
            401,
            403,
            404,
        ], "List agents should not crash"

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return a list of agents"


class TestSkillWorkflow:
    """Test basic skill operations don't crash."""

    def test_can_list_skills(self, client):
        """Verify listing skills works."""
        response = client.get("/api/v1/skills")

        assert response.status_code in [
            200,
            401,
            403,
            404,
        ], "List skills should not crash"

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return a list of skills"


class TestSessionWorkflow:
    """Test basic session operations don't crash."""

    def test_can_list_sessions(self, client):
        """Verify listing sessions works."""
        response = client.get("/api/v1/sessions")

        assert response.status_code in [
            200,
            401,
            403,
            404,
        ], "List sessions should not crash"

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return a list of sessions"


class TestErrorHandling:
    """Test that errors are handled gracefully."""

    def test_404_not_found(self, client):
        """Verify 404 errors are handled properly."""
        response = client.get("/api/v1/nonexistent-endpoint")

        assert response.status_code == 404, "Should return 404 for unknown endpoints"

    def test_invalid_project_id(self, client):
        """Verify invalid IDs are handled gracefully."""
        response = client.get("/api/v1/projects/definitely-does-not-exist-12345")

        # Should either be 404, 400, or 422 (validation error), not 500
        assert response.status_code in [
            400,
            404,
            422,
        ], "Invalid IDs should not cause server errors"

    def test_malformed_request_handled(self, client):
        """Verify malformed requests don't crash the server."""
        # Send invalid JSON
        response = client.post(
            "/api/v1/sessions",
            headers={"Content-Type": "application/json"},
            content="{invalid json}",
        )

        # Should be 400 or 422 (validation error), not 500
        assert response.status_code in [
            400,
            422,
        ], "Malformed requests should be rejected gracefully"


# Minimal test to verify the app doesn't immediately crash
class TestSanity:
    """Absolute bare minimum - does the app even start?"""

    def test_app_responds(self, client):
        """The most basic test - does ANY endpoint respond?"""
        response = client.get("/")

        # We don't care what the response is, just that it doesn't crash
        assert response.status_code < 500, (
            "Application should respond without server errors"
        )


# Run with:
# pytest tests/smoke/test_critical_paths.py -v
