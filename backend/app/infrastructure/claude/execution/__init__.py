"""Execution management for Claude sessions.

This module handles session execution, queue processing, and hooks.
"""

from app.infrastructure.claude.execution.executor import SessionExecutor
from app.infrastructure.claude.execution.execution import Execution
from app.infrastructure.claude.execution.hooks import inject_session_context_hook
from app.infrastructure.claude.execution.queue_processor import MessageQueueProcessor

__all__ = [
    "SessionExecutor",
    "Execution",
    "inject_session_context_hook",
    "MessageQueueProcessor",
]
