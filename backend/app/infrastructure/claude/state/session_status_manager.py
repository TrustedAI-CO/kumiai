"""Session status manager for executor.

This is the ONLY place that should update session status.
All other components must call methods here instead of directly updating status.

THREAD SAFETY: Uses per-session locks to prevent race conditions.
"""

import asyncio
from typing import Dict, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.domain.value_objects import SessionStatus
from app.infrastructure.database.connection import get_repository_session
from app.infrastructure.database.repositories import SessionRepositoryImpl
from app.infrastructure.claude.streaming.events import SessionStatusEvent
from app.infrastructure.sse.manager import sse_manager

logger = get_logger(__name__)


class SessionStatusManager:
    """
    Manages ALL session status updates and broadcasting.

    **CRITICAL**: This is the SINGLE SOURCE OF TRUTH for status updates.
    No other component should directly assign session.status = X.

    Centralizes all session status transitions:
    - IDLE/INITIALIZING → WORKING (when processing starts)
    - WORKING → IDLE (when processing completes successfully)
    - WORKING → ERROR (when processing fails)
    - ERROR → WORKING (when user sends new message to recover)
    - ERROR → IDLE (when resetting/resuming from error state)
    - Any status → INTERRUPTED (when user interrupts)

    Thread Safety:
    - Uses per-session asyncio.Lock to prevent concurrent updates
    - Has transition validation (currently not enforced in update methods)
    - Handles database commits atomically

    Also handles:
    - Database persistence
    - SSE broadcasting to clients
    - Claude session ID storage for resume
    - Kanban stage synchronization
    """

    def __init__(self):
        """Initialize with per-session locks."""
        self._locks: Dict[UUID, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()  # Lock for the locks dict itself

    async def _get_lock(self, session_id: UUID) -> asyncio.Lock:
        """Get or create a lock for a specific session."""
        async with self._locks_lock:
            if session_id not in self._locks:
                self._locks[session_id] = asyncio.Lock()
            return self._locks[session_id]

    def _is_valid_transition(
        self, from_status: SessionStatus, to_status: SessionStatus
    ) -> bool:
        """
        Validate if a status transition is allowed.

        Valid transitions:
        - IDLE/INITIALIZING → WORKING
        - WORKING → IDLE
        - WORKING → ERROR
        - ERROR → WORKING (recovery by sending new message)
        - ERROR → IDLE (resume to idle after error)
        - Any status → INTERRUPTED

        NOTE: This method is currently not called. Consider integrating it
        into update methods for proper validation.
        """
        if to_status == SessionStatus.INTERRUPTED:
            return True

        valid_transitions = {
            SessionStatus.IDLE: {SessionStatus.WORKING},
            SessionStatus.INITIALIZING: {SessionStatus.WORKING},
            SessionStatus.WORKING: {SessionStatus.IDLE, SessionStatus.ERROR},
            SessionStatus.ERROR: {
                SessionStatus.WORKING,  # Recovery by sending new message
                SessionStatus.IDLE,  # Resume to idle
            },
        }

        return to_status in valid_transitions.get(from_status, set())

    async def update_to_working(self, session_id: UUID) -> None:
        """
        Update session status to WORKING and broadcast.

        Args:
            session_id: Session UUID
        """
        lock = await self._get_lock(session_id)
        async with lock:
            try:
                async with get_repository_session() as db:
                    session_repo = SessionRepositoryImpl(db)
                    session_entity = await session_repo.get_by_id(session_id)
                    if session_entity:
                        # Clear error_message if recovering from ERROR state
                        # This prevents frontend from showing stale error banner
                        if session_entity.status == SessionStatus.ERROR:
                            session_entity.error_message = None

                        session_entity.status = SessionStatus.WORKING
                        session_entity.sync_kanban_stage()
                        await session_repo.update(session_entity)
                        await db.commit()

                        status_event = SessionStatusEvent(
                            session_id=str(session_id),
                            status=SessionStatus.WORKING.value,
                        )
                        await sse_manager.broadcast(session_id, status_event.to_sse())
                        logger.info(
                            "session_status_updated_to_working",
                            extra={"session_id": str(session_id)},
                        )
            except Exception as e:
                logger.error(
                    "failed_to_update_session_status_to_working",
                    extra={"session_id": str(session_id), "error": str(e)},
                )

    async def update_after_execution(
        self,
        session_id: UUID,
        execution_error: Optional[Exception],
        claude_session_id: Optional[str] = None,
    ) -> None:
        """
        Update session status to IDLE or ERROR after execution.

        Args:
            session_id: Session UUID
            execution_error: Exception if execution failed, None if successful
            claude_session_id: Claude session ID to save for resume (optional)
        """
        lock = await self._get_lock(session_id)
        async with lock:
            try:
                async with get_repository_session() as db:
                    session_repo = SessionRepositoryImpl(db)
                    session_entity = await session_repo.get_by_id(session_id)
                    if not session_entity:
                        logger.warning(
                            "session_not_found_for_status_update",
                            extra={"session_id": str(session_id)},
                        )
                        return

                    if execution_error:
                        session_entity.status = SessionStatus.ERROR
                        session_entity.error_message = str(execution_error)
                        await session_repo.update(session_entity)
                        await db.commit()

                        status_event = SessionStatusEvent(
                            session_id=str(session_id), status=SessionStatus.ERROR.value
                        )
                        await sse_manager.broadcast(session_id, status_event.to_sse())
                        logger.info(
                            "session_status_set_to_error",
                            extra={
                                "session_id": str(session_id),
                                "error": str(execution_error),
                            },
                        )
                    else:
                        session_entity.status = SessionStatus.IDLE
                        session_entity.error_message = None

                        # Save claude_session_id for resume
                        if claude_session_id:
                            session_entity.claude_session_id = claude_session_id
                            logger.info(
                                "saved_claude_session_id",
                                extra={
                                    "session_id": str(session_id),
                                    "claude_session_id": claude_session_id,
                                },
                            )
                        else:
                            logger.warning(
                                "no_claude_session_id_to_save",
                                extra={"session_id": str(session_id)},
                            )

                        session_entity.sync_kanban_stage()
                        await session_repo.update(session_entity)
                        await db.commit()

                        status_event = SessionStatusEvent(
                            session_id=str(session_id), status=SessionStatus.IDLE.value
                        )
                        await sse_manager.broadcast(session_id, status_event.to_sse())
                        logger.info(
                            "session_status_reset_to_idle",
                            extra={"session_id": str(session_id)},
                        )
            except Exception as e:
                logger.error(
                    "failed_to_update_session_status_after_execution",
                    extra={
                        "session_id": str(session_id),
                        "error": str(e),
                        "had_execution_error": execution_error is not None,
                    },
                )

    async def reset_to_idle(
        self, session_id: UUID, clear_claude_session: bool = False
    ) -> None:
        """
        Reset session status to IDLE (for recreate/reset operations).

        Args:
            session_id: Session UUID
            clear_claude_session: If True, also clears the claude_session_id
        """
        lock = await self._get_lock(session_id)
        async with lock:
            try:
                async with get_repository_session() as db:
                    session_repo = SessionRepositoryImpl(db)
                    session_entity = await session_repo.get_by_id(session_id)
                    if not session_entity:
                        logger.warning(
                            "session_not_found_for_reset",
                            extra={"session_id": str(session_id)},
                        )
                        return

                    session_entity.status = SessionStatus.IDLE
                    session_entity.error_message = None
                    if clear_claude_session:
                        session_entity.claude_session_id = None

                    session_entity.sync_kanban_stage()
                    await session_repo.update(session_entity)
                    await db.commit()

                    status_event = SessionStatusEvent(
                        session_id=str(session_id), status=SessionStatus.IDLE.value
                    )
                    await sse_manager.broadcast(session_id, status_event.to_sse())
                    logger.info(
                        "session_reset_to_idle",
                        extra={
                            "session_id": str(session_id),
                            "cleared_claude_session": clear_claude_session,
                        },
                    )
            except Exception as e:
                logger.error(
                    "failed_to_reset_session_to_idle",
                    extra={"session_id": str(session_id), "error": str(e)},
                )

    async def update_to_interrupted(self, session_id: UUID) -> None:
        """
        Update session status to INTERRUPTED when user interrupts execution.

        This can be called from any status and will always succeed.

        Args:
            session_id: Session UUID
        """
        lock = await self._get_lock(session_id)
        async with lock:
            try:
                async with get_repository_session() as db:
                    session_repo = SessionRepositoryImpl(db)
                    session_entity = await session_repo.get_by_id(session_id)
                    if not session_entity:
                        logger.warning(
                            "session_not_found_for_interrupt",
                            extra={"session_id": str(session_id)},
                        )
                        return

                    session_entity.status = SessionStatus.INTERRUPTED
                    session_entity.sync_kanban_stage()
                    await session_repo.update(session_entity)
                    await db.commit()

                    status_event = SessionStatusEvent(
                        session_id=str(session_id),
                        status=SessionStatus.INTERRUPTED.value,
                    )
                    await sse_manager.broadcast(session_id, status_event.to_sse())
                    logger.info(
                        "session_status_updated_to_interrupted",
                        extra={"session_id": str(session_id)},
                    )
            except Exception as e:
                logger.error(
                    "failed_to_update_session_status_to_interrupted",
                    extra={"session_id": str(session_id), "error": str(e)},
                )


# Global singleton instance
session_status_manager = SessionStatusManager()
