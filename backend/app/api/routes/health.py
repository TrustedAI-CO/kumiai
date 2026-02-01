"""Health check endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.connection import get_db_session, get_engine
from app.infrastructure.sse.manager import sse_manager

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db_session)) -> dict:
    """
    Health check endpoint with database and filesystem verification.

    Returns:
        Dict with status, version, environment, and component health information
    """
    health_status = {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "checks": {},
    }

    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check required directories
    directories = {
        "kumiai_home": settings.kumiai_home,
        "agents_dir": settings.agents_dir,
        "skills_dir": settings.skills_dir,
        "projects_dir": settings.projects_dir,
    }

    dirs_status = {}
    for name, path in directories.items():
        try:
            path_obj = Path(path)
            dirs_status[name] = {
                "status": "exists" if path_obj.exists() else "missing",
                "path": str(path),
                "writable": path_obj.exists() and path_obj.is_dir(),
            }
            if not path_obj.exists():
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["status"] = "degraded"
            dirs_status[name] = {
                "status": "error",
                "path": str(path),
                "error": str(e),
            }

    health_status["checks"]["directories"] = dirs_status

    # Check API key configuration
    api_key_configured = bool(
        settings.anthropic_api_key
        and settings.anthropic_api_key != "your_anthropic_api_key_here"
    )
    health_status["checks"]["api_key"] = {
        "status": "configured" if api_key_configured else "missing",
    }
    if not api_key_configured:
        health_status["status"] = "degraded"

    # Check database connection pool status
    try:
        engine = get_engine()
        pool = engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "status": "healthy",
        }

        # Calculate pool utilization percentage
        total_available = pool.size() + pool.overflow()
        if total_available > 0:
            utilization = (pool.checkedout() / total_available) * 100
            pool_status["utilization_percent"] = round(utilization, 2)

            # Warn if pool utilization is high
            if utilization > 80:
                pool_status["status"] = "warning"
                pool_status["message"] = "Pool utilization above 80%"
                health_status["status"] = "degraded"

        health_status["checks"]["connection_pool"] = pool_status
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["connection_pool"] = {
            "status": "error",
            "error": str(e),
        }

    # Check SSE connection status
    try:
        total_sse_connections = sse_manager.get_total_connections()
        session_connections = sse_manager.get_all_session_connections()

        sse_status = {
            "total_connections": total_sse_connections,
            "active_sessions": len(session_connections),
            "status": "healthy",
        }

        # Warn if too many connections (potential leak)
        if total_sse_connections > 50:
            sse_status["status"] = "warning"
            sse_status["message"] = (
                f"High number of SSE connections: {total_sse_connections}"
            )
            health_status["status"] = "degraded"

        health_status["checks"]["sse_connections"] = sse_status
    except Exception as e:
        health_status["checks"]["sse_connections"] = {
            "status": "error",
            "error": str(e),
        }

    return health_status
