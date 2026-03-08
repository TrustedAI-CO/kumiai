"""Task API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_task_service
from app.application.dtos.task_dto import CreateTaskRequest, TaskDTO, UpdateTaskRequest
from app.application.services.exceptions import ProjectNotFoundError, TaskNotFoundError
from app.application.services.task_service import TaskService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: UUID,
    request: CreateTaskRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskDTO:
    try:
        return await service.create_task(project_id, request)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/projects/{project_id}/tasks", response_model=List[TaskDTO])
async def list_tasks(
    project_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> List[TaskDTO]:
    return await service.list_tasks(project_id)


@router.get("/tasks/{task_id}", response_model=TaskDTO)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskDTO:
    try:
        return await service.get_task(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/tasks/{task_id}", response_model=TaskDTO)
async def update_task(
    task_id: UUID,
    request: UpdateTaskRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskDTO:
    try:
        return await service.update_task(task_id, request)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> None:
    try:
        await service.delete_task(task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
