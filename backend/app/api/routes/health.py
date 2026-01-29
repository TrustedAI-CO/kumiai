"""Health check endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.connection import get_db_session

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

    return health_status
