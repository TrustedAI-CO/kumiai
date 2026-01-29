"""Base repository implementation with common functionality."""

from typing import Generic, Optional, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFound


# Type variable for domain entities
EntityType = TypeVar("EntityType")


class BaseRepositoryImpl(Generic[EntityType]):
    """
    Base repository implementation providing common functionality.

    This class provides helper methods that eliminate code duplication
    across repository implementations, particularly for the common
    "get and raise if not found" pattern.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_or_raise(
        self, entity_id: UUID, entity_name: str = "Entity"
    ) -> EntityType:
        """
        Get entity by ID or raise EntityNotFound.

        This helper eliminates the common pattern:
            entity = await repo.get_by_id(id)
            if entity is None:
                raise EntityNotFoundError(...)

        Args:
            entity_id: UUID of the entity to retrieve
            entity_name: Name of the entity type for error messages

        Returns:
            Entity if found

        Raises:
            EntityNotFound: If entity with given ID doesn't exist
        """
        entity = await self.get_by_id(entity_id)  # type: ignore
        if entity is None:
            raise EntityNotFound(f"{entity_name} {entity_id} not found")
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[EntityType]:
        """
        Retrieve entity by ID.

        This method must be implemented by subclasses.

        Args:
            entity_id: UUID of the entity to retrieve

        Returns:
            Entity if found, None otherwise
        """
        raise NotImplementedError("Subclasses must implement get_by_id")
