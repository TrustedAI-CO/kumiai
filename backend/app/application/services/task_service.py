"""Task service - application layer use cases."""

from typing import List
from uuid import UUID, uuid4

from app.application.dtos.task_dto import CreateTaskRequest, TaskDTO, UpdateTaskRequest
from app.application.services.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.domain.entities.task import Task
from app.domain.repositories import ProjectRepository
from app.domain.repositories.task_repository import TaskRepository
from app.domain.value_objects.task_status import TaskStatus


class TaskService:
    """Orchestrates task-related use cases."""

    def __init__(self, task_repo: TaskRepository, project_repo: ProjectRepository):
        self._task_repo = task_repo
        self._project_repo = project_repo

    async def create_task(
        self, project_id: UUID, request: CreateTaskRequest
    ) -> TaskDTO:
        project = await self._project_repo.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        task = Task(
            id=uuid4(),
            project_id=project_id,
            name=request.name,
            description=request.description,
        )
        task.validate()
        created = await self._task_repo.create(task)
        return TaskDTO.from_entity(created)

    async def get_task(self, task_id: UUID) -> TaskDTO:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")
        return TaskDTO.from_entity(task)

    async def list_tasks(self, project_id: UUID) -> List[TaskDTO]:
        tasks = await self._task_repo.get_by_project_id(project_id)
        return [TaskDTO.from_entity(t) for t in tasks]

    async def update_task(self, task_id: UUID, request: UpdateTaskRequest) -> TaskDTO:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")

        if request.name is not None or request.description is not None:
            task.update_metadata(name=request.name, description=request.description)

        if request.status is not None:
            task.status = TaskStatus(request.status)

        updated = await self._task_repo.update(task)
        return TaskDTO.from_entity(updated)

    async def delete_task(self, task_id: UUID) -> None:
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task {task_id} not found")
        await self._task_repo.delete(task_id)
