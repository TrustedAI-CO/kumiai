"""Task DTOs."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dtos.base import TimestampedDTO
from app.domain.entities.task import Task


class TaskDTO(TimestampedDTO):
    """Task response DTO."""

    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    status: str

    @classmethod
    def from_entity(cls, entity: Task) -> "TaskDTO":
        return cls(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            description=entity.description,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CreateTaskRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
