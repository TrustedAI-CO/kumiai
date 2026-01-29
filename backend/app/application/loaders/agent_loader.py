"""Agent loader service for session initialization."""

import logging
from pathlib import Path
from typing import Optional

from app.domain.entities.agent import Agent
from app.domain.repositories.agent_repository import AgentRepository

logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Service for loading agent content and creating symlinks for session access.

    Loads agent definitions from the filesystem for session initialization.
    """

    def __init__(self, agent_repository: AgentRepository):
        """
        Initialize agent loader.

        Args:
            agent_repository: Repository for loading agent data
        """
        self.agent_repository = agent_repository

    async def load_agent(self, agent_id: str) -> Agent:
        """
        Load agent entity with all metadata.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent entity

        Raises:
            NotFoundError: If agent not found
        """
        agent = await self.agent_repository.get_by_id(agent_id)
        if agent is None:
            from app.core.exceptions import EntityNotFound

            raise EntityNotFound(f"Agent '{agent_id}' not found")
        logger.debug(
            f"Loaded agent: {agent_id} (skills: {agent.skills}, tools: {agent.allowed_tools}, mcps: {agent.allowed_mcps})"
        )
        return agent

    async def load_agent_content(self, agent_id: str) -> str:
        """
        Load agent's CLAUDE.md content (without frontmatter).

        Args:
            agent_id: Agent identifier

        Returns:
            Agent content markdown (body only, no YAML frontmatter)

        Raises:
            NotFoundError: If agent not found
        """
        import re

        content = await self.agent_repository.load_agent_content(agent_id)

        # Strip YAML frontmatter (--- ... ---)
        pattern = r"^---\s*\n.*?\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)

        if match:
            # Extract content after frontmatter
            body = content[match.end() :].strip()
            logger.debug(
                f"Loaded agent content for {agent_id} (length: {len(body)} chars, frontmatter stripped)"
            )
            return body

        # No frontmatter found, return as-is
        logger.debug(
            f"Loaded agent content for {agent_id} (length: {len(content)} chars, no frontmatter)"
        )
        return content.strip()

    async def create_symlink(
        self,
        agent_id: str,
        target_dir: Path,
        symlink_name: Optional[str] = None,
    ) -> Path:
        """
        Create symlink to agent directory for CLI access.

        Args:
            agent_id: Agent identifier
            target_dir: Directory where symlink should be created
            symlink_name: Name for the symlink (defaults to agent_id)

        Returns:
            Path to created symlink

        Raises:
            NotFoundError: If agent not found
            RepositoryError: If symlink creation fails
        """
        agent = await self.agent_repository.get_by_id(agent_id)

        # Get actual filesystem path from repository
        agent_path = await self.agent_repository.get_agent_directory(agent_id)

        if symlink_name is None:
            symlink_name = agent_id

        symlink_path = target_dir / symlink_name

        try:
            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)

            # Remove existing symlink if present
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            # Create symlink
            symlink_path.symlink_to(agent_path, target_is_directory=True)
            logger.debug(f"Created symlink: {symlink_path} -> {agent_path}")

            return symlink_path

        except Exception as e:
            logger.error(f"Failed to create symlink for agent {agent_id}: {e}")
            raise

    async def load_agent_for_session(
        self,
        agent_id: str,
        session_dir: Optional[Path] = None,
    ) -> tuple[Agent, str, Optional[Path]]:
        """
        Load agent with content and optionally create symlink.

        Convenience method for session initialization.

        Args:
            agent_id: Agent identifier
            session_dir: Optional session directory for creating symlink

        Returns:
            Tuple of (agent entity, content, symlink path)

        Raises:
            NotFoundError: If agent not found
        """
        # Load agent entity and content
        agent = await self.load_agent(agent_id)
        content = await self.load_agent_content(agent_id)

        # Create symlink if session directory provided
        symlink_path = None
        if session_dir:
            agents_dir = session_dir / "agents"
            symlink_path = await self.create_symlink(agent_id, agents_dir)

        logger.info(
            f"Loaded agent for session: {agent_id} "
            f"(skills: {len(agent.skills)}, tools: {len(agent.allowed_tools)}, "
            f"mcps: {len(agent.allowed_mcps)})"
        )

        return agent, content, symlink_path
