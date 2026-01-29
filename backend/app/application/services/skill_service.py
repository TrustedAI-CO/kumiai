"""Skill service - application layer use cases."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import yaml

from app.application.dtos import (
    FileContentRequest,
    FileContentResponse,
    FileInfoDTO,
)
from app.application.dtos.skill_dto import ImportSkillResponse, SkillDTO
from app.application.services.exceptions import SkillNotFoundError
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.domain.entities import Skill
from app.domain.repositories import SkillRepository
from app.infrastructure.filesystem import FileService

logger = get_logger(__name__)


class SkillService:
    """
    Skill service - manage skills.

    Responsibilities:
    - Create/manage skills
    - Search skills by tags
    - Enforce business rules
    """

    def __init__(
        self,
        skill_repo: SkillRepository,
        file_service: Optional[FileService] = None,
    ):
        """Initialize service with repository and optional file service."""
        self._skill_repo = skill_repo
        self._file_service = file_service or FileService()

    async def create_skill(
        self,
        name: str,
        file_path: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        icon: str = "zap",
        icon_color: str = "#4A90E2",
    ) -> SkillDTO:
        """
        Create a new skill (file-based).

        Args:
            name: Skill name
            file_path: Path to skill directory (e.g., /skills/database-query/)
            description: Skill description (optional)
            tags: List of tags (optional)
            icon: Icon name (default: zap)
            icon_color: Icon color (default: #4A90E2)

        Returns:
            Created skill DTO
        """
        # Generate skill ID from file_path or name
        # Extract directory name from path like /skills/database-query/
        skill_id = Path(file_path).name or name.lower().replace(" ", "-")

        # Create domain entity
        skill = Skill(
            id=skill_id,
            name=name,
            description=description,
            file_path=file_path,
            tags=tags or [],
            icon=icon,
            icon_color=icon_color,
        )

        # Persist (creates SKILL.md with frontmatter)
        await self._skill_repo.create(skill)

        # Reload from repository to get actual filesystem path
        reloaded = await self._skill_repo.get_by_id(skill_id)

        return SkillDTO.from_entity(reloaded)

    async def import_skill(
        self, source: str, custom_skill_id: Optional[str] = None
    ) -> ImportSkillResponse:
        """
        Import a skill from a GitHub URL or local filesystem path.

        Args:
            source: GitHub URL or local filesystem path to skill directory
            custom_skill_id: Optional custom skill ID (defaults to directory name)

        Returns:
            ImportSkillResponse with imported skill and status message

        Raises:
            ValidationError: If source is invalid or SKILL.md is missing/invalid
        """
        logger.info(
            "=== IMPORT_SKILL_METHOD_CALLED ===",
            source=source,
            version="v2_with_detailed_errors",
        )

        # Determine if source is a URL or local path
        parsed_url = urlparse(source)
        is_github_url = parsed_url.netloc in ["github.com", "www.github.com"]

        logger.info(
            "import_skill_start",
            source=source,
            is_github_url=is_github_url,
            custom_skill_id=custom_skill_id,
        )

        temp_dir = None
        source_path: Path

        try:
            if is_github_url:
                # Handle GitHub URL
                logger.info("import_skill_cloning_github", url=source)
                source_path, temp_dir = await self._clone_github_skill(source)
                logger.info("import_skill_cloned", source_path=str(source_path))
            else:
                # Handle local path
                source_path = Path(source).expanduser().resolve()
                if not source_path.exists():
                    raise ValidationError(f"Local path does not exist: {source}")
                if not source_path.is_dir():
                    raise ValidationError(f"Path is not a directory: {source}")

            # Validate SKILL.md exists
            skill_md = source_path / "SKILL.md"
            if not skill_md.exists():
                raise ValidationError(
                    "SKILL.md not found in source directory. "
                    "A valid skill must contain a SKILL.md file."
                )

            # Read and validate SKILL.md frontmatter
            skill_md_content = skill_md.read_text(encoding="utf-8")
            self._validate_skill_md_frontmatter(skill_md_content)

            # Parse frontmatter to extract metadata
            match = re.match(r"^---\n(.*?)\n---", skill_md_content, re.DOTALL)
            if not match:
                raise ValidationError("Invalid SKILL.md format")

            frontmatter = yaml.safe_load(match.group(1))

            # Determine skill ID
            skill_id = custom_skill_id or source_path.name
            # Sanitize skill ID
            skill_id = re.sub(r"[^a-z0-9-_]", "-", skill_id.lower())

            # Check if skill already exists
            if await self._skill_repo.exists(skill_id):
                raise ValidationError(
                    f"Skill '{skill_id}' already exists. "
                    f"Please choose a different skill ID or delete the existing skill first."
                )

            # Get skill repository base path (use directly, don't modify)
            base_path = await self._skill_repo.get_base_path()

            # Ensure it exists (but don't change the path itself)
            base_path.mkdir(parents=True, exist_ok=True)

            dest_path = base_path / skill_id

            logger.info(
                "import_skill_copying",
                source=str(source_path),
                destination=str(dest_path),
                skill_id=skill_id,
            )

            # Copy skill directory to repository
            if dest_path.exists():
                logger.info("import_skill_removing_existing", path=str(dest_path))
                shutil.rmtree(dest_path)
            shutil.copytree(source_path, dest_path)

            # Verify SKILL.md was copied
            copied_skill_md = dest_path / "SKILL.md"
            if not copied_skill_md.exists():
                raise ValidationError(
                    f"SKILL.md was not copied correctly to {dest_path}"
                )

            logger.info(
                "import_skill_files_copied",
                skill_id=skill_id,
                dest_path=str(dest_path),
                files_count=len(list(dest_path.rglob("*"))),
            )

            # Reload from repository to get the skill entity
            # (file-based repository will read from the filesystem)
            try:
                imported_skill = await self._skill_repo.get_by_id(skill_id)
                logger.info("import_skill_loaded", skill_id=skill_id)
            except Exception as e:
                # If loading fails, provide detailed error
                logger.error(
                    "import_skill_load_failed",
                    skill_id=skill_id,
                    base_path=str(base_path),
                    dest_path=str(dest_path),
                    error=str(e),
                )
                raise ValidationError(
                    f"Skill files copied to {dest_path} but failed to load. "
                    f"Error: {str(e)}"
                )

            skill_dto = SkillDTO.from_entity(imported_skill)

            return ImportSkillResponse(
                skill=skill_dto,
                status="success",
                message=f"Successfully imported skill '{skill_dto.name}' (ID: {skill_id})",
            )

        except subprocess.CalledProcessError as e:
            raise ValidationError(f"Failed to clone GitHub repository: {e}")
        except ValidationError:
            # Re-raise ValidationError as-is
            raise
        except NotFoundError as e:
            # NotFoundError during import shouldn't happen (we check exists() first)
            # but if it does, provide clear error
            logger.error(
                "import_skill_not_found_error",
                error_message=str(e),
                source=source,
                skill_id=skill_id if "skill_id" in locals() else None,
            )
            raise ValidationError(f"Import failed: {str(e)}")
        except Exception as e:
            # Catch any other unexpected exception
            logger.error(
                "import_skill_unexpected_error",
                error_type=type(e).__name__,
                error_message=str(e),
                source=source,
            )
            raise ValidationError(
                f"Failed to import skill: {type(e).__name__}: {str(e)}"
            )
        finally:
            # Clean up temporary directory if created
            if temp_dir is not None and temp_dir.exists():
                shutil.rmtree(temp_dir)

    async def _clone_github_skill(self, github_url: str) -> tuple[Path, Path]:
        """
        Clone a skill from GitHub.

        Args:
            github_url: GitHub URL (e.g., https://github.com/user/repo/tree/branch/path)

        Returns:
            Tuple of (skill_directory_path, temp_directory_path)

        Raises:
            ValidationError: If URL is invalid or cloning fails
        """
        # Parse GitHub URL
        # Supports formats:
        # - https://github.com/anthropics/skills/tree/main/skills/internal-comms
        # - https://github.com/user/repo/tree/branch/.claude/skills/skill-name

        parsed = urlparse(github_url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 2:
            raise ValidationError(f"Invalid GitHub URL format: {github_url}")

        owner = path_parts[0]
        repo = path_parts[1]

        # Extract branch and subdirectory if present
        branch = "main"
        subdirectory = None

        if len(path_parts) > 3 and path_parts[2] == "tree":
            branch = path_parts[3]
            if len(path_parts) > 4:
                subdirectory = "/".join(path_parts[4:])

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="kumiai_skill_import_"))

        try:
            # Clone repository
            clone_url = f"https://github.com/{owner}/{repo}.git"
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    branch,
                    clone_url,
                    str(temp_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            # Navigate to subdirectory if specified
            if subdirectory:
                skill_path = temp_dir / subdirectory
                if not skill_path.exists():
                    raise ValidationError(
                        f"Subdirectory not found in repository: {subdirectory}"
                    )
            else:
                skill_path = temp_dir

            return skill_path, temp_dir

        except subprocess.CalledProcessError as e:
            # Clean up on failure
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise ValidationError(
                f"Failed to clone GitHub repository: {e.stderr if e.stderr else str(e)}"
            )

    def _normalize_tags(self, tags: any) -> List[str]:
        """Normalize tags to list format."""
        if isinstance(tags, str):
            # Comma-separated string
            return [tag.strip() for tag in tags.split(",") if tag.strip()]
        elif isinstance(tags, list):
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        else:
            return []

    async def get_skill(self, skill_id: str) -> SkillDTO:
        """
        Get skill by ID.

        Args:
            skill_id: Skill ID (directory name)

        Returns:
            Skill DTO

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        return SkillDTO.from_entity(skill)

    async def list_skills(self) -> List[SkillDTO]:
        """
        List all skills.

        Returns:
            List of skill DTOs
        """
        skills = await self._skill_repo.get_all()
        return [SkillDTO.from_entity(s) for s in skills]

    async def search_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> List[SkillDTO]:
        """
        Search skills by tags.

        Args:
            tags: List of tags to search for
            match_all: If True, skill must have ALL tags; if False, ANY tag

        Returns:
            List of matching skill DTOs
        """
        skills = await self._skill_repo.get_by_tags(tags, match_all=match_all)
        return [SkillDTO.from_entity(s) for s in skills]

    async def update_skill(
        self,
        skill_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        icon: Optional[str] = None,
        icon_color: Optional[str] = None,
    ) -> SkillDTO:
        """
        Update skill metadata (updates SKILL.md frontmatter).

        Args:
            skill_id: Skill ID (directory name)
            name: New name (optional)
            description: New description (optional)
            file_path: New file path (optional)
            tags: New tags (optional)
            icon: New icon (optional)
            icon_color: New icon color (optional)

        Returns:
            Updated skill DTO

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Update fields
        if name is not None:
            skill.name = name
        if description is not None:
            skill.description = description
        if file_path is not None:
            skill.file_path = file_path
        if tags is not None:
            skill.tags = tags
        if icon is not None:
            skill.icon = icon
        if icon_color is not None:
            skill.icon_color = icon_color

        # Persist (updates SKILL.md frontmatter)
        updated = await self._skill_repo.update(skill)

        return SkillDTO.from_entity(updated)

    async def delete_skill(self, skill_id: str) -> None:
        """
        Soft-delete a skill (renames directory with .deleted suffix).

        Args:
            skill_id: Skill ID (directory name)

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        exists = await self._skill_repo.exists(skill_id)
        if not exists:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        await self._skill_repo.delete(skill_id)

    # File Operations

    async def list_skill_files(self, skill_id: str) -> List[FileInfoDTO]:
        """
        List all files in skill directory.

        Args:
            skill_id: Skill ID (directory name)

        Returns:
            List of file information DTOs

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Get actual filesystem path from repository
        actual_path = await self._skill_repo.get_skill_directory(skill_id)
        if not actual_path.exists():
            return []

        file_infos = await self._file_service.list_files(actual_path)

        return [
            FileInfoDTO(
                path=info.path,
                name=info.name,
                size=info.size,
                is_directory=info.is_directory,
                modified_at=info.modified_at,
            )
            for info in file_infos
        ]

    def _validate_skill_md_frontmatter(self, content: str) -> None:
        """
        Validate SKILL.md has proper YAML frontmatter with required fields.

        Args:
            content: File content to validate

        Raises:
            ValidationError: If frontmatter is missing or invalid
        """
        # Check for frontmatter markers
        if not content.startswith("---"):
            raise ValidationError(
                "SKILL.md must start with YAML frontmatter (---). "
                "Format:\n---\nname: Skill Name\ndescription: Description\n"
                'tags: [tag1, tag2]\nicon: zap\niconColor: "#4A90E2"\n---'
            )

        # Extract frontmatter
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            raise ValidationError(
                "Invalid YAML frontmatter format in SKILL.md. "
                "Frontmatter must be enclosed between --- markers."
            )

        try:
            frontmatter = yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            raise ValidationError(
                f"Invalid YAML syntax in SKILL.md frontmatter: {e}"
            ) from e

        # Validate it's a dictionary
        if not isinstance(frontmatter, dict):
            raise ValidationError(
                "SKILL.md frontmatter must be a YAML object (dictionary)"
            )

        # Validate required fields
        required_fields = ["name"]
        missing_fields = [
            field for field in required_fields if field not in frontmatter
        ]
        if missing_fields:
            raise ValidationError(
                f"SKILL.md frontmatter missing required fields: {', '.join(missing_fields)}"
            )

        # Validate name is not empty
        if not frontmatter["name"] or not str(frontmatter["name"]).strip():
            raise ValidationError("SKILL.md frontmatter 'name' field cannot be empty")

        # Normalize and validate optional fields
        if "tags" in frontmatter:
            value = frontmatter["tags"]
            # Accept both list format and comma-separated string format
            if isinstance(value, str):
                # Comma-separated string is acceptable (will be normalized on read)
                pass
            elif not isinstance(value, list):
                raise ValidationError(
                    "SKILL.md frontmatter 'tags' field must be a list or comma-separated string"
                )

        if "description" in frontmatter and frontmatter["description"] is not None:
            if not isinstance(frontmatter["description"], str):
                raise ValidationError(
                    "SKILL.md frontmatter 'description' field must be a string"
                )

    async def get_skill_file_content(
        self, skill_id: str, file_path: str
    ) -> FileContentResponse:
        """
        Read file content from skill directory.

        Args:
            skill_id: Skill ID (directory name)
            file_path: Path relative to skill directory

        Returns:
            File content response

        Raises:
            SkillNotFoundError: If skill doesn't exist
            ValidationError: If file path is invalid or file type not allowed
            FileSystemError: If file doesn't exist or can't be read
        """
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Get actual filesystem path from repository
        base_path = await self._skill_repo.get_skill_directory(skill_id)

        # Validate path and extension
        full_path = self._file_service.validate_path(base_path, file_path)
        self._file_service.validate_extension(file_path)

        # Read file
        content, size = await self._file_service.read_file(full_path)

        return FileContentResponse(
            file_path=file_path,
            content=content,
            size=size,
        )

    async def update_skill_file_content(
        self, skill_id: str, request: FileContentRequest
    ) -> FileContentResponse:
        """
        Update or create file in skill directory.

        Args:
            skill_id: Skill ID (directory name)
            request: File content request

        Returns:
            File content response

        Raises:
            SkillNotFoundError: If skill doesn't exist
            ValidationError: If file path is invalid, file type not allowed,
                           or SKILL.md has invalid frontmatter
            FileSystemError: If file can't be written
        """
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Get actual filesystem path from repository
        base_path = await self._skill_repo.get_skill_directory(skill_id)

        # Validate path and extension
        full_path = self._file_service.validate_path(base_path, request.file_path)
        self._file_service.validate_extension(request.file_path)

        # Special validation for SKILL.md - ensure proper YAML frontmatter
        if request.file_path.upper() == "SKILL.MD":
            self._validate_skill_md_frontmatter(request.content)

        # Write file (filesystem mtime handles timestamp)
        size = await self._file_service.write_file(full_path, request.content)

        return FileContentResponse(
            file_path=request.file_path,
            content=request.content,
            size=size,
        )

    async def delete_skill_file(self, skill_id: str, file_path: str) -> None:
        """
        Delete file from skill directory.

        Protected files (SKILL.md) cannot be deleted.

        Args:
            skill_id: Skill ID (directory name)
            file_path: Path relative to skill directory

        Raises:
            SkillNotFoundError: If skill doesn't exist
            ValidationError: If file path is invalid or file is protected
            FileSystemError: If file doesn't exist or can't be deleted
        """
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Prevent deletion of main skill file
        if self._file_service.is_protected_file(file_path) or file_path == "SKILL.md":
            raise ValidationError(f"Cannot delete protected file: {file_path}")

        # Get actual filesystem path from repository
        base_path = await self._skill_repo.get_skill_directory(skill_id)

        # Validate path
        full_path = self._file_service.validate_path(base_path, file_path)

        # Delete file
        await self._file_service.delete_file(full_path)

    # Claude SDK-specific methods

    async def load_skill_content(self, skill_id: str) -> str:
        """
        Load full SKILL.md content for loading into AI context.

        Args:
            skill_id: Skill ID (directory name)

        Returns:
            Full SKILL.md content including frontmatter

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        # Check if repository has this method (file-based does)
        if hasattr(self._skill_repo, "load_skill_content"):
            return await self._skill_repo.load_skill_content(skill_id)

        # Fallback: read file manually
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Get actual filesystem path from repository
        skill_dir = await self._skill_repo.get_skill_directory(skill_id)
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            raise SkillNotFoundError(f"SKILL.md not found for skill: {skill_id}")

        return skill_md.read_text(encoding="utf-8")

    async def load_supporting_doc(self, skill_id: str, doc_path: str) -> str:
        """
        Load supporting document (e.g., FORMS.md, reference/finance.md).

        Args:
            skill_id: Skill ID (directory name)
            doc_path: Relative path to document within skill directory

        Returns:
            Document content

        Raises:
            SkillNotFoundError: If skill or document doesn't exist
            ValidationError: If doc_path is invalid
        """
        # Check if repository has this method (file-based does)
        if hasattr(self._skill_repo, "load_supporting_doc"):
            return await self._skill_repo.load_supporting_doc(skill_id, doc_path)

        # Fallback: read file manually
        skill = await self._skill_repo.get_by_id(skill_id)
        if skill is None:
            raise SkillNotFoundError(f"Skill {skill_id} not found")

        # Get actual filesystem path from repository
        skill_dir = await self._skill_repo.get_skill_directory(skill_id)
        doc_file = skill_dir / doc_path

        # Security: Ensure path is within skill directory
        if not doc_file.resolve().is_relative_to(skill_dir.resolve()):
            raise ValidationError(f"Invalid document path: {doc_path}")

        if not doc_file.exists():
            raise SkillNotFoundError(
                f"Document not found: {doc_path} in skill {skill_id}"
            )

        return doc_file.read_text(encoding="utf-8")
