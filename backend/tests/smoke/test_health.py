"""
Smoke Tests - Health & Basic Functionality

These tests verify that the basic application functionality works.
They should be fast and catch catastrophic failures.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestApplicationHealth:
    """Test basic application health and startup."""

    def test_app_starts_without_crash(self, client):
        """Verify the application starts and responds to requests."""
        response = client.get("/api/health")
        assert response.status_code == 200, "Health endpoint should return 200"

    def test_health_endpoint_response_format(self, client):
        """Verify health endpoint returns expected structure."""
        response = client.get("/api/health")
        data = response.json()

        assert "status" in data, "Health response should include status"
        # In test environment, may be degraded due to missing API key
        assert data["status"] in [
            "healthy",
            "degraded",
        ], "Application status should be healthy or degraded"

    def test_api_docs_accessible(self, client):
        """Verify API documentation is accessible."""
        response = client.get("/api/docs")
        assert response.status_code == 200, "API docs should be accessible"

    def test_openapi_spec_accessible(self, client):
        """Verify OpenAPI spec is available."""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200, "OpenAPI spec should be accessible"

        spec = response.json()
        assert "openapi" in spec, "Should return valid OpenAPI spec"
        assert spec["info"]["title"] == "KumiAI Backend API"


class TestCriticalEndpoints:
    """Test that critical API endpoints are accessible."""

    def test_projects_endpoint_exists(self, client):
        """Verify projects endpoint is accessible (may be empty)."""
        response = client.get("/api/v1/projects")
        # Accept both 200 (success) and 401/403 (auth required)
        assert response.status_code in [200, 401, 403], "Projects endpoint should exist"

    def test_agents_endpoint_exists(self, client):
        """Verify agents endpoint is accessible."""
        response = client.get("/api/v1/agents")
        assert response.status_code in [200, 401, 403], "Agents endpoint should exist"

    def test_skills_endpoint_exists(self, client):
        """Verify skills endpoint is accessible."""
        response = client.get("/api/v1/skills")
        assert response.status_code in [200, 401, 403], "Skills endpoint should exist"

    def test_sessions_endpoint_exists(self, client):
        """Verify sessions endpoint is accessible."""
        response = client.get("/api/v1/sessions")
        assert response.status_code in [200, 401, 403], "Sessions endpoint should exist"


class TestConfiguration:
    """Test that configuration is properly loaded."""

    def test_cors_middleware_enabled(self, client):
        """Verify CORS headers are present."""
        response = client.get(
            "/api/health", headers={"Origin": "http://localhost:1420"}
        )
        # CORS headers should be present in response
        assert "access-control-allow-origin" in [
            h.lower() for h in response.headers.keys()
        ], "CORS should be configured"

    def test_app_metadata(self, client):
        """Verify application metadata is correct."""
        response = client.get("/api/openapi.json")
        spec = response.json()

        assert spec["info"]["version"] == "2.0.0", "Version should be 2.0.0"
        assert "description" in spec["info"], "Should have description"


class TestDatabaseConnection:
    """Test database connectivity (basic smoke test)."""

    def test_database_accessible(self, client):
        """Verify database operations don't crash the app."""
        # Making any request that touches the database
        # If database is broken, this will fail
        response = client.get("/api/v1/projects")

        # We don't care about the exact response, just that it doesn't crash
        assert response.status_code < 500, (
            "Database operations should not cause server errors"
        )


# Run these tests with:
# pytest tests/smoke/ -v
# pytest tests/smoke/test_health.py -v
# pytest tests/smoke/test_health.py::TestApplicationHealth -v
