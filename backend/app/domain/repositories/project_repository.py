"""Project repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities import Project


class ProjectRepository(ABC):
    """
    Abstract repository interface for Project entities.

    This interface defines the contract for project persistence without
    specifying the implementation details.
    """

    @abstractmethod
    async def create(self, project: Project) -> Project:
        """
        Create and persist a new project.

        Args:
            project: Project entity to create.

        Returns:
            Created project with ID assigned and any database-generated
            fields populated.

        Raises:
            RepositoryError: If creation fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        """
        Retrieve project by ID.

        Args:
            project_id: UUID of the project to retrieve.

        Returns:
            Project entity if found, None otherwise.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_all(self, include_deleted: bool = False) -> List[Project]:
        """
        Get all projects.

        Args:
            include_deleted: Whether to include soft-deleted projects.
                           Defaults to False.

        Returns:
            List of all projects (may be empty).

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def update(self, project: Project) -> Project:
        """
        Update existing project.

        Args:
            project: Project entity with updated values. Must have a valid ID.

        Returns:
            Updated project with any database-generated fields refreshed.

        Raises:
            NotFoundError: If project with given ID doesn't exist.
            RepositoryError: If update fails due to database errors.
        """
        pass

    @abstractmethod
    async def delete(self, project_id: UUID) -> None:
        """
        Soft-delete a project.

        Sets the deleted_at timestamp without removing the record from
        the database.

        Args:
            project_id: UUID of project to delete.

        Raises:
            NotFoundError: If project with given ID doesn't exist.
            RepositoryError: If deletion fails due to database errors.
        """
        pass

    @abstractmethod
    async def exists(self, project_id: UUID) -> bool:
        """
        Check if project exists (including soft-deleted projects).

        Args:
            project_id: UUID of project to check.

        Returns:
            True if project exists (even if soft-deleted), False otherwise.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass
