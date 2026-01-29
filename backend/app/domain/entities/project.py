"""Project domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ValidationError


@dataclass
class Project:
    """
    Project domain entity.

    A project represents a workspace containing code, files, and associated
    sessions. Projects can have a PM agent for coordination.

    Business rules:
    - Name and path are required and non-empty
    - PM agent and session must both be set or both be None (consistency)
    - Path must be a valid filesystem path
    """

    id: UUID
    name: str
    description: Optional[str]
    pm_agent_id: Optional[str] = (
        None  # Agent ID (string-based, e.g., 'product-manager')
    )
    pm_session_id: Optional[UUID] = None
    team_member_ids: Optional[List[str]] = None
    path: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def assign_pm(self, agent_id: str, session_id: UUID) -> None:
        """
        Assign a PM agent and session to this project.

        Args:
            agent_id: ID of the agent to assign as PM (e.g., 'product-manager')
            session_id: ID of the PM session
        """
        self.pm_agent_id = agent_id
        self.pm_session_id = session_id
        self._update_timestamp()

    def remove_pm(self) -> None:
        """Remove PM assignment from project."""
        self.pm_agent_id = None
        self.pm_session_id = None
        self._update_timestamp()

    def has_pm(self) -> bool:
        """
        Check if project has an assigned PM.

        Returns:
            True if both PM agent and session are assigned, False otherwise
        """
        return self.pm_agent_id is not None and self.pm_session_id is not None

    def update_metadata(
        self, name: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        """
        Update project metadata.

        Args:
            name: New project name (optional)
            description: New project description (optional)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self._update_timestamp()

    def _update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def validate(self) -> None:
        """
        Validate project invariants.

        Raises:
            ValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Project name cannot be empty")

        if not self.path or not self.path.strip():
            raise ValidationError("Project path cannot be empty")

        # PM consistency: both or neither
        if (self.pm_agent_id is None) != (self.pm_session_id is None):
            raise ValidationError(
                "pm_agent_id and pm_session_id must both be set or both be None"
            )
