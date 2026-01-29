"""SQLAlchemy implementation of SessionRepository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DatabaseError, EntityNotFound
from app.domain.entities import Session as SessionEntity
from app.domain.repositories import SessionRepository
from app.domain.value_objects import SessionStatus, SessionType
from app.infrastructure.database.mappers import SessionMapper
from app.infrastructure.database.models import Session
from app.infrastructure.database.repositories.base_repository import BaseRepositoryImpl


class SessionRepositoryImpl(BaseRepositoryImpl[SessionEntity], SessionRepository):
    """
    SQLAlchemy implementation of SessionRepository.

    Adapts domain Session entities to Session model persistence.
    Inherits common functionality from BaseRepositoryImpl.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session)
        self._mapper = SessionMapper()

    async def create(self, session: SessionEntity) -> SessionEntity:
        """Create and persist a new session."""
        try:
            model = self._mapper.to_model(session)
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to create session: {e}") from e

    async def get_by_id(
        self, session_id: UUID, with_messages: bool = False, with_project: bool = False
    ) -> Optional[SessionEntity]:
        """
        Retrieve session by ID with optional eager loading.

        Args:
            session_id: UUID of session to retrieve
            with_messages: Eager load messages relationship to avoid N+1
            with_project: Eager load project relationship to avoid N+1

        Returns:
            Session entity if found, None otherwise
        """
        try:
            stmt = select(Session).where(
                Session.id == session_id, Session.deleted_at.is_(None)
            )

            # Add eager loading to prevent N+1 queries
            if with_messages:
                stmt = stmt.options(selectinload(Session.messages))
            if with_project:
                stmt = stmt.options(selectinload(Session.project))

            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to get session {session_id}: {e}") from e

    async def get_by_project_id(
        self,
        project_id: UUID,
        include_deleted: bool = False,
        with_messages: bool = False,
    ) -> List[SessionEntity]:
        """
        Get all sessions associated with a project.

        Args:
            project_id: UUID of the project
            include_deleted: Whether to include soft-deleted sessions
            with_messages: Eager load messages to avoid N+1 queries

        Returns:
            List of session entities
        """
        try:
            stmt = select(Session).where(Session.project_id == project_id)

            if not include_deleted:
                stmt = stmt.where(Session.deleted_at.is_(None))

            # Add eager loading to prevent N+1 queries when accessing messages
            if with_messages:
                stmt = stmt.options(selectinload(Session.messages))

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [self._mapper.to_entity(model) for model in models]
        except Exception as e:
            raise DatabaseError(
                f"Failed to get sessions for project {project_id}: {e}"
            ) from e

    async def get_active_sessions(self) -> List[SessionEntity]:
        """Get all active (non-deleted) sessions, including ERROR sessions."""
        try:
            # Active sessions are INITIALIZING, IDLE, WORKING, ERROR
            active_statuses = [
                SessionStatus.INITIALIZING.value,
                SessionStatus.IDLE.value,
                SessionStatus.WORKING.value,
                SessionStatus.ERROR.value,
            ]

            stmt = select(Session).where(
                Session.status.in_(active_statuses), Session.deleted_at.is_(None)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [self._mapper.to_entity(model) for model in models]
        except Exception as e:
            raise DatabaseError(f"Failed to get active sessions: {e}") from e

    async def get_by_status(self, status: SessionStatus) -> List[SessionEntity]:
        """Get sessions by status."""
        try:
            stmt = select(Session).where(
                Session.status == status.value, Session.deleted_at.is_(None)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [self._mapper.to_entity(model) for model in models]
        except Exception as e:
            raise DatabaseError(
                f"Failed to get sessions with status {status}: {e}"
            ) from e

    async def update(self, session: SessionEntity) -> SessionEntity:
        """Update existing session."""
        try:
            from sqlalchemy.orm import attributes

            # Get existing model
            stmt = select(Session).where(Session.id == session.id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise EntityNotFound(f"Session {session.id} not found")

            # Update model from entity
            model = self._mapper.to_model(session, model)
            # Mark context as modified to ensure JSONB changes are persisted
            attributes.flag_modified(model, "context")
            await self._session.flush()
            await self._session.refresh(model)

            return self._mapper.to_entity(model)
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update session {session.id}: {e}") from e

    async def delete(self, session_id: UUID) -> None:
        """Soft-delete a session."""
        try:
            stmt = select(Session).where(Session.id == session_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise EntityNotFound(f"Session {session_id} not found")

            model.deleted_at = datetime.utcnow()
            await self._session.flush()
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete session {session_id}: {e}") from e

    async def exists(self, session_id: UUID) -> bool:
        """Check if session exists (including soft-deleted)."""
        try:
            stmt = select(Session.id).where(Session.id == session_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check session existence: {e}") from e

    async def get_latest_pm_session(self, project_id: UUID) -> Optional[SessionEntity]:
        """
        Get the latest PM session for a project.

        Retrieves the most recently created PM session that is not deleted.
        This is useful for specialists to find their project manager, and will
        support PM restart/recreate scenarios where a new PM replaces an old one.

        Args:
            project_id: The project UUID to find PM session for

        Returns:
            The latest PM session entity, or None if no PM found

        Raises:
            DatabaseError: If query fails
        """
        try:
            stmt = (
                select(Session)
                .where(
                    Session.project_id == project_id,
                    Session.session_type == SessionType.PM.value,
                    Session.deleted_at.is_(None),
                )
                .order_by(Session.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(
                f"Failed to get latest PM session for project {project_id}: {e}"
            ) from e
