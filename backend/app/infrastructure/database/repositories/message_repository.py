"""SQLAlchemy implementation of MessageRepository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError, EntityNotFound
from app.domain.entities import Message as MessageEntity
from app.domain.repositories import MessageRepository
from app.infrastructure.database.mappers import MessageMapper
from app.infrastructure.database.models import Message
from app.infrastructure.database.repositories.base_repository import BaseRepositoryImpl


class MessageRepositoryImpl(BaseRepositoryImpl[MessageEntity], MessageRepository):
    """
    SQLAlchemy implementation of MessageRepository.

    Adapts domain Message entities to Message model persistence.
    Inherits common functionality from BaseRepositoryImpl.
    Note: Messages do not support soft delete (no deleted_at field).
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session)
        self._mapper = MessageMapper()

    async def create(self, message: MessageEntity) -> MessageEntity:
        """Create and persist a new message."""
        try:
            model = self._mapper.to_model(message)
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to create message: {e}") from e

    async def create_batch(self, messages: List[MessageEntity]) -> List[MessageEntity]:
        """Create and persist multiple messages in a batch."""
        try:
            models = [self._mapper.to_model(msg) for msg in messages]
            self._session.add_all(models)
            await self._session.flush()

            # Refresh all models to get database-generated fields
            for model in models:
                await self._session.refresh(model)

            return [self._mapper.to_entity(model) for model in models]
        except Exception as e:
            raise DatabaseError(f"Failed to batch create messages: {e}") from e

    async def get_by_id(self, message_id: UUID) -> Optional[MessageEntity]:
        """Retrieve message by ID."""
        try:
            stmt = select(Message).where(Message.id == message_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._mapper.to_entity(model)
        except Exception as e:
            raise DatabaseError(f"Failed to get message {message_id}: {e}") from e

    async def get_by_session_id(
        self, session_id: UUID, include_deleted: bool = False
    ) -> List[MessageEntity]:
        """Get all messages for a session."""
        try:
            # Note: Messages don't have deleted_at field, so include_deleted is ignored
            stmt = select(Message).where(Message.session_id == session_id)
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [self._mapper.to_entity(model) for model in models]
        except Exception as e:
            raise DatabaseError(
                f"Failed to get messages for session {session_id}: {e}"
            ) from e

    async def get_by_session_ordered(
        self,
        session_id: UUID,
        include_deleted: bool = False,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> List[MessageEntity]:
        """
        Get messages for a session, ordered by sequence number with cursor-based pagination.

        Messages are ordered by sequence (primary) and created_at (secondary) to handle
        race conditions where multiple messages might temporarily have the same sequence.
        """
        try:
            # Note: Messages don't have deleted_at field, so include_deleted is ignored
            stmt = select(Message).where(Message.session_id == session_id)

            # Apply cursor filter if provided (using created_at for backward compatibility)
            if cursor:
                try:
                    cursor_timestamp = datetime.fromisoformat(
                        cursor.replace("Z", "+00:00")
                    )
                    stmt = stmt.where(Message.created_at < cursor_timestamp)
                except (ValueError, AttributeError) as e:
                    raise DatabaseError(f"Invalid cursor format: {cursor}") from e

            # Order by sequence DESC (most recent first), then created_at DESC, then reverse
            stmt = stmt.order_by(
                Message.sequence.desc(), Message.created_at.desc()
            ).limit(limit)
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            # Reverse to return chronological order (oldest first)
            return [self._mapper.to_entity(model) for model in reversed(models)]
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(
                f"Failed to get ordered messages for session {session_id}: {e}"
            ) from e

    async def get_next_sequence(self, session_id: UUID) -> int:
        """
        Get next sequence number for a session atomically.

        Uses SELECT MAX(sequence) with FOR UPDATE to ensure atomicity
        in concurrent scenarios. This prevents race conditions where
        multiple messages get the same sequence number.

        Args:
            session_id: Session UUID

        Returns:
            Next sequence number (0 for first message, then 1, 2, 3...)
        """
        try:
            # Get max sequence with row lock to prevent race conditions
            stmt = (
                select(func.max(Message.sequence))
                .where(Message.session_id == session_id)
                .with_for_update()
            )
            result = await self._session.execute(stmt)
            max_seq = result.scalar_one_or_none()

            # Return 0 for first message, otherwise max + 1
            return 0 if max_seq is None else max_seq + 1
        except Exception as e:
            raise DatabaseError(
                f"Failed to get next sequence for session {session_id}: {e}"
            ) from e

    async def update(self, message: MessageEntity) -> MessageEntity:
        """Update existing message."""
        try:
            # Get existing model
            stmt = select(Message).where(Message.id == message.id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise EntityNotFound(f"Message {message.id} not found")

            # Update model from entity
            model = self._mapper.to_model(message, model)
            await self._session.flush()
            await self._session.refresh(model)

            return self._mapper.to_entity(model)
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update message {message.id}: {e}") from e

    async def delete(self, message_id: UUID) -> None:
        """
        Soft-delete a message.

        Note: Messages don't have a deleted_at field in the current schema.
        This implementation performs a hard delete by removing the record.
        """
        try:
            stmt = select(Message).where(Message.id == message_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                raise EntityNotFound(f"Message {message_id} not found")

            # Hard delete since Message model doesn't have deleted_at
            await self._session.delete(model)
            await self._session.flush()
        except EntityNotFound:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to delete message {message_id}: {e}") from e

    async def exists(self, message_id: UUID) -> bool:
        """Check if message exists."""
        try:
            stmt = select(Message.id).where(Message.id == message_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check message existence: {e}") from e

    async def get_count_by_session(self, session_id: UUID) -> int:
        """Get the count of messages in a session."""
        try:
            stmt = select(func.count(Message.id)).where(
                Message.session_id == session_id
            )
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            return count
        except Exception as e:
            raise DatabaseError(
                f"Failed to count messages for session {session_id}: {e}"
            ) from e

    async def delete_by_session_id(self, session_id: UUID) -> int:
        """Delete all messages for a session (hard delete)."""
        try:
            stmt = delete(Message).where(Message.session_id == session_id)
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount
        except Exception as e:
            raise DatabaseError(
                f"Failed to delete messages for session {session_id}: {e}"
            ) from e
