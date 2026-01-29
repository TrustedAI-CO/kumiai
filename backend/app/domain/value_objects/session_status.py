"""Session status value object with state machine logic."""

from enum import Enum
from typing import Dict, Set


# State machine transitions mapping (defined outside class to avoid enum member conflict)
_STATE_TRANSITIONS: Dict[str, Set[str]] = {
    "initializing": {"working", "error"},
    "working": {"idle", "error", "done", "interrupted"},
    "idle": {"working", "error", "done"},
    "error": {"idle"},  # Can resume from error
    "done": {"working"},  # Can resume from done
    "interrupted": {"idle"},  # Can resume from interrupted
}


class SessionStatus(str, Enum):
    """
    Session status with state machine transitions.

    Valid state transitions enforce business rules:
    - initializing → working, error
    - working → idle, error, done, interrupted
    - idle → working, error, done
    - error → idle (resume)
    - done → working (resume)
    - interrupted → idle (resume)
    """

    INITIALIZING = "initializing"
    WORKING = "working"
    IDLE = "idle"
    ERROR = "error"
    DONE = "done"
    INTERRUPTED = "interrupted"

    @classmethod
    def can_transition(
        cls, from_status: "SessionStatus", to_status: "SessionStatus"
    ) -> bool:
        """
        Check if transition from one status to another is valid.

        Args:
            from_status: Current session status
            to_status: Target session status

        Returns:
            True if transition is valid, False otherwise

        Examples:
            >>> SessionStatus.can_transition(SessionStatus.IDLE, SessionStatus.WORKING)
            True
            >>> SessionStatus.can_transition(SessionStatus.ERROR, SessionStatus.WORKING)
            False
        """
        return to_status.value in _STATE_TRANSITIONS.get(from_status.value, set())

    def can_transition_to(self, new_status: "SessionStatus") -> bool:
        """
        Check if this status can transition to new status.

        Args:
            new_status: Target session status

        Returns:
            True if transition is valid, False otherwise

        Examples:
            >>> status = SessionStatus.IDLE
            >>> status.can_transition_to(SessionStatus.WORKING)
            True
        """
        return new_status.value in _STATE_TRANSITIONS.get(self.value, set())

    def is_terminal(self) -> bool:
        """
        Check if this is a terminal state (no valid transitions).

        Note: DONE can resume to WORKING, so it's not strictly terminal.

        Returns:
            True if terminal (no transitions), False otherwise

        Examples:
            >>> SessionStatus.DONE.is_terminal()
            False
            >>> SessionStatus.IDLE.is_terminal()
            False
        """
        return len(_STATE_TRANSITIONS.get(self.value, set())) == 0

    def is_active(self) -> bool:
        """
        Check if session is in an active state (not in error).

        Returns:
            True if active, False otherwise

        Examples:
            >>> SessionStatus.WORKING.is_active()
            True
            >>> SessionStatus.ERROR.is_active()
            False
        """
        return self != self.ERROR

    def is_busy(self) -> bool:
        """
        Check if session is currently processing (working).

        Returns:
            True if busy, False otherwise

        Examples:
            >>> SessionStatus.WORKING.is_busy()
            True
            >>> SessionStatus.IDLE.is_busy()
            False
        """
        return self == self.WORKING

    def get_valid_next_states(self) -> Set["SessionStatus"]:
        """
        Get all valid next states from current status.

        Returns:
            Set of valid SessionStatus values for transition

        Examples:
            >>> status = SessionStatus.IDLE
            >>> next_states = status.get_valid_next_states()
            >>> SessionStatus.WORKING in next_states
            True
        """
        valid_values = _STATE_TRANSITIONS.get(self.value, set())
        return {self.__class__(v) for v in valid_values}
