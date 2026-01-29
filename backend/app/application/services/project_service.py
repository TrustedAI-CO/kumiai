"""Project service - application layer use cases."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

from app.application.dtos.project_dto import ProjectDTO
from app.application.dtos.requests import (
    AssignPMRequest,
    CreateProjectRequest,
    UpdateProjectRequest,
)
from app.application.services.exceptions import (
    ProjectNotFoundError,
)
from app.core.config import settings
from app.domain.config.templates import get_project_template
from app.domain.entities import Project
from app.domain.repositories import (
    AgentRepository,
    ProjectRepository,
    SessionRepository,
)


class ProjectService:
    """
    Project service - orchestrates project-related use cases.

    Responsibilities:
    - Create/manage projects
    - Assign/remove PM from projects
    - Enforce business rules
    - Atomic PM assignment (create session + update project)
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        session_repo: SessionRepository,
        agent_repo: AgentRepository,
    ):
        """Initialize service with repositories."""
        self._project_repo = project_repo
        self._session_repo = session_repo
        self._agent_repo = agent_repo

    def _sanitize_project_name(self, name: str, add_suffix: bool = True) -> str:
        """
        Sanitize project name for directory creation.

        Args:
            name: Project name
            add_suffix: Whether to add a random suffix to avoid collisions

        Returns:
            Sanitized name safe for filesystem use with optional random suffix
        """
        # Convert to lowercase, replace spaces and special chars with hyphens
        sanitized = re.sub(r"[^\w\s-]", "", name.lower())
        sanitized = re.sub(r"[-\s]+", "-", sanitized)
        sanitized = sanitized.strip("-")

        # Add random suffix to avoid collisions
        if add_suffix:
            random_suffix = uuid4().hex[:8]
            sanitized = f"{sanitized}-{random_suffix}"

        return sanitized

    async def _create_project_md(
        self,
        project_path: str,
        project_id: UUID,
        name: str,
        description: Optional[str],
        sanitized_name: str,
    ) -> None:
        """
        Create PROJECT.md file in project directory.

        Args:
            project_path: Absolute path to project directory
            project_id: Project UUID
            name: Project name
            description: Project description
            sanitized_name: Sanitized project name with suffix
        """
        project_md_path = Path(project_path) / "PROJECT.md"

        # Skip creation if PROJECT.md already exists
        if project_md_path.exists():
            return

        created_date = datetime.now().strftime("%Y-%m-%d")

        # Get all sessions for this project to build team members list
        sessions = await self._session_repo.get_by_project_id(project_id)

        # Batch load all agents to avoid N+1 queries
        agent_ids = {session.agent_id for session in sessions}
        agents_map = {}
        for agent_id in agent_ids:
            agent = await self._agent_repo.get_by_id(agent_id)
            if agent:
                agents_map[agent_id] = agent

        # Separate PM and team members
        pm_agent = None
        team_members_lines = []

        from app.domain.value_objects import SessionType

        for session in sessions:
            agent = agents_map.get(session.agent_id)
            if agent:
                # Format: (agent-id) agent-name: description
                agent_line = f"**({agent.id}) {agent.name}:** {agent.description or 'No description'}"

                # Check if this is a PM session
                if session.session_type == SessionType.PM:
                    pm_agent = agent_line
                else:
                    team_members_lines.append(agent_line)

        # Format PM section
        project_manager = pm_agent if pm_agent else "Not assigned"

        # Format team members section
        if not team_members_lines:
            team_members = "No team members assigned yet"
        else:
            team_members = "\n".join(team_members_lines)

        content = get_project_template(
            project_name=name,
            project_id=sanitized_name,
            project_path=project_path,
            created_date=created_date,
            description=description or "No description provided",
            project_manager=project_manager,
            team_members=team_members,
        )

        project_md_path.write_text(content, encoding="utf-8")

    async def create_project(self, request: CreateProjectRequest) -> ProjectDTO:
        """
        Create a new project.

        If no path is provided, creates project directory under ~/.kumiai/projects/{sanitized-name}.

        Args:
            request: Project creation request

        Returns:
            Created project DTO
        """
        project_id = uuid4()

        # Determine project path and sanitized name
        if request.path:
            # User provided a path - expand and resolve it
            project_path = os.path.expanduser(request.path)
            project_path = os.path.abspath(project_path)
            # For custom paths, use directory name as sanitized name
            sanitized_name = Path(project_path).name
        else:
            # Create directory under ~/.kumiai/projects
            sanitized_name = self._sanitize_project_name(request.name)
            project_path = str(settings.projects_dir / sanitized_name)

        # Create project directory if it doesn't exist
        Path(project_path).mkdir(parents=True, exist_ok=True)

        # Create domain entity
        project = Project(
            id=project_id,
            name=request.name,
            description=request.description,
            path=project_path,
            pm_agent_id=request.pm_agent_id,
            team_member_ids=request.team_member_ids,
        )

        # Persist project first
        created = await self._project_repo.create(project)

        # If PM agent is assigned, create PM session
        if request.pm_agent_id:
            from app.domain.entities import Session
            from app.domain.value_objects import SessionStatus, SessionType

            # Create PM session with agent_id
            pm_session = Session(
                id=uuid4(),
                agent_id=request.pm_agent_id,
                project_id=project_id,
                session_type=SessionType.PM,
                status=SessionStatus.IDLE,
                context={"description": "Project Manager"},
            )
            created_session = await self._session_repo.create(pm_session)

            # Update project with PM session reference
            created.pm_session_id = created_session.id
            created = await self._project_repo.update(created)

        # Create PROJECT.md file after sessions are created
        await self._create_project_md(
            project_path=project_path,
            project_id=project_id,
            name=request.name,
            description=request.description,
            sanitized_name=sanitized_name,
        )

        return ProjectDTO.from_entity(created)

    async def get_project(self, project_id: UUID) -> ProjectDTO:
        """
        Get project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project DTO

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = await self._project_repo.get_or_raise(project_id, "Project")

        return ProjectDTO.from_entity(project)

    async def list_projects(self) -> List[ProjectDTO]:
        """
        List all projects.

        Returns:
            List of project DTOs
        """
        projects = await self._project_repo.get_all()
        return [ProjectDTO.from_entity(p) for p in projects]

    async def update_project(
        self, project_id: UUID, request: UpdateProjectRequest
    ) -> ProjectDTO:
        """
        Update project metadata.

        Args:
            project_id: Project UUID
            request: Update request

        Returns:
            Updated project DTO

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = await self._project_repo.get_or_raise(project_id, "Project")

        # Update metadata
        if request.name is not None or request.description is not None:
            project.update_metadata(name=request.name, description=request.description)

        if request.path is not None:
            project.path = request.path

        if request.team_member_ids is not None:
            project.team_member_ids = request.team_member_ids

        # Persist
        updated = await self._project_repo.update(project)

        return ProjectDTO.from_entity(updated)

    async def assign_pm(self, project_id: UUID, request: AssignPMRequest) -> ProjectDTO:
        """
        Assign PM to project (atomic operation).

        This is a complex operation that requires:
        1. Creating PM session
        2. Updating project with PM references

        Note: In a full implementation, this should be wrapped in a database
        transaction to ensure atomicity.

        Args:
            project_id: Project UUID
            request: PM assignment request

        Returns:
            Updated project DTO

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Validate project exists
        project = await self._project_repo.get_or_raise(project_id, "Project")

        # Create PM session (simplified - in real implementation would use SessionService)

        # Note: Sessions now use agent_id directly.
        # TODO: Implement proper session creation logic here.

        # For now, just update the project with the agent ID
        # Session creation will be handled separately
        project.pm_agent_id = request.pm_agent_id
        updated = await self._project_repo.update(project)

        return ProjectDTO.from_entity(updated)

    async def remove_pm(self, project_id: UUID) -> ProjectDTO:
        """
        Remove PM assignment from project.

        Args:
            project_id: Project UUID

        Returns:
            Updated project DTO

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = await self._project_repo.get_or_raise(project_id, "Project")

        # Remove PM assignment
        project.remove_pm()
        updated = await self._project_repo.update(project)

        return ProjectDTO.from_entity(updated)

    async def delete_project(self, project_id: UUID) -> None:
        """
        Soft-delete a project.

        Args:
            project_id: Project UUID

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        exists = await self._project_repo.exists(project_id)
        if not exists:
            raise ProjectNotFoundError(f"Project {project_id} not found")

        await self._project_repo.delete(project_id)
