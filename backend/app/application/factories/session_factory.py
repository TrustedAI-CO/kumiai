"""Session factory for creating configured sessions."""

import logging
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from claude_agent_sdk import ClaudeAgentOptions

from app.core.exceptions import ValidationError
from app.domain.entities.session import Session
from app.domain.value_objects.session_type import SessionType
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.skill_repository import SkillRepository
from app.application.loaders.agent_loader import AgentLoader
from app.application.loaders.skill_loader import SkillLoader
from app.application.session_builders import (
    SessionBuildContext,
    PMSessionBuilder,
    SpecialistSessionBuilder,
    AssistantSessionBuilder,
)

logger = logging.getLogger(__name__)


class SessionFactory:
    """
    Factory for creating configured sessions with appropriate builders.

    Routes to session-type-specific builders and creates Session entities
    with ClaudeAgentOptions ready for initialization.
    """

    def __init__(
        self,
        agent_repository: AgentRepository,
        skill_repository: SkillRepository,
        credential_service: Optional[Any] = None,
    ):
        """
        Initialize session factory.

        Args:
            agent_repository: Repository for loading agents
            skill_repository: Repository for loading skills
            credential_service: Service for fetching provider credentials
        """
        # Initialize loaders
        self.agent_loader = AgentLoader(agent_repository)
        self.skill_loader = SkillLoader(skill_repository)
        self._credential_service = credential_service

        # Initialize builders
        self.pm_builder = PMSessionBuilder(self.agent_loader, self.skill_loader)
        self.specialist_builder = SpecialistSessionBuilder(
            self.agent_loader, self.skill_loader
        )
        self.assistant_builder = AssistantSessionBuilder(
            self.agent_loader, self.skill_loader
        )

    async def create_session(
        self,
        session_type: SessionType,
        instance_id: str,
        working_dir: Path,
        agent_id: Optional[str] = None,
        project_id: Optional[UUID] = None,
        project_path: Optional[Path] = None,
        model: str = "sonnet",
        resume_session_id: Optional[str] = None,
    ) -> tuple[Session, ClaudeAgentOptions]:
        """
        Create a new session with appropriate configuration.

        Args:
            session_type: Type of session to create
            instance_id: Unique instance identifier
            working_dir: Working directory for the session
            agent_id: Optional agent identifier
            project_id: Optional project UUID
            project_path: Optional project path
            model: LLM model to use (default: "sonnet")
            resume_session_id: Optional Claude session ID to resume

        Returns:
            Tuple of (Session entity, ClaudeAgentOptions)

        Raises:
            ValidationError: If configuration is invalid
            NotFoundError: If agent/skill not found
        """
        # Validate configuration
        await self._validate_configuration(session_type, agent_id, project_id)

        # Fetch provider environment variables (AWS Bedrock credentials etc.)
        provider_env = {}
        if self._credential_service:
            provider_env = await self._credential_service.get_provider_env()

        # Build context
        build_context = SessionBuildContext(
            session_type=session_type,
            instance_id=instance_id,
            working_dir=working_dir,
            agent_id=agent_id,
            project_id=project_id,
            project_path=project_path,
            model=model,
            resume_session_id=resume_session_id,
            provider_env=provider_env,
        )

        # Route to appropriate builder
        builder = self._get_builder(session_type)
        options = await builder.build_options(build_context)

        # Create Session entity
        from app.domain.value_objects import SessionStatus

        session = Session(
            id=UUID(instance_id) if isinstance(instance_id, str) else instance_id,
            session_type=session_type,
            agent_id=agent_id or "",  # Provide default for assistant sessions
            project_id=project_id,
            status=SessionStatus.INITIALIZING,
        )

        logger.info(
            f"Created {session_type.value} session: {instance_id} "
            f"(agent: {agent_id or 'none'}, project: {project_id or 'none'})"
        )

        return session, options

    def _get_builder(self, session_type: SessionType):
        """
        Get appropriate builder for session type.

        Args:
            session_type: Type of session

        Returns:
            Session builder instance

        Raises:
            ValidationError: If session type not supported
        """
        if session_type == SessionType.PM:
            return self.pm_builder
        elif session_type == SessionType.SPECIALIST:
            return self.specialist_builder
        elif session_type in (
            SessionType.ASSISTANT,
            SessionType.AGENT_ASSISTANT,
            SessionType.SKILL_ASSISTANT,
        ):
            return self.assistant_builder
        else:
            raise ValidationError(f"Unsupported session type: {session_type}")

    async def _validate_configuration(
        self,
        session_type: SessionType,
        agent_id: Optional[str],
        project_id: Optional[UUID],
    ) -> None:
        """
        Validate session configuration.

        Args:
            session_type: Type of session
            agent_id: Optional agent identifier
            project_id: Optional project UUID

        Raises:
            ValidationError: If configuration is invalid
        """
        # PM sessions require project_id
        if session_type == SessionType.PM and not project_id:
            raise ValidationError("PM sessions require project_id")

        # Specialist sessions require agent_id
        if session_type == SessionType.SPECIALIST and not agent_id:
            raise ValidationError("Specialist sessions require agent_id")

        # Validate agent exists for sessions that use agents
        if agent_id and session_type in (
            SessionType.SPECIALIST,
            SessionType.AGENT_ASSISTANT,
        ):
            agent = await self.agent_loader.agent_repository.get_by_id(agent_id)
            if agent is None:
                # Get list of available agents
                available_agents = await self.agent_loader.agent_repository.get_all()
                agent_list = (
                    ", ".join([f"'{a.id}'" for a in available_agents])
                    if available_agents
                    else "none"
                )
                raise ValidationError(
                    f"Agent '{agent_id}' not found. Available agents: {agent_list}"
                )

        logger.debug(
            f"Validated {session_type.value} session config "
            f"(agent: {agent_id or 'none'}, project: {project_id or 'none'})"
        )
