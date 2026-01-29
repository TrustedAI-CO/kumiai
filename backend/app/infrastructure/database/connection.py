"""Database connection and session management.

This module provides async database session factory and lifecycle management
using SQLAlchemy 2.0 async engine and sessions.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Global engine instance (created once at startup)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the global async database engine.

    Returns:
        AsyncEngine: SQLAlchemy async engine instance
    """
    global _engine
    if _engine is None:
        # Ensure kumiai_home directory exists
        settings.kumiai_home.mkdir(parents=True, exist_ok=True)

        # Get database URL with interpolated paths
        database_url = settings.get_database_url()

        # Create engine with appropriate settings for SQLite
        is_sqlite = database_url.startswith("sqlite")

        if is_sqlite:
            # SQLite-specific configuration
            _engine = create_async_engine(
                database_url,
                echo=False,
                connect_args={"check_same_thread": False},  # Required for SQLite
            )
        else:
            # PostgreSQL or other database configuration
            _engine = create_async_engine(
                database_url,
                echo=False,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=settings.db_pool_timeout,
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=True,
            )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the global session factory.

    Returns:
        async_sessionmaker: Session factory for creating async sessions
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autoflush=False,  # Manual control over flushing
            autocommit=False,  # Use explicit transactions
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session with automatic lifecycle.

    Usage in FastAPI routes:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            repo = SessionRepositoryImpl(db)
            ...

    Yields:
        AsyncSession: Database session with automatic commit/rollback
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_repository_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for manual session management outside FastAPI.

    Usage for background tasks or manual transaction control:
        async with get_repository_session() as session:
            repo = SessionRepositoryImpl(session)
            await repo.create(entity)
            # Session auto-commits on exit

    Yields:
        AsyncSession: Database session with manual transaction control
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection() -> None:
    """
    Close database engine and cleanup connections.

    Should be called during application shutdown to properly
    dispose of connection pool and close all connections.
    """
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
