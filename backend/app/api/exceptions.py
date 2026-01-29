"""Global exception handlers for API layer."""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.application.services.exceptions import (
    AgentNotFoundError,
    InvalidSessionStateError,
    MessageNotFoundError,
    ProjectNotFoundError,
    ServiceError,
    SessionNotFoundError,
    SkillNotFoundError,
)
from app.core.exceptions import (
    ApplicationError,
    DatabaseError,
    DomainError,
    EntityNotFound,
    InfrastructureError,
    InvalidStateTransition,
    KumiAIError,
    NotFoundError,
    RepositoryError,
    ValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle domain validation errors."""
    logger.warning(
        "validation_error",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "message": str(exc),
            "detail": exc.details if hasattr(exc, "details") else None,
        },
    )


async def not_found_error_handler(
    request: Request, exc: EntityNotFound
) -> JSONResponse:
    """Handle entity not found errors."""
    logger.info(
        "entity_not_found",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "NotFoundError",
            "message": str(exc),
        },
    )


async def service_not_found_error_handler(
    request: Request,
    exc: (
        SessionNotFoundError
        | ProjectNotFoundError
        | AgentNotFoundError
        | SkillNotFoundError
        | MessageNotFoundError
    ),
) -> JSONResponse:
    """Handle service-specific not found errors."""
    logger.info(
        "resource_not_found",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
        },
    )


async def invalid_session_state_handler(
    request: Request, exc: InvalidSessionStateError
) -> JSONResponse:
    """Handle invalid session state errors."""
    logger.warning(
        "invalid_session_state",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "InvalidSessionStateError",
            "message": str(exc),
        },
    )


async def invalid_state_transition_handler(
    request: Request, exc: InvalidStateTransition
) -> JSONResponse:
    """Handle invalid state transition errors."""
    logger.warning(
        "invalid_state_transition",
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "InvalidStateTransition",
            "message": str(exc),
        },
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors."""
    logger.error(
        "database_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    debug_mode = getattr(request.app.state, "debug", False)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": "Database operation failed",
            "detail": str(exc) if debug_mode else None,
        },
    )


async def infrastructure_error_handler(
    request: Request, exc: InfrastructureError
) -> JSONResponse:
    """Handle infrastructure layer errors."""
    logger.error(
        "infrastructure_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    # Return 404 for file not found errors
    if "File not found" in str(exc) or "not found" in str(exc).lower():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
            },
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": type(exc).__name__,
            "message": "Service temporarily unavailable",
            "detail": str(exc),
        },
    )


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handle domain layer errors."""
    logger.warning(
        "domain_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
        },
    )


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Handle service layer errors."""
    logger.error(
        "service_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
        },
    )


async def application_error_handler(
    request: Request, exc: ApplicationError
) -> JSONResponse:
    """Handle generic application errors."""
    logger.error(
        "application_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
        },
    )


async def generic_kumiai_error_handler(
    request: Request, exc: KumiAIError
) -> JSONResponse:
    """Handle any uncaught KumiAI errors."""
    logger.error(
        "kumiai_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "details": exc.details if hasattr(exc, "details") else None,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any uncaught exceptions."""
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )

    debug_mode = getattr(request.app.state, "debug", False)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc) if debug_mode else None,
        },
    )


EXCEPTION_HANDLERS = {
    # Domain layer exceptions
    ValidationError: validation_error_handler,
    EntityNotFound: not_found_error_handler,
    NotFoundError: not_found_error_handler,  # Add NotFoundError specifically
    InvalidStateTransition: invalid_state_transition_handler,
    DomainError: domain_error_handler,
    # Service layer exceptions
    SessionNotFoundError: service_not_found_error_handler,
    ProjectNotFoundError: service_not_found_error_handler,
    AgentNotFoundError: service_not_found_error_handler,
    SkillNotFoundError: service_not_found_error_handler,
    MessageNotFoundError: service_not_found_error_handler,
    InvalidSessionStateError: invalid_session_state_handler,
    ServiceError: service_error_handler,
    # Infrastructure layer exceptions
    RepositoryError: validation_error_handler,  # Return 400 for repository errors
    DatabaseError: database_error_handler,
    InfrastructureError: infrastructure_error_handler,
    # Application layer exceptions
    ApplicationError: application_error_handler,
    # Generic handlers (fallbacks)
    KumiAIError: generic_kumiai_error_handler,
    Exception: generic_exception_handler,
}
