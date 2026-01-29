"""Batch message processing and formatting."""

from typing import List
from uuid import UUID
from collections import defaultdict

from app.core.logging import get_logger
from app.infrastructure.claude.types import QueuedMessage
from app.domain.entities import Message as MessageEntity
from app.infrastructure.claude.message_persistence import MessagePersistence
from app.infrastructure.database.repositories import MessageRepositoryImpl

logger = get_logger(__name__)


class BatchMessageProcessor:
    """
    Handles grouping, merging, and formatting of batched messages.

    Responsibilities:
    - Group messages by sender
    - Merge messages from same sender
    - Format messages for Claude with sender attribution
    - Save merged messages to database
    """

    def __init__(self, message_persistence: MessagePersistence):
        """Initialize with message persistence component."""
        self._message_persistence = message_persistence

    async def group_and_merge_messages(
        self,
        session_id: UUID,
        batch_messages: List[QueuedMessage],
        message_service,
        db_session,
    ) -> List[MessageEntity]:
        """
        Group messages by sender and merge them.

        Args:
            session_id: Session UUID
            batch_messages: List of queued messages to process
            message_service: Message service for database operations
            db_session: Database session

        Returns:
            List of merged message entities
        """
        from app.infrastructure.sse.manager import sse_manager
        from app.infrastructure.claude.events import UserMessageEvent

        # Group by sender
        grouped_messages = defaultdict(list)
        for queued_msg in batch_messages:
            sender_key = (
                str(queued_msg.sender_session_id)
                if queued_msg.sender_session_id
                else "user"
            )
            grouped_messages[sender_key].append(queued_msg)

        logger.info(
            "grouped_messages_by_sender",
            extra={
                "total_messages": len(batch_messages),
                "unique_senders": len(grouped_messages),
                "session_id": str(session_id),
            },
        )

        # Merge and save
        message_repo = MessageRepositoryImpl(db_session)
        incoming_messages = []

        for sender_key, msgs in grouped_messages.items():
            merged_content = (
                "\n\n".join([msg.message for msg in msgs])
                if len(msgs) > 1
                else msgs[0].message
            )
            first_msg = msgs[0]

            # Save user message using MessagePersistence
            message_entity = await self._message_persistence.save_user_message(
                message_service=message_service,
                message_repo=message_repo,
                db_session=db_session,
                session_id=session_id,
                content=merged_content,
                agent_id=first_msg.sender_agent_id,
                agent_name=first_msg.sender_name,
                from_instance_id=first_msg.sender_session_id,
                location="queue_processor_merged",
                merged_count=len(msgs),
            )
            incoming_messages.append(message_entity)

        logger.info(
            "merged_messages_saved",
            extra={
                "original_count": len(batch_messages),
                "merged_count": len(incoming_messages),
                "session_id": str(session_id),
            },
        )

        # Broadcast user message events
        for msg in incoming_messages:
            user_msg_event = UserMessageEvent(
                session_id=str(session_id),
                message_id=str(msg.id),
                content=msg.content,
                agent_id=msg.agent_id,
                agent_name=msg.agent_name,
                from_instance_id=(
                    str(msg.from_instance_id) if msg.from_instance_id else None
                ),
                timestamp=msg.created_at.isoformat() if msg.created_at else None,
            )
            await sse_manager.broadcast(session_id, user_msg_event.to_sse())

        return incoming_messages

    def format_batch_for_claude(self, incoming_messages: List[MessageEntity]) -> str:
        """
        Format merged messages with sender attribution for Claude.

        Args:
            incoming_messages: List of message entities

        Returns:
            Formatted message content for Claude
        """
        if len(incoming_messages) == 1:
            msg = incoming_messages[0]
            formatted_message = msg.content

            if msg.agent_name or msg.from_instance_id:
                sender_parts = []
                if msg.agent_name:
                    sender_parts.append(msg.agent_name)
                if msg.from_instance_id:
                    sender_parts.append(f"instance: {msg.from_instance_id}")
                sender_info = ", ".join(sender_parts)
                formatted_message = f"**Message from {sender_info}:**\n\n{msg.content}"

                if msg.from_instance_id:
                    formatted_message += (
                        f"\n\nNote: This message is from another instance. "
                        f"They won't see your response in this session - "
                        f'use contact_instance(instance_id="{msg.from_instance_id}") '
                        f"if you need to reply to them. Your session is your workspace."
                    )
        else:
            parts = [
                f"You have received messages from {len(incoming_messages)} different senders while you were processing. Here they are:\n"
            ]
            for msg in incoming_messages:
                sender_label = msg.agent_name or "User"
                if msg.from_instance_id:
                    sender_label += f", from instance: {msg.from_instance_id}"
                parts.append(f"\n**From {sender_label}:**\n{msg.content}\n")

            parts.append(
                "\n\nNote: These messages are from other instances. "
                "They won't see your responses in this session - "
                "use contact_instance or contact_pm to reply to them. "
                "Your session is your workspace."
            )
            formatted_message = "".join(parts)

        return formatted_message

    @staticmethod
    def format_message_for_claude(queued_msg: QueuedMessage) -> str:
        """
        Format single message with sender attribution for Claude.

        Args:
            queued_msg: Queued message to format

        Returns:
            Formatted message content
        """
        formatted_content = queued_msg.message
        if queued_msg.sender_session_id:
            sender_label = queued_msg.sender_name or "User"
            formatted_content = (
                f"**Message from {sender_label} (instance: {queued_msg.sender_session_id}):**\n\n"
                f"{queued_msg.message}\n\n"
                f"Note: This message is from another instance. They won't see your response in this session - "
                f'use contact_instance(instance_id="{queued_msg.sender_session_id}") '
                f"if you need to reply to them. Your session is your workspace."
            )
        return formatted_content
