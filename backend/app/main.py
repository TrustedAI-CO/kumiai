"""KumiAI Backend v2.0 - FastAPI Application Entry Point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.exceptions import EXCEPTION_HANDLERS
from app.api.middleware import setup_middleware
from app.api.routes import (
    agents,
    health,
    mcp,
    messages,
    onboarding,
    projects,
    sessions,
    session_files,
    skills,
    system,
    user_profile,
)
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.infrastructure.database.connection import (
    close_db_connection,
    get_engine,
)
from app.infrastructure.database.models import Base

logger = get_logger(__name__)


async def _seed_default_data() -> None:
    """Copy example agents and skills when their directories are empty.

    Runs once on first startup so new installations have useful defaults.
    """
    import shutil
    from pathlib import Path

    examples_base = Path(__file__).resolve().parent.parent / "examples"

    for kind, target_dir in [
        ("agents", settings.agents_dir),
        ("skills", settings.skills_dir),
    ]:
        target_dir.mkdir(parents=True, exist_ok=True)

        existing = [d for d in target_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if existing:
            logger.debug(f"{kind}_seed_skipped", existing_count=len(existing))
            continue

        source = examples_base / kind
        if not source.is_dir():
            logger.debug(f"{kind}_seed_no_examples", path=str(source))
            continue

        copied = 0
        for item_dir in source.iterdir():
            if not item_dir.is_dir():
                continue
            dest = target_dir / item_dir.name
            if not dest.exists():
                shutil.copytree(item_dir, dest)
                copied += 1

        if copied:
            logger.info(f"{kind}_seeded", count=copied, source=str(source))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger.info(
        "application_starting", version="2.0.0", environment=settings.environment
    )

    # Initialize database connection pool
    try:
        engine = get_engine()
        database_url = settings.get_database_url()
        db_type = "SQLite" if database_url.startswith("sqlite") else "PostgreSQL"
        logger.info("database_engine_initialized", type=db_type)

        # Auto-create tables on startup (SQLite only, PostgreSQL uses migrations)
        if database_url.startswith("sqlite"):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("database_tables_created", type="SQLite")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise

    # Seed default agents from examples if agents directory is empty
    try:
        await _seed_default_data()
    except Exception as e:
        logger.warning("agent_seed_failed", error=str(e))

    # TODO: Load MCP servers (if enabled)
    if settings.enable_mcp:
        logger.info("mcp_enabled", loading_mcp_servers=True)
        # MCP initialization will be added in future sprint

    logger.info("application_startup_complete")

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Shutdown Claude clients
    try:
        from app.api.dependencies import _claude_client_manager

        if _claude_client_manager is not None:
            await _claude_client_manager.shutdown()
            logger.info("claude_clients_shutdown_complete")
    except Exception as e:
        logger.error("claude_shutdown_failed", error=str(e))

    # Close database connections
    try:
        await close_db_connection()
        logger.info("database_connections_closed")
    except Exception as e:
        logger.error("database_shutdown_failed", error=str(e))

    logger.info("application_shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="KumiAI Backend API",
        description="Multi-agent collaboration platform with Clean Architecture",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Setup middleware (CORS, logging, etc.)
    setup_middleware(app)

    # Register exception handlers
    for exc_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)

    # Register API routers
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(sessions.router, prefix="/api/v1", tags=["Sessions"])
    app.include_router(session_files.router, prefix="/api/v1", tags=["Session Files"])
    app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
    app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
    app.include_router(skills.router, prefix="/api/v1", tags=["Skills"])
    app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
    app.include_router(mcp.router, prefix="/api/v1", tags=["MCP"])
    app.include_router(user_profile.router, prefix="/api/v1", tags=["User Profile"])
    app.include_router(
        onboarding.router, prefix="/api/v1/onboarding", tags=["Onboarding"]
    )
    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])

    # Store debug mode in app state for error handlers
    app.state.debug = settings.environment == "development"

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
