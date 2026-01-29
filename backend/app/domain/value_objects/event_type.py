"""Event type value object for activity logging."""

from enum import Enum


class EventType(str, Enum):
    """
    Activity log event types.

    Event types categorize system activities for logging and auditing:
    - Session events: creation, start, completion, failure
    - Message events: sent
    - Tool events: execution
    - Project events: creation, updates
    """

    SESSION_CREATED = "session_created"
    SESSION_STARTED = "session_started"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"
    MESSAGE_SENT = "message_sent"
    TOOL_EXECUTED = "tool_executed"
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"

    def is_session_event(self) -> bool:
        """
        Check if this is a session-related event.

        Returns:
            True if event is session-related, False otherwise

        Examples:
            >>> EventType.SESSION_CREATED.is_session_event()
            True
            >>> EventType.MESSAGE_SENT.is_session_event()
            False
        """
        return self in {
            self.SESSION_CREATED,
            self.SESSION_STARTED,
            self.SESSION_COMPLETED,
            self.SESSION_FAILED,
        }

    def is_project_event(self) -> bool:
        """
        Check if this is a project-related event.

        Returns:
            True if event is project-related, False otherwise

        Examples:
            >>> EventType.PROJECT_CREATED.is_project_event()
            True
            >>> EventType.SESSION_CREATED.is_project_event()
            False
        """
        return self in {
            self.PROJECT_CREATED,
            self.PROJECT_UPDATED,
        }

    def is_error_event(self) -> bool:
        """
        Check if this event indicates an error condition.

        Returns:
            True if event indicates an error, False otherwise

        Examples:
            >>> EventType.SESSION_FAILED.is_error_event()
            True
            >>> EventType.SESSION_CREATED.is_error_event()
            False
        """
        return self == self.SESSION_FAILED
