"""Skill loader service for session initialization."""

import logging
from pathlib import Path
from typing import List, Optional

from app.domain.entities.skill import Skill
from app.domain.repositories.skill_repository import SkillRepository

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    Service for loading skill content and creating symlinks for session access.

    Loads skill descriptions for system prompt injection and creates symlinks
    for CLI access to skill documentation.
    """

    def __init__(self, skill_repository: SkillRepository):
        """
        Initialize skill loader.

        Args:
            skill_repository: Repository for loading skill data
        """
        self.skill_repository = skill_repository

    async def load_skill(self, skill_id: str) -> Skill:
        """
        Load skill entity with all metadata.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill entity

        Raises:
            NotFoundError: If skill not found
        """
        skill = await self.skill_repository.get_by_id(skill_id)
        logger.debug(f"Loaded skill: {skill_id}")
        return skill

    async def load_skill_content(self, skill_id: str) -> str:
        """
        Load skill's SKILL.md content (without frontmatter).

        Args:
            skill_id: Skill identifier

        Returns:
            Skill content markdown

        Raises:
            NotFoundError: If skill not found
        """
        content = await self.skill_repository.load_skill_content(skill_id)
        logger.debug(
            f"Loaded skill content for {skill_id} (length: {len(content)} chars)"
        )
        return content

    async def load_skill_description(self, skill_id: str) -> str:
        """
        Load formatted skill description for system prompt.

        Args:
            skill_id: Skill identifier

        Returns:
            Formatted skill description

        Raises:
            NotFoundError: If skill not found
        """
        skill = await self.load_skill(skill_id)
        content = await self.load_skill_content(skill_id)

        # Format for system prompt
        description = f"""### {skill.name}

{skill.description or "No description provided"}

**Documentation:** See `skills/{skill_id}/SKILL.md` for detailed instructions.

{content[:500]}{"..." if len(content) > 500 else ""}
"""
        return description

    async def create_symlink(
        self,
        skill_id: str,
        target_dir: Path,
        symlink_name: Optional[str] = None,
    ) -> Path:
        """
        Create symlink to skill directory for CLI access.

        Args:
            skill_id: Skill identifier
            target_dir: Directory where symlink should be created
            symlink_name: Name for the symlink (defaults to skill_id)

        Returns:
            Path to created symlink

        Raises:
            NotFoundError: If skill not found
            RepositoryError: If symlink creation fails
        """
        skill = await self.skill_repository.get_by_id(skill_id)

        # Get actual filesystem path from repository
        skill_path = await self.skill_repository.get_skill_directory(skill_id)

        if symlink_name is None:
            symlink_name = skill_id

        symlink_path = target_dir / symlink_name

        try:
            # Create target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)

            # Remove existing symlink if present
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            # Create symlink
            symlink_path.symlink_to(skill_path, target_is_directory=True)
            logger.debug(f"Created symlink: {symlink_path} -> {skill_path}")

            return symlink_path

        except Exception as e:
            logger.error(f"Failed to create symlink for skill {skill_id}: {e}")
            raise

    async def load_skills_for_session(
        self,
        skill_ids: List[str],
        session_dir: Optional[Path] = None,
    ) -> List[str]:
        """
        Load multiple skills with descriptions and optionally create symlinks.

        Convenience method for session initialization.

        Args:
            skill_ids: List of skill identifiers
            session_dir: Optional session directory for creating symlinks

        Returns:
            List of formatted skill descriptions for system prompt

        Raises:
            NotFoundError: If any skill not found
        """
        descriptions = []
        skills_dir = session_dir / "skills" if session_dir else None

        for skill_id in skill_ids:
            try:
                # Load skill description
                description = await self.load_skill_description(skill_id)
                descriptions.append(description)

                # Create symlink if session directory provided
                if skills_dir:
                    await self.create_symlink(skill_id, skills_dir)

            except Exception as e:
                logger.error(f"Failed to load skill {skill_id}: {e}")
                # Continue with other skills rather than failing completely
                continue

        logger.info(f"Loaded {len(descriptions)}/{len(skill_ids)} skills for session")
        return descriptions
