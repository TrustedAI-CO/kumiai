"""FastAPI dependency injection providers.

This module provides dependency functions for FastAPI routes,
including database session injection and future dependencies
for authentication, logging, etc.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for FastAPI dependency injection.

    This is a wrapper around get_db_session() to provide a clean
    dependency interface for FastAPI routes.

    Usage:
        @router.get("/sessions/{session_id}")
        async def get_session(
            session_id: UUID,
            db: AsyncSession = Depends(get_db)
        ):
            repo = SessionRepositoryImpl(db)
            return await repo.get_by_id(session_id)

    Yields:
        AsyncSession: Database session with automatic lifecycle
    """
    async for session in get_db_session():
        yield session
