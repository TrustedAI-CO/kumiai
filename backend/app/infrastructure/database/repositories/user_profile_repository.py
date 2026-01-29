"""User profile repository implementation."""

from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.user_profile_repository import UserProfileRepository
from app.infrastructure.database.models import UserProfile


class PostgresUserProfileRepository(UserProfileRepository):
    """PostgreSQL implementation of user profile repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_default_profile(self) -> Optional[dict]:
        """Get the default user profile (singleton)."""
        # Query for any user profile (singleton table)
        result = await self.session.execute(select(UserProfile))
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        return {
            "id": profile.id,
            "settings": profile.settings or {},
        }

    async def create_or_update_profile(self, settings: dict) -> dict:
        """Create or update the default user profile."""
        # Query for any existing profile
        result = await self.session.execute(select(UserProfile))
        profile = result.scalar_one_or_none()

        if profile:
            # Update existing profile settings by merging with existing
            current_settings = profile.settings or {}
            current_settings.update(settings)
            profile.settings = current_settings
            # Mark the JSONB column as modified to ensure SQLAlchemy detects the change
            from sqlalchemy.orm import attributes

            attributes.flag_modified(profile, "settings")
        else:
            # Create new profile with settings
            profile = UserProfile(id=uuid4(), settings=settings)
            self.session.add(profile)

        await self.session.commit()
        await self.session.refresh(profile)

        # Return profile
        return {
            "id": profile.id,
            "settings": profile.settings or {},
        }
