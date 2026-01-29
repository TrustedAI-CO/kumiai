"""Message response DTO."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.application.dtos.base import BaseDTO
from app.domain.entities import Message
from app.domain.value_objects import MessageRole


class MessageDTO(BaseDTO):
    """Message response DTO.

    This DTO maps database fields to frontend-expected field names:
    - session_id -> instance_id (frontend terminology)
    - created_at -> timestamp (frontend terminology)
    - metadata.tool_name -> tool_name (top-level for frontend compatibility)
    - metadata.tool_args -> tool_args (top-level for frontend compatibility)
    """

    id: UUID
    instance_id: UUID  # Maps from entity.session_id
    role: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime  # Maps from entity.created_at

    # Sender attribution fields
    agent_id: Optional[str] = None  # Source of truth for which agent sent the message
    agent_name: Optional[str] = None  # Display name of the sending agent
    from_instance_id: Optional[UUID] = (
        None  # Session ID where message originated (for cross-session routing)
    )

    # Response grouping for UI
    response_id: Optional[str] = (
        None  # UUID shared by all messages in the same Claude response
    )

    # Tool-related fields (extracted from metadata for frontend compatibility)
    tool_name: Optional[str] = None  # Tool name for tool messages
    tool_args: Optional[Dict[str, Any]] = None  # Tool arguments for tool messages

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageDTO":
        """Convert domain entity to DTO."""
        # Handle both enum and string role
        role_value = (
            entity.role.value if isinstance(entity.role, MessageRole) else entity.role
        )

        # Extract tool_name and tool_args from metadata (for frontend compatibility)
        tool_name = entity.metadata.get("tool_name") if entity.metadata else None
        tool_args = entity.metadata.get("tool_args") if entity.metadata else None

        return cls(
            id=entity.id,
            instance_id=entity.session_id,  # Map session_id to instance_id for frontend
            role=role_value,
            content=entity.content,
            metadata=entity.metadata,
            timestamp=entity.created_at,
            agent_id=entity.agent_id,
            agent_name=entity.agent_name,
            from_instance_id=entity.from_instance_id,
            response_id=entity.response_id,
            tool_name=tool_name,
            tool_args=tool_args,
        )
