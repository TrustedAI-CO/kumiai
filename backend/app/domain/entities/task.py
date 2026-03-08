"""Task domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.exceptions import ValidationError
from app.domain.value_objects.task_status import TaskStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Task:
    """
    Task domain entity.

    A task groups multiple sessions working toward the same goal within a project.

    Business rules:
    - name is required and non-empty
    - project_id is required
    - status follows defined transitions
    """

    id: UUID
    project_id: UUID
    name: str
    description: Optional[str] = None
    status: TaskStatus = field(default=TaskStatus.OPEN)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("Task name cannot be empty")

    def start(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self._touch()

    def complete(self) -> None:
        self.status = TaskStatus.DONE
        self._touch()

    def archive(self) -> None:
        self.status = TaskStatus.ARCHIVED
        self._touch()

    def reopen(self) -> None:
        self.status = TaskStatus.OPEN
        self._touch()

    def update_metadata(
        self, name: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self._touch()

    def _touch(self) -> None:
        self.updated_at = _utcnow()
