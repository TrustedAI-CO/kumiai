"""Skill API endpoints (File-based, Claude SDK compatible)."""

from typing import List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_skill_service
from app.application.dtos import (
    FileContentRequest,
    FileContentResponse,
    FileInfoDTO,
)
from app.application.dtos.requests import (
    CreateSkillRequest,
    ImportSkillRequest,
    UpdateSkillRequest,
)
from app.application.dtos.skill_dto import ImportSkillResponse, SkillDTO
from app.application.services import SkillService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/skills/debug/repo-info")
async def get_repo_debug_info(
    service: SkillService = Depends(get_skill_service),
):
    """Debug endpoint to check repository configuration."""
    from app.api.dependencies import get_skill_repository

    repo = get_skill_repository()
    base_path = await repo.get_base_path()

    return {
        "base_path": str(base_path),
        "base_path_absolute": base_path.is_absolute(),
        "base_path_exists": base_path.exists(),
        "base_path_resolved": str(base_path.resolve()),
    }


@router.post(
    "/skills",
    response_model=SkillDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new skill",
    description="Create a new skill with name, file path, and optional tags",
)
async def create_skill(
    request: CreateSkillRequest,
    service: SkillService = Depends(get_skill_service),
) -> SkillDTO:
    """
    Create a new skill.

    Args:
        request: Skill creation request
        service: Skill service (injected)

    Returns:
        Created skill

    Raises:
        400: Validation error
    """
    logger.info(
        "create_skill_request",
        name=request.name,
        tags=request.tags,
    )

    # Auto-generate file_path if not provided
    file_path = request.file_path
    if not file_path:
        # Use custom ID if provided, otherwise generate from name
        skill_id = (
            request.id
            if request.id
            else request.name.lower().replace(" ", "-").replace("_", "-")
        )
        file_path = f"/skills/{skill_id}/"

    return await service.create_skill(
        name=request.name,
        file_path=file_path,
        description=request.description,
        tags=request.tags,
        icon=request.icon or "zap",
        icon_color=request.iconColor or "#4A90E2",
    )


@router.post(
    "/skills/import",
    response_model=ImportSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import a skill from GitHub or local path",
    description="Import a skill from a GitHub URL or local filesystem path",
)
async def import_skill(
    request: ImportSkillRequest,
    service: SkillService = Depends(get_skill_service),
) -> ImportSkillResponse:
    """
    Import a skill from a source URL or local path.

    Supports:
    - GitHub URLs (e.g., https://github.com/anthropics/skills/tree/main/skills/internal-comms)
    - Local filesystem paths (e.g., /path/to/skill/directory)

    Args:
        request: Import request with source URL/path and optional custom skill ID
        service: Skill service (injected)

    Returns:
        Import response with imported skill details and status message

    Raises:
        400: Validation error (invalid source, missing SKILL.md, etc.)
        409: Skill with same ID already exists
    """
    logger.info(
        "import_skill_request",
        source=request.source,
        custom_skill_id=request.skill_id,
    )

    return await service.import_skill(
        source=request.source,
        custom_skill_id=request.skill_id,
    )


@router.get(
    "/skills/search",
    response_model=List[SkillDTO],
    summary="Search skills by tags",
    description="Search skills by tags with AND/OR matching",
)
async def search_skills_by_tags(
    tags: List[str] = Query(..., description="Tags to search for"),
    match_all: bool = Query(
        False, description="If True, match ALL tags (AND). If False, match ANY tag (OR)"
    ),
    service: SkillService = Depends(get_skill_service),
) -> List[SkillDTO]:
    """
    Search skills by tags.

    Args:
        tags: List of tags to search for
        match_all: If True, require all tags (AND). If False, match any tag (OR)
        service: Skill service (injected)

    Returns:
        List of matching skills
    """
    logger.info(
        "search_skills_request",
        tags=tags,
        match_all=match_all,
    )
    return await service.search_by_tags(tags=tags, match_all=match_all)


@router.get(
    "/skills",
    response_model=List[SkillDTO],
    summary="List all skills",
    description="Retrieve a list of all skills",
)
async def list_skills(
    service: SkillService = Depends(get_skill_service),
) -> List[SkillDTO]:
    """
    List all skills.

    Args:
        service: Skill service (injected)

    Returns:
        List of skills
    """
    return await service.list_skills()


@router.get(
    "/skills/{skill_id}",
    response_model=SkillDTO,
    summary="Get skill by ID",
    description="Retrieve a skill by its ID (directory name)",
)
async def get_skill(
    skill_id: str,
    service: SkillService = Depends(get_skill_service),
) -> SkillDTO:
    """
    Get skill by ID.

    Args:
        skill_id: Skill ID (directory name, e.g., "database-query")
        service: Skill service (injected)

    Returns:
        Skill details

    Raises:
        404: Skill not found
    """
    return await service.get_skill(skill_id)


@router.patch(
    "/skills/{skill_id}",
    response_model=SkillDTO,
    summary="Update a skill",
    description="Update skill metadata (updates SKILL.md frontmatter)",
)
@router.put(
    "/skills/{skill_id}",
    response_model=SkillDTO,
    summary="Update a skill",
    description="Update skill metadata (updates SKILL.md frontmatter)",
)
async def update_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    service: SkillService = Depends(get_skill_service),
) -> SkillDTO:
    """
    Update a skill.

    Args:
        skill_id: Skill ID (directory name)
        request: Update request with fields to change
        service: Skill service (injected)

    Returns:
        Updated skill

    Raises:
        404: Skill not found
        400: Validation error
    """
    logger.info(
        "update_skill_request",
        skill_id=skill_id,
        update_fields=list(request.model_dump(exclude_unset=True).keys()),
    )
    return await service.update_skill(
        skill_id=skill_id,
        name=request.name,
        description=request.description,
        file_path=request.file_path,
        tags=request.tags,
        icon=request.icon,
        icon_color=request.iconColor,
    )


