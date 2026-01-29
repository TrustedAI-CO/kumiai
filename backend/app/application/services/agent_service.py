"""Agent service - application layer use cases."""

from typing import List, Optional

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
from app.application.services.exceptions import AgentNotFoundError
from app.core.exceptions import ValidationError
from app.domain.entities.agent import Agent
from app.domain.repositories.agent_repository import AgentRepository
from app.infrastructure.filesystem import FileService


class AgentService:
    """
    Agent service - manage agents.

    Responsibilities:
    - Create/manage agents
    - List/filter agents by tags
    - Manage agent files
    - Enforce business rules
    """

    def __init__(
        self,
        agent_repo: AgentRepository,
        file_service: Optional[FileService] = None,
    ):
        """Initialize service with repository and optional file service."""
        self._agent_repo = agent_repo
        self._file_service = file_service or FileService()

    async def create_agent(self, request: CreateAgentRequest) -> AgentDTO:
        """
        Create a new agent.

        Args:
            request: Agent creation request

        Returns:
            Created agent DTO
        """
        # Auto-generate agent ID from name if not provided
        agent_id = request.id
        if not agent_id:
            # Generate from name: name-slug
            agent_id = request.name.lower().replace(" ", "-").replace("_", "-")
            # Remove non-alphanumeric characters except hyphens
            import re

            agent_id = re.sub(r"[^a-z0-9-]", "", agent_id)
            agent_id = re.sub(r"-+", "-", agent_id)  # Remove duplicate hyphens
            agent_id = agent_id.strip("-")  # Remove leading/trailing hyphens

        # Auto-generate file_path from agent_id
        file_path = request.file_path
        if not file_path:
            file_path = f"/agents/{agent_id}/"

        # Create domain entity
        agent = Agent(
            id=agent_id,
            name=request.name,
            description=request.description,
            file_path=file_path,
            default_model=request.default_model or "sonnet",
            tags=request.tags or [],
            skills=request.skills or [],
            allowed_tools=request.allowed_tools or [],
            allowed_mcps=request.allowed_mcps or [],
            icon_color=request.icon_color or "#4A90E2",
        )

        # Validate
        agent.validate()

        # Persist (creates CLAUDE.md with frontmatter)
        await self._agent_repo.create(agent)

        # Reload from repository to get actual filesystem path
        reloaded = await self._agent_repo.get_by_id(agent_id)

        return AgentDTO.from_entity(reloaded)

    async def get_agent(self, agent_id: str) -> AgentDTO:
        """
        Get agent by ID.

        Args:
            agent_id: Agent ID (directory name)

        Returns:
            Agent DTO

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        return AgentDTO.from_entity(agent)

    async def list_agents(self) -> List[AgentDTO]:
        """
        List all agents.

        Returns:
            List of agent DTOs
        """
        agents = await self._agent_repo.get_all()
        return [AgentDTO.from_entity(a) for a in agents]

    async def search_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> List[AgentDTO]:
        """
        Search agents by tags.

        Args:
            tags: Tags to search for
            match_all: If True, match ALL tags (AND). If False, match ANY tag (OR).

        Returns:
            List of matching agent DTOs
        """
        agents = await self._agent_repo.get_by_tags(tags, match_all)
        return [AgentDTO.from_entity(a) for a in agents]

    async def update_agent(
        self, agent_id: str, request: UpdateAgentRequest
    ) -> AgentDTO:
        """
        Update agent metadata.

        Args:
            agent_id: Agent ID
            request: Update request

        Returns:
            Updated agent DTO

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # Update fields
        agent.update_metadata(
            name=request.name,
            description=request.description,
            default_model=request.default_model,
            tags=request.tags,
            skills=request.skills,
            allowed_tools=request.allowed_tools,
            allowed_mcps=request.allowed_mcps,
            icon_color=request.icon_color,
        )

        # Validate
        agent.validate()

        # Persist
        updated = await self._agent_repo.update(agent)

        return AgentDTO.from_entity(updated)

    async def delete_agent(self, agent_id: str) -> None:
        """
        Soft-delete an agent.

        Args:
            agent_id: Agent ID

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        await self._agent_repo.delete(agent_id)

    async def list_agent_files(self, agent_id: str) -> List[FileInfoDTO]:
        """
        List all files in agent directory.

        Args:
            agent_id: Agent ID

        Returns:
            List of file info DTOs

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # Get actual filesystem path from repository
        agent_dir = await self._agent_repo.get_agent_directory(agent_id)
        file_infos = await self._file_service.list_files(agent_dir)

        # Convert FileInfo value objects to FileInfoDTO
        return [
            FileInfoDTO(
                path=fi.path,
                name=fi.name,
                size=fi.size,
                is_directory=fi.is_directory,
                modified_at=fi.modified_at,
            )
            for fi in file_infos
        ]

    async def get_agent_file_content(
        self, agent_id: str, file_path: str
    ) -> FileContentResponse:
        """
        Get content of a file in agent directory.

        Args:
            agent_id: Agent ID
            file_path: Relative path to file within agent directory

        Returns:
            File content response

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # Get actual filesystem path from repository
        agent_dir = await self._agent_repo.get_agent_directory(agent_id)
        full_path = agent_dir / file_path

        # Security: Ensure path is within agent directory
        if not full_path.resolve().is_relative_to(agent_dir.resolve()):
            raise ValidationError("Invalid file path")

        content, size = await self._file_service.read_file(full_path)
        return FileContentResponse(file_path=file_path, content=content, size=size)

    async def update_agent_file_content(
        self, agent_id: str, request: FileContentRequest
    ) -> FileContentResponse:
        """
        Update content of a file in agent directory.

        If the file is CLAUDE.md, validates frontmatter before writing.

        Args:
            agent_id: Agent ID
            request: File content update request

        Returns:
            Updated file content response

        Raises:
            AgentNotFoundError: If agent doesn't exist
            ValidationError: If CLAUDE.md frontmatter is invalid
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # Get actual filesystem path from repository
        agent_dir = await self._agent_repo.get_agent_directory(agent_id)
        full_path = agent_dir / request.file_path

        # Security: Ensure path is within agent directory
        if not full_path.resolve().is_relative_to(agent_dir.resolve()):
            raise ValidationError("Invalid file path")

        # If updating CLAUDE.md, validate frontmatter
        if full_path.name == "CLAUDE.md":
            self._validate_claude_md_frontmatter(request.content)

        await self._file_service.write_file(full_path, request.content)
        return FileContentResponse(
            file_path=str(request.file_path),
            content=request.content,
            size=full_path.stat().st_size,
        )

    async def delete_agent_file(self, agent_id: str, file_path: str) -> None:
        """
        Delete a file from agent directory.

        Protects CLAUDE.md from deletion.

        Args:
            agent_id: Agent ID
            file_path: Relative path to file within agent directory

        Raises:
            AgentNotFoundError: If agent doesn't exist
            ValidationError: If attempting to delete CLAUDE.md
        """
        agent = await self._agent_repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # Protect CLAUDE.md
        if file_path == "CLAUDE.md":
            raise ValidationError("Cannot delete CLAUDE.md")

        # Get actual filesystem path from repository
        agent_dir = await self._agent_repo.get_agent_directory(agent_id)
        full_path = agent_dir / file_path

        # Security: Ensure path is within agent directory
        if not full_path.resolve().is_relative_to(agent_dir.resolve()):
            raise ValidationError("Invalid file path")

        self._file_service.delete_file(full_path)

    async def load_agent_content(self, agent_id: str) -> str:
        """
        Load full CLAUDE.md content for AI context.

        This is used to inject agent definitions into AI prompts.

        Args:
            agent_id: Agent ID

        Returns:
            Complete CLAUDE.md content

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        return await self._agent_repo.load_agent_content(agent_id)

    async def load_supporting_doc(self, agent_id: str, doc_path: str) -> str:
        """
        Load a supporting document from agent directory.

        Args:
            agent_id: Agent ID
            doc_path: Relative path to document within agent directory

        Returns:
            Document content

        Raises:
            AgentNotFoundError: If agent or document doesn't exist
        """
        return await self._agent_repo.load_supporting_doc(agent_id, doc_path)

    def _validate_claude_md_frontmatter(self, content: str) -> None:
        """
        Validate CLAUDE.md frontmatter structure.

        Args:
            content: Full CLAUDE.md content

        Raises:
            ValidationError: If frontmatter is invalid
        """
        import re
        import yaml

        if not content.startswith("---"):
            raise ValidationError("CLAUDE.md must start with YAML frontmatter")

        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            raise ValidationError("Invalid YAML frontmatter format")

        try:
            frontmatter = yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML syntax: {e}")

        if not isinstance(frontmatter, dict):
            raise ValidationError("Frontmatter must be a dictionary")

        # Validate required fields
        if "name" not in frontmatter or not frontmatter["name"]:
            raise ValidationError("Missing required field: name")

        # Validate field types (accept both list and comma-separated string formats)
        for field in ["tags", "skills", "allowed_tools", "allowed_mcps"]:
            if field in frontmatter:
                value = frontmatter[field]
                # Accept both list format and comma-separated string format
                if isinstance(value, str):
                    # Comma-separated string is acceptable (will be normalized on read)
                    pass
                elif not isinstance(value, list):
                    raise ValidationError(
                        f"Field '{field}' must be a list or comma-separated string"
                    )
