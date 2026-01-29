"""SSE event types for streaming responses."""

from dataclasses import dataclass
from typing import Literal, Dict, Any, Optional
import json


@dataclass
class StreamDeltaEvent:
    """Text content chunk streamed from Claude."""

    session_id: str
    content: str
    content_index: int = 0  # Content block index from Claude SDK
    type: Literal["stream_delta"] = "stream_delta"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        return {
            "event": self.type,
            "data": json.dumps(
                {"session_id": self.session_id, "content": self.content}
            ),
        }


@dataclass
class ToolUseEvent:
    """Tool execution started."""

    session_id: str
    tool_use_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    response_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    type: Literal["tool_use"] = "tool_use"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        data = {
            "session_id": self.session_id,
            "tool_use_id": self.tool_use_id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
        }
        if self.response_id is not None:
            data["response_id"] = self.response_id
        if self.agent_id is not None:
            data["agent_id"] = self.agent_id
        if self.agent_name is not None:
            data["agent_name"] = self.agent_name
        return {"event": self.type, "data": json.dumps(data)}


@dataclass
class ToolCompleteEvent:
    """Tool execution completed."""

    session_id: str
    tool_use_id: str
    result: Optional[str] = (
        None  # Tool execution result (can be text, JSON, or error message)
    )
    is_error: bool = False  # Whether the tool execution failed
    type: Literal["tool_complete"] = "tool_complete"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        data = {"session_id": self.session_id, "tool_use_id": self.tool_use_id}
        if self.result is not None:
            data["result"] = self.result
        if self.is_error:
            data["is_error"] = self.is_error

        return {"event": self.type, "data": json.dumps(data)}


@dataclass
class MessageStartEvent:
    """Message started - clear all buffers."""

    session_id: str
    type: Literal["message_start_marker"] = "message_start_marker"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format - not sent to client."""
        return {"event": "internal", "data": "{}"}


@dataclass
class ContentBlockStopEvent:
    """Marker event to trigger buffer flush."""

    session_id: str
    content_index: int = 0  # Content block index from Claude SDK
    type: Literal["content_block_stop_marker"] = "content_block_stop_marker"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format - not sent to client."""
        return {"event": "internal", "data": "{}"}


@dataclass
class ContentBlockEvent:
    """Complete content block at transition points."""

    session_id: str
    content: str
    block_type: Literal["text", "tool"]
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    response_id: Optional[str] = None
    type: Literal["content_block"] = "content_block"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        data = {
            "session_id": self.session_id,
            "content": self.content,
            "block_type": self.block_type,
        }
        if self.agent_id is not None:
            data["agent_id"] = self.agent_id
        if self.agent_name is not None:
            data["agent_name"] = self.agent_name
        if self.response_id is not None:
            data["response_id"] = self.response_id
        return {"event": self.type, "data": json.dumps(data)}


@dataclass
class MessageCompleteEvent:
    """Assistant response completed."""

    session_id: str
    type: Literal["message_complete"] = "message_complete"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        return {"event": self.type, "data": json.dumps({"session_id": self.session_id})}


@dataclass
class ResultEvent:
    """Execution result (final message)."""

    session_id: str
    result: str
    type: Literal["result"] = "result"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        return {
            "event": self.type,
            "data": json.dumps({"session_id": self.session_id, "result": self.result}),
        }


@dataclass
class ErrorEvent:
    """Execution error occurred."""

    session_id: str
    error: str
    error_type: Optional[str] = None
    type: Literal["error"] = "error"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        data = {"session_id": self.session_id, "error": self.error}
        if self.error_type:
            data["error_type"] = self.error_type

        return {"event": self.type, "data": json.dumps(data)}


@dataclass
class UserMessageEvent:
    """User message received (including cross-session messages)."""

    session_id: str
    message_id: str
    content: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    from_instance_id: Optional[str] = None
    timestamp: Optional[str] = None
    type: Literal["user_message"] = "user_message"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        data = {
            "session_id": self.session_id,
            "message_id": self.message_id,
            "content": self.content,
        }
        if self.agent_id is not None:
            data["agent_id"] = self.agent_id
        if self.agent_name is not None:
            data["agent_name"] = self.agent_name
        if self.from_instance_id is not None:
            data["from_instance_id"] = self.from_instance_id
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp

        return {"event": self.type, "data": json.dumps(data)}


@dataclass
class QueuedMessagePreview:
    """Preview of a queued message."""

    sender_name: Optional[str]
    sender_session_id: Optional[str]
    content_preview: str  # Truncated message content
    timestamp: str  # ISO timestamp


@dataclass
class QueueStatusEvent:
    """Queue status update with message previews."""

    session_id: str
    messages: list[QueuedMessagePreview] = None  # Preview of queued messages
    type: Literal["queue_status"] = "queue_status"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        data = {
            "session_id": self.session_id,
        }
        if self.messages:
            data["messages"] = [
                {
                    "sender_name": msg.sender_name,
                    "sender_session_id": msg.sender_session_id,
                    "content_preview": msg.content_preview,
                    "timestamp": msg.timestamp,
                }
                for msg in self.messages
            ]
        return {"event": self.type, "data": json.dumps(data)}


@dataclass
class SessionStatusEvent:
    """Session status update (idle, working, error)."""

    session_id: str
    status: str  # SessionStatus value: 'idle', 'working', 'error', etc.
    type: Literal["session_status"] = "session_status"

    def to_sse(self) -> Dict[str, Any]:
        """Convert to SSE format."""
        return {
            "event": self.type,
            "data": json.dumps({"session_id": self.session_id, "status": self.status}),
        }


# Type alias for all event types
SSEEvent = (
    StreamDeltaEvent
    | ContentBlockEvent
    | ToolUseEvent
    | ToolCompleteEvent
    | MessageCompleteEvent
    | ResultEvent
    | ErrorEvent
    | UserMessageEvent
    | QueueStatusEvent
    | SessionStatusEvent
)
