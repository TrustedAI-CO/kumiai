"""Project API endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_project_service
from app.application.dtos.project_dto import ProjectDTO
from app.application.dtos.requests import (
    AssignPMRequest,
    CreateProjectRequest,
    UpdateProjectRequest,
)
from app.application.services import ProjectService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/projects",
    response_model=ProjectDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with optional PM assignment",
)
async def create_project(
    request: CreateProjectRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDTO:
    """
    Create a new project.

    Args:
        request: Project creation request
        service: Project service (injected)

    Returns:
        Created project

    Raises:
        400: Validation error
    """
    logger.info(
        "create_project_request",
        name=request.name,
        has_pm=request.pm_agent_id is not None,
    )
    return await service.create_project(request)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectDTO,
    summary="Get project by ID",
    description="Retrieve a project by its UUID",
)
async def get_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDTO:
    """
    Get project by ID.

    Args:
        project_id: Project UUID
        service: Project service (injected)

    Returns:
        Project details

    Raises:
        404: Project not found
    """
    return await service.get_project(project_id)


@router.get(
    "/projects",
    response_model=List[ProjectDTO],
    summary="List all projects",
    description="Retrieve a list of all projects",
)
async def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> List[ProjectDTO]:
    """
    List all projects.

    Args:
        service: Project service (injected)

    Returns:
        List of projects
    """
    return await service.list_projects()


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectDTO,
    summary="Update a project",
    description="Update project metadata (name, description, path)",
)
async def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDTO:
    """
    Update a project.

    Args:
        project_id: Project UUID
        request: Update request with fields to change
        service: Project service (injected)

    Returns:
        Updated project

    Raises:
        404: Project not found
        400: Validation error
    """
    logger.info(
        "update_project_request",
        project_id=str(project_id),
        update_fields=list(request.model_dump(exclude_unset=True).keys()),
    )
    return await service.update_project(project_id, request)


@router.post(
    "/projects/{project_id}/assign-pm",
    response_model=ProjectDTO,
    summary="Assign PM to project",
    description="Assign a PM agent to the project (atomic operation: creates session + updates project)",
)
async def assign_pm(
    project_id: UUID,
    request: AssignPMRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDTO:
    """
    Assign a PM to the project.

    This is an atomic operation that:
    1. Creates a PM session for the agent
    2. Updates the project with PM assignment

    Args:
        project_id: Project UUID
        request: PM assignment request
        service: Project service (injected)

    Returns:
        Updated project with PM assignment

    Raises:
        404: Project not found
    """
    logger.info(
        "assign_pm_request",
        project_id=str(project_id),
        pm_agent_id=request.pm_agent_id,
    )
    return await service.assign_pm(project_id, request)


@router.delete(
    "/projects/{project_id}/pm",
    response_model=ProjectDTO,
    summary="Remove PM from project",
    description="Remove PM assignment from project",
)
async def remove_pm(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDTO:
    """
    Remove PM from project.

    Args:
        project_id: Project UUID
        service: Project service (injected)

    Returns:
        Updated project without PM

    Raises:
        404: Project not found
    """
    logger.info("remove_pm_request", project_id=str(project_id))
    return await service.remove_pm(project_id)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Soft-delete a project",
)
async def delete_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """
    Delete a project (soft delete).

    Args:
        project_id: Project UUID
        service: Project service (injected)

    Raises:
        404: Project not found
    """
    logger.info("delete_project_request", project_id=str(project_id))
    await service.delete_project(project_id)
