"""Message domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.exceptions import ValidationError
from app.domain.value_objects import MessageRole


@dataclass
class Message:
    """
    Message domain entity.

    A message represents a single turn in a conversation (user query,
    assistant response, system message, or tool result).

    Business rules:
    - Content is required (non-empty)
    - Tool result messages must have tool_use_id
    - Sequence must be non-negative
    - Sequence must be unique within session (enforced by repository)
    """

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    tool_use_id: Optional[str] = None
    sequence: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Sender attribution fields for message rendering
    agent_id: Optional[str] = None  # Source of truth for which agent sent the message
    agent_name: Optional[str] = None  # Display name of the sending agent
    from_instance_id: Optional[UUID] = (
        None  # Session ID where message originated (for cross-session routing)
    )

    # Response grouping for UI
    response_id: Optional[str] = (
        None  # UUID shared by all messages in the same Claude response
    )

    def is_tool_result(self) -> bool:
        """
        Check if this is a tool result message.

        Returns:
            True if message role is TOOL_RESULT, False otherwise
        """
        return self.role == MessageRole.TOOL_RESULT

    def is_user_message(self) -> bool:
        """
        Check if this is a user message.

        Returns:
            True if message role is USER, False otherwise
        """
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """
        Check if this is an assistant message.

        Returns:
            True if message role is ASSISTANT, False otherwise
        """
        return self.role == MessageRole.ASSISTANT

    def validate(self) -> None:
        """
        Validate message invariants.

        Raises:
            ValidationError: If validation fails
        """
        if not self.content:
            raise ValidationError("Message content cannot be empty")

        if self.role == MessageRole.TOOL_RESULT and not self.tool_use_id:
            raise ValidationError("Tool result messages must have tool_use_id")

        if self.sequence < 0:
            raise ValidationError("Message sequence must be non-negative")
