"""API middleware for CORS, logging, and request tracking."""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """
    Configure middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    _setup_cors_middleware(app)
    _setup_trusted_host_middleware(app)
    _setup_logging_middleware(app)


def _setup_cors_middleware(app: FastAPI) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    logger.info(
        "cors_middleware_configured",
        allowed_origins=settings.cors_origins,
    )


def _setup_trusted_host_middleware(app: FastAPI) -> None:
    """Configure trusted host middleware if allowed hosts are specified."""
    if hasattr(settings, "allowed_hosts") and settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )
        logger.info(
            "trusted_host_middleware_configured",
            allowed_hosts=settings.allowed_hosts,
        )


def _setup_logging_middleware(app: FastAPI) -> None:
    """Configure request/response logging middleware."""

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        """Log all HTTP requests and responses."""
        request_id = request.headers.get("X-Request-ID", "")
        start_time = time.time()

        # Skip logging for GET /sessions (too noisy)
        should_log = not (
            request.method == "GET" and request.url.path == "/api/v1/sessions"
        )

        if should_log:
            log_func = logger.debug if request.method == "GET" else logger.info
            log_func(
                "request_started",
                method=request.method,
                path=request.url.path,
                query_params=(
                    str(request.query_params) if request.query_params else None
                ),
                client_host=request.client.host if request.client else None,
                request_id=request_id or None,
            )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(exc),
                error_type=type(exc).__name__,
                request_id=request_id or None,
            )
            raise

        duration_ms = round((time.time() - start_time) * 1000, 2)

        if should_log:
            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "request_id": request_id or None,
            }

            if response.status_code >= 500:
                logger.error("request_completed", **log_data)
            elif response.status_code >= 400:
                logger.warning("request_completed", **log_data)
            elif request.method == "GET" and response.status_code < 400:
                # Log successful GET requests at DEBUG level to reduce noise
                logger.debug("request_completed", **log_data)
            else:
                logger.info("request_completed", **log_data)

        if request_id:
            response.headers["X-Request-ID"] = request_id

        return response
