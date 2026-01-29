"""Domain events for the KumiAI backend."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.

    Events are immutable records of things that happened in the domain.
    They capture important state changes and enable event-driven architectures,
    audit logging, and eventual consistency patterns.

    All domain events include:
    - event_id: Unique identifier for this event occurrence
    - occurred_at: Timestamp when the event occurred
    - aggregate_id: ID of the aggregate root that triggered the event
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: Optional[UUID] = None


@dataclass(frozen=True)
class SessionCreated(DomainEvent):
    """
    Fired when a new session is created.

    This event marks the creation of a new session entity,
    regardless of session type.
    """

    session_id: UUID = field(default=None)
    agent_id: str = field(default=None)
    session_type: str = field(default=None)
    project_id: Optional[UUID] = None


@dataclass(frozen=True)
class SessionStatusChanged(DomainEvent):
    """
    Fired when a session's status changes.

    This event captures state transitions in the session lifecycle,
    enabling monitoring, analytics, and downstream processing.
    """

    session_id: UUID = field(default=None)
    old_status: str = field(default=None)
    new_status: str = field(default=None)
    reason: Optional[str] = None


@dataclass(frozen=True)
class SessionFailed(DomainEvent):
    """
    Fired when a session fails with an error.

    This event indicates that a session has transitioned to the ERROR state,
    requiring investigation or retry logic.
    """

    session_id: UUID = field(default=None)
    error_message: str = field(default=None)
    error_details: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class SessionCompleted(DomainEvent):
    """
    Fired when a session completes successfully.

    This event marks the successful completion of a session's work,
    enabling cleanup, result processing, and completion tracking.
    """

    session_id: UUID = field(default=None)
    result_summary: Optional[str] = None


@dataclass(frozen=True)
class MessageAdded(DomainEvent):
    """
    Fired when a message is added to a session.

    This event tracks the conversation flow and enables
    message-based analytics and processing.
    """

    session_id: UUID = field(default=None)
    message_id: UUID = field(default=None)
    role: str = field(default=None)
    sequence: int = field(default=None)


@dataclass(frozen=True)
class ProjectPMAssigned(DomainEvent):
    """
    Fired when a PM (Project Manager) is assigned to a project.

    This event captures the assignment of a PM agent to manage a project,
    establishing the PM's authority over the project.
    """

    project_id: UUID = field(default=None)
    pm_agent_id: str = field(default=None)
    pm_session_id: UUID = field(default=None)


@dataclass(frozen=True)
class ProjectPMRemoved(DomainEvent):
    """
    Fired when a PM is removed from a project.

    This event captures the removal or reassignment of a PM agent,
    potentially requiring handoff or cleanup actions.
    """

    project_id: UUID = field(default=None)
    old_pm_agent_id: str = field(default=None)
    old_pm_session_id: Optional[UUID] = None
    reason: Optional[str] = None
