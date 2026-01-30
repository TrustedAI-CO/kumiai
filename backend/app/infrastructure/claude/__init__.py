"""
Claude SDK infrastructure module.

Provides Claude SDK client management and integration.
"""

from app.infrastructure.claude.core.client import ClaudeClient
from app.infrastructure.claude.core.client_manager import ClaudeClientManager
from app.infrastructure.claude.config import ClaudeSettings
from app.infrastructure.claude.execution.executor import SessionExecutor
from app.infrastructure.claude.streaming.converter import convert_message_to_events
from app.infrastructure.claude.streaming.events import (
    StreamDeltaEvent,
    ToolUseEvent,
    ToolCompleteEvent,
    MessageCompleteEvent,
    MessageStartEvent,
    ResultEvent,
    ErrorEvent,
    SSEEvent,
    ContentBlockEvent,
    ContentBlockStopEvent,
    UserMessageEvent,
    QueueStatusEvent,
    SessionStatusEvent,
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
    "MessageStartEvent",
    "ResultEvent",
    "ErrorEvent",
    "SSEEvent",
    "ContentBlockEvent",
    "ContentBlockStopEvent",
    "UserMessageEvent",
    "QueueStatusEvent",
    "SessionStatusEvent",
    "ClaudeError",
    "ClaudeConnectionError",
    "ClaudeSessionNotFoundError",
    "ClaudeExecutionError",
    "ClientNotFoundError",
    "AgentNotFoundError",
]
