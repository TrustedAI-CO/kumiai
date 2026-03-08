"""
CLI client manager.

Manages multiple CLI backend clients (one per session) with agent configuration
loading from the filesystem and SessionFactory integration.

Supports:
- Claude: Uses claude_agent_sdk (ClaudeClient) directly
- Codex/Gemini/OpenCode: Uses codeagent-wrapper (CodeAgentWrapperClient)
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
from uuid import UUID


from app.core.logging import get_logger
from app.domain.entities.session import Session
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.skill_repository import SkillRepository
from app.infrastructure.claude.core.client import ClaudeClient
from app.infrastructure.claude.config import ClaudeSettings
from app.infrastructure.claude.exceptions import (
    AgentNotFoundError,
    ClientNotFoundError,
    ClaudeConnectionError,
)
from app.infrastructure.cli.config import (
    BACKEND_CLAUDE,
    CODEAGENT_WRAPPER_BACKENDS,
    CLIBackendConfig,
    DEFAULT_MODELS,
)
from app.infrastructure.cli.codeagent_client import CodeAgentWrapperClient
from app.application.factories.session_factory import SessionFactory

logger = get_logger(__name__)

# Union type for all supported CLI clients
CLIClient = Union[ClaudeClient, CodeAgentWrapperClient]


class ClaudeClientManager:
    """
    Manages multiple CLI backend clients with agent-based configuration.

    Responsibilities:
    - Create CLI clients (Claude SDK or codeagent-wrapper) using SessionFactory
    - Route to appropriate backend based on agent's cli_backend setting
    - Track session_id → client and session_id mappings
    - Handle client lifecycle (create, retrieve, cleanup)
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        skill_repo: SkillRepository,
        config: ClaudeSettings,
    ) -> None:
        """
        Initialize client manager.

        Args:
            agent_repo: Repository for loading agent configurations
            skill_repo: Repository for loading skill configurations
            config: Claude SDK configuration settings
        """
        self._agent_repo = agent_repo
        self._skill_repo = skill_repo
        self._config = config
        self._cli_config = CLIBackendConfig()

        # Initialize session factory
        self._session_factory = SessionFactory(agent_repo, skill_repo)

        # Session tracking (supports both ClaudeClient and CodeAgentWrapperClient)
        self._clients: Dict[UUID, CLIClient] = {}
        self._claude_sessions: Dict[UUID, str] = {}

        logger.info(
            "client_manager_initialized",
            max_concurrent_sessions=config.max_concurrent_sessions,
            default_model=config.default_model,
        )

    async def _resolve_agent_backend(
        self, agent_id: Optional[str]
    ) -> tuple[str, str]:
        """Resolve CLI backend and model from agent configuration.

        Returns:
            Tuple of (cli_backend, model)
        """
        if not agent_id:
            return BACKEND_CLAUDE, self._config.default_model

        agent = await self._agent_repo.get_by_id(agent_id)
        if not agent:
            return BACKEND_CLAUDE, self._config.default_model

        cli_backend = getattr(agent, "cli_backend", BACKEND_CLAUDE)
        model = agent.default_model or DEFAULT_MODELS.get(
            cli_backend, self._config.default_model
        )
        return cli_backend, model

    async def create_client_from_session(
        self,
        session: Session,
        working_dir: Path,
        project_path: Optional[Path] = None,
        resume_session: Optional[str] = None,
    ) -> CLIClient:
        """
        Create a new CLI client from a Session entity.

        Routes to Claude SDK (for claude backend) or codeagent-wrapper
        (for codex/gemini/opencode) based on agent's cli_backend setting.

        Args:
            session: Session domain entity
            working_dir: Working directory for the session
            project_path: Optional project root path
            resume_session: Optional session ID to resume

        Returns:
            Configured and connected CLI client

        Raises:
            AgentNotFoundError: If agent not found
            ClaudeConnectionError: If connection fails
        """
        session_id = session.id
        agent_id = session.agent_id

        # Resolve which backend to use from agent config
        cli_backend, model = await self._resolve_agent_backend(agent_id)

        try:
            logger.info(
                "creating_client_from_session",
                session_id=str(session_id),
                agent_id=agent_id,
                cli_backend=cli_backend,
                model=model,
                resume=bool(resume_session),
            )

            if cli_backend in CODEAGENT_WRAPPER_BACKENDS:
                client = await self._create_codeagent_client(
                    session=session,
                    working_dir=working_dir,
                    cli_backend=cli_backend,
                    model=model,
                )
            else:
                client = await self._create_claude_client(
                    session=session,
                    working_dir=working_dir,
                    project_path=project_path,
                    model=model,
                    resume_session=resume_session,
                )

            # Store client
            self._clients[session_id] = client

            logger.info(
                "client_created",
                session_id=str(session_id),
                agent_id=agent_id,
                cli_backend=cli_backend,
                model=model,
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
                cli_backend=cli_backend,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def _create_claude_client(
        self,
        session: Session,
        working_dir: Path,
        project_path: Optional[Path],
        model: str,
        resume_session: Optional[str],
    ) -> ClaudeClient:
        """Create a Claude SDK client."""
        session_id = session.id

        _, options = await self._session_factory.create_session(
            session_type=session.session_type,
            instance_id=str(session_id),
            working_dir=working_dir,
            agent_id=session.agent_id,
            project_id=session.project_id,
            project_path=project_path,
            model=model,
            resume_session_id=resume_session,
        )

        client = ClaudeClient(
            options=options,
            timeout_seconds=self._config.connection_timeout_seconds,
        )

        try:
            await client.connect()
        except ClaudeConnectionError as e:
            if resume_session and self._is_resume_failure(str(e)):
                logger.warning(
                    "resume_failed_retrying_fresh",
                    session_id=str(session_id),
                    error=str(e),
                )
                await self._clear_stale_session_id(session_id)

                _, options_fresh = await self._session_factory.create_session(
                    session_type=session.session_type,
                    instance_id=str(session_id),
                    working_dir=working_dir,
                    agent_id=session.agent_id,
                    project_id=session.project_id,
                    project_path=project_path,
                    model=model,
                    resume_session_id=None,
                )
                client = ClaudeClient(
                    options=options_fresh,
                    timeout_seconds=self._config.connection_timeout_seconds,
                )
                await client.connect()
            else:
                raise

        return client

    async def _create_codeagent_client(
        self,
        session: Session,
        working_dir: Path,
        cli_backend: str,
        model: str,
    ) -> CodeAgentWrapperClient:
        """Create a codeagent-wrapper client for non-Claude backends."""
        # Load agent for system prompt
        system_prompt = None
        allowed_tools = []
        if session.agent_id:
            agent = await self._agent_repo.get_by_id(session.agent_id)
            if agent:
                allowed_tools = agent.allowed_tools
                # Load agent content for system prompt
                try:
                    from app.application.loaders.agent_loader import AgentLoader

                    loader = AgentLoader(self._agent_repo)
                    content = await loader.load_agent_content(session.agent_id)
                    system_prompt = content
                except Exception as e:
                    logger.warning(
                        "failed_to_load_agent_content_for_codeagent",
                        agent_id=session.agent_id,
                        error=str(e),
                    )

        client = CodeAgentWrapperClient(
            backend=cli_backend,
            model=model,
            cwd=working_dir,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            config=self._cli_config,
        )
        await client.connect()
        return client

    async def get_client(self, session_id: UUID) -> CLIClient:
        """
        Retrieve existing CLI client for a session.

        Args:
            session_id: Session identifier

        Returns:
            CLI client (ClaudeClient or CodeAgentWrapperClient)

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

    async def _save_claude_session_id_to_db(
        self, session_id: UUID, claude_session_id: str
    ) -> None:
        """
        Save claude_session_id to database immediately after capture.

        This ensures the database is always the single source of truth
        for session IDs, enabling resume after server restarts.

        Args:
            session_id: Internal session UUID
            claude_session_id: Claude SDK session ID to save
        """
        try:
            from app.infrastructure.database.connection import get_repository_session
            from app.infrastructure.database.repositories import SessionRepositoryImpl

            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)

                if session_entity:
                    session_entity.claude_session_id = claude_session_id
                    await session_repo.update(session_entity)
                    await db.commit()

                    logger.info(
                        "claude_session_id_saved_to_db",
                        session_id=str(session_id),
                        claude_session_id=claude_session_id,
                    )
        except Exception as e:
            logger.error(
                "failed_to_save_claude_session_id_to_db",
                session_id=str(session_id),
                claude_session_id=claude_session_id,
                error=str(e),
            )

    async def _clear_stale_session_id(self, session_id: UUID) -> None:
        """
        Clear stale claude_session_id from database when resume fails.

        Args:
            session_id: Session identifier
        """
        try:
            from app.infrastructure.database.connection import get_repository_session
            from app.infrastructure.database.repositories import SessionRepositoryImpl

            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)

                if session_entity and session_entity.claude_session_id:
                    logger.info(
                        "clearing_stale_claude_session_id",
                        session_id=str(session_id),
                        stale_claude_session_id=session_entity.claude_session_id,
                    )

                    session_entity.claude_session_id = None
                    await session_repo.update(session_entity)
                    await db.commit()

                    logger.info(
                        "stale_claude_session_id_cleared",
                        session_id=str(session_id),
                    )
        except Exception as e:
            logger.error(
                "failed_to_clear_stale_session_id",
                session_id=str(session_id),
                error=str(e),
            )
