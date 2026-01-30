"""Streaming and message handling components.

This module handles event conversion, batch processing, persistence, and text buffering.
"""

from app.infrastructure.claude.streaming.events import (
    StreamDeltaEvent,
    MessageStartEvent,
    ContentBlockEvent,
    ContentBlockStopEvent,
    UserMessageEvent,
    QueueStatusEvent,
    SessionStatusEvent,
    ErrorEvent,
)
from app.infrastructure.claude.streaming.converter import convert_message_to_events
from app.infrastructure.claude.streaming.batch_processor import BatchMessageProcessor
from app.infrastructure.claude.streaming.persistence import MessagePersistence
from app.infrastructure.claude.streaming.text_buffer import TextBufferManager

__all__ = [
    # Events
    "StreamDeltaEvent",
    "MessageStartEvent",
    "ContentBlockEvent",
    "ContentBlockStopEvent",
    "UserMessageEvent",
    "QueueStatusEvent",
    "SessionStatusEvent",
    "ErrorEvent",
    # Utilities
    "convert_message_to_events",
    "BatchMessageProcessor",
    "MessagePersistence",
    "TextBufferManager",
]
