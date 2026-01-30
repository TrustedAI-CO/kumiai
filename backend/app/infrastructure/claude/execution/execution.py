"""
Simple execution handler for Claude sessions.

One Execution = One session lifecycle (start → process messages → end cleanly).
"""

import asyncio
from typing import AsyncIterator
from uuid import UUID

from app.core.logging import get_logger
from app.infrastructure.claude.types import QueuedMessage
from app.infrastructure.claude.streaming.converter import convert_message_to_events
from app.infrastructure.claude.streaming.events import MessageCompleteEvent

logger = get_logger(__name__)


class Execution:
    """
    Handles one execution lifecycle for a session.

    Simple flow:
    1. Stream messages from queue to Claude
    2. Receive and broadcast responses
    3. End when queue empty + Claude completes
    """

    def __init__(
        self,
        session_id: UUID,
        client,
        queue: asyncio.Queue,
        message_service,
        db_session,
        session_entity,  # Session entity for agent info
        db_lock: asyncio.Lock,  # Lock for database operations
        on_queue_change=None,  # Callback to broadcast queue status
    ):
        self.session_id = session_id
        self.client = client
        self.queue = queue
        self.message_service = message_service
        self.db_session = db_session
        self.session_entity = session_entity
        self.db_lock = db_lock  # Prevent concurrent db operations
        self.completion_event = asyncio.Event()
        self.on_queue_change = on_queue_change  # Callback for queue updates
        self.is_processing = False  # True when Claude is actively processing

    async def run(self) -> AsyncIterator:
        """
        Run execution and yield events.

        Returns async generator of SSE events.
        """
        # Start query with streaming input
        query_task = asyncio.create_task(self.client.query(self._message_generator()))

        try:
            # Process responses and yield events
            async for event in self._process_responses():
                yield event
        finally:
            # Signal completion and cleanup
            self.completion_event.set()
            await query_task

    async def _message_generator(self) -> AsyncIterator[dict]:
        """
        Stream messages from queue to Claude.

        Keeps running until completion_event is set.
        """
        # Get and send first message
        first_msg = await self.queue.get()
        logger.info(
            "streaming_initial_message",
            session_id=str(self.session_id),
            message_preview=first_msg.message[:50],
        )

        # Save and broadcast user message
        await self._save_and_broadcast_user_message(first_msg)

        # Note: is_processing is set by UserPromptSubmit hook (no manual setting needed)

        yield self._format_message(first_msg)
        self.queue.task_done()

        # Broadcast updated queue status after consuming message
        if self.on_queue_change:
            await self.on_queue_change()

        # Stream subsequent messages as they arrive
        while True:
            # Race between queue.get() and completion_event
            # This allows messages to be sent immediately when they arrive
            queue_task = asyncio.create_task(self.queue.get())
            event_task = asyncio.create_task(self.completion_event.wait())

            done, pending = await asyncio.wait(
                {queue_task, event_task}, return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Exit if completion signaled
            if event_task in done:
                logger.info("message_stream_ended", session_id=str(self.session_id))
                break

            # Got a message - send it immediately
            msg = await queue_task
            logger.info(
                "streaming_queued_message",
                session_id=str(self.session_id),
                queue_size=self.queue.qsize(),
            )

            # Save and broadcast user message
            await self._save_and_broadcast_user_message(msg)

            # Note: is_processing is set by UserPromptSubmit hook (no manual setting needed)

            yield self._format_message(msg)
            self.queue.task_done()

            # Broadcast updated queue status after consuming message
            if self.on_queue_change:
                await self.on_queue_change()

    async def _process_responses(self) -> AsyncIterator:
        """
        Receive responses from Claude and yield as events.

        Exits when queue empty + MessageCompleteEvent received.
        """
        from app.infrastructure.claude.streaming.text_buffer import TextBufferManager
        from app.infrastructure.claude.streaming.events import (
            ContentBlockStopEvent,
            MessageStartEvent,
            StreamDeltaEvent,
        )
        from uuid import uuid4

        buffer_manager = TextBufferManager()
        response_id = str(uuid4())

        # Get agent info for events
        agent_id = self.session_entity.agent_id
        agent_name = agent_id.replace("-", " ").title() if agent_id else None

        # Track if we've saved claude_session_id yet
        claude_session_id_saved = False

        async for message in self.client.receive_messages():
            # Save claude_session_id as soon as it's captured (first message)
            if not claude_session_id_saved:
                captured_id = self.client.get_session_id()
                if captured_id:
                    await self._save_claude_session_id_immediately(captured_id)
                    claude_session_id_saved = True
            events = convert_message_to_events(
                message, str(self.session_id), response_id, agent_id, agent_name
            )

            for event in events:
                # Skip message start markers
                if isinstance(event, MessageStartEvent):
                    continue

                # Buffer text deltas
                if isinstance(event, StreamDeltaEvent):
                    buffer_manager.buffer_delta(event)
                    continue

                # Flush buffer on content block stop
                if isinstance(event, ContentBlockStopEvent):
                    flushed = buffer_manager.flush_buffer(
                        event.content_index,
                        self.session_id,
                        agent_id,
                        agent_name,
                        response_id,
                    )
                    if flushed:
                        yield flushed
                    continue

                # Flush all on completion
                if isinstance(event, MessageCompleteEvent):
                    for flushed in buffer_manager.flush_all_buffers(
                        self.session_id, agent_id, agent_name, response_id
                    ):
                        yield flushed

                    # Note: is_processing is cleared by Stop hook (no manual clearing needed)
                    # Just set has_more_messages based on current state
                    if isinstance(event, MessageCompleteEvent):
                        queue_size = self.queue.qsize()

                        # Set has_more based on is_processing OR queue
                        # is_processing is managed by hooks (UserPromptSubmit/Stop)
                        event.has_more_messages = self.is_processing or queue_size > 0

                        logger.info(
                            "message_complete_from_claude",
                            session_id=str(self.session_id),
                            is_processing=self.is_processing,
                            queue_size=queue_size,
                            has_more=event.has_more_messages,
                        )

                # Yield event
                yield event

                # Log continuation info
                if isinstance(event, MessageCompleteEvent):
                    queue_size = self.queue.qsize()
                    logger.info(
                        "message_complete",
                        session_id=str(self.session_id),
                        queue_size=queue_size,
                        has_more_messages=event.has_more_messages,
                    )
                    # Don't return - keep processing until Claude closes connection

        # Safety: Flush any remaining buffers
        for flushed in buffer_manager.flush_all_buffers(
            self.session_id, agent_id, agent_name, response_id
        ):
            yield flushed

    def _format_message(self, queued_msg: QueuedMessage) -> dict:
        """Format queued message for Claude."""
        from app.infrastructure.claude.batch_message_processor import (
            BatchMessageProcessor,
        )

        content = BatchMessageProcessor.format_message_for_claude(queued_msg)
        return {
            "type": "user",
            "message": {"role": "user", "content": content},
            "parent_tool_use_id": None,
        }

    async def _save_claude_session_id_immediately(self, claude_session_id: str) -> None:
        """
        Save claude_session_id to database immediately when captured.

        This ensures we can resume sessions even if the execution doesn't complete
        normally (e.g., interrupted, server restart, etc.).
        """
        try:
            from app.infrastructure.database.connection import get_repository_session
            from app.infrastructure.database.repositories import SessionRepositoryImpl

            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(self.session_id)

                if session_entity:
                    session_entity.claude_session_id = claude_session_id
                    await session_repo.update(session_entity)
                    await db.commit()

                    logger.info(
                        "claude_session_id_saved_immediately",
                        session_id=str(self.session_id),
                        claude_session_id=claude_session_id,
                    )
                else:
                    logger.warning(
                        "session_not_found_for_claude_id_save",
                        session_id=str(self.session_id),
                    )
        except Exception as e:
            logger.error(
                "failed_to_save_claude_session_id_immediately",
                session_id=str(self.session_id),
                claude_session_id=claude_session_id,
                error=str(e),
            )

    async def _save_and_broadcast_user_message(self, queued_msg: QueuedMessage) -> None:
        """Save user message to database and broadcast via SSE."""
        from app.infrastructure.database.repositories import MessageRepositoryImpl
        from app.infrastructure.claude.streaming.persistence import MessagePersistence
        from app.infrastructure.claude.streaming.events import UserMessageEvent
        from app.infrastructure.sse.manager import sse_manager

        # Save to database (with lock to prevent concurrent flushes)
        async with self.db_lock:
            message_repo = MessageRepositoryImpl(self.db_session)
            message_persistence = MessagePersistence()

            message_entity = await message_persistence.save_user_message(
                message_service=self.message_service,
                message_repo=message_repo,
                db_session=self.db_session,
                session_id=self.session_id,
                content=queued_msg.message,
                agent_id=queued_msg.sender_agent_id,
                agent_name=queued_msg.sender_name,
                from_instance_id=queued_msg.sender_session_id,
                location="execution",
            )

            await self.db_session.commit()

            logger.info(
                "user_message_saved_to_db",
                session_id=str(self.session_id),
                message_id=str(message_entity.id),
            )

        # Broadcast via SSE
        user_msg_event = UserMessageEvent(
            session_id=str(self.session_id),
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
        await sse_manager.broadcast(self.session_id, user_msg_event.to_sse())
