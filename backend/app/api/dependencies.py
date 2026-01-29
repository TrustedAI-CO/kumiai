"""Dependency injection for API layer."""

from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import (
    MessageService,
    ProjectService,
    SessionService,
    SkillService,
    UserProfileService,
)
from app.application.services.agent_service import AgentService
from app.core.config import settings
from app.core.dependencies import get_db
from app.infrastructure.database.repositories import (
    MessageRepositoryImpl,
    PostgresUserProfileRepository,
    ProjectRepositoryImpl,
    SessionRepositoryImpl,
)
from app.infrastructure.filesystem import FileBasedSkillRepository, FileService
from app.infrastructure.filesystem.agent_repository import FileBasedAgentRepository
from app.infrastructure.claude.client_manager import ClaudeClientManager
from app.infrastructure.claude.config import ClaudeSettings
from app.infrastructure.claude.executor import SessionExecutor
from app.infrastructure.sse.manager import SSEManager, sse_manager

# Singleton instances (stateless, thread-safe)
_file_service: Optional[FileService] = None
_skill_repository: Optional[FileBasedSkillRepository] = None
_agent_repository: Optional[FileBasedAgentRepository] = None
_claude_settings: Optional[ClaudeSettings] = None
_claude_client_manager: Optional[ClaudeClientManager] = None
_session_executor: Optional[SessionExecutor] = None


def get_file_service() -> FileService:
    """
    Get FileService singleton instance.

    Returns:
        FileService instance
    """
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service


def get_skill_repository() -> FileBasedSkillRepository:
    """
    Get FileBasedSkillRepository singleton instance.

    Returns:
        FileBasedSkillRepository instance
    """
    global _skill_repository
    if _skill_repository is None:
        _skill_repository = FileBasedSkillRepository(base_path=settings.skills_dir)
    return _skill_repository


def get_agent_repository() -> FileBasedAgentRepository:
    """
    Get FileBasedAgentRepository singleton instance.

    Returns:
        FileBasedAgentRepository instance
    """
    global _agent_repository
    if _agent_repository is None:
        _agent_repository = FileBasedAgentRepository(base_path=settings.agents_dir)
    return _agent_repository


async def get_session_service(
    db: AsyncSession = Depends(get_db),
    agent_repo: FileBasedAgentRepository = Depends(get_agent_repository),
) -> SessionService:
    """
    Get SessionService with injected repositories.

    Args:
        db: Database session
        agent_repo: Agent repository (injected)

    Returns:
        SessionService instance
    """
    return SessionService(
        session_repo=SessionRepositoryImpl(db),
        project_repo=ProjectRepositoryImpl(db),
        agent_repo=agent_repo,
        message_repo=MessageRepositoryImpl(db),
    )


async def get_project_service(
    db: AsyncSession = Depends(get_db),
    agent_repo: FileBasedAgentRepository = Depends(get_agent_repository),
) -> ProjectService:
    """
    Get ProjectService with injected repositories.

    Args:
        db: Database session
        agent_repo: Agent repository (injected)

    Returns:
        ProjectService instance
    """
    return ProjectService(
        project_repo=ProjectRepositoryImpl(db),
        session_repo=SessionRepositoryImpl(db),
        agent_repo=agent_repo,
    )


async def get_skill_service() -> SkillService:
    """
    Get SkillService with file-based repository.

    Returns:
        SkillService instance
    """
    return SkillService(
        skill_repo=get_skill_repository(),
    )


async def get_agent_service() -> AgentService:
    """
    Get AgentService with file-based repository.

    Returns:
        AgentService instance
    """
    return AgentService(
        agent_repo=get_agent_repository(),
    )


async def get_message_service(
    db: AsyncSession = Depends(get_db),
) -> MessageService:
    """
    Get MessageService with injected repository.

    Args:
        db: Database session

    Returns:
        MessageService instance
    """
    return MessageService(
        message_repo=MessageRepositoryImpl(db),
        session_repo=SessionRepositoryImpl(db),
    )


async def get_user_profile_service(
    db: AsyncSession = Depends(get_db),
) -> UserProfileService:
    """
    Get UserProfileService with injected repository.

    Args:
        db: Database session

    Returns:
        UserProfileService instance
    """
    return UserProfileService(
        user_profile_repo=PostgresUserProfileRepository(db),
    )


def get_claude_settings() -> ClaudeSettings:
    """
    Get ClaudeSettings singleton instance.

    Returns:
        ClaudeSettings instance
    """
    global _claude_settings
    if _claude_settings is None:
        _claude_settings = ClaudeSettings()
    return _claude_settings


def get_claude_client_manager(
    agent_repo: FileBasedAgentRepository = Depends(get_agent_repository),
    skill_repo: FileBasedSkillRepository = Depends(get_skill_repository),
    settings: ClaudeSettings = Depends(get_claude_settings),
) -> ClaudeClientManager:
    """
    Get ClaudeClientManager singleton instance.

    Args:
        agent_repo: Agent repository for loading agent configurations
        skill_repo: Skill repository for loading skill configurations
        settings: Claude SDK configuration settings

    Returns:
        ClaudeClientManager instance
    """
    global _claude_client_manager
    if _claude_client_manager is None:
        _claude_client_manager = ClaudeClientManager(
            agent_repo=agent_repo,
            skill_repo=skill_repo,
            config=settings,
        )
    return _claude_client_manager


def get_session_executor(
    client_manager: ClaudeClientManager = Depends(get_claude_client_manager),
) -> SessionExecutor:
    """
    Get SessionExecutor singleton instance.

    Args:
        client_manager: ClaudeClientManager instance

    Returns:
        SessionExecutor instance
    """
    global _session_executor
    if _session_executor is None:
        _session_executor = SessionExecutor(client_manager=client_manager)
    return _session_executor


def get_sse_manager() -> SSEManager:
    """
    Get SSEManager singleton instance.

    Returns:
        SSEManager instance
    """
    return sse_manager
