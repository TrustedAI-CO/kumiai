"""Context injection for MCP tool execution.

Provides dependency injection mechanism for tools to access
database sessions, services, and other runtime dependencies.
"""

from contextvars import ContextVar
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import threading


# Context variables for dependency injection
_db_session: ContextVar[Optional[AsyncSession]] = ContextVar("db_session", default=None)
_session_service: ContextVar[Optional[Any]] = ContextVar(
    "session_service", default=None
)
_agent_service: ContextVar[Optional[Any]] = ContextVar("agent_service", default=None)
_project_service: ContextVar[Optional[Any]] = ContextVar(
    "project_service", default=None
)
_session_info: ContextVar[Optional[dict]] = ContextVar("session_info", default=None)

# Global session info storage for cross-context access (used by Claude SDK hooks)
# Maps internal session UUID -> {"source_instance_id": str, "project_id": str}
_global_session_info: Dict[str, dict] = {}
_global_session_info_lock = threading.Lock()


def set_tool_context(
    db: AsyncSession,
    session_service: Any,
    agent_service: Any,
    project_service: Any,
) -> None:
    """Set context before tool execution.

    Args:
        db: Database session for queries
        session_service: Service for session operations
        agent_service: Service for agent operations
        project_service: Service for project operations
    """
    _db_session.set(db)
    _session_service.set(session_service)
    _agent_service.set(agent_service)
    _project_service.set(project_service)


def get_db_session() -> AsyncSession:
    """Get database session from context.

    Returns:
        AsyncSession: Database session

    Raises:
        RuntimeError: If database session not set in context
    """
    session = _db_session.get()
    if session is None:
        raise RuntimeError("Database session not set in tool context")
    return session


def get_session_service() -> Any:
    """Get session service from context.

    Returns:
        Session service instance

    Raises:
        RuntimeError: If session service not set in context
    """
    service = _session_service.get()
    if service is None:
        raise RuntimeError("Session service not set in tool context")
    return service


def get_agent_service() -> Any:
    """Get agent service from context.

    Returns:
        Agent service instance

    Raises:
        RuntimeError: If agent service not set in context
    """
    service = _agent_service.get()
    if service is None:
        raise RuntimeError("Agent service not set in tool context")
    return service


def get_project_service() -> Any:
    """Get project service from context.

    Returns:
        Project service instance

    Raises:
        RuntimeError: If project service not set in context
    """
    service = _project_service.get()
    if service is None:
        raise RuntimeError("Project service not set in tool context")
    return service


def set_session_info(source_instance_id: str, project_id: Optional[str] = None) -> None:
    """Set current session information for hook access.

    This stores session info in both ContextVar (for same-context access) and
    a global dict (for cross-context access by Claude SDK hooks).

    Args:
        source_instance_id: Internal instance UUID of the calling session
        project_id: Project UUID (if session belongs to a project)
    """
    session_data = {"source_instance_id": source_instance_id, "project_id": project_id}

    # Set in ContextVar for same-context access
    _session_info.set(session_data)

    # Store in global dict for cross-context access (Claude SDK hooks)
    with _global_session_info_lock:
        _global_session_info[source_instance_id] = session_data


def get_current_session_info() -> Optional[dict]:
    """Get current session information.

    Returns:
        Dict with source_instance_id and project_id, or None if not set
    """
    # Try ContextVar first (same async context)
    info = _session_info.get()
    if info:
        return info

    # Fallback: check global storage (for Claude SDK hooks in different contexts)
    # Note: We don't have the session_id here, so we return the first one
    # This is a limitation - hooks should pass session_id if they need it
    with _global_session_info_lock:
        if _global_session_info:
            # Return any available session info (there should only be one active)
            return next(iter(_global_session_info.values()))

    return None


def get_session_info_by_id(session_id: str) -> Optional[dict]:
    """Get session information by session ID.

    This is useful for hooks that receive a session_id parameter.

    Args:
        session_id: Internal session UUID

    Returns:
        Dict with source_instance_id and project_id, or None if not found
    """
    with _global_session_info_lock:
        return _global_session_info.get(session_id)


def clear_session_info(source_instance_id: str) -> None:
    """Clear session information when session ends.

    Args:
        source_instance_id: Internal instance UUID of the session to clear
    """
    with _global_session_info_lock:
        _global_session_info.pop(source_instance_id, None)
