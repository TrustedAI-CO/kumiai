"""
Session executor for streaming Claude responses.

This module provides the SessionExecutor class which manages the execution
of Claude AI sessions with support for:
- Streaming responses with real-time message injection
- Message queuing and batching
- Session state management
- Database persistence and SSE broadcasting

HIGH-LEVEL FLOW:
1. execute() - Main entry point for executing user messages
2. enqueue() - Queue messages for background processing
3. _process_queue() - Background task that processes queued messages

The executor handles lazy client creation, concurrent message streaming,
and automatic session status management.
"""

from pathlib import Path
from typing import AsyncIterator, Dict, Optional, List
from uuid import UUID, uuid4
import asyncio

from app.core.logging import get_logger
from app.infrastructure.claude.client_manager import ClaudeClientManager
from app.infrastructure.claude.exceptions import (
    ClaudeExecutionError,
    ClientNotFoundError,
)
from app.infrastructure.claude.message_converter import convert_message_to_events
from app.infrastructure.claude.events import (
    SSEEvent,
    ContentBlockStopEvent,
    MessageStartEvent,
    StreamDeltaEvent,
    MessageCompleteEvent,
)
from app.infrastructure.claude.types import QueuedMessage, StopStreamingSignal
from app.infrastructure.claude.text_buffer_manager import TextBufferManager
from app.infrastructure.claude.message_persistence import MessagePersistence
from app.infrastructure.claude.session_status_manager import SessionStatusManager
from app.infrastructure.claude.queue_processor import MessageQueueProcessor
from app.infrastructure.claude.response_streamer import ClaudeResponseStreamer
from app.infrastructure.claude.batch_message_processor import BatchMessageProcessor
from app.infrastructure.claude.streaming_input_handler import StreamingInputHandler
from app.infrastructure.mcp.servers.context import set_tool_context, set_session_info

logger = get_logger(__name__)


# =============================================================================
# SESSION EXECUTOR
# =============================================================================


