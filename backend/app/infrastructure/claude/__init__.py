"""
Claude SDK infrastructure module.

Provides Claude SDK client management and integration.
"""

from app.infrastructure.claude.client import ClaudeClient
from app.infrastructure.claude.client_manager import ClaudeClientManager
from app.infrastructure.claude.config import ClaudeSettings
from app.infrastructure.claude.executor import SessionExecutor
from app.infrastructure.claude.message_converter import convert_message_to_events
from app.infrastructure.claude.events import (
    StreamDeltaEvent,
    ToolUseEvent,
    ToolCompleteEvent,
    MessageCompleteEvent,
    ResultEvent,
    ErrorEvent,
    SSEEvent,
)
from app.infrastructure.claude.exceptions import (
    AgentNotFoundError,
    ClaudeConnectionError,
    ClaudeError,
    ClaudeExecutionError,
    ClaudeSessionNotFoundError,
    ClientNotFoundError,
)

__all__ = [
    "ClaudeClient",
    "ClaudeClientManager",
    "ClaudeSettings",
    "SessionExecutor",
    "convert_message_to_events",
    "StreamDeltaEvent",
    "ToolUseEvent",
    "ToolCompleteEvent",
    "MessageCompleteEvent",
    "ResultEvent",
    "ErrorEvent",
    "SSEEvent",
    "ClaudeError",
    "ClaudeConnectionError",
    "ClaudeSessionNotFoundError",
    "ClaudeExecutionError",
    "ClientNotFoundError",
    "AgentNotFoundError",
]
