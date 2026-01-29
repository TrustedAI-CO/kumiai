"""File-based skill repository implementation."""

import re
from pathlib import Path
from typing import List, Optional

import yaml

from app.core.exceptions import NotFoundError, RepositoryError
from app.core.logging import get_logger
from app.domain.entities import Skill
from app.domain.repositories import SkillRepository

logger = get_logger(__name__)


class FileBasedSkillRepository(SkillRepository):
    """
    File-based implementation of SkillRepository.

    Skills are stored as directories following Claude SDK format:
        /data/skills/{skill-id}/
        ├── SKILL.md (with YAML frontmatter)
        ├── examples.md (optional)
        └── scripts/ (optional)

    Metadata is stored in YAML frontmatter of SKILL.md:
        ---
        name: Database Query
        description: Execute SQL queries
        tags: [database, sql]
        icon: database
        iconColor: "#4A90E2"
        ---
        # Skill content...
    """

    def __init__(self, base_path: Path | str = Path("data/skills")):
        """
        Initialize file-based skill repository.

        Args:
            base_path: Base directory for skill storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _parse_skill_md(self, skill_md_path: Path) -> dict:
        """
        Parse SKILL.md with YAML frontmatter.

        Args:
            skill_md_path: Path to SKILL.md file

        Returns:
            Dictionary with frontmatter metadata

        Raises:
            RepositoryError: If parsing fails
        """
        try:
            content = skill_md_path.read_text(encoding="utf-8")

            # Check for frontmatter (--- at start)
            if not content.startswith("---"):
                # No frontmatter, use defaults
                skill_id = skill_md_path.parent.name
                return {
                    "name": skill_id.replace("-", " ").title(),
                    "description": "",
                    "tags": [],
                    "icon": "zap",
                    "iconColor": "#4A90E2",
                }

            # Extract frontmatter
            match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
            if not match:
                raise RepositoryError(f"Invalid frontmatter format in {skill_md_path}")

            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                raise RepositoryError(
                    f"Frontmatter must be a dictionary in {skill_md_path}"
                )

            # Validate required fields
            if "name" not in frontmatter or not frontmatter["name"]:
                raise RepositoryError(
                    f"Missing required field 'name' in {skill_md_path}"
                )

            # Normalize list fields (handle comma-separated strings from legacy files)
            for field in ["tags"]:
                if field in frontmatter:
                    value = frontmatter[field]
                    if isinstance(value, str):
                        # Parse comma-separated string or empty string
                        if value.strip():
                            frontmatter[field] = [
                                item.strip()
                                for item in value.split(",")
                                if item.strip()
                            ]
                        else:
                            frontmatter[field] = []
                    elif not isinstance(value, list):
                        # Convert other types to list
                        frontmatter[field] = [value] if value else []

            return frontmatter

        except Exception as e:
            logger.error(
                "parse_skill_md_failed",
                skill_md_path=str(skill_md_path),
                error=str(e),
            )
            raise RepositoryError(f"Failed to parse SKILL.md: {e}") from e

    def _write_skill_md(
        self,
        skill_dir: Path,
        metadata: dict,
        content: Optional[str] = None,
    ) -> None:
        """
        Write SKILL.md with YAML frontmatter.

        Args:
            skill_dir: Skill directory path
            metadata: Frontmatter metadata dictionary
            content: Optional markdown content (body)

        Raises:
            RepositoryError: If writing fails
        """
        try:
            skill_md = skill_dir / "SKILL.md"

            # Generate frontmatter with inline lists (comma-separated)
            # Use flow style for lists to get [item1, item2] instead of multi-line
            class InlineListDumper(yaml.SafeDumper):
                pass

            def represent_list(dumper, data):
                return dumper.represent_sequence(
                    "tag:yaml.org,2002:seq", data, flow_style=True
                )

            InlineListDumper.add_representer(list, represent_list)

            frontmatter_yaml = yaml.dump(
                metadata,
                Dumper=InlineListDumper,
                allow_unicode=True,
                sort_keys=False,
            )

            # If updating existing file, preserve body
            if content is None and skill_md.exists():
                existing_content = skill_md.read_text(encoding="utf-8")
                if existing_content.startswith("---"):
                    match = re.match(
                        r"^---\n(.*?)\n---\n(.*)",
                        existing_content,
                        re.DOTALL,
                    )
                    if match:
                        content = match.group(2)

            # Default content if none provided - create comprehensive template
            if content is None:
                skill_name = metadata.get("name", "Skill")
                description = metadata.get("description", "")
                content = f"""
# {skill_name}

{description}

## Overview

Provide a detailed overview of what this skill does and when to use it.