class SessionExecutor:
    """
    Executes Claude sessions with streaming responses and message queuing.

    Key responsibilities:
    - Execute user messages through Claude AI
    - Stream responses as SSE events
    - Queue and batch messages for background processing
    - Manage session lifecycle and status
    - Handle database persistence and SSE broadcasting
    """

    def __init__(self, client_manager: ClaudeClientManager):
        """Initialize session executor with Claude client manager."""
        self._client_manager = client_manager
        self._session_locks: Dict[UUID, asyncio.Lock] = {}
        self._queue_processors: Dict[UUID, asyncio.Task] = {}

        # Component managers
        self._message_persistence = MessagePersistence()
        self._session_status_manager = SessionStatusManager()
        self._queue_manager = MessageQueueProcessor()
        self._response_streamer = ClaudeResponseStreamer()
        self._batch_processor = BatchMessageProcessor(self._message_persistence)
        self._streaming_input = StreamingInputHandler(
            self._message_persistence, self._queue_manager.get_queue
        )

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def execute(
        self,
        session_id: UUID,
        user_message: str,
        agent_id: str,
        db_session,
        session_service,
        agent_service,
        project_service,
        project_path: str = ".",
        resume_session_id: str | None = None,
        message_service=None,
    ) -> AsyncIterator[SSEEvent]:
        """
        Execute user message and stream SSE events.

        HIGH-LEVEL FLOW:
        1. Setup context and acquire session lock
        2. Get or create Claude client
        3. Send query with streaming input from queue
        4. Stream responses and convert to SSE events
        5. Buffer and flush text content
        6. Cleanup streaming resources

        Args:
            session_id: Session UUID
            user_message: User's message text
            agent_id: Agent ID
            db_session: Database session
            session_service: Session service
            agent_service: Agent service
            project_service: Project service
            project_path: Project root directory
            resume_session_id: Optional Claude session ID to resume
            message_service: Message service for saving streamed messages

        Yields:
            SSE event objects

        Raises:
            ClaudeExecutionError: If execution fails
        """
        session_dir = Path(project_path) / ".sessions" / str(session_id)
        self._log_execution_start(
            session_id, agent_id, user_message, project_path, session_dir
        )

        try:
            # Setup
            lock = self._get_or_create_lock(session_id)
            await self._setup_tool_context(
                session_id, db_session, session_service, agent_service, project_service
            )
            agent_name = await self._get_agent_name(agent_id, agent_service, session_id)

            # Update status to WORKING before execution
            await self._update_session_status_to_working(session_id)

            # Execute with lock
            async with lock:
                client = await self._get_or_create_client(
                    session_id, agent_id, project_path, session_dir, resume_session_id
                )
                query_task = await self._send_query(
                    client,
                    session_id,
                    user_message,
                    message_service,
                    db_session,
                )

            # Stream responses
            async for event in self._stream_responses(
                client, session_id, agent_id, agent_name
            ):
                yield event

            # Cleanup
            await self._cleanup_streaming(session_id, message_service, query_task)

            logger.info(
                "session_execution_completed",
                extra={
                    "session_id": str(session_id),
                    "claude_session_id": client.get_session_id(),
                },
            )

        except Exception as e:
            logger.error(
                "session_execution_failed",
                extra={
                    "session_id": str(session_id),
                    "agent_id": agent_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            # Update status to ERROR on exception
            await self._update_session_status_after_execution(session_id, e)
            raise ClaudeExecutionError(f"Execution failed: {e}") from e

    async def enqueue(
        self,
        session_id: UUID,
        message: str,
        sender_name: Optional[str] = None,
        sender_session_id: Optional[UUID] = None,
        sender_agent_id: Optional[str] = None,
    ) -> None:
        """
        Enqueue a message for execution by the session.

        This is the main entry point for inter-instance messaging.
        Messages are queued and processed sequentially to prevent race conditions.

        Args:
            session_id: Target session UUID
            message: Message content
            sender_name: Optional display name of sender
            sender_session_id: Optional session ID of sender
            sender_agent_id: Optional agent ID of sender
        """
        logger.info(
            "enqueue_message",
            extra={
                "session_id": str(session_id),
                "sender_name": sender_name,
                "message_length": len(message),
            },
        )

        # Initialize queue if needed
        self._ensure_queue_exists(session_id)

        # Enqueue message
        queued_msg = QueuedMessage(
            message, sender_name, sender_session_id, sender_agent_id
        )
        queue = self._queue_manager.get_queue(session_id)
        await queue.put(queued_msg)

        queue_size = queue.qsize()
        logger.info(
            "message_enqueued", session_id=str(session_id), queue_size=queue_size
        )

        # Broadcast queue status
        await self._broadcast_queue_status(session_id)

        # Start processor if not running
        if not self._is_processor_running(session_id):
            self._queue_processors[session_id] = asyncio.create_task(
                self._process_queue(session_id)
            )
            logger.info(
                "started_queue_processor", extra={"session_id": str(session_id)}
            )

    async def get_claude_session_id(self, session_id: UUID) -> str | None:
        """
        Get Claude session ID for a session.

        First tries in-memory client (fast path), then falls back to database.

        Args:
            session_id: Session UUID

        Returns:
            Claude session ID if available, None otherwise
        """
        try:
            client = await self._client_manager.get_client(session_id)
            claude_session_id = client.get_session_id()
            logger.info(
                "got_claude_session_id_from_client",
                extra={
                    "session_id": str(session_id),
                    "claude_session_id": claude_session_id,
                    "source": "in_memory_client",
                },
            )
            return claude_session_id
        except ClientNotFoundError:
            return await self._get_claude_session_id_from_db(session_id)

    async def interrupt(self, session_id: UUID) -> None:
        """
        Interrupt a running session and stop Claude execution.

        STEPS:
        1. Interrupt Claude client
        2. Clear message queue
        3. Cancel queue processor
        4. Reset processing flag

        Args:
            session_id: Session UUID

        Raises:
            ClaudeExecutionError: If interrupt fails
        """
        logger.warning(
            "INTERRUPT_SESSION_STARTED", extra={"session_id": str(session_id)}
        )

        try:
            await self._interrupt_claude_client(session_id)
            await self._clear_message_queue(session_id)
            await self._cancel_queue_processor(session_id)

            self._queue_manager.set_processing(session_id, False)

            # Update status to IDLE after interrupt
            await self._update_session_status_after_execution(session_id, None)

            logger.info(
                "interrupt_session_completed", extra={"session_id": str(session_id)}
            )

        except Exception as e:
            logger.error(
                "interrupt_session_failed",
                extra={"session_id": str(session_id), "error": str(e)},
            )
            raise ClaudeExecutionError(f"Failed to interrupt session: {e}") from e

    def is_processing(self, session_id: UUID) -> bool:
        """Check if a session is currently processing a message."""
        return self._queue_manager.is_processing(session_id)

    def get_queue_size(self, session_id: UUID) -> int:
        """Get the number of queued messages for a session."""
        return self._queue_manager.get_queue_size(session_id)

    # =========================================================================
    # EXECUTION FLOW HELPERS
    # =========================================================================

    def _log_execution_start(
        self,
        session_id: UUID,
        agent_id: str,
        user_message: str,
        project_path: str,
        session_dir: Path,
    ) -> None:
        """Log execution start with context."""
        logger.info(
            "session_execution_started",
            extra={
                "session_id": str(session_id),
                "agent_id": agent_id,
                "message_length": len(user_message),
                "project_path": project_path,
                "session_dir": str(session_dir),
            },
        )

    def _get_or_create_lock(self, session_id: UUID) -> asyncio.Lock:
        """Get or create lock for session."""
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]

    async def _setup_tool_context(
        self,
        session_id: UUID,
        db_session,
        session_service,
        agent_service,
        project_service,
    ) -> None:
        """Setup tool context and session info for MCP tools."""
        set_tool_context(
            db=db_session,
            session_service=session_service,
            agent_service=agent_service,
            project_service=project_service,
        )
        await self._set_session_info_async(session_id)
        logger.debug("tool_context_set", extra={"session_id": str(session_id)})

    async def _set_session_info_async(self, session_id: UUID) -> None:
        """Set session info asynchronously for hooks."""
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        try:
            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)
                if session_entity:
                    set_session_info(
                        source_instance_id=str(session_id),
                        project_id=(
                            str(session_entity.project_id)
                            if session_entity.project_id
                            else None
                        ),
                    )
        except Exception as e:
            logger.warning(
                "failed_to_set_session_info",
                extra={"session_id": str(session_id), "error": str(e)},
            )

    async def _get_agent_name(
        self, agent_id: str, agent_service, session_id: UUID
    ) -> Optional[str]:
        """Get agent name from agent service."""
        if not agent_id:
            return None

        try:
            agent = await agent_service.get_agent(agent_id)
            return agent.name
        except Exception as e:
            logger.warning(
                "failed_to_get_agent_name",
                extra={
                    "session_id": str(session_id),
                    "agent_id": agent_id,
                    "error": str(e),
                },
            )
            return None

    async def _send_query(
        self,
        client,
        session_id: UUID,
        user_message: str,
        message_service,
        db_session,
    ) -> asyncio.Task:
        """
        Send streaming query to Claude.

        Returns query task for cleanup.
        """
        logger.info(
            "sending_streaming_query_to_claude",
            extra={
                "session_id": str(session_id),
                "message_length": len(user_message),
            },
        )
        message_stream = self._streaming_input.create_message_stream(
            session_id, user_message, db_session, message_service
        )
        query_task = asyncio.create_task(client.query(message_stream))
        logger.info(
            "streaming_query_task_started", extra={"session_id": str(session_id)}
        )
        return query_task

    async def _stream_responses(
        self, client, session_id: UUID, agent_id: str, agent_name: Optional[str]
    ) -> AsyncIterator[SSEEvent]:
        """
        Stream responses from Claude and convert to SSE events.

        Handles text buffering per content block and flushes at appropriate times.
        """
        buffer_manager = TextBufferManager()
        response_id = str(uuid4())

        logger.info(
            "waiting_for_claude_response",
            extra={"session_id": str(session_id), "response_id": response_id},
        )

        async for message in client.receive_messages():
            logger.debug(
                "received_message_from_claude",
                extra={
                    "session_id": str(session_id),
                    "message_type": type(message).__name__,
                },
            )

            events = convert_message_to_events(
                message, str(session_id), response_id, agent_id, agent_name
            )

            for event in events:
                # Skip message start markers
                if isinstance(event, MessageStartEvent):
                    continue

                # Buffer text deltas
                if isinstance(event, StreamDeltaEvent):
                    buffer_manager.buffer_delta(event)
                    continue

                # Flush specific buffer when content block stops
                if isinstance(event, ContentBlockStopEvent):
                    flushed_event = buffer_manager.flush_buffer(
                        event.content_index,
                        session_id,
                        agent_id,
                        agent_name,
                        response_id,
                    )
                    if flushed_event:
                        yield flushed_event
                    continue

                # Flush all buffers on completion
                if isinstance(event, MessageCompleteEvent):
                    for flushed_event in buffer_manager.flush_all_buffers(
                        session_id, agent_id, agent_name, response_id
                    ):
                        yield flushed_event

                # Yield non-delta events
                logger.debug(
                    "streaming_event",
                    extra={"session_id": str(session_id), "event_type": event.type},
                )
                yield event

                # Update status to IDLE when MessageCompleteEvent is received
                # (but don't break the streaming loop - keep it running)
                if isinstance(event, MessageCompleteEvent):
                    logger.info(
                        "message_complete_updating_status_to_idle",
                        extra={"session_id": str(session_id)},
                    )
                    # Update status to IDLE in database
                    await self._update_session_status_after_execution(session_id, None)

                # DISABLED: Normal completion via MessageCompleteEvent
                # if isinstance(event, MessageCompleteEvent):
                #     conversation_complete = True

            # DISABLED: Normal completion break
            # if conversation_complete:
            #     break

        # Safety net: flush any remaining buffers
        for flushed_event in buffer_manager.flush_all_buffers(
            session_id, agent_id, agent_name, response_id
        ):
            yield flushed_event

    async def _cleanup_streaming(
        self,
        session_id: UUID,
        message_service,
        query_task: asyncio.Task,
    ) -> None:
        """Cleanup streaming resources (send stop signal and wait for query task)."""
        # Send stop signal
        queue = self._queue_manager.get_queue(session_id)
        if queue:
            try:
                queue_size_before = queue.qsize()
                await queue.put(StopStreamingSignal())
                logger.info(
                    "stop_signal_sent_from_execute",
                    session_id=str(session_id),
                    queue_size_before_stop=queue_size_before,
                    queue_size_after_stop=queue.qsize(),
                )
            except Exception as e:
                logger.warning(
                    "failed_to_send_stop_signal_from_execute",
                    extra={"session_id": str(session_id), "error": str(e)},
                )

        # Wait for query task
        try:
            await query_task
            logger.info(
                "streaming_query_task_completed",
                extra={"session_id": str(session_id)},
            )
        except Exception as e:
            logger.error(
                "streaming_query_task_failed",
                extra={
                    "session_id": str(session_id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

    # =========================================================================
    # QUEUE PROCESSING (Background Task)
    # =========================================================================

    async def _process_queue(self, session_id: UUID) -> None:
        """
        Background task that processes queued messages for a session.

        HIGH-LEVEL FLOW:
        1. Wait for messages with timeout
        2. Collect batch of messages
        3. Group and merge messages by sender
        4. Update session status to WORKING
        5. Execute merged messages
        6. Save responses to database
        7. Update session status to IDLE or ERROR

        Args:
            session_id: Session UUID
        """
        logger.info("queue_processor_started", extra={"session_id": str(session_id)})

        try:
            queue = self._queue_manager.get_queue(session_id)
            if not queue:
                logger.warning("queue_not_found", extra={"session_id": str(session_id)})
                return

            while True:
                # Wait for first message
                first_msg = await self._wait_for_first_message(queue, session_id)
                if first_msg is None:
                    break

                # Collect batch
                batch_messages = await self._collect_message_batch(
                    queue, session_id, first_msg
                )

                # Broadcast queue status
                await self._broadcast_queue_status(session_id)

                # Update session status to WORKING
                await self._update_session_status_to_working(session_id)

                # Execute batch
                self._queue_manager.set_processing(session_id, True)
                execution_error = None

                try:
                    await self._execute_message_batch(session_id, batch_messages)
                except Exception as e:
                    execution_error = e
                    logger.error(
                        "queued_message_execution_failed",
                        extra={
                            "session_id": str(session_id),
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        exc_info=True,
                    )
                finally:
                    logger.info(
                        "queue_processing_complete",
                        session_id=str(session_id),
                        final_queue_size=queue.qsize(),
                        had_error=execution_error is not None,
                    )
                    self._queue_manager.set_processing(session_id, False)
                    for _ in batch_messages:
                        queue.task_done()

                    # Update session status
                    await self._update_session_status_after_execution(
                        session_id, execution_error
                    )

        except Exception as e:
            logger.error(
                "queue_processor_failed",
                extra={"session_id": str(session_id), "error": str(e)},
            )
        finally:
            logger.info(
                "queue_processor_stopped", extra={"session_id": str(session_id)}
            )

    async def _wait_for_first_message(
        self, queue: asyncio.Queue, session_id: UUID
    ) -> Optional[QueuedMessage]:
        """Wait for first message in queue with timeout."""
        return await self._queue_manager.wait_for_first_message(session_id)

    async def _collect_message_batch(
        self, queue: asyncio.Queue, session_id: UUID, first_msg: QueuedMessage
    ) -> List[QueuedMessage]:
        """Collect all messages currently in queue (batching)."""
        batch_messages = [first_msg]

        logger.info(
            "BATCH_COLLECT_START",
            session_id=str(session_id),
            queue_size_before=queue.qsize(),
            first_message_preview=first_msg.message[:50],
        )

        while not queue.empty():
            try:
                msg = queue.get_nowait()
                if not isinstance(msg, StopStreamingSignal):
                    batch_messages.append(msg)
                    logger.debug(
                        "BATCH_COLLECT_MESSAGE",
                        session_id=str(session_id),
                        message_preview=msg.message[:50],
                    )
                else:
                    logger.warning(
                        "stop_signal_found_in_batch",
                        extra={"session_id": str(session_id)},
                    )
                    queue.task_done()
            except asyncio.QueueEmpty:
                break

        logger.info(
            "BATCH_COLLECT_COMPLETE",
            session_id=str(session_id),
            batch_size=len(batch_messages),
            remaining_in_queue=queue.qsize(),
            messages_preview=[msg.message[:20] for msg in batch_messages],
        )

        return batch_messages

    async def _execute_message_batch(
        self, session_id: UUID, batch_messages: List[QueuedMessage]
    ) -> None:
        """
        Execute a batch of queued messages.

        STEPS:
        1. Load session and dependencies
        2. Group messages by sender
        3. Merge messages from same sender
        4. Save merged messages to DB
        5. Format for Claude with attribution
        6. Execute and broadcast events
        """
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import (
            SessionRepositoryImpl,
            ProjectRepositoryImpl,
            MessageRepositoryImpl,
        )
        from app.application.services import SessionService, MessageService
        from app.application.services.agent_service import AgentService
        from app.application.services.project_service import ProjectService
        from app.infrastructure.filesystem.agent_repository import (
            FileBasedAgentRepository,
        )
        from app.core.config import settings

        async with get_repository_session() as db:
            # Initialize repositories and services
            session_repo = SessionRepositoryImpl(db)
            project_repo = ProjectRepositoryImpl(db)
            message_repo = MessageRepositoryImpl(db)
            agent_repo = FileBasedAgentRepository(settings.agents_dir)

            session_service = SessionService(session_repo, project_repo, agent_repo)
            message_service = MessageService(message_repo, session_repo)
            agent_service = AgentService(agent_repo)
            project_service = ProjectService(project_repo, session_repo, agent_repo)

            # Load session
            session_entity = await session_repo.get_by_id(session_id)
            if not session_entity:
                logger.error("session_not_found", extra={"session_id": str(session_id)})
                return

            logger.info(
                "loaded_session_for_queue_processing",
                extra={
                    "session_id": str(session_id),
                    "claude_session_id": session_entity.claude_session_id,
                    "has_claude_session_id": bool(session_entity.claude_session_id),
                },
            )

            # Determine project path
            project_path = await self._get_project_path(
                session_entity.project_id, project_repo
            )

            # Group and merge messages
            incoming_messages = await self._batch_processor.group_and_merge_messages(
                session_id, batch_messages, message_service, db
            )

            # Format messages for Claude
            formatted_message = self._batch_processor.format_batch_for_claude(
                incoming_messages
            )

            # Execute and broadcast
            await self._execute_and_broadcast(
                session_id,
                session_entity,
                formatted_message,
                db,
                session_service,
                agent_service,
                project_service,
                message_service,
                project_path,
            )

    async def _execute_and_broadcast(
        self,
        session_id: UUID,
        session_entity,
        formatted_message: str,
        db,
        session_service,
        agent_service,
        project_service,
        message_service,
        project_path: str,
    ) -> None:
        """Execute message and broadcast events to SSE clients."""
        from app.infrastructure.sse.manager import sse_manager

        logger.info("executing_merged_messages", extra={"session_id": str(session_id)})

        async for event in self.execute(
            session_id=session_id,
            user_message=formatted_message,
            agent_id=session_entity.agent_id,
            db_session=db,
            session_service=session_service,
            agent_service=agent_service,
            project_service=project_service,
            project_path=project_path,
            resume_session_id=session_entity.claude_session_id,
            message_service=message_service,
        ):
            # Save messages at transitions
            if event.type == "content_block" and event.block_type == "text":
                await self._save_assistant_message(
                    session_id, session_entity, event, message_service, db
                )
            elif event.type == "tool_use":
                await self._save_tool_message(
                    session_id, session_entity, event, message_service, db
                )

            # Broadcast event
            await sse_manager.broadcast(session_id, event.to_sse())

        logger.info("queued_message_executed", extra={"session_id": str(session_id)})

    async def _save_assistant_message(
        self, session_id: UUID, session_entity, event, message_service, db
    ) -> None:
        """Save assistant message to database."""
        from app.infrastructure.database.repositories import MessageRepositoryImpl

        agent_id = session_entity.agent_id
        agent_name = agent_id.replace("-", " ").title() if agent_id else None

        message_repo = MessageRepositoryImpl(db)

        # Save assistant message using MessagePersistence
        await self._message_persistence.save_assistant_message(
            message_service=message_service,
            message_repo=message_repo,
            db_session=db,
            session_id=session_id,
            content=event.content,
            agent_id=agent_id,
            agent_name=agent_name,
            response_id=event.response_id,
        )

    async def _save_tool_message(
        self, session_id: UUID, session_entity, event, message_service, db
    ) -> None:
        """Save tool call message to database."""
        from app.infrastructure.database.repositories import MessageRepositoryImpl

        agent_id = session_entity.agent_id
        agent_name = agent_id.replace("-", " ").title() if agent_id else None

        message_repo = MessageRepositoryImpl(db)

        # Save tool message using MessagePersistence
        await self._message_persistence.save_tool_message(
            message_service=message_service,
            message_repo=message_repo,
            db_session=db,
            session_id=session_id,
            agent_id=agent_id,
            agent_name=agent_name,
            response_id=event.response_id,
            tool_name=event.tool_name,
            tool_args=event.tool_input,
        )

    # =========================================================================
    # DATABASE HELPERS
    # =========================================================================

    async def _get_project_path(self, project_id: Optional[UUID], project_repo) -> str:
        """Get project path from project ID."""
        if not project_id:
            return "."

        project = await project_repo.get_by_id(project_id)
        if not project or not project.path:
            return "."

        import os

        expanded_path = os.path.expanduser(project.path)
        expanded_path = os.path.abspath(expanded_path)
        return expanded_path if os.path.isdir(expanded_path) else "."

    async def _get_claude_session_id_from_db(self, session_id: UUID) -> Optional[str]:
        """Get Claude session ID from database."""
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        logger.info(
            "client_not_in_memory_querying_db", extra={"session_id": str(session_id)}
        )

        try:
            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)
                if session_entity:
                    claude_session_id = session_entity.claude_session_id
                    logger.info(
                        "got_claude_session_id_from_db",
                        extra={
                            "session_id": str(session_id),
                            "claude_session_id": claude_session_id,
                            "source": "database",
                        },
                    )
                    return claude_session_id

                logger.warning(
                    "session_entity_not_found_in_db",
                    extra={"session_id": str(session_id)},
                )
                return None
        except Exception as e:
            logger.error(
                "failed_to_get_claude_session_id_from_db",
                extra={"session_id": str(session_id), "error": str(e)},
            )
            return None

    async def _update_session_status_to_working(self, session_id: UUID) -> None:
        """Update session status to WORKING and broadcast."""
        await self._session_status_manager.update_to_working(session_id)

    async def _update_session_status_after_execution(
        self, session_id: UUID, execution_error: Optional[Exception]
    ) -> None:
        """Update session status to IDLE or ERROR after execution."""
        # Get claude_session_id for resume (only needed on success)
        claude_session_id = None
        if not execution_error:
            claude_session_id = await self.get_claude_session_id(session_id)

        await self._session_status_manager.update_after_execution(
            session_id, execution_error, claude_session_id
        )

    # =========================================================================
    # SSE HELPERS
    # =========================================================================

    async def _broadcast_queue_status(self, session_id: UUID) -> None:
        """Broadcast queue status with message previews to SSE clients."""
        from app.infrastructure.sse.manager import sse_manager
        from app.infrastructure.claude.events import (
            QueueStatusEvent,
            QueuedMessagePreview,
        )
        from datetime import datetime

        queue = self._queue_manager.get_queue(session_id)
        if not queue:
            return

        queue_size = queue.qsize()

        message_previews = []
        if queue_size > 0:
            queue_items = list(queue._queue)
            for queued_msg in queue_items[:10]:
                preview = queued_msg.message[:100]
                if len(queued_msg.message) > 100:
                    preview += "..."

                message_previews.append(
                    QueuedMessagePreview(
                        sender_name=queued_msg.sender_name,
                        sender_session_id=(
                            str(queued_msg.sender_session_id)
                            if queued_msg.sender_session_id
                            else None
                        ),
                        content_preview=preview,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        queue_event = QueueStatusEvent(
            session_id=str(session_id),
            messages=message_previews if message_previews else None,
        )
        await sse_manager.broadcast(session_id, queue_event.to_sse())

    # =========================================================================
    # CLIENT MANAGEMENT
    # =========================================================================

    async def _get_or_create_client(
        self,
        session_id: UUID,
        agent_id: str,
        project_path: str,
        session_dir: Path,
        resume_session_id: str | None,
    ):
        """Get existing client or create new one (lazy creation)."""
        try:
            client = await self._client_manager.get_client(session_id)
            logger.debug("using_existing_client", extra={"session_id": str(session_id)})
            return client
        except ClientNotFoundError:
            return await self._create_new_client(
                session_id, agent_id, project_path, session_dir, resume_session_id
            )

    async def _create_new_client(
        self,
        session_id: UUID,
        agent_id: str,
        project_path: str,
        session_dir: Path,
        resume_session_id: str | None,
    ):
        """Create new Claude client using SessionFactory."""
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            session_entity = await session_repo.get_by_id(session_id)

        if not session_entity:
            raise ClaudeExecutionError(f"Session not found: {session_id}")

        session_dir.mkdir(parents=True, exist_ok=True)
        resume_id = session_entity.claude_session_id or resume_session_id

        logger.info(
            "creating_new_client",
            extra={
                "session_id": str(session_id),
                "session_type": session_entity.session_type.value,
                "agent_id": agent_id,
                "project_path": project_path,
                "session_dir": str(session_dir),
                "will_resume": bool(resume_id),
            },
        )

        try:
            client = await self._client_manager.create_client_from_session(
                session=session_entity,
                working_dir=session_dir,
                project_path=Path(project_path) if project_path else None,
                resume_session=resume_id,
            )
            logger.info(
                "client_created_successfully", extra={"session_id": str(session_id)}
            )
            return client
        except Exception as e:
            logger.error(
                "client_creation_failed",
                extra={
                    "session_id": str(session_id),
                    "agent_id": agent_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            raise ClaudeExecutionError(f"Failed to create client: {e}") from e

    # =========================================================================
    # INTERRUPT HELPERS
    # =========================================================================

    async def _interrupt_claude_client(self, session_id: UUID) -> None:
        """Interrupt Claude client execution."""
        try:
            client = await self._client_manager.get_client(session_id)
            await client.interrupt()
            logger.warning(
                "CLAUDE_CLIENT_INTERRUPTED", extra={"session_id": str(session_id)}
            )

            await self._client_manager.remove_client(session_id)
            logger.warning(
                "CLAUDE_CLIENT_REMOVED_AFTER_INTERRUPT",
                extra={"session_id": str(session_id)},
            )
        except ClientNotFoundError:
            logger.warning(
                "NO_ACTIVE_CLIENT_TO_INTERRUPT", extra={"session_id": str(session_id)}
            )

    async def _clear_message_queue(self, session_id: UUID) -> None:
        """Clear all messages from queue."""
        await self._queue_manager.clear_queue(session_id)

    async def _cancel_queue_processor(self, session_id: UUID) -> None:
        """Cancel queue processor task."""
        if session_id not in self._queue_processors:
            return

        task = self._queue_processors[session_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(
                    "queue_processor_cancel_error",
                    extra={"session_id": str(session_id), "error": str(e)},
                )

        del self._queue_processors[session_id]
        logger.info("queue_processor_cancelled", extra={"session_id": str(session_id)})

    # =========================================================================
    # UTILITY HELPERS
    # =========================================================================

    def _ensure_queue_exists(self, session_id: UUID) -> None:
        """Ensure message queue exists for session."""
        self._queue_manager.ensure_queue_exists(session_id)

    def _is_processor_running(self, session_id: UUID) -> bool:
        """Check if queue processor is running for session."""
        return (
            session_id in self._queue_processors
            and not self._queue_processors[session_id].done()
        )
