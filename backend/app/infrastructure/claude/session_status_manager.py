"""Session status manager for executor."""

from typing import Optional
from uuid import UUID

from app.core.logging import get_logger
from app.domain.value_objects import SessionStatus
from app.infrastructure.database.connection import get_repository_session
from app.infrastructure.database.repositories import SessionRepositoryImpl
from app.infrastructure.claude.events import SessionStatusEvent
from app.infrastructure.sse.manager import sse_manager

logger = get_logger(__name__)


class SessionStatusManager:
    """
    Manages session status updates and broadcasting.

    Centralizes all session status transitions:
    - IDLE → WORKING (when processing starts)
    - WORKING → IDLE (when processing completes successfully)
    - WORKING → ERROR (when processing fails)

    Also handles:
    - Database persistence
    - SSE broadcasting to clients
    - Claude session ID storage for resume
    - Kanban stage synchronization
    """

    async def update_to_working(self, session_id: UUID) -> None:
        """
        Update session status to WORKING and broadcast.

        Args:
            session_id: Session UUID
        """
        try:
            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)
                if session_entity:
                    session_entity.status = SessionStatus.WORKING
                    session_entity.sync_kanban_stage()
                    await session_repo.update(session_entity)
                    await db.commit()

                    status_event = SessionStatusEvent(
                        session_id=str(session_id), status=SessionStatus.WORKING.value
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
        try:
            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(session_id)
                if not session_entity:
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
