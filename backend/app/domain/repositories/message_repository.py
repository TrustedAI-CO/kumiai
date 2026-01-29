"""Message repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities import Message


class MessageRepository(ABC):
    """
    Abstract repository interface for Message entities.

    This interface defines the contract for message persistence without
    specifying the implementation details.
    """

    @abstractmethod
    async def create(self, message: Message) -> Message:
        """
        Create and persist a new message.

        Args:
            message: Message entity to create.

        Returns:
            Created message with ID assigned and any database-generated
            fields populated.

        Raises:
            RepositoryError: If creation fails due to database errors.
        """
        pass

    @abstractmethod
    async def create_batch(self, messages: List[Message]) -> List[Message]:
        """
        Create and persist multiple messages in a batch.

        Args:
            messages: List of message entities to create.

        Returns:
            List of created messages with IDs assigned and any
            database-generated fields populated.

        Raises:
            RepositoryError: If batch creation fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Optional[Message]:
        """
        Retrieve message by ID.

        Args:
            message_id: UUID of the message to retrieve.

        Returns:
            Message entity if found, None otherwise.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_by_session_id(
        self, session_id: UUID, include_deleted: bool = False
    ) -> List[Message]:
        """
        Get all messages for a session.

        Args:
            session_id: UUID of the session.
            include_deleted: Whether to include soft-deleted messages.
                           Defaults to False.

        Returns:
            List of messages for the session (may be empty).
            Messages are not guaranteed to be in any particular order.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_by_session_ordered(
        self,
        session_id: UUID,
        include_deleted: bool = False,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> List[Message]:
        """
        Get messages for a session, ordered by created_at timestamp.

        This is the primary method for retrieving conversation history
        in the correct chronological order with cursor-based pagination support.

        Args:
            session_id: UUID of the session.
            include_deleted: Whether to include soft-deleted messages.
                           Defaults to False.
            limit: Maximum number of messages to return. Defaults to 50.
            cursor: Optional cursor for pagination (ISO timestamp of last message).
                   If provided, returns messages created before this timestamp.

        Returns:
            List of messages for the session, ordered by created_at timestamp
            (ascending). May be empty.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def update(self, message: Message) -> Message:
        """
        Update existing message.

        Args:
            message: Message entity with updated values. Must have a valid ID.

        Returns:
            Updated message with any database-generated fields refreshed.

        Raises:
            NotFoundError: If message with given ID doesn't exist.
            RepositoryError: If update fails due to database errors.
        """
        pass

    @abstractmethod
    async def delete(self, message_id: UUID) -> None:
        """
        Soft-delete a message.

        Sets the deleted_at timestamp without removing the record from
        the database.

        Args:
            message_id: UUID of message to delete.

        Raises:
            NotFoundError: If message with given ID doesn't exist.
            RepositoryError: If deletion fails due to database errors.
        """
        pass

    @abstractmethod
    async def exists(self, message_id: UUID) -> bool:
        """
        Check if message exists (including soft-deleted messages).

        Args:
            message_id: UUID of message to check.

        Returns:
            True if message exists (even if soft-deleted), False otherwise.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def get_count_by_session(self, session_id: UUID) -> int:
        """
        Get the count of messages in a session (excluding deleted).

        Args:
            session_id: UUID of the session.

        Returns:
            Number of messages in the session.

        Raises:
            RepositoryError: If query fails due to database errors.
        """
        pass

    @abstractmethod
    async def delete_by_session_id(self, session_id: UUID) -> int:
        """
        Delete all messages for a session (hard delete).

        Used when recreating/resetting a session to start fresh.

        Args:
            session_id: UUID of the session.

        Returns:
            Number of messages deleted.

        Raises:
            RepositoryError: If deletion fails due to database errors.
        """
        pass
