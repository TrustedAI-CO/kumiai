"""SQLAlchemy implementation of TaskRepository."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError, EntityNotFound
from app.domain.entities.task import Task as TaskEntity
from app.domain.repositories.task_repository import TaskRepository
from app.infrastructure.database.mappers import TaskMapper
from app.infrastructure.database.models import Task
from app.infrastructure.database.repositories.base_repository import BaseRepositoryImpl


class TaskRepositoryImpl(BaseRepositoryImpl[TaskEntity], TaskRepository):
    """SQLAlchemy implementation of TaskRepository."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._mapper = TaskMapper()

    async def create(self, task: TaskEntity) -> TaskEntity:
        try:
            model = self._mapper.to_model(task)
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to create task: {e}") from e

    async def get_by_id(self, task_id: UUID) -> Optional[TaskEntity]:
        try:
            stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._mapper.to_entity(model) if model else None
        except Exception as e:
            raise DatabaseError(f"Failed to get task: {e}") from e

    async def get_by_project_id(self, project_id: UUID) -> List[TaskEntity]:
        try:
            stmt = (
                select(Task)
                .where(Task.project_id == project_id, Task.deleted_at.is_(None))
                .order_by(Task.created_at)
            )
            result = await self._session.execute(stmt)
            return [self._mapper.to_entity(m) for m in result.scalars().all()]
        except Exception as e:
            raise DatabaseError(f"Failed to list tasks: {e}") from e

    async def update(self, task: TaskEntity) -> TaskEntity:
        try:
            stmt = select(Task).where(Task.id == task.id, Task.deleted_at.is_(None))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is None:
                raise EntityNotFound(f"Task {task.id} not found")

            self._mapper.to_model(task, model)
            await self._session.flush()
            await self._session.refresh(model)
            return self._mapper.to_entity(model)
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update task: {e}") from e

    async def delete(self, task_id: UUID) -> None:
        try:
            stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is None:
                raise EntityNotFound(f"Task {task_id} not found")

            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete task: {e}") from e
