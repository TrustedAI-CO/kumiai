"""Tests for UserProfileService."""

import pytest
from uuid import uuid4

from app.application.services.user_profile_service import UserProfileService


class MockUserProfileRepository:
    """Mock repository for testing."""

    def __init__(self):
        self.profile = None

    async def get_default_profile(self):
        return self.profile

    async def create_or_update_profile(
        self, avatar=None, description=None, preferences=None
    ):
        self.profile = {
            "id": uuid4(),
            "avatar": avatar,
            "description": description,
            "preferences": preferences,
        }
        return self.profile


@pytest.mark.asyncio
async def test_get_profile_returns_empty_when_none_exists():
    """Test that get_profile returns empty profile when none exists."""
    repo = MockUserProfileRepository()
    service = UserProfileService(user_profile_repo=repo)

    profile = await service.get_profile()

    assert profile["avatar"] is None
    assert profile["description"] is None
    assert profile["preferences"] is None


@pytest.mark.asyncio
async def test_get_profile_returns_existing_profile():
    """Test that get_profile returns existing profile."""
    repo = MockUserProfileRepository()
    repo.profile = {
        "id": uuid4(),
        "avatar": "test-avatar",
        "description": "Test description",
        "preferences": {"theme": "dark"},
    }
    service = UserProfileService(user_profile_repo=repo)

    profile = await service.get_profile()

    assert profile["avatar"] == "test-avatar"
    assert profile["description"] == "Test description"
    assert profile["preferences"] == {"theme": "dark"}


@pytest.mark.asyncio
async def test_update_profile_creates_new_profile():
    """Test that update_profile creates a new profile."""
    repo = MockUserProfileRepository()
    service = UserProfileService(user_profile_repo=repo)

    profile = await service.update_profile(
        avatar="new-avatar",
        description="New description",
        preferences={"theme": "light"},
    )

    assert profile["avatar"] == "new-avatar"
    assert profile["description"] == "New description"
    assert profile["preferences"] == {"theme": "light"}


@pytest.mark.asyncio
async def test_update_profile_updates_existing_profile():
    """Test that update_profile updates existing profile."""
    repo = MockUserProfileRepository()
    repo.profile = {
        "id": uuid4(),
        "avatar": "old-avatar",
        "description": "Old description",
        "preferences": {"theme": "dark"},
    }
    service = UserProfileService(user_profile_repo=repo)

    profile = await service.update_profile(
        avatar="updated-avatar",
        description="Updated description",
    )

    assert profile["avatar"] == "updated-avatar"
    assert profile["description"] == "Updated description"
    # preferences should remain unchanged (not passed in update)


@pytest.mark.asyncio
async def test_update_profile_with_none_values():
    """Test that update_profile handles None values correctly."""
    repo = MockUserProfileRepository()
    service = UserProfileService(user_profile_repo=repo)

    profile = await service.update_profile(
        avatar=None,
        description=None,
        preferences=None,
    )

    assert profile["avatar"] is None
    assert profile["description"] is None
    assert profile["preferences"] is None
