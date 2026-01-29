"""Custom exceptions for the application."""

from typing import Optional


class KumiAIError(Exception):
    """Base exception for all KumiAI errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Domain Errors
class DomainError(KumiAIError):
    """Base exception for domain layer errors."""

    pass


class ValidationError(DomainError):
    """Validation failed."""

    pass


class InvalidStateTransition(DomainError):
    """Invalid state transition attempted."""

    pass


class EntityNotFound(DomainError):
    """Entity not found."""

    pass


class DuplicateEntity(DomainError):
    """Entity with same identifier already exists."""

    pass


class NotFoundError(DomainError):
    """Resource not found."""

    pass


# Infrastructure Errors
class InfrastructureError(KumiAIError):
    """Base exception for infrastructure layer errors."""

    pass


class DatabaseError(InfrastructureError):
    """Database operation failed."""

    pass


class ClaudeClientError(InfrastructureError):
    """Claude SDK client error."""

    pass


class FileSystemError(InfrastructureError):
    """File system operation failed."""

    pass


class RepositoryError(InfrastructureError):
    """Repository operation failed."""

    pass


# Application Errors
class ApplicationError(KumiAIError):
    """Base exception for application layer errors."""

    pass


class SessionError(ApplicationError):
    """Session operation failed."""

    pass


class ProjectError(ApplicationError):
    """Project operation failed."""

    pass


class AgentError(ApplicationError):
    """Agent operation failed."""

    pass


# API Errors
class APIError(KumiAIError):
    """Base exception for API layer errors."""

    pass


class AuthenticationError(APIError):
    """Authentication failed."""

    pass


class AuthorizationError(APIError):
    """Authorization failed."""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""

    pass


class SecurityError(APIError):
    """Security violation detected (e.g., path traversal)."""

    pass
