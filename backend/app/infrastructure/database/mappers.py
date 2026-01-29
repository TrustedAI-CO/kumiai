"""Entity-model mappers for bidirectional conversion.

This module provides mappers to convert between rich domain entities
and SQLAlchemy database models. Mappers handle:
- Enum conversions (string ↔ enum)
- JSON serialization (dict ↔ JSONB)
- Optional field handling
- Timestamp management
"""

from typing import Optional

from app.domain.entities import (
    Message as MessageEntity,
    Project as ProjectEntity,
    Session as SessionEntity,
)
from app.domain.value_objects import MessageRole, SessionStatus, SessionType
from app.infrastructure.database.models import Message, Project, Session


class SessionMapper:
    """Maps between Session entity and Session model."""

    @staticmethod
    def to_entity(model: Session) -> SessionEntity:
        """
        Convert database model to domain entity.

        Args:
            model: SQLAlchemy session model

        Returns:
            Session domain entity
        """
        return SessionEntity(
            id=model.id,
            agent_id=model.agent_id or "",  # Ensure non-null for entity
            project_id=model.project_id,
            session_type=SessionType(model.session_type),
            status=SessionStatus(model.status),
            claude_session_id=model.claude_session_id,
            context=model.context or {},
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: SessionEntity, model: Optional[Session] = None) -> Session:
        """
        Convert domain entity to database model.

        Args:
            entity: Session domain entity
            model: Optional existing model to update

        Returns:
            SQLAlchemy session model
        """
        if model is None:
            model = Session(id=entity.id)

        model.agent_id = entity.agent_id
        model.project_id = entity.project_id
        model.session_type = entity.session_type.value
        model.status = entity.status.value
        model.claude_session_id = entity.claude_session_id
        # Create new dict to ensure SQLAlchemy detects JSONB changes
        model.context = dict(entity.context) if entity.context else {}
        model.error_message = entity.error_message
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

        return model


class ProjectMapper:
    """Maps between Project entity and Project model."""

    @staticmethod
    def to_entity(model: Project) -> ProjectEntity:
        """
        Convert database model to domain entity.

        Args:
            model: SQLAlchemy project model

        Returns:
            Project domain entity
        """
        return ProjectEntity(
            id=model.id,
            name=model.name,
            description=model.description,
            pm_agent_id=model.pm_agent_id,
            pm_session_id=model.pm_session_id,
            path=model.path,
            team_member_ids=model.team_member_ids,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: ProjectEntity, model: Optional[Project] = None) -> Project:
        """
        Convert domain entity to database model.

        Args:
            entity: Project domain entity
            model: Optional existing model to update

        Returns:
            SQLAlchemy project model
        """
        if model is None:
            model = Project(id=entity.id)

        model.name = entity.name
        model.description = entity.description
        model.pm_agent_id = entity.pm_agent_id
        model.pm_session_id = entity.pm_session_id
        model.path = entity.path
        model.team_member_ids = entity.team_member_ids
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at

        return model


class MessageMapper:
    """Maps between Message entity and Message model."""

    @staticmethod
    def to_entity(model: Message) -> MessageEntity:
        """
        Convert database model to domain entity.

        Args:
            model: SQLAlchemy message model

        Returns:
            Message domain entity
        """
        return MessageEntity(
            id=model.id,
            session_id=model.session_id,
            role=MessageRole(model.role),
            content=model.content,
            tool_use_id=model.tool_use_id,
            sequence=model.sequence,
            metadata=model.meta or {},
            created_at=model.created_at,
            agent_id=model.agent_id,
            agent_name=model.agent_name,
            from_instance_id=model.from_instance_id,
            response_id=model.response_id,
        )

    @staticmethod
    def to_model(entity: MessageEntity, model: Optional[Message] = None) -> Message:
        """
        Convert domain entity to database model.

        Args:
            entity: Message domain entity
            model: Optional existing model to update

        Returns:
            SQLAlchemy message model
        """
        if model is None:
            model = Message(id=entity.id)

        model.session_id = entity.session_id
        model.role = entity.role.value
        model.content = entity.content
        model.tool_use_id = entity.tool_use_id
        model.sequence = entity.sequence
        model.meta = entity.metadata
        model.created_at = entity.created_at
        model.agent_id = entity.agent_id
        model.agent_name = entity.agent_name
        model.from_instance_id = entity.from_instance_id
        model.response_id = entity.response_id

        return model


# NOTE: SkillMapper removed - Skills are now file-based (Claude SDK format)
# See: app/infrastructure/filesystem/skill_repository.py
