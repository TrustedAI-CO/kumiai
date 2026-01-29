"""Session domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.exceptions import InvalidStateTransition, ValidationError
from app.domain.value_objects import SessionStatus, SessionType


def _utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class Session:
    """
    Session domain entity.

    A session represents an active instance of an agent working
    within a project context. Sessions maintain conversation history, status,
    and configuration.

    Business rules:
    - PM sessions must be associated with a project
    - Status transitions follow state machine
    - Error sessions must have error_message
    - Context is session-specific mutable state
    - agent_id is required
    """

    id: UUID
    agent_id: str  # Agent string ID (e.g., 'product-manager')
    project_id: Optional[UUID]
    session_type: SessionType
    status: SessionStatus
    claude_session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def start(self) -> None:
        """
        Start the session (transition to working state).

        Raises:
            InvalidStateTransition: If current status doesn't allow starting
        """
        if self.status not in [SessionStatus.IDLE, SessionStatus.INITIALIZING]:
            raise InvalidStateTransition(
                f"Cannot start session from status '{self.status.value}'"
            )
        self.status = SessionStatus.WORKING
        self._update_timestamp()

    def complete_task(self) -> None:
        """
        Mark task as completed (transition to idle state).

        Raises:
            InvalidStateTransition: If not in working state
        """
        if self.status != SessionStatus.WORKING:
            raise InvalidStateTransition(
                f"Cannot complete task from status '{self.status.value}'"
            )
        self.status = SessionStatus.IDLE
        self._update_timestamp()

    def fail(self, error: str) -> None:
        """
        Mark session as failed with error message.

        Args:
            error: Error message describing the failure
        """
        self.status = SessionStatus.ERROR
        self.error_message = error
        self._update_timestamp()

    def interrupt(self) -> None:
        """
        Interrupt a running session.

        Raises:
            InvalidStateTransition: If not in working state
        """
        if self.status != SessionStatus.WORKING:
            raise InvalidStateTransition(
                f"Cannot interrupt session from status '{self.status.value}'"
            )
        self.status = SessionStatus.INTERRUPTED
        self._update_timestamp()

    def resume(self) -> None:
        """
        Resume session from error or interrupted state.

        Raises:
            InvalidStateTransition: If not in error or interrupted state
        """
        if self.status not in [SessionStatus.ERROR, SessionStatus.INTERRUPTED]:
            raise InvalidStateTransition(
                f"Can only resume from error or interrupted state, not '{self.status.value}'"
            )
        self.status = SessionStatus.IDLE
        self.error_message = None
        self._update_timestamp()

    def update_context(self, key: str, value: Any) -> None:
        """
        Update session context.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        self._update_timestamp()

    def is_active(self) -> bool:
        """
        Check if session is in an active (non-error) state.

        Returns:
            True if session is active, False otherwise
        """
        return self.status != SessionStatus.ERROR

    def is_busy(self) -> bool:
        """
        Check if session is currently processing.

        Returns:
            True if session is busy (working), False otherwise
        """
        return self.status == SessionStatus.WORKING

    def _update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = _utcnow()

    def validate(self) -> None:
        """
        Validate session invariants.

        Raises:
            ValidationError: If validation fails
        """
        # Must have agent_id
        if not self.agent_id:
            raise ValidationError("Session must have agent_id")

        if self.session_type == SessionType.PM and not self.project_id:
            raise ValidationError("PM sessions must have a project_id")

    def sync_kanban_stage(self) -> None:
        """
        Sync kanban_stage in context based on current session status.

        Status to kanban_stage mapping:
        - INITIALIZING → backlog
        - WORKING → active
        - IDLE → waiting
        - ERROR → waiting

        This method updates the session's context dict in place.
        """
        status_to_stage = {
            SessionStatus.INITIALIZING: "backlog",
            SessionStatus.WORKING: "active",
            SessionStatus.IDLE: "waiting",
            SessionStatus.ERROR: "waiting",
        }

        if self.status in status_to_stage:
            if self.context is None:
                self.context = {}
            self.context["kanban_stage"] = status_to_stage[self.status]
