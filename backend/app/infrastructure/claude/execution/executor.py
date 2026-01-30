"""
Simplified executor using the Execution class.

Key simplifications:
- No background queue processor
- Direct execution trigger on enqueue
- Clear execution lifecycle
"""

from pathlib import Path
from typing import Dict, Optional
from uuid import UUID
import asyncio

from app.core.logging import get_logger
from app.infrastructure.claude.core.client_manager import ClaudeClientManager
from app.infrastructure.claude.exceptions import (
    ClaudeExecutionError,
    ClientNotFoundError,
)
from app.infrastructure.claude.types import QueuedMessage
from app.infrastructure.claude.execution.queue_processor import MessageQueueProcessor
from app.infrastructure.claude.state.session_status_manager import SessionStatusManager
from app.infrastructure.claude.streaming.persistence import MessagePersistence
from app.infrastructure.claude.execution.execution import Execution

logger = get_logger(__name__)


class SessionExecutor:
    """
    Simplified session executor with clear execution lifecycle.

    Key differences from original:
    - No background queue processor task
    - Direct execution trigger
    - Uses Execution class for clear boundaries
    """

    def __init__(self, client_manager: ClaudeClientManager):
        self._client_manager = client_manager
        self._session_locks: Dict[UUID, asyncio.Lock] = {}
        self._executions: Dict[UUID, asyncio.Task] = {}  # Running executions

        # Component managers (reuse existing)
        self._message_persistence = MessagePersistence()
        self._session_status_manager = SessionStatusManager()
        self._queue_manager = MessageQueueProcessor()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def enqueue(
        self,
        session_id: UUID,
        message: str,
        sender_name: Optional[str] = None,
        sender_session_id: Optional[UUID] = None,
        sender_agent_id: Optional[str] = None,
    ) -> None:
        """
        Enqueue message and trigger execution if needed.

        SIMPLIFIED: No background processor. Direct trigger.
        """
        logger.info(
            "enqueue_message",
            extra={
                "session_id": str(session_id),
                "sender_name": sender_name,
                "message_length": len(message),
            },
        )

        # Ensure queue exists
        self._queue_manager.ensure_queue_exists(session_id)

        # Add to queue
        queued_msg = QueuedMessage(
            message, sender_name, sender_session_id, sender_agent_id
        )
        queue = self._queue_manager.get_queue(session_id)
        await queue.put(queued_msg)

        logger.info(
            "message_enqueued",
            session_id=str(session_id),
            queue_size=queue.qsize(),
        )

        # Broadcast queue status
        await self._broadcast_queue_status(session_id)

        # Trigger execution if not already running
        await self._trigger_execution_if_needed(session_id)

    async def interrupt(self, session_id: UUID) -> None:
        """
        Interrupt running execution and clear queue.

        SIMPLIFIED: Just cancel the execution task.
        """
        logger.warning(
            "interrupt_session_started", extra={"session_id": str(session_id)}
        )

        try:
            # Interrupt Claude client
            await self._interrupt_claude_client(session_id)

            # Clear queue
            await self._queue_manager.clear_queue(session_id)

            # Cancel execution task if running
            lock = self._get_or_create_lock(session_id)
            async with lock:
                if session_id in self._executions:
                    task = self._executions[session_id]
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                    del self._executions[session_id]

            # Update status
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
        """Check if session is currently executing."""
        return (
            session_id in self._executions and not self._executions[session_id].done()
        )

    def get_queue_size(self, session_id: UUID) -> int:
        """Get number of queued messages."""
        return self._queue_manager.get_queue_size(session_id)

    async def get_claude_session_id(self, session_id: UUID) -> str | None:
        """Get Claude session ID for resume."""
        try:
            client = await self._client_manager.get_client(session_id)
            return client.get_session_id()
        except ClientNotFoundError:
            return await self._get_claude_session_id_from_db(session_id)

    # =========================================================================
    # EXECUTION FLOW
    # =========================================================================

    async def _trigger_execution_if_needed(self, session_id: UUID) -> None:
        """
        Start execution if not already running.

        ATOMIC: Lock prevents race condition on check-and-create.
        """
        lock = self._get_or_create_lock(session_id)
        async with lock:
            # Check if already executing
            if session_id in self._executions:
                task = self._executions[session_id]
                if not task.done():
                    logger.debug(
                        "execution_already_running",
                        session_id=str(session_id),
                    )
                    return

            # Start new execution
            logger.info("starting_execution", session_id=str(session_id))
            self._executions[session_id] = asyncio.create_task(
                self._execute_session(session_id)
            )

    async def _execute_session(self, session_id: UUID) -> None:
        """
        Execute one session lifecycle.

        SIMPLIFIED: Load context, create Execution, run, cleanup.
        """
        context = None
        try:
            # Update status
            await self._update_session_status_to_working(session_id)

            # Load execution context
            context = await self._load_execution_context(session_id)

            # Setup MCP tool context (for PM tools, etc.)
            await self._setup_tool_context(
                session_id,
                context["db_session"],
                context["session_service"],
            )

            # Create execution
            execution = Execution(
                session_id=session_id,
                client=context["client"],
                queue=self._queue_manager.get_queue(session_id),
                message_service=context["message_service"],
                db_session=context["db_session"],
                session_entity=context["session_entity"],
                db_lock=context["db_lock"],
                on_queue_change=lambda: self._broadcast_queue_status(session_id),
            )

            # Run and broadcast events
            async for event in execution.run():
                # Save messages to database at transitions (reuse same db session)
                if event.type == "content_block" and event.block_type == "text":
                    await self._save_assistant_message(
                        session_id,
                        context["session_entity"],
                        event,
                        context["message_service"],
                        context["db_session"],
                        context["db_lock"],
                    )
                elif event.type == "tool_use":
                    await self._save_tool_message(
                        session_id,
                        context["session_entity"],
                        event,
                        context["message_service"],
                        context["db_session"],
                        context["db_lock"],
                    )

                # Broadcast to SSE
                from app.infrastructure.sse.manager import sse_manager

                await sse_manager.broadcast(session_id, event.to_sse())

            # Commit all saves (with lock)
            async with context["db_lock"]:
                await context["db_session"].commit()

            # Update status to IDLE
            await self._update_session_status_after_execution(session_id, None)

        except Exception as e:
            logger.error(
                "execution_failed",
                extra={
                    "session_id": str(session_id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            # Rollback on error
            if context and context.get("db_session"):
                await context["db_session"].rollback()
            # Update status to ERROR
            await self._update_session_status_after_execution(session_id, e)
            raise

        finally:
            # Close database session
            if context and context.get("db_session"):
                await context["db_session"].close()
            # Cleanup
            await self._cleanup_execution(session_id)

    async def _cleanup_execution(self, session_id: UUID) -> None:
        """
        Clean up execution state.

        Note: Remaining messages in queue will be processed when next
        enqueue() call triggers a new execution. This avoids creating
        background tasks that don't get properly consumed.
        """
        lock = self._get_or_create_lock(session_id)
        async with lock:
            # Remove execution task
            if session_id in self._executions:
                del self._executions[session_id]

            # Check for remaining messages (for logging/metrics)
            queue = self._queue_manager.get_queue(session_id)
            if queue and queue.qsize() > 0:
                logger.info(
                    "messages_remain_in_queue_after_cleanup",
                    session_id=str(session_id),
                    remaining=queue.qsize(),
                )

    # =========================================================================
    # HELPERS (reuse from original executor)
    # =========================================================================

    def _get_or_create_lock(self, session_id: UUID) -> asyncio.Lock:
        """Get or create lock for session."""
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]

    async def _load_execution_context(self, session_id: UUID) -> dict:
        """Load all context needed for execution."""
        from app.infrastructure.database.connection import get_session_factory
        from app.infrastructure.database.repositories import (
            SessionRepositoryImpl,
            ProjectRepositoryImpl,
            MessageRepositoryImpl,
        )
        from app.application.services import SessionService, MessageService
        from app.infrastructure.filesystem.agent_repository import (
            FileBasedAgentRepository,
        )
        from app.core.config import settings

        # Create session WITHOUT context manager - we'll manage lifecycle manually
        session_factory = get_session_factory()
        db = session_factory()

        # Repositories
        session_repo = SessionRepositoryImpl(db)
        project_repo = ProjectRepositoryImpl(db)
        message_repo = MessageRepositoryImpl(db)
        agent_repo = FileBasedAgentRepository(settings.agents_dir)

        # Services
        session_service = SessionService(session_repo, project_repo, agent_repo)
        message_service = MessageService(message_repo, session_repo)

        # Load session
        session_entity = await session_repo.get_by_id(session_id)
        if not session_entity:
            raise ClaudeExecutionError(f"Session not found: {session_id}")

        # Get project path
        project_path = "."
        if session_entity.project_id:
            project = await project_repo.get_by_id(session_entity.project_id)
            if project and project.path:
                import os

                expanded = os.path.expanduser(project.path)
                project_path = (
                    os.path.abspath(expanded) if os.path.isdir(expanded) else "."
                )

        # Get or create client
        session_dir = Path(project_path) / ".sessions" / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        client = await self._get_or_create_client(
            session_id,
            session_entity.agent_id,
            project_path,
            session_dir,
            session_entity.claude_session_id,
        )

        return {
            "client": client,
            "db_session": db,
            "session_service": session_service,
            "message_service": message_service,
            "session_entity": session_entity,
            "db_lock": asyncio.Lock(),  # Prevent concurrent db operations
        }

    async def _get_or_create_client(
        self, session_id, agent_id, project_path, session_dir, resume_id
    ):
        """Get existing client or create new one."""
        try:
            client = await self._client_manager.get_client(session_id)
            return client
        except ClientNotFoundError:
            from app.infrastructure.database.connection import get_repository_session
            from app.infrastructure.database.repositories import SessionRepositoryImpl

            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)

            if not session_entity:
                raise ClaudeExecutionError(f"Session not found: {session_id}")

            client = await self._client_manager.create_client_from_session(
                session=session_entity,
                working_dir=session_dir,
                project_path=Path(project_path) if project_path else None,
                resume_session=resume_id,
            )
            return client

    async def _interrupt_claude_client(self, session_id: UUID) -> None:
        """Interrupt Claude client."""
        try:
            client = await self._client_manager.get_client(session_id)
            await client.interrupt()
            await self._client_manager.remove_client(session_id)
        except ClientNotFoundError:
            pass

    async def _update_session_status_to_working(self, session_id: UUID) -> None:
        """Update status to WORKING."""
        await self._session_status_manager.update_to_working(session_id)

    async def _update_session_status_after_execution(
        self, session_id: UUID, error: Optional[Exception]
    ) -> None:
        """Update status after execution."""
        claude_session_id = None
        if not error:
            claude_session_id = await self.get_claude_session_id(session_id)

        await self._session_status_manager.update_after_execution(
            session_id, error, claude_session_id
        )

    async def _get_claude_session_id_from_db(self, session_id: UUID) -> Optional[str]:
        """Get Claude session ID from database."""
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        try:
            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)
                return session_entity.claude_session_id if session_entity else None
        except Exception as e:
            logger.error(
                "failed_to_get_claude_session_id_from_db", extra={"error": str(e)}
            )
            return None

    async def _save_assistant_message(
        self,
        session_id: UUID,
        session_entity,
        event,
        message_service,
        db_session,
        db_lock,
    ) -> None:
        """Save assistant message to database."""
        from app.infrastructure.database.repositories import MessageRepositoryImpl

        agent_id = session_entity.agent_id
        agent_name = agent_id.replace("-", " ").title() if agent_id else None

        # Save with lock to prevent concurrent flushes
        async with db_lock:
            # Reuse existing db session (avoids SQLite locking issues)
            message_repo = MessageRepositoryImpl(db_session)

            # Save assistant message using MessagePersistence
            await self._message_persistence.save_assistant_message(
                message_service=message_service,
                message_repo=message_repo,
                db_session=db_session,
                session_id=session_id,
                content=event.content,
                agent_id=agent_id,
                agent_name=agent_name,
                response_id=event.response_id,
            )
            await db_session.commit()

    async def _save_tool_message(
        self,
        session_id: UUID,
        session_entity,
        event,
        message_service,
        db_session,
        db_lock,
    ) -> None:
        """Save tool call message to database."""
        from app.infrastructure.database.repositories import MessageRepositoryImpl

        agent_id = session_entity.agent_id
        agent_name = agent_id.replace("-", " ").title() if agent_id else None

        # Save with lock to prevent concurrent flushes
        async with db_lock:
            # Reuse existing db session (avoids SQLite locking issues)
            message_repo = MessageRepositoryImpl(db_session)

            # Save tool message using MessagePersistence
            await self._message_persistence.save_tool_message(
                message_service=message_service,
                message_repo=message_repo,
                db_session=db_session,
                session_id=session_id,
                agent_id=agent_id,
                agent_name=agent_name,
                response_id=event.response_id,
                tool_name=event.tool_name,
                tool_args=event.tool_input,
            )
            await db_session.commit()

    async def _setup_tool_context(
        self,
        session_id: UUID,
        db_session,
        session_service,
    ) -> None:
        """Setup tool context and session info for MCP tools (PM tools, etc.)."""

        # Set session info (source_instance_id and project_id) for PM tools
        await self._set_session_info_async(session_id)
        logger.debug("tool_context_set", extra={"session_id": str(session_id)})

    async def _set_session_info_async(self, session_id: UUID) -> None:
        """Set session info asynchronously for MCP tool hooks."""
        from app.infrastructure.mcp.servers.context import set_session_info
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
                    logger.info(
                        "session_info_set_for_mcp_tools",
                        extra={
                            "session_id": str(session_id),
                            "project_id": (
                                str(session_entity.project_id)
                                if session_entity.project_id
                                else None
                            ),
                        },
                    )
        except Exception as e:
            logger.warning(
                "failed_to_set_session_info",
                extra={"session_id": str(session_id), "error": str(e)},
            )

    async def _broadcast_queue_status(self, session_id: UUID) -> None:
        """Broadcast queue status to SSE."""
        from app.infrastructure.sse.manager import sse_manager
        from app.infrastructure.claude.streaming.events import (
            QueueStatusEvent,
            QueuedMessagePreview,
        )
        from datetime import datetime

        queue = self._queue_manager.get_queue(session_id)
        if not queue:
            return

        message_previews = []
        if queue.qsize() > 0:
            queue_items = list(queue._queue)
            for msg in queue_items[:10]:
                preview = msg.message[:100]
                if len(msg.message) > 100:
                    preview += "..."
                message_previews.append(
                    QueuedMessagePreview(
                        sender_name=msg.sender_name,
                        sender_session_id=(
                            str(msg.sender_session_id)
                            if msg.sender_session_id
                            else None
                        ),
                        content_preview=preview,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        event = QueueStatusEvent(
            session_id=str(session_id),
            messages=message_previews if message_previews else None,
        )
        await sse_manager.broadcast(session_id, event.to_sse())
