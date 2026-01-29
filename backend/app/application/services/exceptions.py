"""Application layer service exceptions."""

from app.core.exceptions import ApplicationError


class ServiceError(ApplicationError):
    """Base exception for service layer errors."""

    pass


class SessionNotFoundError(ServiceError):
    """Session not found."""

    pass


class InvalidSessionStateError(ServiceError):
    """Invalid session state for requested operation."""

    pass


class ProjectNotFoundError(ServiceError):
    """Project not found."""

    pass


class SkillNotFoundError(ServiceError):
    """Skill not found."""

    pass


class MessageNotFoundError(ServiceError):
    """Message not found."""

    pass


class AgentNotFoundError(ServiceError):
    """Agent not found."""

    pass
