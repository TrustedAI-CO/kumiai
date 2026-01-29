"""
Claude SDK infrastructure exceptions.

Custom exception hierarchy for Claude SDK client operations.
"""


class ClaudeError(Exception):
    """Base exception for Claude SDK errors."""

    pass


class ClaudeConnectionError(ClaudeError):
    """Connection to Claude SDK failed or timed out."""

    pass


class ClaudeSessionNotFoundError(ClaudeError):
    """Failed to resume session - conversation not found."""

    pass


class ClaudeExecutionError(ClaudeError):
    """Runtime execution error in Claude SDK."""

    pass


class ClientNotFoundError(ClaudeError):
    """Client not found in manager."""

    pass


class AgentNotFoundError(ClaudeError):
    """Agent configuration not found or malformed."""

    pass
