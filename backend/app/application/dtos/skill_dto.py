"""Skill response DTO."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.entities import Skill


class SkillDTO(BaseModel):
    """Skill response DTO (file-based, Claude SDK compatible)."""

    id: str  # Directory name (e.g., "database-query")
    name: str
    description: Optional[str]
    file_path: str  # Path to skill directory
    tags: List[str]
    icon: str
    icon_color: str

    @classmethod
    def from_entity(cls, entity: Skill) -> "SkillDTO":
        """Convert domain entity to DTO."""
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            file_path=entity.file_path,
            tags=entity.tags,
            icon=entity.icon,
            icon_color=entity.icon_color,
        )


class ImportSkillResponse(BaseModel):
    """Response after importing a skill."""

    skill: SkillDTO = Field(..., description="The imported skill definition")
    status: str = Field(..., description="Import status: success, error")
    message: str = Field(..., description="Human-readable status message")
