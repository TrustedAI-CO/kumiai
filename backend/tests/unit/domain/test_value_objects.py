"""Tests for domain value objects."""

from app.domain.value_objects import EventType, MessageRole, SessionStatus, SessionType


class TestSessionStatus:
    """Tests for SessionStatus value object."""

    def test_all_statuses_defined(self):
        """Test all session statuses are defined."""
        assert SessionStatus.INITIALIZING == "initializing"
        assert SessionStatus.WORKING == "working"
        assert SessionStatus.IDLE == "idle"
        assert SessionStatus.ERROR == "error"

    def test_valid_transitions_from_initializing(self):
        """Test valid transitions from initializing state."""
        assert SessionStatus.can_transition(
            SessionStatus.INITIALIZING, SessionStatus.WORKING
        )
        assert SessionStatus.can_transition(
            SessionStatus.INITIALIZING, SessionStatus.ERROR
        )
        # Invalid transitions
        assert not SessionStatus.can_transition(
            SessionStatus.INITIALIZING, SessionStatus.IDLE
        )

    def test_valid_transitions_from_working(self):
        """Test valid transitions from working state."""
        assert SessionStatus.can_transition(SessionStatus.WORKING, SessionStatus.IDLE)
        assert SessionStatus.can_transition(SessionStatus.WORKING, SessionStatus.ERROR)
        # Invalid transitions
        assert not SessionStatus.can_transition(
            SessionStatus.WORKING, SessionStatus.INITIALIZING
        )

    def test_valid_transitions_from_idle(self):
        """Test valid transitions from idle state."""
        assert SessionStatus.can_transition(SessionStatus.IDLE, SessionStatus.WORKING)
        assert SessionStatus.can_transition(SessionStatus.IDLE, SessionStatus.ERROR)
        # Invalid transitions
        assert not SessionStatus.can_transition(
            SessionStatus.IDLE, SessionStatus.INITIALIZING
        )

    def test_valid_transitions_from_error(self):
        """Test valid transitions from error state (resume)."""
        assert SessionStatus.can_transition(SessionStatus.ERROR, SessionStatus.IDLE)
        # Invalid transitions
        assert not SessionStatus.can_transition(
            SessionStatus.ERROR, SessionStatus.WORKING
        )
        assert not SessionStatus.can_transition(
            SessionStatus.ERROR, SessionStatus.INITIALIZING
        )

    def test_can_transition_to_instance_method(self):
        """Test can_transition_to instance method."""
        idle_status = SessionStatus.IDLE
        assert idle_status.can_transition_to(SessionStatus.WORKING)
        assert idle_status.can_transition_to(SessionStatus.ERROR)
        assert not idle_status.can_transition_to(SessionStatus.INITIALIZING)

    def test_is_terminal(self):
        """Test is_terminal method (no terminal states in simplified state machine)."""
        # In the simplified state machine, ERROR can transition to IDLE
        assert not SessionStatus.ERROR.is_terminal()
        assert not SessionStatus.IDLE.is_terminal()
        assert not SessionStatus.WORKING.is_terminal()
        assert not SessionStatus.INITIALIZING.is_terminal()

    def test_is_active(self):
        """Test is_active method."""
        # Active states
        assert SessionStatus.INITIALIZING.is_active()
        assert SessionStatus.IDLE.is_active()
        assert SessionStatus.WORKING.is_active()
        # Inactive states
        assert not SessionStatus.ERROR.is_active()

    def test_is_busy(self):
        """Test is_busy method."""
        # Busy state
        assert SessionStatus.WORKING.is_busy()
        # Not busy states
        assert not SessionStatus.IDLE.is_busy()
        assert not SessionStatus.INITIALIZING.is_busy()
        assert not SessionStatus.ERROR.is_busy()

    def test_get_valid_next_states(self):
        """Test get_valid_next_states method."""
        idle_status = SessionStatus.IDLE
        next_states = idle_status.get_valid_next_states()
        assert SessionStatus.WORKING in next_states
        assert SessionStatus.ERROR in next_states
        assert SessionStatus.INITIALIZING not in next_states
        assert len(next_states) == 2

        # Error state can resume to idle
        error_status = SessionStatus.ERROR
        error_next = error_status.get_valid_next_states()
        assert SessionStatus.IDLE in error_next
        assert len(error_next) == 1


