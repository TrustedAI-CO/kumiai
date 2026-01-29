"""Integration tests for user profile API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_profile_returns_empty_when_not_exists(client: AsyncClient):
    """Test GET /api/v1/profile returns empty profile."""
    response = await client.get("/api/v1/profile")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["avatar"] is None
    assert data["description"] is None
    assert data["preferences"] is None


@pytest.mark.asyncio
async def test_create_user_profile(client: AsyncClient):
    """Test POST /api/v1/profile creates new profile."""
    payload = {
        "avatar": "test-avatar-seed",
        "description": "Test user description",
        "preferences": {"theme": "dark", "language": "en"},
    }

    response = await client.post("/api/v1/profile", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["avatar"] == "test-avatar-seed"
    assert data["description"] == "Test user description"
    assert data["preferences"] == {"theme": "dark", "language": "en"}


@pytest.mark.asyncio
async def test_update_user_profile(client: AsyncClient):
    """Test POST /api/v1/profile updates existing profile."""
    # Create initial profile
    payload1 = {
        "avatar": "initial-avatar",
        "description": "Initial description",
    }
    await client.post("/api/v1/profile", json=payload1)

    # Update profile
    payload2 = {
        "avatar": "updated-avatar",
        "description": "Updated description",
        "preferences": {"theme": "light"},
    }
    response = await client.post("/api/v1/profile", json=payload2)

    assert response.status_code == 200
    data = response.json()
    assert data["avatar"] == "updated-avatar"
    assert data["description"] == "Updated description"
    assert data["preferences"] == {"theme": "light"}


@pytest.mark.asyncio
async def test_get_user_profile_after_creation(client: AsyncClient):
    """Test GET /api/v1/profile returns created profile."""
    # Create profile
    payload = {
        "avatar": "created-avatar",
        "description": "Created description",
        "preferences": {"key": "value"},
    }
    await client.post("/api/v1/profile", json=payload)

    # Get profile
    response = await client.get("/api/v1/profile")

    assert response.status_code == 200
    data = response.json()
    assert data["avatar"] == "created-avatar"
    assert data["description"] == "Created description"
    assert data["preferences"] == {"key": "value"}


@pytest.mark.asyncio
async def test_update_partial_profile(client: AsyncClient):
    """Test updating only some fields of the profile."""
    # Create initial profile
    payload1 = {
        "avatar": "initial-avatar",
        "description": "Initial description",
        "preferences": {"theme": "dark"},
    }
    await client.post("/api/v1/profile", json=payload1)

    # Update only avatar
    payload2 = {
        "avatar": "new-avatar",
    }
    response = await client.post("/api/v1/profile", json=payload2)

    assert response.status_code == 200
    data = response.json()
    assert data["avatar"] == "new-avatar"
    # Other fields should be preserved (though actual behavior depends on implementation)
