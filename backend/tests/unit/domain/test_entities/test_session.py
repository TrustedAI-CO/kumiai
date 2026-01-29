"""Tests for Session domain entity."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import InvalidStateTransition, ValidationError
from app.domain.entities.session import Session
from app.domain.value_objects import SessionStatus, SessionType


class TestSessionCreation:
    """Tests for Session entity creation."""

    def test_create_session_with_required_fields(self):
        """Test creating a session with required fields."""
        session_id = uuid4()
        agent_id = "test-agent"
        project_id = uuid4()

        session = Session(
            id=session_id,
            agent_id=agent_id,
            project_id=project_id,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.INITIALIZING,
        )

        assert session.id == session_id
        assert session.agent_id == agent_id
        assert session.project_id == project_id
        assert session.session_type == SessionType.SPECIALIST
        assert session.status == SessionStatus.INITIALIZING
        assert session.claude_session_id is None
        assert session.context == {}
        assert session.error_message is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_create_session_with_optional_fields(self):
        """Test creating a session with optional fields."""
        session_id = uuid4()
        agent_id = "test-agent"
        context = {"key": "value"}

        session = Session(
            id=session_id,
            agent_id=agent_id,
            project_id=None,
            session_type=SessionType.ASSISTANT,
            status=SessionStatus.IDLE,
            claude_session_id="claude-123",
            context=context,
            error_message="test error",
        )

        assert session.claude_session_id == "claude-123"
        assert session.context == context
        assert session.error_message == "test error"


class TestSessionStart:
    """Tests for Session.start() method."""

    def test_start_from_idle(self):
        """Test starting a session from idle status."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
        )
        initial_updated_at = session.updated_at

        session.start()

        assert session.status == SessionStatus.WORKING
        assert session.updated_at > initial_updated_at

    def test_start_from_initializing(self):
        """Test starting a session from initializing status."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.INITIALIZING,
        )

        session.start()

        assert session.status == SessionStatus.WORKING

    def test_start_from_error_raises_error(self):
        """Test that starting from error status raises error."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.ERROR,
        )

        with pytest.raises(InvalidStateTransition) as exc_info:
            session.start()

        assert "Cannot start session from status 'error'" in str(exc_info.value)


class TestSessionCompleteTask:
    """Tests for Session.complete_task() method."""

    def test_complete_task_from_working(self):
        """Test completing a task from working status transitions to idle."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )
        initial_updated_at = session.updated_at

        session.complete_task()

        assert session.status == SessionStatus.IDLE
        assert session.updated_at > initial_updated_at

    def test_complete_task_from_non_working_raises_error(self):
        """Test that completing from non-working status raises error."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
        )

        with pytest.raises(InvalidStateTransition) as exc_info:
            session.complete_task()

        assert "Cannot complete task from status 'idle'" in str(exc_info.value)


class TestSessionFail:
    """Tests for Session.fail() method."""

    def test_fail_sets_error_and_status(self):
        """Test that failing a session sets error message and status."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )
        initial_updated_at = session.updated_at
        error_msg = "Test error message"

        session.fail(error_msg)

        assert session.status == SessionStatus.ERROR
        assert session.error_message == error_msg
        assert session.updated_at > initial_updated_at

    def test_fail_from_any_status(self):
        """Test that fail works from any status."""
        statuses = [
            SessionStatus.INITIALIZING,
            SessionStatus.IDLE,
            SessionStatus.WORKING,
        ]

        for status in statuses:
            session = Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=status,
            )
            session.fail("error")
            assert session.status == SessionStatus.ERROR


class TestSessionCancel:
    """Tests for Session.cancel() method."""

    def test_cancel_transitions_to_idle(self):
        """Test cancelling transitions to idle status."""
        statuses = [
            SessionStatus.INITIALIZING,
            SessionStatus.IDLE,
            SessionStatus.WORKING,
            SessionStatus.ERROR,
        ]

        for status in statuses:
            session = Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=status,
            )
            initial_updated_at = session.updated_at

            session.cancel()

            assert session.status == SessionStatus.IDLE
            assert session.updated_at >= initial_updated_at


class TestSessionResume:
    """Tests for Session.resume() method."""

    def test_resume_from_error(self):
        """Test resuming from error status."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.ERROR,
            error_message="Previous error",
        )
        initial_updated_at = session.updated_at

        session.resume()

        assert session.status == SessionStatus.IDLE
        assert session.error_message is None
        assert session.updated_at > initial_updated_at

    def test_resume_from_non_error_raises_error(self):
        """Test that resuming from non-error status raises error."""
        non_resumable = [
            SessionStatus.INITIALIZING,
            SessionStatus.IDLE,
            SessionStatus.WORKING,
        ]

        for status in non_resumable:
            session = Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=status,
            )

            with pytest.raises(InvalidStateTransition) as exc_info:
                session.resume()

            assert "Can only resume from error state" in str(exc_info.value)


