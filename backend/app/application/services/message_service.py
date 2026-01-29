"""Message service - application layer use cases."""

from typing import List, Optional
from uuid import UUID

from app.application.dtos.base import PaginatedResult
from app.application.dtos.message_dto import MessageDTO
from app.application.services.exceptions import (
    MessageNotFoundError,
)
from app.domain.entities import Message
from app.domain.repositories import MessageRepository, SessionRepository


class MessageService:
    """
    Message service - manage conversation messages.

    Responsibilities:
    - Retrieve messages for a session
    - Save individual messages
    - Batch save messages
    - Enforce business rules
    """

    def __init__(
        self,
        message_repo: MessageRepository,
        session_repo: SessionRepository,
    ):
        """Initialize service with repositories."""
        self._message_repo = message_repo
        self._session_repo = session_repo

    async def get_messages(
        self, session_id: UUID, limit: int = 50, cursor: Optional[str] = None
    ) -> PaginatedResult[MessageDTO]:
        """
        Get messages for a session with cursor-based pagination.

        Args:
            session_id: Session UUID
            limit: Maximum number of messages to return (default: 50)
            cursor: Optional cursor for pagination (ISO timestamp)

        Returns:
            PaginatedResult containing message DTOs and pagination metadata

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Validate session exists
        await self._session_repo.get_or_raise(session_id, "Session")

        # Fetch one extra message to determine if there are more
        fetch_limit = limit + 1
        messages = await self._message_repo.get_by_session_ordered(
            session_id, limit=fetch_limit, cursor=cursor
        )

        # Determine if there are more messages
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        # Calculate next cursor (oldest message's created_at in the current page)
        next_cursor = None
        if has_more and messages:
            # Cursor points to the oldest message in the current batch
            next_cursor = messages[0].created_at.isoformat()

        # Convert to DTOs
        message_dtos = [MessageDTO.from_entity(m) for m in messages]

        # Get total count
        total_count = await self._message_repo.get_count_by_session(session_id)

        return PaginatedResult(
            items=message_dtos,
            next_cursor=next_cursor,
            has_more=has_more,
            total_count=total_count,
        )

    async def get_message(self, message_id: UUID) -> MessageDTO:
        """
        Get message by ID.

        Args:
            message_id: Message UUID

        Returns:
            Message DTO

        Raises:
            MessageNotFoundError: If message doesn't exist
        """
        message = await self._message_repo.get_or_raise(message_id, "Message")

        return MessageDTO.from_entity(message)

    async def save_message(self, message: Message) -> MessageDTO:
        """
        Save a single message.

        Args:
            message: Message domain entity

        Returns:
            Saved message DTO

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        # Validate session exists
        await self._session_repo.get_or_raise(message.session_id, "Session")

        # Save message
        created = await self._message_repo.create(message)
        return MessageDTO.from_entity(created)

    async def save_batch(self, messages: List[Message]) -> List[MessageDTO]:
        """
        Batch save multiple messages.

        Args:
            messages: List of message domain entities

        Returns:
            List of saved message DTOs

        Raises:
            SessionNotFoundError: If any session doesn't exist
        """
        if not messages:
            return []

        # Validate all sessions exist (unique session IDs)
        session_ids = set(m.session_id for m in messages)
        for session_id in session_ids:
            await self._session_repo.get_or_raise(session_id, "Session")

        # Batch save
        created = await self._message_repo.create_batch(messages)
        return [MessageDTO.from_entity(m) for m in created]

    async def delete_message(self, message_id: UUID) -> None:
        """
        Soft-delete a message.

        Args:
            message_id: Message UUID

        Raises:
            MessageNotFoundError: If message doesn't exist
        """
        exists = await self._message_repo.exists(message_id)
        if not exists:
            raise MessageNotFoundError(f"Message {message_id} not found")

        await self._message_repo.delete(message_id)
