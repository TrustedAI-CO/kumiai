"""Agent API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_agent_service
from app.application.dtos import (
    FileContentRequest,
    FileContentResponse,
    FileInfoDTO,
)
from app.application.dtos.agent_dto import AgentDTO
from app.application.dtos.requests import (
    CreateAgentRequest,
    UpdateAgentRequest,
)
from app.application.services.agent_service import AgentService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/agents",
    response_model=AgentDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new agent with skills and tool permissions",
)
async def create_agent(
    request: CreateAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentDTO:
    """
    Create a new agent.

    Args:
        request: Agent creation request
        service: Agent service (injected)

    Returns:
        Created agent

    Raises:
        400: Validation error
    """
    logger.info(
        "create_agent_request",
        name=request.name,
    )
    return await service.create_agent(request)


@router.get(
    "/agents",
    response_model=List[AgentDTO],
    summary="List agents",
    description="List all agents",
)
async def list_agents(
    service: AgentService = Depends(get_agent_service),
) -> List[AgentDTO]:
    """
    List all agents.

    Args:
        service: Agent service (injected)

    Returns:
        List of agents
    """
    return await service.list_agents()


@router.get(
    "/agents/search",
    response_model=List[AgentDTO],
    summary="Search agents by tags",
    description="Search agents by tags with AND/OR logic",
)
async def search_agents(
    tags: str = Query(..., description="Comma-separated list of tags"),
    match_all: bool = Query(
        False, description="If true, match ALL tags (AND). If false, match ANY tag (OR)"
    ),
    service: AgentService = Depends(get_agent_service),
) -> List[AgentDTO]:
    """
    Search agents by tags.

    Args:
        tags: Comma-separated list of tags
        match_all: Match ALL tags (AND) or ANY tag (OR)
        service: Agent service (injected)

    Returns:
        List of matching agents
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    return await service.search_by_tags(tag_list, match_all)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentDTO,
    summary="Get agent by ID",
    description="Retrieve an agent by its ID",
)
async def get_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentDTO:
    """
    Get agent by ID.

    Args:
        agent_id: Agent ID (directory name)
        service: Agent service (injected)

    Returns:
        Agent details

    Raises:
        404: Agent not found
    """
    return await service.get_agent(agent_id)


@router.patch(
    "/agents/{agent_id}",
    response_model=AgentDTO,
    summary="Update an agent",
    description="Update agent metadata",
)
@router.put(
    "/agents/{agent_id}",
    response_model=AgentDTO,
    summary="Update an agent",
    description="Update agent metadata",
)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentDTO:
    """
    Update an agent.

    Args:
        agent_id: Agent ID
        request: Update request with fields to change
        service: Agent service (injected)

    Returns:
        Updated agent

    Raises:
        404: Agent not found
        400: Validation error
    """
    logger.info(
        "update_agent_request",
        agent_id=agent_id,
        update_fields=list(request.model_dump(exclude_unset=True).keys()),
    )
    return await service.update_agent(agent_id, request)


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent",
    description="Soft-delete an agent",
)
async def delete_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> None:
    """
    Delete an agent (soft delete).

    Args:
        agent_id: Agent ID
        service: Agent service (injected)

    Raises:
        404: Agent not found
    """
    logger.info("delete_agent_request", agent_id=agent_id)
    await service.delete_agent(agent_id)


# File Operations


@router.get(
    "/agents/{agent_id}/files",
    response_model=List[FileInfoDTO],
    summary="List agent files",
    description="List all files in agent directory (recursive)",
)
async def list_agent_files(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> List[FileInfoDTO]:
    """
    List all files in agent directory.

    Args:
        agent_id: Agent ID
        service: Agent service (injected)

    Returns:
        List of file information

    Raises:
        404: Agent not found
    """
    return await service.list_agent_files(agent_id)


@router.get(
    "/agents/{agent_id}/files/content",
    response_model=FileContentResponse,
    summary="Get file content",
    description="Read file content from agent directory",
)
async def get_agent_file_content(
    agent_id: str,
    file_path: str = Query(..., description="Path to file relative to agent directory"),
    service: AgentService = Depends(get_agent_service),
) -> FileContentResponse:
    """
    Read file content from agent directory.

    Args:
        agent_id: Agent ID
        file_path: Path relative to agent directory
        service: Agent service (injected)

    Returns:
        File content and metadata

    Raises:
        404: Agent or file not found
        400: Invalid file path or file type not allowed
    """
    logger.info(
        "get_agent_file_content",
        agent_id=agent_id,
        file_path=file_path,
    )
    return await service.get_agent_file_content(agent_id, file_path)


@router.put(
    "/agents/{agent_id}/files/content",
    response_model=FileContentResponse,
    summary="Update file content",
    description="Update or create file in agent directory",
)
async def update_agent_file_content(
    agent_id: str,
    request: FileContentRequest,
    service: AgentService = Depends(get_agent_service),
) -> FileContentResponse:
    """
    Update or create file in agent directory.

    Args:
        agent_id: Agent ID
        request: File content request
        service: Agent service (injected)

    Returns:
        Updated file content and metadata

    Raises:
        404: Agent not found
        400: Invalid file path or file type not allowed
    """
    logger.info(
        "update_agent_file_content",
        agent_id=agent_id,
        file_path=request.file_path,
    )
    return await service.update_agent_file_content(agent_id, request)


@router.delete(
    "/agents/{agent_id}/files",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete file from agent directory",
)
async def delete_agent_file(
    agent_id: str,
    file_path: str = Query(..., description="Path to file relative to agent directory"),
    service: AgentService = Depends(get_agent_service),
) -> None:
    """
    Delete file from agent directory.

    Protected files (CLAUDE.md) cannot be deleted.

    Args:
        agent_id: Agent ID
        file_path: Path relative to agent directory
        service: Agent service (injected)

    Raises:
        404: Agent or file not found
        400: Invalid file path or protected file
    """
    logger.info(
        "delete_agent_file",
        agent_id=agent_id,
        file_path=file_path,
    )
    await service.delete_agent_file(agent_id, file_path)


# Agent Content Loading (for AI Context)


@router.get(
    "/agents/{agent_id}/content",
    response_model=str,
    summary="Load CLAUDE.md content",
    description="Load full CLAUDE.md content for AI context",
)
async def load_agent_content(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> str:
    """
    Load full CLAUDE.md content for AI context.

    This endpoint returns the complete CLAUDE.md file including
    frontmatter and body, suitable for embedding in prompts.

    Args:
        agent_id: Agent ID
        service: Agent service (injected)

    Returns:
        Complete CLAUDE.md content

    Raises:
        404: Agent not found
    """
    logger.info("load_agent_content", agent_id=agent_id)
    return await service.load_agent_content(agent_id)


@router.get(
    "/agents/{agent_id}/docs/{doc_path:path}",
    response_model=str,
    summary="Load supporting document",
    description="Load a supporting document from agent directory",
)
async def load_supporting_doc(
    agent_id: str,
    doc_path: str,
    service: AgentService = Depends(get_agent_service),
) -> str:
    """
    Load a supporting document from agent directory.

    Args:
        agent_id: Agent ID
        doc_path: Relative path to document within agent directory
        service: Agent service (injected)

    Returns:
        Document content

    Raises:
        404: Agent or document not found
        403: Path traversal attempt detected
    """
    logger.info(
        "load_supporting_doc",
        agent_id=agent_id,
        doc_path=doc_path,
    )
    return await service.load_supporting_doc(agent_id, doc_path)