class TestSessionUpdateContext:
    """Tests for Session.update_context() method."""

    def test_update_context_adds_key(self):
        """Test that update_context adds a new key."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
        )
        initial_updated_at = session.updated_at

        session.update_context("key1", "value1")

        assert session.context["key1"] == "value1"
        assert session.updated_at > initial_updated_at

    def test_update_context_updates_existing_key(self):
        """Test that update_context updates existing key."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
            context={"key1": "old_value"},
        )

        session.update_context("key1", "new_value")

        assert session.context["key1"] == "new_value"

    def test_update_context_with_complex_values(self):
        """Test update_context with complex values."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.IDLE,
        )

        session.update_context("dict_key", {"nested": "value"})
        session.update_context("list_key", [1, 2, 3])
        session.update_context("int_key", 42)

        assert session.context["dict_key"] == {"nested": "value"}
        assert session.context["list_key"] == [1, 2, 3]
        assert session.context["int_key"] == 42


class TestSessionIsActive:
    """Tests for Session.is_active() method."""

    def test_is_active_for_active_statuses(self):
        """Test is_active returns True for active statuses."""
        active_statuses = [
            SessionStatus.INITIALIZING,
            SessionStatus.IDLE,
            SessionStatus.WORKING,
        ]

        for status in active_statuses:
            session = Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=status,
            )
            assert session.is_active() is True

    def test_is_active_for_error_status(self):
        """Test is_active returns False for error status."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.ERROR,
        )
        assert session.is_active() is False


class TestSessionIsBusy:
    """Tests for Session.is_busy() method."""

    def test_is_busy_for_working_status(self):
        """Test is_busy returns True for working status."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.WORKING,
        )
        assert session.is_busy() is True

    def test_is_busy_for_non_busy_statuses(self):
        """Test is_busy returns False for non-busy statuses."""
        non_busy = [
            SessionStatus.INITIALIZING,
            SessionStatus.IDLE,
            SessionStatus.ERROR,
        ]

        for status in non_busy:
            session = Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=SessionType.SPECIALIST,
                status=status,
            )
            assert session.is_busy() is False


class TestSessionValidation:
    """Tests for Session.validate() method."""

    def test_validate_pm_session_without_project_raises_error(self):
        """Test that PM sessions without project_id fail validation."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=None,
            session_type=SessionType.PM,
            status=SessionStatus.IDLE,
        )

        with pytest.raises(ValidationError) as exc_info:
            session.validate()

        assert "PM sessions must have a project_id" in str(exc_info.value)

    def test_validate_pm_session_with_project_passes(self):
        """Test that PM sessions with project_id pass validation."""
        session = Session(
            id=uuid4(),
            agent_id="test-agent",
            project_id=uuid4(),
            session_type=SessionType.PM,
            status=SessionStatus.IDLE,
        )

        # Should not raise
        session.validate()

    def test_validate_non_pm_session_without_project_passes(self):
        """Test that non-PM sessions without project_id pass validation."""
        session_types = [
            SessionType.SPECIALIST,
            SessionType.ASSISTANT,
        ]

        for session_type in session_types:
            session = Session(
                id=uuid4(),
                agent_id="test-agent",
                project_id=None,
                session_type=session_type,
                status=SessionStatus.IDLE,
            )

            # Should not raise
            session.validate()
