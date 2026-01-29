"""Session service - application layer use cases."""

from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from app.application.dtos.requests import CreateSessionRequest
from app.application.dtos.session_dto import SessionDTO
from app.application.services.exceptions import (
    InvalidSessionStateError,
    SessionNotFoundError,
)
from app.core.exceptions import ValidationError
from app.domain.entities import Session, Message
from app.domain.repositories import (
    AgentRepository,
    MessageRepository,
    ProjectRepository,
    SessionRepository,
)
from app.domain.value_objects import SessionStatus, SessionType, MessageRole


class SessionService:
    """
    Session service - orchestrates session-related use cases.

    Responsibilities:
    - Create/manage sessions
    - Handle session lifecycle (start, complete, fail, cancel, resume)
    - Enforce business rules
    - Manage transactions
    - Provide session metadata (sender attribution, etc.)
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        project_repo: ProjectRepository,
        agent_repo: AgentRepository,
        message_repo: Optional[MessageRepository] = None,
    ):
        """Initialize service with repositories."""
        self._session_repo = session_repo
        self._project_repo = project_repo
        self._agent_repo = agent_repo
        self._message_repo = message_repo

    async def create_session(self, request: CreateSessionRequest) -> SessionDTO:
        """
        Create a new session.

        Business rules:
        - agent_id must be provided
        - PM sessions must have a project
        - Project must exist (if provided)

        Args:
            request: Session creation request

        Returns:
            Created session DTO

        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValidationError: If business rules are violated
        """
        # Validate project for PM sessions
        session_type = SessionType(request.session_type)
        if session_type == SessionType.PM:
            if request.project_id is None:
                raise ValidationError("PM sessions must have a project_id")

            await self._project_repo.get_or_raise(request.project_id, "Project")

        # Create domain entity
        session = Session(
            id=uuid4(),
            agent_id=request.agent_id,
            project_id=request.project_id,
            session_type=session_type,
            status=SessionStatus.INITIALIZING,
            context=request.context or {},
        )

        # Sync kanban_stage with initial status (INITIALIZING → backlog)
        if session.context is None:
            session.context = {}
        session.context["kanban_stage"] = "backlog"

        # Persist
        created = await self._session_repo.create(session)

        # Create welcome message for supported session types
        await self._create_welcome_message(created.id, session_type, request.agent_id)

        return SessionDTO.from_entity(created)

    async def get_session(self, session_id: UUID) -> SessionDTO:
        """
        Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        # Sync kanban_stage with current status before returning
        session.sync_kanban_stage()

        return SessionDTO.from_entity(session)

    async def list_sessions(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[SessionDTO]:
        """
        List sessions with optional filters.

        Args:
            project_id: Filter by project ID (optional)
            status: Filter by status (optional)

        Returns:
            List of session DTOs
        """
        if project_id:
            sessions = await self._session_repo.get_by_project_id(project_id)
        elif status:
            sessions = await self._session_repo.get_by_status(SessionStatus(status))
        else:
            sessions = await self._session_repo.get_active_sessions()

        # Sync kanban_stage with current status for each session before returning
        for session in sessions:
            session.sync_kanban_stage()

        return [SessionDTO.from_entity(s) for s in sessions]

    async def start_session(self, session_id: UUID) -> SessionDTO:
        """
        Start a session (transition to thinking state).

        Args:
            session_id: Session UUID

        Returns:
            Updated session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
            InvalidSessionStateError: If session can't be started
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        try:
            session.start()
        except Exception as e:
            raise InvalidSessionStateError(str(e)) from e

        updated = await self._session_repo.update(session)
        return SessionDTO.from_entity(updated)

    async def complete_session(self, session_id: UUID) -> SessionDTO:
        """
        Mark session as completed.

        Args:
            session_id: Session UUID

        Returns:
            Updated session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
            InvalidSessionStateError: If session can't be completed
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        try:
            session.complete_task()
        except Exception as e:
            raise InvalidSessionStateError(str(e)) from e

        updated = await self._session_repo.update(session)
        return SessionDTO.from_entity(updated)

    async def fail_session(self, session_id: UUID, error: str) -> SessionDTO:
        """
        Mark session as failed.

        Args:
            session_id: Session UUID
            error: Error message

        Returns:
            Updated session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        session.fail(error)
        updated = await self._session_repo.update(session)
        return SessionDTO.from_entity(updated)

    async def interrupt_session(self, session_id: UUID) -> SessionDTO:
        """
        Interrupt a running session.

        Args:
            session_id: Session UUID

        Returns:
            Updated session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
            InvalidSessionStateError: If session can't be interrupted
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        try:
            session.interrupt()
        except Exception as e:
            raise InvalidSessionStateError(str(e)) from e

        updated = await self._session_repo.update(session)
        return SessionDTO.from_entity(updated)

    async def resume_session(self, session_id: UUID) -> SessionDTO:
        """
        Resume a completed/failed session.

        Args:
            session_id: Session UUID

        Returns:
            Updated session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
            InvalidSessionStateError: If session can't be resumed
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        try:
            session.resume()
        except Exception as e:
            raise InvalidSessionStateError(str(e)) from e

        updated = await self._session_repo.update(session)
        return SessionDTO.from_entity(updated)

    async def delete_session(self, session_id: UUID) -> None:
        """
        Soft-delete a session.

        Args:
            session_id: Session UUID

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        exists = await self._session_repo.exists(session_id)
        if not exists:
            raise SessionNotFoundError(f"Session {session_id} not found")

        await self._session_repo.delete(session_id)

    async def update_session_stage(self, session_id: UUID, stage: str) -> SessionDTO:
        """
        Update the kanban stage of a session.

        Args:
            session_id: Session UUID
            stage: New kanban stage (backlog, active, waiting, done)

        Returns:
            Updated session DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        session = await self._session_repo.get_or_raise(session_id, "Session")

        # Update kanban_stage in context
        if session.context is None:
            session.context = {}
        session.context["kanban_stage"] = stage

        # Update session in database
        updated = await self._session_repo.update(session)
        return SessionDTO.from_entity(updated)

    async def get_sender_fields(
        self, session_id: UUID
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get sender attribution fields for a session.

        This method provides agent_id and agent_name for message attribution
        without requiring the caller to load agents separately.

        Args:
            session_id: Session UUID

        Returns:
            Tuple of (agent_id, agent_name). Returns (None, None) if session
            doesn't exist or has no agent assigned.

        Note:
            If agent file cannot be loaded, falls back to using agent_id as name.
        """
        session = await self._session_repo.get_by_id(session_id)

        if not session or not session.agent_id:
            return None, None

        agent_id = session.agent_id

        # Load agent name from repository
        try:
            agent = await self._agent_repo.get_by_id(session.agent_id)
            agent_name = agent.name if agent else session.agent_id
        except Exception:
            # Fallback: use agent_id as name if loading fails
            agent_name = session.agent_id

        return agent_id, agent_name

    async def _create_welcome_message(
        self, session_id: UUID, session_type: SessionType, agent_id: Optional[str]
    ) -> None:
        """
        Create a welcome message for sessions.

        This message is saved directly to the database and does not go through
        the agent SDK flow. It's displayed in the frontend as an initial greeting.

        Args:
            session_id: Session UUID
            session_type: Type of session
            agent_id: Agent ID for attribution (optional)
        """
        if not self._message_repo:
            return  # Skip if message_repo not available

        # Get welcome message config for this session type
        from app.domain.config.welcome_messages import get_welcome_message

        message_config = get_welcome_message(session_type)
        if not message_config:
            return  # No welcome message for this session type

        # Load agent name for attribution
        agent_name = message_config["default_name"]
        if agent_id:
            try:
                agent = await self._agent_repo.get_by_id(agent_id)
                if agent:
                    agent_name = agent.name
            except Exception:
                pass  # Use default if loading fails

        # Create welcome message
        welcome_message = Message(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=message_config["content"],
            sequence=0,
            agent_id=agent_id,
            agent_name=agent_name,
        )

        # Save to database
        await self._message_repo.create(welcome_message)

    async def transition_to_working(self, session_id: UUID) -> Optional[SessionDTO]:
        """
        Transition a session to WORKING status with kanban sync.

        This is the centralized function used by:
        - User messages (via /enqueue endpoint)
        - Cross-session messages (via MCP tools)

        Only transitions if session is in INITIALIZING or IDLE state.

        Args:
            session_id: Session UUID to transition

        Returns:
            Updated session DTO if transition occurred, None if session not found
            or already in non-transitionable state
        """
        session = await self._session_repo.get_by_id(session_id)

        if not session:
            return None

        # Transition to WORKING (from INITIALIZING or IDLE)
        if session.status in [SessionStatus.INITIALIZING, SessionStatus.IDLE]:
            session.status = SessionStatus.WORKING
            # Sync kanban stage with new status (uses domain entity method)
            session.sync_kanban_stage()
            updated = await self._session_repo.update(session)
            return SessionDTO.from_entity(updated)

        # Session exists but not in transitionable state
        return None
