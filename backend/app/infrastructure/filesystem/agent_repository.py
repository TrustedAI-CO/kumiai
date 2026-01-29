"""File-based agent repository implementation."""

import re
from pathlib import Path
from typing import List, Optional

import yaml

from app.core.exceptions import NotFoundError, RepositoryError, SecurityError
from app.core.logging import get_logger
from app.domain.entities.agent import Agent
from app.domain.repositories.agent_repository import AgentRepository

logger = get_logger(__name__)


class FileBasedAgentRepository(AgentRepository):
    """
    File-based implementation of AgentRepository.

    Agents are stored as directories following Claude SDK format:
        /data/agents/{agent-id}/
        ├── CLAUDE.md (with YAML frontmatter)
        └── docs/ (optional)

    Metadata is stored in YAML frontmatter of CLAUDE.md:
        ---
        name: Product Manager
        tags: [management, planning]
        skills: [project-planning]
        allowed_tools: [Read, Write, Edit]
        allowed_mcps: []
        icon_color: "#4A90E2"
        ---
        # Agent description...
    """

    def __init__(self, base_path: Path | str = Path("data/agents")):
        """
        Initialize file-based agent repository.

        Args:
            base_path: Base directory for agent storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _parse_claude_md(self, claude_md_path: Path) -> dict:
        """
        Parse CLAUDE.md with YAML frontmatter.

        Args:
            claude_md_path: Path to CLAUDE.md file

        Returns:
            Dictionary with frontmatter metadata

        Raises:
            RepositoryError: If parsing fails
        """
        try:
            content = claude_md_path.read_text(encoding="utf-8")

            # Check for frontmatter (--- at start)
            if not content.startswith("---"):
                # No frontmatter, use defaults
                agent_id = claude_md_path.parent.name
                return {
                    "name": agent_id.replace("-", " ").title(),
                    "default_model": "sonnet",
                    "tags": [],
                    "skills": [],
                    "allowed_tools": [],
                    "allowed_mcps": [],
                    "icon_color": "#4A90E2",
                }

            # Extract frontmatter
            match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
            if not match:
                raise RepositoryError(f"Invalid frontmatter format in {claude_md_path}")

            frontmatter = yaml.safe_load(match.group(1))
            if not isinstance(frontmatter, dict):
                raise RepositoryError(
                    f"Frontmatter must be a dictionary in {claude_md_path}"
                )

            # Validate required fields
            if "name" not in frontmatter or not frontmatter["name"]:
                raise RepositoryError(
                    f"Missing required field 'name' in {claude_md_path}"
                )

            # Normalize list fields (handle comma-separated strings from legacy files)
            for field in ["tags", "skills", "allowed_tools", "allowed_mcps"]:
                if field in frontmatter:
                    value = frontmatter[field]
                    if isinstance(value, str):
                        # Parse comma-separated string or empty string
                        if value.strip():
                            frontmatter[field] = [
                                item.strip()
                                for item in value.split(",")
                                if item.strip()
                            ]
                        else:
                            frontmatter[field] = []
                    elif not isinstance(value, list):
                        # Convert other types to list
                        frontmatter[field] = [value] if value else []

            return frontmatter

        except Exception as e:
            logger.error(
                "parse_claude_md_failed",
                claude_md_path=str(claude_md_path),
                error=str(e),
            )
            raise RepositoryError(f"Failed to parse CLAUDE.md: {e}") from e

    def _write_claude_md(
        self,
        agent_dir: Path,
        metadata: dict,
        content: Optional[str] = None,
    ) -> None:
        """
        Write CLAUDE.md with YAML frontmatter.

        Args:
            agent_dir: Agent directory path
            metadata: Frontmatter metadata dictionary
            content: Optional markdown content (body)

        Raises:
            RepositoryError: If writing fails
        """
        try:
            claude_md = agent_dir / "CLAUDE.md"

            # Generate frontmatter with inline lists (comma-separated)
            # Use flow style for lists to get [item1, item2] instead of multi-line
            class InlineListDumper(yaml.SafeDumper):
                pass

            def represent_list(dumper, data):
                return dumper.represent_sequence(
                    "tag:yaml.org,2002:seq", data, flow_style=True
                )

            InlineListDumper.add_representer(list, represent_list)

            frontmatter_yaml = yaml.dump(
                metadata,
                Dumper=InlineListDumper,
                allow_unicode=True,
                sort_keys=False,
            )

            # If updating existing file, preserve body
            if content is None and claude_md.exists():
                existing_content = claude_md.read_text(encoding="utf-8")
                if existing_content.startswith("---"):
                    match = re.match(
                        r"^---\n(.*?)\n---\n(.*)",
                        existing_content,
                        re.DOTALL,
                    )
                    if match:
                        content = match.group(2)

            # Default content if none provided - create comprehensive template
            if content is None:
                agent_name = metadata.get("name", "Agent")
                content = f"""
