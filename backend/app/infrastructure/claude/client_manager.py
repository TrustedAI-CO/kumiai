"""
Claude SDK client manager.

Manages multiple Claude SDK clients (one per session) with agent configuration
loading from the filesystem and SessionFactory integration.
"""

from pathlib import Path
from typing import Dict, Optional
from uuid import UUID


from app.core.logging import get_logger
from app.domain.entities.session import Session
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.skill_repository import SkillRepository
from app.infrastructure.claude.client import ClaudeClient
from app.infrastructure.claude.config import ClaudeSettings
from app.infrastructure.claude.exceptions import (
    AgentNotFoundError,
    ClientNotFoundError,
    ClaudeConnectionError,
)
from app.application.factories.session_factory import SessionFactory

logger = get_logger(__name__)


class ClaudeClientManager:
    """
    Manages multiple Claude SDK clients with agent-based configuration.

    Responsibilities:
    - Create Claude clients using SessionFactory
    - Track session_id → client and claude_session_id mappings
    - Handle client lifecycle (create, retrieve, cleanup)
    - Integrate with unified session architecture
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        skill_repo: SkillRepository,
        config: ClaudeSettings,
    ) -> None:
        """
        Initialize Claude client manager.

        Args:
            agent_repo: Repository for loading agent configurations
            skill_repo: Repository for loading skill configurations
            config: Claude SDK configuration settings
        """
        self._agent_repo = agent_repo
        self._skill_repo = skill_repo
        self._config = config

        # Initialize session factory
        self._session_factory = SessionFactory(agent_repo, skill_repo)

        # Session tracking
        self._clients: Dict[UUID, ClaudeClient] = {}
        self._claude_sessions: Dict[UUID, str] = {}

        logger.info(
            "claude_client_manager_initialized",
            max_concurrent_sessions=config.max_concurrent_sessions,
            default_model=config.default_model,
        )

    async def create_client_from_session(
        self,
        session: Session,
        working_dir: Path,
        project_path: Optional[Path] = None,
        resume_session: Optional[str] = None,
    ) -> ClaudeClient:
        """
        Create a new Claude client from a Session entity.

        TEMPORARY: Copied from create_client() to incrementally add SessionFactory.

        Args:
            session: Session domain entity
            working_dir: Working directory for the session
            project_path: Optional project root path
            resume_session: Optional Claude session ID to resume

        Returns:
            Configured and connected Claude client

        Raises:
            AgentNotFoundError: If agent not found
            ClaudeConnectionError: If connection fails
        """
        # Extract parameters from session entity
        session_id = session.id
        agent_id = session.agent_id
        # Test: Use working_dir (session subdir) as cwd instead of project_path
        project_path_str = str(working_dir)

        try:
            logger.info(
                "creating_claude_client_from_session",
                session_id=str(session_id),
                agent_id=agent_id,
                project_path=project_path_str,
                resume=bool(resume_session),
            )

            # Build ClaudeAgentOptions using SessionFactory
            _, options = await self._session_factory.create_session(
                session_type=session.session_type,
                instance_id=str(session_id),
                working_dir=working_dir,
                agent_id=agent_id,
                project_id=session.project_id,
                project_path=project_path,
                model=self._config.default_model,
                resume_session_id=resume_session,
            )

            # Create client
            client = ClaudeClient(
                options=options,
                timeout_seconds=self._config.connection_timeout_seconds,
            )

            # Connect with resume failure handling
            try:
                await client.connect()
            except ClaudeConnectionError as e:
                # Check if this is a resume failure
                if resume_session and self._is_resume_failure(str(e)):
                    logger.warning(
                        "resume_failed_retrying_fresh",
                        session_id=str(session_id),
                        resume_session=resume_session,
                        error=str(e),
                    )

                    # Retry without resume using SessionFactory
                    _, options_fresh = await self._session_factory.create_session(
                        session_type=session.session_type,
                        instance_id=str(session_id),
                        working_dir=working_dir,
                        agent_id=agent_id,
                        project_id=session.project_id,
                        project_path=project_path,
                        model=self._config.default_model,
                        resume_session_id=None,  # No resume
                    )

                    client = ClaudeClient(
                        options=options_fresh,
                        timeout_seconds=self._config.connection_timeout_seconds,
                    )
                    await client.connect()

                    logger.info(
                        "resume_failed_created_fresh_session",
                        session_id=str(session_id),
                    )
                else:
                    raise

            # Store client
            self._clients[session_id] = client

            logger.info(
                "claude_client_created",
                session_id=str(session_id),
                agent_id=agent_id,
                model=self._config.default_model,
            )

            return client

        except AgentNotFoundError:
            raise
        except ClaudeConnectionError:
            raise
        except Exception as e:
            logger.error(
                "create_client_failed",
                session_id=str(session_id),
                agent_id=agent_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def get_client(self, session_id: UUID) -> ClaudeClient:
        """
        Retrieve existing Claude client for a session.

        Args:
            session_id: Session identifier

        Returns:
            Claude client for the session

        Raises:
            ClientNotFoundError: If no client exists for session
        """
        client = self._clients.get(session_id)
        if not client:
            raise ClientNotFoundError(f"No client found for session {session_id}")
        return client

    async def remove_client(self, session_id: UUID) -> None:
        """
        Remove and cleanup Claude client for a session.

        Args:
            session_id: Session identifier
        """
        client = self._clients.get(session_id)
        if client:
            try:
                await client.disconnect()
            except Exception as e:
                logger.warning(
                    "client_disconnect_failed",
                    session_id=str(session_id),
                    error=str(e),
                )

            del self._clients[session_id]

            # Clean up claude session ID mapping
            if session_id in self._claude_sessions:
                del self._claude_sessions[session_id]

            logger.info("claude_client_removed", session_id=str(session_id))

    def set_claude_session_id(self, session_id: UUID, claude_session_id: str) -> None:
        """
        Store Claude session ID mapping.

        Args:
            session_id: Our session identifier
            claude_session_id: Claude SDK's session identifier
        """
        self._claude_sessions[session_id] = claude_session_id
        logger.debug(
            "claude_session_id_stored",
            session_id=str(session_id),
            claude_session_id=claude_session_id,
        )

    def get_claude_session_id(self, session_id: UUID) -> Optional[str]:
        """
        Retrieve Claude session ID for a session.

        Args:
            session_id: Our session identifier

        Returns:
            Claude SDK session ID if available, None otherwise
        """
        return self._claude_sessions.get(session_id)

    async def shutdown(self) -> None:
        """
        Shutdown all Claude clients and cleanup resources.

        Called during application shutdown to gracefully disconnect
        all active Claude SDK clients.
        """
        if not self._clients:
            logger.info("no_active_claude_clients_to_shutdown")
            return

        logger.info("shutting_down_claude_clients", count=len(self._clients))

        # Disconnect all clients
        session_ids = list(self._clients.keys())
        for session_id in session_ids:
            try:
                await self.remove_client(session_id)
            except Exception as e:
                logger.error(
                    "client_shutdown_failed",
                    session_id=str(session_id),
                    error=str(e),
                )

        logger.info("claude_clients_shutdown_complete")

    def _is_resume_failure(self, error_message: str) -> bool:
        """
        Check if error indicates resume failure (conversation not found).

        Args:
            error_message: Error message to check

        Returns:
            True if error indicates resume failure
        """
        error_lower = error_message.lower()
        return (
            "no conversation found" in error_lower
            or "conversation not found" in error_lower
            or "exit code 1" in error_lower
        )
