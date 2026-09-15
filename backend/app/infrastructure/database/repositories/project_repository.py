"""SQLAlchemy implementation of ProjectRepository."""

# feature: WORK-01

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError, EntityNotFound
from app.domain.entities import Project as ProjectEntity
from app.domain.repositories import ProjectRepository
from app.infrastructure.database.mappers import ProjectMapper
from app.infrastructure.database.models import Project
from app.infrastructure.database.repositories.base_repository import BaseRepositoryImpl


class ProjectRepositoryImpl(BaseRepositoryImpl[ProjectEntity], ProjectRepository):
    """
    SQLAlchemy implementation of ProjectRepository.

    Adapts domain Project entities to Project model persistence.
    Inherits common functionality from BaseRepositoryImpl.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session)
        self._mapper = ProjectMapper()

    async def create(self, project: ProjectEntity) -> ProjectEntity:
        """Create and persist a new project."""
        try:
            model = self._mapper.to_model(project)
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to create project: {e}") from e

    async def get_by_id(self, project_id: UUID) -> Optional[ProjectEntity]:
        """Retrieve project by ID."""
        try:
            stmt = select(Project).where(
                Project.id == project_id, Project.deleted_at.is_(None)
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to get project {project_id}: {e}") from e

    async def get_all(self, include_deleted: bool = False) -> List[ProjectEntity]:
        """Get all projects."""
        try:
            stmt = select(Project)

            if not include_deleted:
                stmt = stmt.where(Project.deleted_at.is_(None))

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [self._mapper.to_entity(model) for model in models]
        except Exception as e:
            raise DatabaseError(f"Failed to get all projects: {e}") from e

    async def update(self, project: ProjectEntity) -> ProjectEntity:
        """Update existing project."""
        try:
            # Get existing model
            stmt = select(Project).where(Project.id == project.id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise EntityNotFound(f"Project {project.id} not found")

            # Update model from entity
            model = self._mapper.to_model(project, model)
            await self._session.flush()
            await self._session.refresh(model)

            return self._mapper.to_entity(model)
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update project {project.id}: {e}") from e

    async def delete(
        self, project_id: UUID, deleted_at: datetime | None = None
    ) -> None:
        """Soft-delete a project."""
        try:
            stmt = select(Project).where(Project.id == project_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise EntityNotFound(f"Project {project_id} not found")

            model.deleted_at = deleted_at or datetime.now(timezone.utc)
            await self._session.flush()
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete project {project_id}: {e}") from e

    async def get_deletion_info(
        self, project_id: UUID
    ) -> Optional[tuple[Optional[datetime], str]]:
        """
        Return (deleted_at, path) for a project, including a deleted one.

        get_by_id deliberately hides deleted projects, but restore has to reason about
        exactly those. Returns None when no such row exists at all, so the caller can
        tell "no such project" from "project exists and is not deleted".
        """
        try:
            stmt = select(Project.deleted_at, Project.path).where(
                Project.id == project_id
            )
            result = await self._session.execute(stmt)
            row = result.first()
            return (row[0], row[1]) if row else None
        except Exception as e:
            raise DatabaseError(
                f"Failed to read deletion info for project {project_id}: {e}"
            ) from e

    async def is_path_taken(self, path: str, exclude_id: UUID) -> bool:
        """Whether a different, live project already occupies this path."""
        try:
            stmt = select(Project.id).where(
                Project.path == path,
                Project.deleted_at.is_(None),
                Project.id != exclude_id,
            )
            result = await self._session.execute(stmt)
            return result.first() is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check path {path}: {e}") from e

    async def restore(self, project_id: UUID) -> None:
        """Clear a project's deleted_at, making it visible again."""
        try:
            stmt = (
                update(Project).where(Project.id == project_id).values(deleted_at=None)
            )
            await self._session.execute(stmt)
            await self._session.flush()
        except Exception as e:
            raise DatabaseError(f"Failed to restore project {project_id}: {e}") from e

    async def exists(self, project_id: UUID) -> bool:
        """Check if project exists (including soft-deleted)."""
        try:
            stmt = select(Project.id).where(Project.id == project_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check project existence: {e}") from e
