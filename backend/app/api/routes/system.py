"""System API endpoints for app management."""

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.infrastructure.database.connection import get_engine
from app.infrastructure.database.models import Base

router = APIRouter()


@router.post("/reset")
async def reset_app() -> dict:
    """
    Reset the application to initial state.

    This will delete all data except projects:
    - Database (kumiai.db)
    - Skills directory
    - Agents directory
    - User settings

    Projects directory will be preserved.
    """
    try:
        # Remove database
        db_path = Path(settings.kumiai_home) / "kumiai.db"
        if db_path.exists():
            db_path.unlink()

        # Remove skills directory
        skills_dir = Path(settings.skills_dir)
        if skills_dir.exists():
            shutil.rmtree(skills_dir)

        # Remove agents directory
        agents_dir = Path(settings.agents_dir)
        if agents_dir.exists():
            shutil.rmtree(agents_dir)

        # Note: Projects directory is NOT deleted
        # projects_dir = Path(settings.projects_dir)

        # Recreate database tables
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        return {
            "message": "Application reset successfully. Database, skills, and agents have been deleted. Projects preserved."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset application: {str(e)}"
        )
