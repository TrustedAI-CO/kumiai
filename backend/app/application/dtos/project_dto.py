"""Project response DTO."""

from typing import List, Optional
from uuid import UUID

from app.application.dtos.base import TimestampedDTO
from app.domain.entities import Project


class ProjectDTO(TimestampedDTO):
    """Project response DTO."""

    id: UUID
    name: str
    description: Optional[str]
    pm_agent_id: Optional[str]
    pm_session_id: Optional[UUID]
    team_member_ids: Optional[List[str]]
    path: str

    @classmethod
    def from_entity(cls, entity: Project) -> "ProjectDTO":
        """Convert domain entity to DTO."""
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            pm_agent_id=entity.pm_agent_id,
            pm_session_id=entity.pm_session_id,
            team_member_ids=entity.team_member_ids,
            path=entity.path,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
