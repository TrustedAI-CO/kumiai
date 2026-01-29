"""Skill repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities import Skill


class SkillRepository(ABC):
    """
    Abstract repository interface for Skill entities.

    This interface defines the contract for skill persistence without
    specifying the implementation details.
    """

    @abstractmethod
    async def create(self, skill: Skill) -> Skill:
        """
        Create and persist a new skill.

        Args:
            skill: Skill entity to create.

        Returns:
            Created skill with ID assigned and any database-generated
            fields populated.

        Raises:
            RepositoryError: If creation fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_by_id(self, skill_id: str) -> Optional[Skill]:
        """
        Retrieve skill by ID.

        Args:
            skill_id: ID (directory name) of the skill to retrieve.

        Returns:
            Skill entity if found, None otherwise.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_all(self, include_deleted: bool = False) -> List[Skill]:
        """
        Get all skills.

        Args:
            include_deleted: Whether to include soft-deleted skills.
                           Defaults to False.

        Returns:
            List of all skills (may be empty).

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_by_tags(
        self, tags: List[str], match_all: bool = True, include_deleted: bool = False
    ) -> List[Skill]:
        """
        Get skills by tags.

        Args:
            tags: List of tags to search for.
            match_all: If True, returns skills that have ALL the specified tags.
                      If False, returns skills that have ANY of the specified tags.
                      Defaults to True.
            include_deleted: Whether to include soft-deleted skills.
                           Defaults to False.

        Returns:
            List of skills matching the tag criteria (may be empty).

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def update(self, skill: Skill) -> Skill:
        """
        Update existing skill.

        Args:
            skill: Skill entity with updated values. Must have a valid ID.

        Returns:
            Updated skill with any database-generated fields refreshed.

        Raises:
            NotFoundError: If skill with given ID doesn't exist.
            RepositoryError: If update fails due to database errors.
        """
        pass

    @abstractmethod
    async def delete(self, skill_id: str) -> None:
        """
        Soft-delete a skill.

        Renames the skill directory with .deleted suffix.

        Args:
            skill_id: ID (directory name) of skill to delete.

        Raises:
            NotFoundError: If skill with given ID doesn't exist.
            RepositoryError: If deletion fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def exists(self, skill_id: str) -> bool:
        """
        Check if skill exists (including soft-deleted skills).

        Args:
            skill_id: ID (directory name) of skill to check.

        Returns:
            True if skill exists (even if soft-deleted), False otherwise.

        Raises:
            RepositoryError: If query fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Skill]:
        """
        Retrieve skill by name.

        Args:
            name: Name of the skill to retrieve.

        Returns:
            Skill entity if found, None otherwise.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_base_path(self):
        """
        Get the base path where skills are stored.

        Returns:
            Path object pointing to the skills directory.
        """
        pass
