"""User profile service."""

from uuid import uuid4

from app.domain.repositories.user_profile_repository import UserProfileRepository


class UserProfileService:
    """Service for user profile operations."""

    def __init__(self, user_profile_repo: UserProfileRepository):
        self.user_profile_repo = user_profile_repo

    async def get_profile(self) -> dict:
        """Get the default user profile, creating an empty one if it doesn't exist."""
        profile = await self.user_profile_repo.get_default_profile()

        if not profile:
            # Return empty profile structure
            return {
                "id": uuid4(),
                "settings": {},
            }

        return profile

    async def update_profile(self, settings: dict) -> dict:
        """Update the user profile settings."""
        return await self.user_profile_repo.create_or_update_profile(
            settings=settings,
        )
