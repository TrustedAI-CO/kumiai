"""Agent repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.agent import Agent


class AgentRepository(ABC):
    """
    Abstract repository interface for Agent entities.

    This interface defines the contract for agent persistence using
    a file-based storage system with CLAUDE.md files.
    """

    @abstractmethod
    async def create(self, agent: Agent) -> Agent:
        """
        Create and persist a new agent.

        Creates a directory for the agent and generates CLAUDE.md with
        YAML frontmatter containing agent metadata.

        Args:
            agent: Agent entity to create.

        Returns:
            Created agent with file_path set to actual filesystem path.

        Raises:
            RepositoryError: If creation fails due to filesystem errors.
            ValidationError: If CLAUDE.md validation fails.
        """
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Retrieve agent by ID (directory name).

        Reads and parses CLAUDE.md to reconstruct the agent entity.

        Args:
            agent_id: ID of the agent (directory name).

        Returns:
            Agent entity if found, None otherwise.

        Raises:
            RepositoryError: If reading fails due to filesystem errors.
            ValidationError: If CLAUDE.md parsing fails.
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Agent]:
        """
        Retrieve agent by name (case-insensitive).

        Scans all agents and matches by name field in CLAUDE.md.

        Args:
            name: Name of the agent to retrieve.

        Returns:
            Agent entity if found, None otherwise.

        Raises:
            RepositoryError: If query fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def get_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> List[Agent]:
        """
        Get agents by tags.

        Args:
            tags: Tags to filter by
            match_all: If True, agent must have ALL tags (AND).
                      If False, agent must have ANY tag (OR).

        Returns:
            List of agents matching the tag criteria (may be empty).

        Raises:
            RepositoryError: If query fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def get_all(self, include_deleted: bool = False) -> List[Agent]:
        """
        Get all agents.

        Scans the agents directory and loads all CLAUDE.md files.

        Args:
            include_deleted: Whether to include soft-deleted agents
                           (directories with .deleted suffix).
                           Defaults to False.

        Returns:
            List of all agents (may be empty).

        Raises:
            RepositoryError: If query fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def update(self, agent: Agent) -> Agent:
        """
        Update existing agent.

        Rewrites CLAUDE.md with updated frontmatter while preserving
        the markdown body content.

        Args:
            agent: Agent entity with updated values. Must have a valid ID.

        Returns:
            Updated agent.

        Raises:
            NotFoundError: If agent with given ID doesn't exist.
            RepositoryError: If update fails due to filesystem errors.
            ValidationError: If CLAUDE.md validation fails.
        """
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        """
        Soft-delete an agent.

        Renames the agent directory with .deleted suffix.

        Args:
            agent_id: ID of agent to delete.

        Raises:
            NotFoundError: If agent with given ID doesn't exist.
            RepositoryError: If deletion fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def exists(self, agent_id: str) -> bool:
        """
        Check if agent exists (including soft-deleted agents).

        Args:
            agent_id: ID of agent to check.

        Returns:
            True if agent exists (even if soft-deleted), False otherwise.

        Raises:
            RepositoryError: If query fails due to filesystem errors.
        """
        pass

    @abstractmethod
    async def load_agent_content(self, agent_id: str) -> str:
        """
        Load full CLAUDE.md content for AI context.

        Returns the complete CLAUDE.md file including frontmatter
        and body, suitable for embedding in prompts.

        Args:
            agent_id: ID of agent to load content from.

        Returns:
            Complete CLAUDE.md content as string.

        Raises:
            NotFoundError: If agent doesn't exist.
            RepositoryError: If reading fails.
        """
        pass

    @abstractmethod
    async def load_supporting_doc(self, agent_id: str, doc_path: str) -> str:
        """
        Load a supporting document from agent directory.

        Validates path to prevent directory traversal attacks.

        Args:
            agent_id: ID of agent
            doc_path: Relative path to document within agent directory

        Returns:
            Document content as string.

        Raises:
            NotFoundError: If agent or document doesn't exist.
            SecurityError: If path traversal attempt detected.
            RepositoryError: If reading fails.
        """
        pass
