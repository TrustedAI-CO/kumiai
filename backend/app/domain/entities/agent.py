"""Agent domain entity."""

from dataclasses import dataclass, field
from typing import List, Optional

from app.core.exceptions import ValidationError


@dataclass
class Agent:
    """
    Agent domain entity.

    An agent represents an AI assistant with specific capabilities, skills,
    and tool permissions. Agent definitions are stored in CLAUDE.md files
    with YAML frontmatter following the Claude SDK format.

    Business rules:
    - Name and file_path are required
    - Name must be unique across system (enforced by repository)
    - Skills must reference existing skill IDs
    - Allowed tools must be from the built-in tool list
    - Allowed MCPs must be from configured MCP servers
    - Icon color must be a valid hex color
    """

    id: str  # Agent ID derived from directory name
    name: str
    file_path: str  # Path to agent directory
    description: Optional[str] = None
    default_model: str = "sonnet"  # LLM model to use (sonnet, opus, haiku)
    tags: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)  # Skill IDs
    allowed_tools: List[str] = field(default_factory=list)  # Built-in tool names
    allowed_mcps: List[str] = field(default_factory=list)  # MCP server IDs
    icon_color: str = "#4A90E2"

    def update_metadata(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None,
        allowed_mcps: Optional[List[str]] = None,
        icon_color: Optional[str] = None,
    ) -> None:
        """
        Update agent metadata.

        Args:
            name: New agent name (optional)
            description: New agent description (optional)
            default_model: New default model (optional)
            tags: New tag list (optional)
            skills: New skill ID list (optional)
            allowed_tools: New allowed tools list (optional)
            allowed_mcps: New allowed MCPs list (optional)
            icon_color: New icon color (optional)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if default_model is not None:
            self.default_model = default_model
        if tags is not None:
            self.tags = tags
        if skills is not None:
            self.skills = skills
        if allowed_tools is not None:
            self.allowed_tools = allowed_tools
        if allowed_mcps is not None:
            self.allowed_mcps = allowed_mcps
        if icon_color is not None:
            self.icon_color = icon_color

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the agent.

        Args:
            tag: Tag to add

        Raises:
            ValidationError: If tag is empty or already exists
        """
        if not tag or not tag.strip():
            raise ValidationError("Tag cannot be empty")

        tag = tag.strip().lower()
        if tag in self.tags:
            raise ValidationError(f"Tag '{tag}' already exists")

        self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the agent.

        Args:
            tag: Tag to remove

        Raises:
            ValidationError: If tag doesn't exist
        """
        tag = tag.strip().lower()
        if tag not in self.tags:
            raise ValidationError(f"Tag '{tag}' does not exist")

        self.tags.remove(tag)

    def add_skill(self, skill_id: str) -> None:
        """
        Add a skill to the agent.

        Args:
            skill_id: Skill ID to add

        Raises:
            ValidationError: If skill_id is empty or already exists
        """
        if not skill_id or not skill_id.strip():
            raise ValidationError("Skill ID cannot be empty")

        skill_id = skill_id.strip()
        if skill_id in self.skills:
            raise ValidationError(f"Skill '{skill_id}' already exists")

        self.skills.append(skill_id)

    def remove_skill(self, skill_id: str) -> None:
        """
        Remove a skill from the agent.

        Args:
            skill_id: Skill ID to remove

        Raises:
            ValidationError: If skill doesn't exist
        """
        skill_id = skill_id.strip()
        if skill_id not in self.skills:
            raise ValidationError(f"Skill '{skill_id}' does not exist")

        self.skills.remove(skill_id)

    def validate(self) -> None:
        """
        Validate agent invariants.

        Raises:
            ValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Agent name cannot be empty")

        if not self.file_path or not self.file_path.strip():
            raise ValidationError("Agent file_path cannot be empty")

        # Validate icon color format (hex color)
        if self.icon_color:
            if not self.icon_color.startswith("#") or len(self.icon_color) not in (
                4,
                7,
            ):
                raise ValidationError(
                    "Icon color must be a valid hex color (e.g., #4A90E2 or #FFF)"
                )
