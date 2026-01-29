"""Streaming input handler for concurrent message injection."""

import asyncio
from typing import AsyncIterator
from uuid import UUID

from app.core.logging import get_logger
from app.infrastructure.claude.types import StopStreamingSignal
from app.infrastructure.claude.message_persistence import MessagePersistence
from app.infrastructure.claude.batch_message_processor import BatchMessageProcessor
from app.infrastructure.database.repositories import MessageRepositoryImpl

logger = get_logger(__name__)


class StreamingInputHandler:
    """
    Handles streaming input for concurrent message injection during execution.

    This component creates an async generator that yields messages from the queue
    to Claude while execution is running, allowing mid-execution message injection.
    """

    def __init__(self, message_persistence: MessagePersistence, queue_getter):
        """
        Initialize streaming input handler.

        Args:
            message_persistence: Message persistence component
            queue_getter: Callable that returns the queue for a session
        """
        self._message_persistence = message_persistence
        self._get_queue = queue_getter

    async def create_message_stream(
        self, session_id: UUID, initial_message: str, db_session, message_service
    ) -> AsyncIterator[dict]:
        """
        Create async generator that streams messages from queue to Claude.

        This generator runs concurrently with Claude's execution, allowing
        messages to be injected mid-execution.

        LIFECYCLE:
        1. Yields initial message immediately
        2. Waits for new messages from queue (300s timeout)
        3. Saves each message to DB and broadcasts via SSE
        4. Yields message to Claude
        5. Exits when StopStreamingSignal received

        Args:
            session_id: Session UUID
            initial_message: Initial message to send
            db_session: Database session
            message_service: Message service for persistence

        Yields:
            Message dictionaries in Claude SDK format
        """
        from app.infrastructure.sse.manager import sse_manager
        from app.infrastructure.claude.events import UserMessageEvent, QueueStatusEvent

        # Yield initial message
        logger.info("streaming_initial_message", session_id=str(session_id))
        yield {
            "type": "user",
            "message": {"role": "user", "content": initial_message},
            "parent_tool_use_id": None,
        }

        # Stream additional messages from queue
        queue = self._get_queue(session_id)
        if not queue:
            logger.warning(
                "no_queue_for_streaming",
                extra={"session_id": str(session_id)},
            )
            return

        while True:
            try:
                logger.info(
                    "stream_waiting_for_next_message",
                    session_id=str(session_id),
                    queue_size_before_wait=queue.qsize(),
                )
                queued_msg = await asyncio.wait_for(queue.get(), timeout=300.0)
                logger.info(
                    "stream_received_message_from_queue",
                    session_id=str(session_id),
                    queue_size_after_get=queue.qsize(),
                )

                # Check for stop signal
                if isinstance(queued_msg, StopStreamingSignal):
                    logger.info(
                        "stream_stop_signal_received",
                        session_id=str(session_id),
                        queue_size=queue.qsize(),
                    )
                    break

                # Save message to database
                message_repo = MessageRepositoryImpl(db_session)
                message_entity = await self._message_persistence.save_user_message(
                    message_service=message_service,
                    message_repo=message_repo,
                    db_session=db_session,
                    session_id=session_id,
                    content=queued_msg.message,
                    agent_id=queued_msg.sender_agent_id,
                    agent_name=queued_msg.sender_name,
                    from_instance_id=queued_msg.sender_session_id,
                    location="streaming_input",
                )

                logger.info(
                    "streaming_message_saved_to_db",
                    session_id=str(session_id),
                    message_id=str(message_entity.id),
                    from_instance=(
                        str(queued_msg.sender_session_id)
                        if queued_msg.sender_session_id
                        else None
                    ),
                    queue_size_after_dequeue=queue.qsize(),
                )

                # Broadcast user message event
                user_msg_event = UserMessageEvent(
                    session_id=str(session_id),
                    message_id=str(message_entity.id),
                    content=queued_msg.message,
                    agent_id=queued_msg.sender_agent_id,
                    agent_name=queued_msg.sender_name,
                    from_instance_id=(
                        str(queued_msg.sender_session_id)
                        if queued_msg.sender_session_id
                        else None
                    ),
                    timestamp=(
                        message_entity.created_at.isoformat()
                        if message_entity.created_at
                        else None
                    ),
                )
                await sse_manager.broadcast(session_id, user_msg_event.to_sse())

                # Format and yield message
                formatted_content = BatchMessageProcessor.format_message_for_claude(
                    queued_msg
                )
                logger.info(
                    "streaming_additional_message_to_claude",
                    session_id=str(session_id),
                    message_id=str(message_entity.id),
                    queue_size_before_yield=queue.qsize(),
                )
                yield {
                    "type": "user",
                    "message": {"role": "user", "content": formatted_content},
                    "parent_tool_use_id": None,
                }

                # Broadcast queue status
                await sse_manager.broadcast(
                    session_id,
                    QueueStatusEvent(
                        session_id=str(session_id), messages=None
                    ).to_sse(),
                )
                queue.task_done()

            except asyncio.TimeoutError:
                logger.info(
                    "stream_timeout_after_5min", extra={"session_id": str(session_id)}
                )
                break
            except Exception as e:
                logger.error(
                    "streaming_message_error",
                    extra={
                        "session_id": str(session_id),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                continue
