"""Message persistence for saving messages to database with sequence management."""

from typing import Optional
from uuid import UUID, uuid4

from app.core.logging import get_logger
from app.domain.entities import Message as MessageEntity
from app.domain.value_objects import MessageRole

logger = get_logger(__name__)


class MessagePersistence:
    """
    Handles saving messages to database with automatic sequence management.

    Centralizes all message persistence logic to eliminate duplication and
    ensure consistent sequence number handling.
    """

    async def save_user_message(
        self,
        message_service,
        message_repo,
        db_session,
        session_id: UUID,
        content: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        from_instance_id: Optional[UUID] = None,
        location: str = "unknown",
        merged_count: int = 1,
    ) -> MessageEntity:
        """
        Save a user message to database with next sequence number.

        Args:
            message_service: Message service
            message_repo: Message repository
            db_session: Database session
            session_id: Session UUID
            content: Message content
            agent_id: Optional agent ID
            agent_name: Optional agent name
            from_instance_id: Optional source instance ID
            location: Where the message was saved from (for logging)
            merged_count: Number of messages merged (for logging)

        Returns:
            Created message entity
        """
        # Get next sequence number atomically
        next_sequence = await message_repo.get_next_sequence(session_id)

        # Create message entity
        message_entity = MessageEntity(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.USER,
            content=content,
            sequence=next_sequence,
            agent_id=agent_id,
            agent_name=agent_name,
            from_instance_id=from_instance_id,
        )

        # Save to database
        await message_service.save_message(message_entity)
        await db_session.commit()

        # Log
        logger.info(
            "USER_MESSAGE_SAVED",
            session_id=str(session_id),
            message_id=str(message_entity.id),
            sequence=next_sequence,
            content_preview=content[:50],
            location=location,
            merged_count=merged_count if merged_count > 1 else None,
        )

        return message_entity

    async def save_assistant_message(
        self,
        message_service,
        message_repo,
        db_session,
        session_id: UUID,
        content: str,
        agent_id: Optional[str],
        agent_name: Optional[str],
        response_id: str,
    ) -> MessageEntity:
        """
        Save an assistant message to database.

        Args:
            message_service: Message service
            message_repo: Message repository
            db_session: Database session
            session_id: Session UUID
            content: Message content
            agent_id: Agent ID
            agent_name: Agent name
            response_id: Response ID for correlation

        Returns:
            Created message entity
        """
        # Get next sequence number atomically
        next_sequence = await message_repo.get_next_sequence(session_id)

        # Create message entity
        assistant_message = MessageEntity(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            sequence=next_sequence,
            agent_id=agent_id,
            agent_name=agent_name,
            from_instance_id=None,
            response_id=response_id,
        )

        # Save to database
        await message_service.save_message(assistant_message)
        await db_session.commit()

        # Log
        logger.info(
            "ASSISTANT_MESSAGE_SAVED",
            session_id=str(session_id),
            message_id=str(assistant_message.id),
            sequence=next_sequence,
            content_preview=content[:50],
            response_id=response_id,
        )

        return assistant_message

    async def save_tool_message(
        self,
        message_service,
        message_repo,
        db_session,
        session_id: UUID,
        agent_id: Optional[str],
        agent_name: Optional[str],
        response_id: str,
        tool_name: str,
        tool_args: dict,
    ) -> MessageEntity:
        """
        Save a tool call message to database.

        Args:
            message_service: Message service
            message_repo: Message repository
            db_session: Database session
            session_id: Session UUID
            agent_id: Agent ID
            agent_name: Agent name
            response_id: Response ID for correlation
            tool_name: Name of the tool being called
            tool_args: Tool arguments

        Returns:
            Created message entity
        """
        logger.info(
            "tool_use_event_detected_saving_to_db",
            extra={
                "session_id": str(session_id),
                "tool_name": tool_name,
            },
        )

        # Get next sequence number atomically
        next_sequence = await message_repo.get_next_sequence(session_id)

        # Create message entity
        tool_message = MessageEntity(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.TOOL_CALL,
            content="",
            sequence=next_sequence,
            agent_id=agent_id,
            agent_name=agent_name,
            from_instance_id=None,
            response_id=response_id,
            metadata={"tool_name": tool_name, "tool_args": tool_args},
        )

        # Save to database
        await message_service.save_message(tool_message)
        await db_session.commit()

        # Log
        logger.info(
            "TOOL_MESSAGE_SAVED",
            session_id=str(session_id),
            message_id=str(tool_message.id),
            sequence=next_sequence,
            tool_name=tool_name,
            response_id=response_id,
        )

        logger.info(
            "tool_message_saved_to_db_successfully",
            extra={
                "session_id": str(session_id),
                "tool_name": tool_name,
                "message_id": str(tool_message.id),
            },
        )

        return tool_message