# {agent_name}

Describe the agent's role and responsibilities here.

## Role Description

Provide a detailed description of what this agent does and when to use it.

## Responsibilities

- Responsibility 1
- Responsibility 2
- Responsibility 3

## Communication Style

Describe how this agent communicates (formal, casual, technical, etc.)

## Skills

This agent has access to the following skills:
{chr(10).join(f"- {skill}" for skill in metadata.get("skills", []))}

## Tools & Capabilities

Allowed tools:
{chr(10).join(f"- {tool}" for tool in metadata.get("allowed_tools", []))}

## Notes

Add any additional notes, warnings, or tips here.
"""

            # Write file
            full_content = f"---\n{frontmatter_yaml}---\n{content}"
            claude_md.write_text(full_content, encoding="utf-8")

            logger.debug(
                "claude_md_written",
                claude_md=str(claude_md),
            )

        except Exception as e:
            logger.error(
                "write_claude_md_failed",
                agent_dir=str(agent_dir),
                error=str(e),
            )
            raise RepositoryError(f"Failed to write CLAUDE.md: {e}") from e

    async def create(self, agent: Agent) -> Agent:
        """Create new agent directory with CLAUDE.md."""
        try:
            agent_dir = self.base_path / agent.id

            # Check if already exists
            if agent_dir.exists():
                raise RepositoryError(f"Agent directory already exists: {agent.id}")

            # Create directory
            agent_dir.mkdir(parents=True, exist_ok=True)

            # Create metadata for frontmatter
            metadata = {
                "name": agent.name,
                "tags": agent.tags,
                "skills": agent.skills,
                "allowed_tools": agent.allowed_tools,
                "allowed_mcps": agent.allowed_mcps,
                "icon_color": agent.icon_color,
            }
            # Add optional fields if provided
            if agent.description:
                metadata["description"] = agent.description
            # Add default_model only if not "sonnet" (default)
            if agent.default_model != "sonnet":
                metadata["default_model"] = agent.default_model

            # Write CLAUDE.md
            self._write_claude_md(agent_dir, metadata)

            logger.info(
                "agent_created",
                agent_id=agent.id,
                agent_path=str(agent_dir),
            )

            # Update entity with logical path before returning
            agent.file_path = f"/agents/{agent.id}/"
            return agent

        except Exception as e:
            logger.error(
                "create_agent_failed",
                agent_id=agent.id,
                error=str(e),
            )
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to create agent: {e}") from e

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Retrieve agent by ID (directory name)."""
        try:
            agent_dir = self.base_path / agent_id
            claude_md = agent_dir / "CLAUDE.md"

            # Check existence (exclude soft-deleted)
            if not claude_md.exists() or agent_dir.name.endswith(".deleted"):
                return None

            # Parse frontmatter
            metadata = self._parse_claude_md(claude_md)

            # Construct entity with logical path
            agent = Agent(
                id=agent_id,
                name=metadata.get("name", agent_id),
                description=metadata.get("description"),
                file_path=f"/agents/{agent_id}/",
                default_model=metadata.get("default_model", "sonnet"),
                tags=metadata.get("tags", []),
                skills=metadata.get("skills", []),
                allowed_tools=metadata.get("allowed_tools", []),
                allowed_mcps=metadata.get("allowed_mcps", []),
                icon_color=metadata.get("icon_color", "#4A90E2"),
            )

            return agent

        except Exception as e:
            logger.error(
                "get_agent_by_id_failed",
                agent_id=agent_id,
                error=str(e),
            )
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(f"Failed to get agent: {e}") from e

    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Retrieve agent by name (case-insensitive)."""
        try:
            agents = await self.get_all()
            name_lower = name.strip().lower()

            for agent in agents:
                if agent.name.lower() == name_lower:
                    return agent

            return None

        except Exception as e:
            logger.error(
                "get_agent_by_name_failed",
                name=name,
                error=str(e),
            )
            raise RepositoryError(f"Failed to get agent by name: {e}") from e

    async def get_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> List[Agent]:
        """Get agents by tags."""
        try:
            all_agents = await self.get_all()
            tags_lower = [tag.lower() for tag in tags]

            if match_all:
                # AND: Agent must have ALL tags
                return [
                    agent
                    for agent in all_agents
                    if all(
                        any(t.lower() == tag_filter for t in agent.tags)
                        for tag_filter in tags_lower
                    )
                ]
            else:
                # OR: Agent must have ANY tag
                return [
                    agent
                    for agent in all_agents
                    if any(tag.lower() in tags_lower for tag in agent.tags)
                ]

        except Exception as e:
            logger.error(
                "get_agents_by_tags_failed",
                tags=tags,
                match_all=match_all,
                error=str(e),
            )
            raise RepositoryError(f"Failed to get agents by tags: {e}") from e

    async def get_all(self, include_deleted: bool = False) -> List[Agent]:
        """Get all agents."""
        try:
            agents = []

            # Iterate through directories
            for agent_dir in self.base_path.iterdir():
                # Skip if not directory
                if not agent_dir.is_dir():
                    continue

                # Skip soft-deleted unless requested
                if agent_dir.name.endswith(".deleted") and not include_deleted:
                    continue

                claude_md = agent_dir / "CLAUDE.md"
                if not claude_md.exists():
                    continue

                # Extract agent_id (remove .deleted suffix if present)
                agent_id = (
                    agent_dir.name.removesuffix(".deleted")
                    if agent_dir.name.endswith(".deleted")
                    else agent_dir.name
                )

                # Parse and load
                metadata = self._parse_claude_md(claude_md)
                agent = Agent(
                    id=agent_id,
                    name=metadata.get("name", agent_id),
                    description=metadata.get("description"),
                    file_path=f"/agents/{agent_id}/",
                    tags=metadata.get("tags", []),
                    skills=metadata.get("skills", []),
                    allowed_tools=metadata.get("allowed_tools", []),
                    allowed_mcps=metadata.get("allowed_mcps", []),
                    icon_color=metadata.get("icon_color", "#4A90E2"),
                )
                agents.append(agent)

            return agents

        except Exception as e:
            logger.error(
                "get_all_agents_failed",
                error=str(e),
            )
            raise RepositoryError(f"Failed to get all agents: {e}") from e

    async def update(self, agent: Agent) -> Agent:
        """Update existing agent."""
        try:
            agent_dir = self.base_path / agent.id
            claude_md = agent_dir / "CLAUDE.md"

            if not claude_md.exists():
                raise NotFoundError(f"Agent not found: {agent.id}")

            # Create metadata for frontmatter
            metadata = {
                "name": agent.name,
                "tags": agent.tags,
                "skills": agent.skills,
                "allowed_tools": agent.allowed_tools,
                "allowed_mcps": agent.allowed_mcps,
                "icon_color": agent.icon_color,
            }
            # Add optional fields if provided
            if agent.description:
                metadata["description"] = agent.description
            # Add default_model only if not "sonnet" (default)
            if agent.default_model != "sonnet":
                metadata["default_model"] = agent.default_model

            # Update CLAUDE.md (preserves body content)
            self._write_claude_md(agent_dir, metadata)

            logger.info(
                "agent_updated",
                agent_id=agent.id,
            )

            return agent

        except Exception as e:
            logger.error(
                "update_agent_failed",
                agent_id=agent.id,
                error=str(e),
            )
            if isinstance(e, (NotFoundError, RepositoryError)):
                raise
            raise RepositoryError(f"Failed to update agent: {e}") from e

    async def delete(self, agent_id: str) -> None:
        """Soft-delete an agent by renaming directory."""
        try:
            agent_dir = self.base_path / agent_id

            if not agent_dir.exists():
                raise NotFoundError(f"Agent not found: {agent_id}")

            # Rename with .deleted suffix
            deleted_dir = self.base_path / f"{agent_id}.deleted"
            agent_dir.rename(deleted_dir)

            logger.info(
                "agent_deleted",
                agent_id=agent_id,
            )

        except Exception as e:
            logger.error(
                "delete_agent_failed",
                agent_id=agent_id,
                error=str(e),
            )
            if isinstance(e, (NotFoundError, RepositoryError)):
                raise
            raise RepositoryError(f"Failed to delete agent: {e}") from e

    async def exists(self, agent_id: str) -> bool:
        """Check if agent exists (including soft-deleted)."""
        try:
            agent_dir = self.base_path / agent_id
            deleted_dir = self.base_path / f"{agent_id}.deleted"

            return (agent_dir / "CLAUDE.md").exists() or (
                deleted_dir / "CLAUDE.md"
            ).exists()

        except Exception as e:
            logger.error(
                "agent_exists_check_failed",
                agent_id=agent_id,
                error=str(e),
            )
            raise RepositoryError(f"Failed to check agent existence: {e}") from e

    async def load_agent_content(self, agent_id: str) -> str:
        """Load full CLAUDE.md content for AI context."""
        try:
            agent_dir = self.base_path / agent_id
            claude_md = agent_dir / "CLAUDE.md"

            if not claude_md.exists():
                raise NotFoundError(f"Agent not found: {agent_id}")

            return claude_md.read_text(encoding="utf-8")

        except Exception as e:
            logger.error(
                "load_agent_content_failed",
                agent_id=agent_id,
                error=str(e),
            )
            if isinstance(e, NotFoundError):
                raise
            raise RepositoryError(f"Failed to load agent content: {e}") from e

    async def load_supporting_doc(self, agent_id: str, doc_path: str) -> str:
        """Load a supporting document from agent directory."""
        try:
            agent_dir = self.base_path / agent_id

            if not agent_dir.exists():
                raise NotFoundError(f"Agent not found: {agent_id}")

            # Resolve document path with security check
            doc_full_path = (agent_dir / doc_path).resolve()

            # Ensure path is within agent directory (prevent traversal)
            if not doc_full_path.is_relative_to(agent_dir.resolve()):
                raise SecurityError(f"Path traversal attempt detected: {doc_path}")

            if not doc_full_path.exists():
                raise NotFoundError(
                    f"Document not found: {doc_path} in agent {agent_id}"
                )

            return doc_full_path.read_text(encoding="utf-8")

        except Exception as e:
            logger.error(
                "load_supporting_doc_failed",
                agent_id=agent_id,
                doc_path=doc_path,
                error=str(e),
            )
            if isinstance(e, (NotFoundError, SecurityError)):
                raise
            raise RepositoryError(f"Failed to load supporting document: {e}") from e

    async def get_agent_directory(self, agent_id: str) -> Path:
        """Get the actual filesystem directory path for an agent."""
        return self.base_path / agent_id
