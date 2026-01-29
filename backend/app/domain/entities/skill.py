"""Skill domain entity."""

from dataclasses import dataclass, field
from typing import List, Optional

from app.core.exceptions import ValidationError


@dataclass
class Skill:
    """
    Skill domain entity (File-based, Claude SDK compatible).

    A skill represents a reusable capability that can be attached to agents.
    Skills are stored as directories with SKILL.md (containing YAML frontmatter)
    following the Claude SDK format.

    Business rules:
    - ID is the directory name (e.g., "database-query")
    - SKILL.md is required in the skill directory
    - Name must be unique across active skills
    - Filesystem handles timestamps (file mtime/ctime)

    Directory structure:
        /data/skills/database-query/
        ├── SKILL.md (with YAML frontmatter)
        ├── examples.md (optional)
        └── scripts/ (optional)
    """

    id: str  # Directory name (e.g., "database-query")
    name: str
    file_path: str  # Full path to skill directory
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    icon: str = "zap"
    icon_color: str = "#4A90E2"

    def update_metadata(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        file_path: Optional[str] = None,
        icon: Optional[str] = None,
        icon_color: Optional[str] = None,
    ) -> None:
        """
        Update skill metadata.

        Args:
            name: New skill name (optional)
            description: New skill description (optional)
            file_path: New file path (optional)
            icon: New icon (optional)
            icon_color: New icon color (optional)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if file_path is not None:
            self.file_path = file_path
        if icon is not None:
            self.icon = icon
        if icon_color is not None:
            self.icon_color = icon_color

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the skill.

        Args:
            tag: Tag to add

        Raises:
            ValidationError: If tag is empty or already exists
        """
        if not tag or not tag.strip():
            raise ValidationError("Tag cannot be empty")

        tag = tag.strip()
        if tag in self.tags:
            raise ValidationError(f"Tag '{tag}' already exists")

        self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the skill.

        Args:
            tag: Tag to remove

        Raises:
            ValidationError: If tag doesn't exist
        """
        if tag not in self.tags:
            raise ValidationError(f"Tag '{tag}' does not exist")

        self.tags.remove(tag)

    def validate(self) -> None:
        """
        Validate skill invariants.

        Raises:
            ValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Skill name cannot be empty")

        if not self.file_path or not self.file_path.strip():
            raise ValidationError("Skill file_path cannot be empty")
