"""Tests for domain events."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.events import (
    DomainEvent,
    SessionCreated,
    SessionStatusChanged,
    SessionFailed,
    SessionCompleted,
    MessageAdded,
    ProjectPMAssigned,
    ProjectPMRemoved,
)


class TestDomainEvent:
    """Test base domain event functionality."""

    def test_domain_event_has_event_id(self):
        """Test that domain event has a unique event ID."""
        event = DomainEvent()
        assert event.event_id is not None
        assert isinstance(event.event_id, type(uuid4()))

    def test_domain_event_has_occurred_at(self):
        """Test that domain event has an occurred_at timestamp."""
        event = DomainEvent()
        assert event.occurred_at is not None
        assert isinstance(event.occurred_at, datetime)

    def test_domain_event_unique_ids(self):
        """Test that each domain event gets a unique ID."""
        event1 = DomainEvent()
        event2 = DomainEvent()
        assert event1.event_id != event2.event_id

    def test_domain_event_immutable(self):
        """Test that domain event is immutable."""
        event = DomainEvent()
        with pytest.raises(Exception):  # FrozenInstanceError
            event.event_id = uuid4()

    def test_domain_event_with_aggregate_id(self):
        """Test domain event with aggregate ID."""
        aggregate_id = uuid4()
        event = DomainEvent(aggregate_id=aggregate_id)
        assert event.aggregate_id == aggregate_id


class TestSessionCreated:
    """Test SessionCreated event."""

    def test_session_created_event(self):
        """Test creating a SessionCreated event."""
        session_id = uuid4()
        agent_id = uuid4()
        project_id = uuid4()

        event = SessionCreated(
            session_id=session_id,
            agent_id=agent_id,
            session_type="pm",
            project_id=project_id,
        )

        assert event.session_id == session_id
        assert event.agent_id == agent_id
        assert event.session_type == "pm"
        assert event.project_id == project_id
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_session_created_immutable(self):
        """Test that SessionCreated is immutable."""
        event = SessionCreated(
            session_id=uuid4(),
            agent_id=uuid4(),
            session_type="pm",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.session_id = uuid4()

    def test_session_created_without_project(self):
        """Test SessionCreated without project ID (assistant session)."""
        event = SessionCreated(
            session_id=uuid4(),
            agent_id=uuid4(),
            session_type="assistant",
            project_id=None,
        )

        assert event.project_id is None


class TestSessionStatusChanged:
    """Test SessionStatusChanged event."""

    def test_session_status_changed_event(self):
        """Test creating a SessionStatusChanged event."""
        session_id = uuid4()
        event = SessionStatusChanged(
            session_id=session_id,
            old_status="idle",
            new_status="thinking",
        )

        assert event.session_id == session_id
        assert event.old_status == "idle"
        assert event.new_status == "thinking"
        assert event.reason is None

    def test_session_status_changed_with_reason(self):
        """Test SessionStatusChanged with reason."""
        event = SessionStatusChanged(
            session_id=uuid4(),
            old_status="thinking",
            new_status="error",
            reason="API timeout",
        )

        assert event.reason == "API timeout"

    def test_session_status_changed_immutable(self):
        """Test that SessionStatusChanged is immutable."""
        event = SessionStatusChanged(
            session_id=uuid4(),
            old_status="idle",
            new_status="thinking",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.new_status = "working"


class TestSessionFailed:
    """Test SessionFailed event."""

    def test_session_failed_event(self):
        """Test creating a SessionFailed event."""
        session_id = uuid4()
        event = SessionFailed(
            session_id=session_id,
            error_message="Connection timeout",
        )

        assert event.session_id == session_id
        assert event.error_message == "Connection timeout"
        assert event.error_details is None

    def test_session_failed_with_details(self):
        """Test SessionFailed with error details."""
        error_details = {
            "error_code": "TIMEOUT",
            "retry_count": 3,
            "last_attempt": "2026-01-20T10:00:00Z",
        }
        event = SessionFailed(
            session_id=uuid4(),
            error_message="Connection timeout",
            error_details=error_details,
        )

        assert event.error_details == error_details
        assert event.error_details["error_code"] == "TIMEOUT"

    def test_session_failed_immutable(self):
        """Test that SessionFailed is immutable."""
        event = SessionFailed(
            session_id=uuid4(),
            error_message="Error",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.error_message = "New error"


class TestSessionCompleted:
    """Test SessionCompleted event."""

    def test_session_completed_event(self):
        """Test creating a SessionCompleted event."""
        session_id = uuid4()
        event = SessionCompleted(
            session_id=session_id,
            result_summary="Task completed successfully",
        )

        assert event.session_id == session_id
        assert event.result_summary == "Task completed successfully"

    def test_session_completed_without_summary(self):
        """Test SessionCompleted without result summary."""
        event = SessionCompleted(
            session_id=uuid4(),
            result_summary=None,
        )

        assert event.result_summary is None

    def test_session_completed_immutable(self):
        """Test that SessionCompleted is immutable."""
        event = SessionCompleted(session_id=uuid4())

        with pytest.raises(Exception):  # FrozenInstanceError
            event.session_id = uuid4()


class TestMessageAdded:
    """Test MessageAdded event."""

    def test_message_added_event(self):
        """Test creating a MessageAdded event."""
        session_id = uuid4()
        message_id = uuid4()
        event = MessageAdded(
            session_id=session_id,
            message_id=message_id,
            role="user",
            sequence=0,
        )

        assert event.session_id == session_id
        assert event.message_id == message_id
        assert event.role == "user"
        assert event.sequence == 0

    def test_message_added_immutable(self):
        """Test that MessageAdded is immutable."""
        event = MessageAdded(
            session_id=uuid4(),
            message_id=uuid4(),
            role="assistant",
            sequence=1,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.sequence = 2


class TestProjectPMAssigned:
    """Test ProjectPMAssigned event."""

    def test_project_pm_assigned_event(self):
        """Test creating a ProjectPMAssigned event."""
        project_id = uuid4()
        pm_agent_id = uuid4()
        pm_session_id = uuid4()

        event = ProjectPMAssigned(
            project_id=project_id,
            pm_agent_id=pm_agent_id,
            pm_session_id=pm_session_id,
        )

        assert event.project_id == project_id
        assert event.pm_agent_id == pm_agent_id
        assert event.pm_session_id == pm_session_id

    def test_project_pm_assigned_immutable(self):
        """Test that ProjectPMAssigned is immutable."""
        event = ProjectPMAssigned(
            project_id=uuid4(),
            pm_agent_id=uuid4(),
            pm_session_id=uuid4(),
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.pm_agent_id = uuid4()


class TestProjectPMRemoved:
    """Test ProjectPMRemoved event."""

    def test_project_pm_removed_event(self):
        """Test creating a ProjectPMRemoved event."""
        project_id = uuid4()
        old_pm_agent_id = uuid4()
        old_pm_session_id = uuid4()

        event = ProjectPMRemoved(
            project_id=project_id,
            old_pm_agent_id=old_pm_agent_id,
            old_pm_session_id=old_pm_session_id,
            reason="PM reassigned to different project",
        )

        assert event.project_id == project_id
        assert event.old_pm_agent_id == old_pm_agent_id
        assert event.old_pm_session_id == old_pm_session_id
        assert event.reason == "PM reassigned to different project"

    def test_project_pm_removed_without_reason(self):
        """Test ProjectPMRemoved without reason."""
        event = ProjectPMRemoved(
            project_id=uuid4(),
            old_pm_agent_id=uuid4(),
        )

        assert event.reason is None
        assert event.old_pm_session_id is None

    def test_project_pm_removed_immutable(self):
        """Test that ProjectPMRemoved is immutable."""
        event = ProjectPMRemoved(
            project_id=uuid4(),
            old_pm_agent_id=uuid4(),
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.project_id = uuid4()
