"""Common types for Claude infrastructure."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class QueuedMessage:
    """Envelope for queued messages with sender metadata."""

    message: str
    sender_name: Optional[str] = None
    sender_session_id: Optional[UUID] = None
    sender_agent_id: Optional[str] = None


@dataclass
class StopStreamingSignal:
    """Sentinel to signal end of message stream."""

    pass
