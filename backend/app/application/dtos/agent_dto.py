"""Agent response DTO."""

from typing import List, Optional

from pydantic import BaseModel

from app.domain.entities.agent import Agent


class AgentDTO(BaseModel):
    """Agent response DTO."""

    id: str
    name: str
    description: Optional[str]
    file_path: str
    default_model: str
    tags: List[str]
    skills: List[str]
    allowed_tools: List[str]
    allowed_mcps: List[str]
    icon_color: str

    @classmethod
    def from_entity(cls, entity: Agent) -> "AgentDTO":
        """Convert domain entity to DTO."""
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            file_path=entity.file_path,
            default_model=entity.default_model,
            tags=entity.tags,
            skills=entity.skills,
            allowed_tools=entity.allowed_tools,
            allowed_mcps=entity.allowed_mcps,
            icon_color=entity.icon_color,
        )