@router.delete(
    "/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a skill",
    description="Soft-delete a skill (renames directory with .deleted suffix)",
)
async def delete_skill(
    skill_id: str,
    service: SkillService = Depends(get_skill_service),
) -> None:
    """
    Delete a skill (soft delete).

    Args:
        skill_id: Skill ID (directory name)
        service: Skill service (injected)

    Raises:
        404: Skill not found
    """
    logger.info("delete_skill_request", skill_id=skill_id)
    await service.delete_skill(skill_id)


# File Operations


@router.get(
    "/skills/{skill_id}/files",
    response_model=List[FileInfoDTO],
    summary="List skill files",
    description="List all files in skill directory (recursive)",
)
async def list_skill_files(
    skill_id: str,
    service: SkillService = Depends(get_skill_service),
) -> List[FileInfoDTO]:
    """
    List all files in skill directory.

    Args:
        skill_id: Skill ID (directory name)
        service: Skill service (injected)

    Returns:
        List of file information

    Raises:
        404: Skill not found
    """
    return await service.list_skill_files(skill_id)


@router.get(
    "/skills/{skill_id}/files/content",
    response_model=FileContentResponse,
    summary="Get file content",
    description="Read file content from skill directory",
)
async def get_skill_file_content(
    skill_id: str,
    file_path: str = Query(..., description="Path to file relative to skill directory"),
    service: SkillService = Depends(get_skill_service),
) -> FileContentResponse:
    """
    Read file content from skill directory.

    Args:
        skill_id: Skill ID (directory name)
        file_path: Path relative to skill directory
        service: Skill service (injected)

    Returns:
        File content and metadata

    Raises:
        404: Skill or file not found
        400: Invalid file path or file type not allowed
    """
    logger.info(
        "get_skill_file_content",
        skill_id=skill_id,
        file_path=file_path,
    )
    return await service.get_skill_file_content(skill_id, file_path)


@router.put(
    "/skills/{skill_id}/files/content",
    response_model=FileContentResponse,
    summary="Update file content",
    description="Update or create file in skill directory",
)
async def update_skill_file_content(
    skill_id: str,
    request: FileContentRequest,
    service: SkillService = Depends(get_skill_service),
) -> FileContentResponse:
    """
    Update or create file in skill directory.

    Args:
        skill_id: Skill ID (directory name)
        request: File content request
        service: Skill service (injected)

    Returns:
        Updated file content and metadata

    Raises:
        404: Skill not found
        400: Invalid file path or file type not allowed
    """
    logger.info(
        "update_skill_file_content",
        skill_id=skill_id,
        file_path=request.file_path,
    )
    return await service.update_skill_file_content(skill_id, request)


@router.delete(
    "/skills/{skill_id}/files",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete file",
    description="Delete file from skill directory",
)
async def delete_skill_file(
    skill_id: str,
    file_path: str = Query(..., description="Path to file relative to skill directory"),
    service: SkillService = Depends(get_skill_service),
) -> None:
    """
    Delete file from skill directory.

    Protected files (SKILL.md) cannot be deleted.

    Args:
        skill_id: Skill ID (directory name)
        file_path: Path relative to skill directory
        service: Skill service (injected)

    Raises:
        404: Skill or file not found
        400: Invalid file path or protected file
    """
    logger.info(
        "delete_skill_file",
        skill_id=skill_id,
        file_path=file_path,
    )
    await service.delete_skill_file(skill_id, file_path)


# Claude SDK-specific endpoints


@router.get(
    "/skills/{skill_id}/content",
    response_class=PlainTextResponse,
    summary="Load SKILL.md content",
    description="Load full SKILL.md content for loading into AI context (Claude SDK)",
)
async def load_skill_content(
    skill_id: str,
    service: SkillService = Depends(get_skill_service),
) -> str:
    """
    Load full SKILL.md content for AI context.

    Args:
        skill_id: Skill ID (directory name)
        service: Skill service (injected)

    Returns:
        Full SKILL.md content including frontmatter

    Raises:
        404: Skill not found
    """
    logger.info("load_skill_content", skill_id=skill_id)
    return await service.load_skill_content(skill_id)


@router.get(
    "/skills/{skill_id}/docs/{doc_path:path}",
    response_class=PlainTextResponse,
    summary="Load supporting document",
    description="Load supporting document (e.g., FORMS.md, reference/finance.md) for AI context",
)
async def load_supporting_doc(
    skill_id: str,
    doc_path: str,
    service: SkillService = Depends(get_skill_service),
) -> str:
    """
    Load supporting document for AI context.

    Args:
        skill_id: Skill ID (directory name)
        doc_path: Relative path to document (e.g., "FORMS.md", "reference/finance.md")
        service: Skill service (injected)

    Returns:
        Document content

    Raises:
        404: Skill or document not found
        400: Invalid document path
    """
    logger.info(
        "load_supporting_doc",
        skill_id=skill_id,
        doc_path=doc_path,
    )
    return await service.load_supporting_doc(skill_id, doc_path)
