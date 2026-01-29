"""User profile repository interface."""

from abc import ABC, abstractmethod
from typing import Optional


class UserProfileRepository(ABC):
    """Repository interface for user profile operations."""

    @abstractmethod
    async def get_default_profile(self) -> Optional[dict]:
        """Get the default user profile (singleton)."""
        pass

    @abstractmethod
    async def create_or_update_profile(self, settings: dict) -> dict:
        """Create or update the default user profile."""
        pass
