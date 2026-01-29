"""Session response DTO."""

from typing import Any, Dict, Optional
from uuid import UUID

from app.application.dtos.base import TimestampedDTO
from app.domain.entities import Session


class SessionDTO(TimestampedDTO):
    """Session response DTO."""

    id: UUID
    agent_id: str
    project_id: Optional[UUID]
    session_type: str
    status: str
    claude_session_id: Optional[str]
    context: Dict[str, Any]
    error_message: Optional[str]
    kanban_stage: Optional[str] = (
        None  # Extracted from context for frontend compatibility
    )

    @classmethod
    def from_entity(cls, entity: Session) -> "SessionDTO":
        """
        Convert domain entity to DTO.

        Args:
            entity: Session domain entity

        Returns:
            SessionDTO
        """
        # Extract kanban_stage from context for frontend compatibility
        kanban_stage = entity.context.get("kanban_stage") if entity.context else None

        return cls(
            id=entity.id,
            agent_id=entity.agent_id,
            project_id=entity.project_id,
            session_type=entity.session_type.value,
            status=entity.status.value,
            claude_session_id=entity.claude_session_id,
            context=entity.context,
            error_message=entity.error_message,
            kanban_stage=kanban_stage,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
