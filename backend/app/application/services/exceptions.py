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


class ProjectNotDeletedError(ServiceError):
    """Restore was requested for a project that is not deleted."""

    pass


class ProjectPathConflictError(ServiceError):
    """Another live project already occupies the path this project needs."""

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


class TaskNotFoundError(ServiceError):
    """Task not found."""

    pass