class TestSessionType:
    """Tests for SessionType value object."""

    def test_all_types_defined(self):
        """Test all session types are defined."""
        assert SessionType.PM == "pm"
        assert SessionType.SPECIALIST == "specialist"
        assert SessionType.ASSISTANT == "assistant"

    def test_requires_project(self):
        """Test requires_project method."""
        assert SessionType.PM.requires_project()
        assert not SessionType.SPECIALIST.requires_project()
        assert not SessionType.ASSISTANT.requires_project()


class TestMessageRole:
    """Tests for MessageRole value object."""

    def test_all_roles_defined(self):
        """Test all message roles are defined."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.TOOL_RESULT == "tool_result"

    def test_is_from_user(self):
        """Test is_from_user method."""
        assert MessageRole.USER.is_from_user()
        assert not MessageRole.ASSISTANT.is_from_user()
        assert not MessageRole.SYSTEM.is_from_user()
        assert not MessageRole.TOOL_RESULT.is_from_user()

    def test_is_from_assistant(self):
        """Test is_from_assistant method."""
        assert MessageRole.ASSISTANT.is_from_assistant()
        assert not MessageRole.USER.is_from_assistant()
        assert not MessageRole.SYSTEM.is_from_assistant()
        assert not MessageRole.TOOL_RESULT.is_from_assistant()

    def test_is_system_or_tool(self):
        """Test is_system_or_tool method."""
        assert MessageRole.SYSTEM.is_system_or_tool()
        assert MessageRole.TOOL_RESULT.is_system_or_tool()
        assert not MessageRole.USER.is_system_or_tool()
        assert not MessageRole.ASSISTANT.is_system_or_tool()

    def test_requires_tool_use_id(self):
        """Test requires_tool_use_id method."""
        assert MessageRole.TOOL_RESULT.requires_tool_use_id()
        assert not MessageRole.USER.requires_tool_use_id()
        assert not MessageRole.ASSISTANT.requires_tool_use_id()
        assert not MessageRole.SYSTEM.requires_tool_use_id()


class TestEventType:
    """Tests for EventType value object."""

    def test_all_types_defined(self):
        """Test all event types are defined."""
        assert EventType.SESSION_CREATED == "session_created"
        assert EventType.SESSION_STARTED == "session_started"
        assert EventType.SESSION_COMPLETED == "session_completed"
        assert EventType.SESSION_FAILED == "session_failed"
        assert EventType.MESSAGE_SENT == "message_sent"
        assert EventType.TOOL_EXECUTED == "tool_executed"
        assert EventType.PROJECT_CREATED == "project_created"
        assert EventType.PROJECT_UPDATED == "project_updated"

    def test_is_session_event(self):
        """Test is_session_event method."""
        assert EventType.SESSION_CREATED.is_session_event()
        assert EventType.SESSION_STARTED.is_session_event()
        assert EventType.SESSION_COMPLETED.is_session_event()
        assert EventType.SESSION_FAILED.is_session_event()
        assert not EventType.MESSAGE_SENT.is_session_event()
        assert not EventType.TOOL_EXECUTED.is_session_event()
        assert not EventType.PROJECT_CREATED.is_session_event()

    def test_is_project_event(self):
        """Test is_project_event method."""
        assert EventType.PROJECT_CREATED.is_project_event()
        assert EventType.PROJECT_UPDATED.is_project_event()
        assert not EventType.SESSION_CREATED.is_project_event()
        assert not EventType.MESSAGE_SENT.is_project_event()
        assert not EventType.TOOL_EXECUTED.is_project_event()

    def test_is_error_event(self):
        """Test is_error_event method."""
        assert EventType.SESSION_FAILED.is_error_event()
        assert not EventType.SESSION_CREATED.is_error_event()
        assert not EventType.SESSION_COMPLETED.is_error_event()
        assert not EventType.MESSAGE_SENT.is_error_event()