## Usage

Explain how to use this skill effectively. Include examples if helpful.

### Examples

```
Add code examples or usage patterns here
```

## Prerequisites

List any requirements or setup needed:
- Requirement 1
- Requirement 2

## Best Practices

- Best practice 1
- Best practice 2

## Notes

Add any additional notes, warnings, or tips here.
"""

            # Write file
            full_content = f"---\n{frontmatter_yaml}---\n{content}"
            skill_md.write_text(full_content, encoding="utf-8")

            logger.debug(
                "skill_md_written",
                skill_md=str(skill_md),
            )

        except Exception as e:
            logger.error(
                "write_skill_md_failed",
                skill_dir=str(skill_dir),
                error=str(e),
            )
            raise RepositoryError(f"Failed to write SKILL.md: {e}") from e

    async def create(self, skill: Skill) -> Skill:
        """Create new skill directory with SKILL.md."""
        try:
            skill_dir = self.base_path / skill.id

            # Check if already exists
            if skill_dir.exists():
                raise RepositoryError(f"Skill directory already exists: {skill.id}")

            # Create directory
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Create metadata for frontmatter
            metadata = {
                "name": skill.name,
                "description": skill.description or "",
                "tags": skill.tags,
                "icon": skill.icon,
                "iconColor": skill.icon_color,
            }

            # Write SKILL.md
            self._write_skill_md(skill_dir, metadata)

            logger.info(
                "skill_created",
                skill_id=skill.id,
                skill_path=str(skill_dir),
            )

            # Update entity with logical path before returning
            skill.file_path = f"/skills/{skill.id}/"
            return skill

        except Exception as e:
            logger.error(
                "create_skill_failed",
                skill_id=skill.id,
                error=str(e),
            )
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to create skill: {e}") from e

    async def get_by_id(self, skill_id: str) -> Skill:
        """Load skill from SKILL.md."""
        try:
            skill_dir = self.base_path / skill_id
            skill_md = skill_dir / "SKILL.md"

            # Check if exists (exclude .deleted directories)
            if not skill_md.exists() or skill_id.endswith(".deleted"):
                raise NotFoundError(f"Skill not found: {skill_id}")

            # Parse frontmatter
            metadata = self._parse_skill_md(skill_md)

            # Build Skill entity with logical path
            skill = Skill(
                id=skill_id,
                name=metadata.get("name", skill_id),
                file_path=f"/skills/{skill_id}/",
                description=metadata.get("description"),
                tags=metadata.get("tags", []),
                icon=metadata.get("icon", "zap"),
                icon_color=metadata.get("iconColor", "#4A90E2"),
            )

            return skill

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "get_skill_by_id_failed",
                skill_id=skill_id,
                error=str(e),
            )
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to get skill {skill_id}: {e}") from e

    async def get_all(self, include_deleted: bool = False) -> List[Skill]:
        """List all skills by scanning directories."""
        try:
            skills = []

            for skill_dir in self.base_path.iterdir():
                if not skill_dir.is_dir():
                    continue

                # Skip deleted directories
                if skill_dir.name.endswith(".deleted") and not include_deleted:
                    continue

                # Check for SKILL.md
                if not (skill_dir / "SKILL.md").exists():
                    continue

                skill = await self.get_by_id(skill_dir.name)
                if skill:
                    skills.append(skill)

            logger.debug(
                "list_all_skills",
                count=len(skills),
                include_deleted=include_deleted,
            )

            return skills

        except Exception as e:
            logger.error(
                "get_all_skills_failed",
                error=str(e),
            )
            raise RepositoryError(f"Failed to list skills: {e}") from e

    async def get_by_tags(
        self,
        tags: List[str],
        match_all: bool = True,
        include_deleted: bool = False,
    ) -> List[Skill]:
        """Get skills by tags."""
        try:
            all_skills = await self.get_all(include_deleted=include_deleted)

            if not tags:
                return all_skills

            # Filter by tags
            filtered_skills = []
            for skill in all_skills:
                skill_tags_set = set(skill.tags)
                search_tags_set = set(tags)

                if match_all:
                    # ALL tags must match
                    if search_tags_set.issubset(skill_tags_set):
                        filtered_skills.append(skill)
                else:
                    # ANY tag must match
                    if search_tags_set.intersection(skill_tags_set):
                        filtered_skills.append(skill)

            logger.debug(
                "get_skills_by_tags",
                tags=tags,
                match_all=match_all,
                count=len(filtered_skills),
            )

            return filtered_skills

        except Exception as e:
            logger.error(
                "get_skills_by_tags_failed",
                tags=tags,
                error=str(e),
            )
            raise RepositoryError(f"Failed to get skills by tags: {e}") from e

    async def update(self, skill: Skill) -> Skill:
        """Update SKILL.md frontmatter."""
        try:
            skill_dir = self.base_path / skill.id
            skill_md = skill_dir / "SKILL.md"

            if not skill_md.exists():
                raise NotFoundError(f"Skill not found: {skill.id}")

            # Update metadata
            metadata = {
                "name": skill.name,
                "description": skill.description or "",
                "tags": skill.tags,
                "icon": skill.icon,
                "iconColor": skill.icon_color,
            }

            # Write updated frontmatter (preserve body)
            self._write_skill_md(skill_dir, metadata)

            logger.info(
                "skill_updated",
                skill_id=skill.id,
            )

            return skill

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "update_skill_failed",
                skill_id=skill.id,
                error=str(e),
            )
            raise RepositoryError(f"Failed to update skill: {e}") from e

    async def delete(self, skill_id: str) -> None:
        """Soft delete: rename directory with .deleted suffix."""
        try:
            skill_dir = self.base_path / skill_id

            if not skill_dir.exists():
                raise NotFoundError(f"Skill not found: {skill_id}")

            # Rename to .deleted
            deleted_dir = self.base_path / f"{skill_id}.deleted"
            skill_dir.rename(deleted_dir)

            logger.info(
                "skill_soft_deleted",
                skill_id=skill_id,
                deleted_path=str(deleted_dir),
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "delete_skill_failed",
                skill_id=skill_id,
                error=str(e),
            )
            raise RepositoryError(f"Failed to delete skill: {e}") from e

    async def exists(self, skill_id: str) -> bool:
        """Check if skill directory exists (excludes soft-deleted skills)."""
        skill_dir = self.base_path / skill_id
        return skill_dir.exists() and (skill_dir / "SKILL.md").exists()

    async def get_skill_directory(self, skill_id: str) -> Path:
        """Get the actual filesystem directory path for a skill."""
        return self.base_path / skill_id

    async def get_by_name(self, name: str) -> Optional[Skill]:
        """Get skill by name."""
        try:
            all_skills = await self.get_all(include_deleted=False)

            for skill in all_skills:
                if skill.name.lower() == name.lower():
                    return skill

            return None

        except Exception as e:
            logger.error(
                "get_skill_by_name_failed",
                name=name,
                error=str(e),
            )
            raise RepositoryError(f"Failed to get skill by name: {e}") from e

    # Additional methods for Claude SDK format

    async def load_skill_content(self, skill_id: str) -> str:
        """
        Load full SKILL.md content for loading into context.

        Args:
            skill_id: Skill ID (directory name)

        Returns:
            Full SKILL.md content including frontmatter

        Raises:
            NotFoundError: If skill not found
            RepositoryError: If reading fails
        """
        try:
            skill_md = self.base_path / skill_id / "SKILL.md"

            if not skill_md.exists():
                raise NotFoundError(f"SKILL.md not found for skill: {skill_id}")

            return skill_md.read_text(encoding="utf-8")

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "load_skill_content_failed",
                skill_id=skill_id,
                error=str(e),
            )
            raise RepositoryError(f"Failed to load skill content: {e}") from e

    async def load_supporting_doc(self, skill_id: str, doc_path: str) -> str:
        """
        Load supporting document (e.g., FORMS.md, reference/finance.md).

        Args:
            skill_id: Skill ID (directory name)
            doc_path: Relative path to document within skill directory

        Returns:
            Document content

        Raises:
            NotFoundError: If document not found
            RepositoryError: If reading fails
        """
        try:
            skill_dir = self.base_path / skill_id
            doc_file = skill_dir / doc_path

            # Security: Ensure path is within skill directory (check this FIRST)
            try:
                if not doc_file.resolve().is_relative_to(skill_dir.resolve()):
                    raise RepositoryError(f"Invalid path: {doc_path}")
            except ValueError:
                # is_relative_to can raise ValueError for invalid paths
                raise RepositoryError(f"Invalid path: {doc_path}")

            if not doc_file.exists():
                raise NotFoundError(
                    f"Document not found: {doc_path} in skill {skill_id}"
                )

            return doc_file.read_text(encoding="utf-8")

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "load_supporting_doc_failed",
                skill_id=skill_id,
                doc_path=doc_path,
                error=str(e),
            )
            raise RepositoryError(f"Failed to load supporting document: {e}") from e

    async def get_base_path(self) -> Path:
        """
        Get the base path where skills are stored.

        Returns:
            Path object pointing to the skills directory.
        """
        return self.base_path
