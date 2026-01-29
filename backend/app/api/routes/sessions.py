"""Session API endpoints."""

import asyncio
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_session_service,
    get_session_executor,
    get_agent_service,
    get_project_service,
)
from app.application.dtos.requests import (
    CreateSessionRequest,
    ExecuteQueryRequest,
    UpdateSessionStageRequest,
)
from app.application.dtos.session_dto import SessionDTO
from app.application.services import SessionService, MessageService
from app.application.services.agent_service import AgentService
from app.application.services.project_service import ProjectService
from app.infrastructure.claude.executor import SessionExecutor
from app.infrastructure.database.connection import get_repository_session
from app.infrastructure.database.repositories import (
    MessageRepositoryImpl,
    ProjectRepositoryImpl,
    SessionRepositoryImpl,
)
from app.infrastructure.filesystem.agent_repository import FileBasedAgentRepository
from app.core.config import settings
from app.domain.entities import Message
from app.domain.value_objects import MessageRole, SessionStatus
from app.core.dependencies import get_db
from app.core.logging import get_logger
from uuid import uuid4

router = APIRouter()
logger = get_logger(__name__)


async def _save_message_in_transaction(
    db_session,
    session_id: UUID,
    role: str,
    content: str,
    tool_name: Optional[str] = None,
    tool_args: Optional[dict] = None,
) -> None:
    """
    Save a message within an existing database transaction.

    This function does NOT commit - the caller must commit.
    Sequential event processing ensures no race conditions.

    Args:
        db_session: Existing database session (shared across stream)
        session_id: Session UUID
        role: Message role ('assistant' or 'tool')
        content: Message content (text for assistant, empty for tool)
        tool_name: Tool name (only for tool)
        tool_args: Tool arguments (only for tool)
    """
    from app.domain.value_objects import MessageRole
    from app.infrastructure.database.repositories import (
        SessionRepositoryImpl,
    )
    from app.infrastructure.filesystem.agent_repository import FileBasedAgentRepository
    from app.application.services import SessionService
    from app.core.config import settings

    message_repo = MessageRepositoryImpl(db_session)
    session_repo = SessionRepositoryImpl(db_session)
    project_repo = ProjectRepositoryImpl(db_session)
    agent_repo = FileBasedAgentRepository(base_path=settings.agents_dir)

    msg_service = MessageService(message_repo, session_repo)
    session_service = SessionService(session_repo, project_repo, agent_repo)

    # Get sender attribution from service
    agent_id, agent_name = await session_service.get_sender_fields(session_id)

    # Map role string to MessageRole enum
    if role == "assistant":
        message_role = MessageRole.ASSISTANT
    elif role == "tool":
        message_role = MessageRole.TOOL_CALL
    else:
        logger.warning(f"Unknown role: {role}, defaulting to ASSISTANT")
        message_role = MessageRole.ASSISTANT

    # Create message entity
    # sequence=0 is kept for backward compatibility but not used for ordering
    message = Message(
        id=uuid4(),
        session_id=session_id,
        role=message_role,
        content=content,
        sequence=0,  # No longer used for ordering, kept for backward compatibility
        agent_id=agent_id,
        agent_name=agent_name,
        from_instance_id=None,
        metadata=(
            {
                "tool_name": tool_name,
                "tool_args": tool_args,
            }
            if tool_name
            else {}
        ),
    )

    # Save to database (no commit - caller commits)
    await msg_service.save_message(message)
    logger.debug("message_queued", message_id=str(message.id), role=role)


async def _update_session_status(
    session_id: UUID,
    executor: "SessionExecutor",
) -> None:
    """
    Update session status to IDLE and save Claude session ID.

    Args:
        session_id: Session UUID
        executor: SessionExecutor to get Claude session ID
    """
    from app.domain.value_objects import SessionStatus

    # Get Claude session ID for resume functionality
    claude_session_id = await executor.get_claude_session_id(session_id)

    logger.info(
        "retrieved_claude_session_id",
        session_id=str(session_id),
        claude_session_id=claude_session_id,
        has_claude_session_id=bool(claude_session_id),
    )

    async with get_repository_session() as db:
        session_repo = SessionRepositoryImpl(db)
        db_session = await session_repo.get_by_id(session_id)

        if db_session:
            logger.info(
                "updating_session_to_idle",
                session_id=str(session_id),
                old_status=db_session.status.value,
                old_claude_session_id=db_session.claude_session_id,
                new_claude_session_id=claude_session_id,
            )
            db_session.status = SessionStatus.IDLE
            if claude_session_id:
                db_session.claude_session_id = claude_session_id
                logger.info(
                    "saved_claude_session_id_to_db",
                    session_id=str(session_id),
                    claude_session_id=claude_session_id,
                )
            else:
                logger.warning(
                    "no_claude_session_id_to_save",
                    session_id=str(session_id),
                    message="Claude session ID not available - session may not resume after reload",
                )
            # Sync kanban stage with new status (uses domain entity method)
            db_session.sync_kanban_stage()
            await session_repo.update(db_session)
            logger.info(
                "session_completed",
                session_id=str(session_id),
                claude_session_id=claude_session_id,
            )


@router.post(
    "/sessions",
    response_model=SessionDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new agent session with specified agent and optional project",
)
async def create_session(
    request: CreateSessionRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Create a new session.

    Args:
        request: Session creation request
        service: Session service (injected)

    Returns:
        Created session

    Raises:
        404: Agent or project not found
        400: Validation error (e.g., PM without project)
    """
    logger.info(
        "create_session_request",
        agent_id=request.agent_id,
        session_type=request.session_type,
        has_project=request.project_id is not None,
    )
    return await service.create_session(request)


@router.post(
    "/sessions/launch",
    response_model=SessionDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Launch a new session (legacy endpoint)",
    description="Launch a session with legacy role-based format. Maps old role names to new session_type values.",
)
async def launch_session(
    request: Dict[str, Any],
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Launch a session using legacy format from frontend.

    Maps old role values to new session_type values:
    - character_assistant -> agent_assistant
    - skill_assistant -> skill_assistant
    - pm -> pm
    - specialist -> specialist
    - assistant -> assistant

    Args:
        request: Legacy session launch request with 'role' field
        service: Session service (injected)

    Returns:
        Created session

    Raises:
        400: Invalid role or validation error
    """

    # Map legacy role to session_type
    role = request.get("role", "assistant")
    role_to_session_type_map = {
        "character_assistant": "agent_assistant",  # Legacy name
        "agent_assistant": "agent_assistant",  # New name (passthrough)
        "skill_assistant": "skill_assistant",
        "pm": "pm",
        "specialist": "specialist",
        "assistant": "assistant",
    }

    session_type = role_to_session_type_map.get(role, "assistant")

    # Extract agent_id (may be empty for assistant sessions)
    agent_id = request.get("agent_id", "")

    # Extract project_id if provided
    project_id_str = request.get("project_id")
    project_id = UUID(project_id_str) if project_id_str else None

    # Build context from legacy fields
    context = {
        "task_description": request.get("session_description", ""),
        "description": request.get("session_description", ""),
    }

    # Add project_path to context if provided
    if request.get("project_path"):
        context["project_path"] = request.get("project_path")

    # Add kanban_stage for specialist sessions
    if session_type == "specialist":
        context["kanban_stage"] = "backlog"

    logger.info(
        "launch_session_request",
        role=role,
        mapped_session_type=session_type,
        agent_id=agent_id,
        has_project=project_id is not None,
    )

    # Create using new format
    create_request = CreateSessionRequest(
        agent_id=agent_id or "",  # Provide empty string if not set
        project_id=project_id,
        session_type=session_type,
        context=context,
    )

    return await service.create_session(create_request)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDTO,
    summary="Get session by ID",
    description="Retrieve a session by its UUID",
)
async def get_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Get session by ID.

    Args:
        session_id: Session UUID
        service: Session service (injected)

    Returns:
        Session details

    Raises:
        404: Session not found
    """
    return await service.get_session(session_id)


@router.get(
    "/sessions",
    response_model=List[SessionDTO],
    summary="List sessions",
    description="List sessions with optional filters (project_id, status)",
)
async def list_sessions(
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    service: SessionService = Depends(get_session_service),
) -> List[SessionDTO]:
    """
    List sessions with optional filters.

    Args:
        project_id: Filter by project (optional)
        status: Filter by status (optional)
        service: Session service (injected)

    Returns:
        List of sessions
    """
    return await service.list_sessions(project_id=project_id, status=status)


@router.post(
    "/sessions/{session_id}/start",
    response_model=SessionDTO,
    summary="Start a session",
    description="Transition session to thinking state",
)
async def start_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Start a session (transition to thinking state).

    Args:
        session_id: Session UUID
        service: Session service (injected)

    Returns:
        Updated session

    Raises:
        404: Session not found
        409: Invalid state transition
    """
    logger.info("start_session_request", session_id=str(session_id))
    return await service.start_session(session_id)


@router.post(
    "/sessions/{session_id}/complete",
    response_model=SessionDTO,
    summary="Complete a session",
    description="Mark session as completed",
)
async def complete_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Complete a session.

    Args:
        session_id: Session UUID
        service: Session service (injected)

    Returns:
        Updated session

    Raises:
        404: Session not found
        409: Invalid state transition
    """
    logger.info("complete_session_request", session_id=str(session_id))
    return await service.complete_session(session_id)


@router.post(
    "/sessions/{session_id}/interrupt",
    response_model=SessionDTO,
    summary="Interrupt a running session",
    description="Interrupt an actively running session and stop Claude execution",
)
async def interrupt_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
    executor: SessionExecutor = Depends(get_session_executor),
) -> SessionDTO:
    """
    Interrupt a running session.

    Args:
        session_id: Session UUID
        service: Session service (injected)
        executor: Session executor (injected)

    Returns:
        Updated session

    Raises:
        404: Session not found
        409: Invalid state transition (not in working state)
    """
    logger.warning("INTERRUPT_SESSION_REQUEST_RECEIVED", session_id=str(session_id))

    # Interrupt Claude execution
    logger.warning("CALLING_EXECUTOR_INTERRUPT", session_id=str(session_id))
    await executor.interrupt(session_id)
    logger.warning("EXECUTOR_INTERRUPT_COMPLETED", session_id=str(session_id))

    # Update session status
    logger.warning("UPDATING_SESSION_STATUS_TO_INTERRUPTED", session_id=str(session_id))
    result = await service.interrupt_session(session_id)
    logger.warning(
        "SESSION_STATUS_UPDATED", session_id=str(session_id), new_status=result.status
    )
    return result


@router.post(
    "/sessions/{session_id}/resume",
    response_model=SessionDTO,
    summary="Resume a session",
    description="Resume a completed or failed session",
)
async def resume_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Resume a session.

    Args:
        session_id: Session UUID
        service: Session service (injected)

    Returns:
        Updated session

    Raises:
        404: Session not found
        409: Invalid state transition
    """
    logger.info("resume_session_request", session_id=str(session_id))
    return await service.resume_session(session_id)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session",
    description="Soft-delete a session",
)
async def delete_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> None:
    """
    Delete a session.

    Args:
        session_id: Session UUID
        service: Session service (injected)

    Raises:
        404: Session not found
    """
    logger.info("delete_session_request", session_id=str(session_id))
    await service.delete_session(session_id)


@router.patch(
    "/sessions/{session_id}/stage",
    response_model=SessionDTO,
    summary="Update session kanban stage",
    description="Update the kanban stage of a session",
)
async def update_session_stage(
    session_id: UUID,
    request: UpdateSessionStageRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionDTO:
    """
    Update session kanban stage.

    Args:
        session_id: Session UUID
        request: Stage update request
        service: Session service (injected)

    Returns:
        Updated session DTO

    Raises:
        404: Session not found
    """
    logger.info(
        "update_session_stage_request",
        session_id=str(session_id),
        new_stage=request.stage,
    )
    return await service.update_session_stage(session_id, request.stage)


@router.post(
    "/sessions/{session_id}/recreate",
    response_model=SessionDTO,
    summary="Recreate/reset a corrupted session",
    description="Recreate a corrupted or stuck session by resetting its state and clearing the Claude client",
)
async def recreate_session(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
    executor: "SessionExecutor" = Depends(get_session_executor),
) -> SessionDTO:
    """
    Recreate a corrupted or stuck session.

    This endpoint resets the session to a clean state by:
    - Deleting all messages (starts fresh conversation)
    - Clearing the claude_session_id (forces new client creation)
    - Resetting status to IDLE
    - Clearing error messages
    - Cleaning up queue state
    - Preserving project association and context

    Use this when:
    - Session is stuck in WORKING but not responding
    - Claude client is lost or corrupted
    - Session has persistent errors that prevent normal operation
    - Backend reload caused session state desync
    - User wants to start a new conversation

    Args:
        session_id: Session UUID to recreate
        service: Session service (injected)
        executor: SessionExecutor (injected)

    Returns:
        Recreated session DTO

    Raises:
        404: Session not found
    """
    logger.info("recreate_session_request", session_id=str(session_id))

    # Load session
    from app.infrastructure.database.repositories import (
        MessageRepositoryImpl,
    )

    async with get_repository_session() as db:
        session_repo = SessionRepositoryImpl(db)
        message_repo = MessageRepositoryImpl(db)
        session = await session_repo.get_by_id(session_id)

        if not session:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Session not found")

        # Store session info for logging
        old_status = session.status.value
        old_claude_session_id = session.claude_session_id
        had_error = bool(session.error_message)

        # Delete all messages for this session (start fresh)
        deleted_count = await message_repo.delete_by_session_id(session_id)
        logger.info(
            "deleted_session_messages", session_id=str(session_id), count=deleted_count
        )

        # Reset session to clean state
        session.status = SessionStatus.IDLE
        session.claude_session_id = None  # Force new client creation
        session.error_message = None

        # Update kanban stage to match IDLE status (waiting) - uses domain entity method
        session.sync_kanban_stage()

        # Persist changes
        await session_repo.update(session)

        # Create welcome message for supported session types
        from app.domain.config.welcome_messages import get_welcome_message

        message_config = get_welcome_message(session.session_type)
        if message_config:
            from uuid import uuid4
            from app.domain.entities import Message
            from app.domain.value_objects import MessageRole

            # Load agent name for attribution
            agent_name = message_config["default_name"]
            if session.agent_id:
                try:
                    from app.api.dependencies import get_agent_repository

                    agent_repo = get_agent_repository()
                    agent = await agent_repo.get_by_id(session.agent_id)
                    if agent:
                        agent_name = agent.name
                except Exception:
                    pass  # Use default if loading fails

            # Create welcome message
            welcome_message = Message(
                id=uuid4(),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=message_config["content"],
                sequence=0,
                agent_id=session.agent_id,
                agent_name=agent_name,
            )

            # Save to database
            await message_repo.create(welcome_message)

        await db.commit()

        logger.info(
            "session_recreated",
            session_id=str(session_id),
            old_status=old_status,
            new_status="idle",
            old_claude_session_id=old_claude_session_id,
            cleared_error=had_error,
            deleted_messages=deleted_count,
        )

    # Clean up executor state (queue, locks, processors)
    # Clear message queue if it exists
    if session_id in executor._message_queues:
        queue = executor._message_queues[session_id]
        queue_size = queue.qsize()
        # Drain queue
        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break
        logger.info(
            "cleared_message_queue", session_id=str(session_id), queue_size=queue_size
        )
        del executor._message_queues[session_id]

    # Clear processing flag
    if session_id in executor._processing:
        executor._processing[session_id] = False
        del executor._processing[session_id]

    # Cancel queue processor task if running
    if session_id in executor._queue_processors:
        task = executor._queue_processors[session_id]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        del executor._queue_processors[session_id]
        logger.info("stopped_queue_processor", session_id=str(session_id))

    # Clear session lock
    if session_id in executor._session_locks:
        del executor._session_locks[session_id]

    # Remove client from client manager (force recreation on next use)
    try:
        client_manager = executor._client_manager
        if (
            hasattr(client_manager, "_clients")
            and session_id in client_manager._clients
        ):
            # Close existing client gracefully
            client = client_manager._clients[session_id]
            if hasattr(client, "close"):
                try:
                    await client.close()
                except (AttributeError, RuntimeError) as close_error:
                    # Log but don't fail if close() fails
                    logger.debug("client_close_failed", error=str(close_error))
            del client_manager._clients[session_id]
            logger.info("removed_client_from_manager", session_id=str(session_id))
    except (AttributeError, KeyError) as e:
        # Client manager structure not as expected or session not in clients
        logger.warning(
            "failed_to_remove_client", session_id=str(session_id), error=str(e)
        )

    # Return updated session
    return await service.get_session(session_id)


@router.post(
    "/sessions/{session_id}/query",
    summary="Execute query with SSE streaming",
    description="Execute a query in the session with Server-Sent Events streaming for real-time updates",
)
async def execute_query(
    session_id: UUID,
    request: ExecuteQueryRequest,
    service: SessionService = Depends(get_session_service),
    agent_service: "AgentService" = Depends(get_agent_service),
    project_service: "ProjectService" = Depends(get_project_service),
    executor: "SessionExecutor" = Depends(get_session_executor),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Execute a query with Claude SDK streaming.

    This endpoint streams responses using Server-Sent Events (SSE) protocol.
    Each event contains a JSON payload with the message data.

    Args:
        session_id: Session UUID
        request: Query execution request
        service: Session service (injected)
        executor: SessionExecutor (injected)

    Returns:
        StreamingResponse with text/event-stream content type

    Raises:
        404: Session not found
        409: Invalid session state

    Example SSE events:
        event: stream_delta
        data: {"session_id": "...", "content": "Hello"}

        event: message_complete
        data: {"session_id": "..."}
    """
    from app.domain.value_objects import SessionStatus
    from app.infrastructure.database.connection import get_repository_session
    from app.infrastructure.database.repositories import (
        MessageRepositoryImpl,
        SessionRepositoryImpl,
    )

    logger.info(
        "execute_query_request",
        session_id=str(session_id),
        query_length=len(request.query),
        stream=request.stream,
    )

    # Verify session exists and is in valid state
    await service.get_session(session_id)

    # Get message service to save messages
    async with get_repository_session() as db:
        message_repo = MessageRepositoryImpl(db)
        session_repo = SessionRepositoryImpl(db)
        project_repo = ProjectRepositoryImpl(db)
        agent_repo = FileBasedAgentRepository(base_path=settings.agents_dir)

        message_service = MessageService(message_repo, session_repo)
        session_service = SessionService(session_repo, project_repo, agent_repo)

        # Get sender attribution from session service
        agent_id, agent_name = await session_service.get_sender_fields(session_id)

        # Save user message to database (user messages don't have agent_id)
        # sequence=0 is kept for backward compatibility but not used for ordering
        user_message = Message(
            id=uuid4(),
            session_id=session_id,
            role=MessageRole.USER,
            content=request.query,
            sequence=0,  # No longer used for ordering, kept for backward compatibility
            agent_id=None,  # User messages have no agent
            agent_name=None,
            from_instance_id=None,  # Same session
        )
        await message_service.save_message(user_message)
        await db.commit()
        logger.info("user_message_saved", message_id=str(user_message.id))

        # Broadcast user message event to SSE clients
        from app.infrastructure.sse.manager import sse_manager
        from app.infrastructure.claude.events import UserMessageEvent

        user_msg_event = UserMessageEvent(
            session_id=str(session_id),
            message_id=str(user_message.id),
            content=request.query,
            agent_id=None,
            agent_name=None,
            from_instance_id=None,
            timestamp=(
                user_message.created_at.isoformat() if user_message.created_at else None
            ),
        )
        await sse_manager.broadcast(session_id, user_msg_event.to_sse())

    async def event_generator():
        """Generate SSE events for query execution."""
        # Import SSE manager and asyncio
        from app.infrastructure.sse.manager import sse_manager
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        # Create event queue for this SSE connection
        event_queue: asyncio.Queue = asyncio.Queue()

        try:
            # Register SSE connection with manager
            await sse_manager.register(session_id, event_queue)
            logger.info("sse_client_registered", extra={"session_id": str(session_id)})

            # Update session status to WORKING
            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                db_session = await session_repo.get_by_id(session_id)
                if db_session:
                    # Transition to WORKING (from INITIALIZING or IDLE)
                    if db_session.status in [
                        SessionStatus.INITIALIZING,
                        SessionStatus.IDLE,
                    ]:
                        db_session.status = SessionStatus.WORKING
                        # Sync kanban stage with new status (uses domain entity method)
                        db_session.sync_kanban_stage()
                        await session_repo.update(db_session)
                        logger.info(
                            "session_status_updated",
                            session_id=str(session_id),
                            status=SessionStatus.WORKING.value,
                        )

                await db.commit()

            # Enqueue the message for execution (fire-and-forget)
            await executor.enqueue(
                session_id=session_id,
                message=request.query,
                sender_name=None,  # UI messages don't have sender attribution
                sender_session_id=None,
            )

            logger.info(
                "message_enqueued_for_ui", extra={"session_id": str(session_id)}
            )

            # Stream events from the queue as they arrive
            # Keep streaming until we receive a MessageCompleteEvent
            while True:
                try:
                    # Wait for next event from queue (with timeout)
                    event_dict = await asyncio.wait_for(
                        event_queue.get(), timeout=600.0
                    )  # 10 min timeout

                    # Convert dict back to SSE format
                    event_type = event_dict.get("event", "message")
                    event_data = event_dict.get("data", "{}")

                    sse_output = f"event: {event_type}\ndata: {event_data}\n\n"
                    yield sse_output

                    # Check if this is a completion event
                    if event_type == "message_complete":
                        logger.info(
                            "stream_complete", extra={"session_id": str(session_id)}
                        )
                        break

                    # Check for error events
                    if event_type == "error":
                        logger.warning(
                            "stream_error_event", extra={"session_id": str(session_id)}
                        )
                        break

                except asyncio.TimeoutError:
                    # No events for 10 minutes - session likely hung
                    logger.error(
                        "stream_timeout", extra={"session_id": str(session_id)}
                    )
                    yield f"event: error\ndata: {json.dumps({'session_id': str(session_id), 'error': 'Stream timeout'})}\n\n"
                    break

            # Small delay to ensure all SSE events are flushed to client
            await asyncio.sleep(0.1)

            # Update session status to IDLE
            await _update_session_status(session_id, executor)

        except Exception as e:
            logger.error(
                "sse_stream_failed",
                session_id=str(session_id),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            # Update session status to ERROR
            try:
                async with get_repository_session() as error_db:
                    error_session_repo = SessionRepositoryImpl(error_db)
                    error_db_session = await error_session_repo.get_by_id(session_id)
                    if error_db_session:
                        error_db_session.status = SessionStatus.ERROR
                        error_db_session.error_message = str(e)
                        await error_session_repo.update(error_db_session)
            except Exception as update_error:
                logger.error("failed_to_update_session_status", error=str(update_error))

            # Send error event
            yield f"event: error\ndata: {json.dumps({'session_id': str(session_id), 'error': str(e)})}\n\n"

        finally:
            # Always unregister SSE connection
            await sse_manager.unregister(session_id, event_queue)
            logger.info(
                "sse_client_unregistered", extra={"session_id": str(session_id)}
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/enqueue", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_message(
    session_id: UUID,
    request: ExecuteQueryRequest,
    service: SessionService = Depends(get_session_service),
    executor: SessionExecutor = Depends(get_session_executor),
) -> dict:
    """
    Enqueue a message for execution (queue-based architecture).

    This endpoint:
    - Saves the user message to database
    - Enqueues the message for processing
    - Returns immediately (fire-and-forget)

    Events are broadcasted via the separate /stream endpoint.
    """
    logger.info("enqueue_message_request", extra={"session_id": str(session_id)})

    # Verify session exists
    await service.get_session(session_id)

    # NOTE: Message will be saved by _process_queue when consumed from queue
    # This ensures consistent save behavior for both user and agent-to-agent messages

    # Update session status to WORKING (using service method)
    await service.transition_to_working(session_id)

    # Enqueue the message for execution
    await executor.enqueue(
        session_id=session_id,
        message=request.query,
        sender_name=None,
        sender_session_id=None,
    )

    logger.info("message_enqueued", extra={"session_id": str(session_id)})

    return {
        "status": "queued",
        "session_id": str(session_id),
        "queue_size": executor.get_queue_size(session_id),
    }


@router.get("/sessions/{session_id}/files/content")
async def get_session_file_content(
    session_id: UUID,
    file_path: str,
    service: SessionService = Depends(get_session_service),
    project_service: ProjectService = Depends(get_project_service),
):
    """
    Get file content as text for preview.

    Security: Files are restricted to the session's project directory only.
    """
    from pathlib import Path

    # Verify session exists and get project
    session = await service.get_session(session_id)

    if not session.project_id:
        raise HTTPException(status_code=400, detail="Session has no associated project")

    # Get project to determine allowed directory
    project = await project_service.get_project(session.project_id)

    # Project directory is the base allowed path
    project_dir = Path(project.path).resolve()

    # Resolve the requested file path
    if Path(file_path).is_absolute():
        target_file = Path(file_path).resolve()
    else:
        # Relative paths are resolved from project directory
        target_file = (project_dir / file_path).resolve()

    # SECURITY: Ensure file is within project directory (prevent path traversal)
    try:
        if not target_file.is_relative_to(project_dir):
            logger.warning(
                f"[FILE_CONTENT] Path traversal attempt blocked: {file_path} "
                f"(resolved to {target_file}, project: {project_dir})"
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied: File is outside project directory",
            )
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail="Access denied: Invalid file path")

    # Check if file exists
    if not target_file.exists():
        logger.warning(f"[FILE_CONTENT] File does not exist: {target_file}")
        raise HTTPException(status_code=404, detail="File not found")

    if not target_file.is_file():
        logger.warning(f"[FILE_CONTENT] Path is not a file: {target_file}")
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Read file content as text
    try:
        content = target_file.read_text(encoding="utf-8", errors="replace")
        logger.info(
            f"[FILE_CONTENT] ✓ Read {len(content)} chars from: {target_file} "
            f"(project: {project.name})"
        )

        return {"content": content, "path": str(target_file), "readonly": False}
    except Exception as e:
        logger.error(f"[FILE_CONTENT] Error reading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.get("/sessions/{session_id}/files/download")
async def download_session_file(
    session_id: UUID,
    file_path: str,
    service: SessionService = Depends(get_session_service),
    project_service: ProjectService = Depends(get_project_service),
):
    """
    Download a file from the session's project directory.

    Security: Files are restricted to the session's project directory only.
    """
    from pathlib import Path
    from fastapi.responses import FileResponse

    # Verify session exists and get project
    session = await service.get_session(session_id)

    if not session.project_id:
        raise HTTPException(status_code=400, detail="Session has no associated project")

    # Get project to determine allowed directory
    project = await project_service.get_project(session.project_id)

    # Project directory is the base allowed path
    project_dir = Path(project.path).resolve()

    # Resolve the requested file path
    if Path(file_path).is_absolute():
        target_file = Path(file_path).resolve()
    else:
        # Relative paths are resolved from project directory
        target_file = (project_dir / file_path).resolve()

    # SECURITY: Ensure file is within project directory (prevent path traversal)
    try:
        if not target_file.is_relative_to(project_dir):
            logger.warning(
                f"[DOWNLOAD] Path traversal attempt blocked: {file_path} "
                f"(resolved to {target_file}, project: {project_dir})"
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied: File is outside project directory",
            )
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail="Access denied: Invalid file path")

    # Check if file exists
    if not target_file.exists():
        logger.warning(f"[DOWNLOAD] File does not exist: {target_file}")
        raise HTTPException(status_code=404, detail="File not found")

    if not target_file.is_file():
        logger.warning(f"[DOWNLOAD] Path is not a file: {target_file}")
        raise HTTPException(status_code=400, detail="Path is not a file")

    logger.info(
        f"[DOWNLOAD] ✓ Downloading file: {target_file} (project: {project.name})"
    )

    # Return file
    return FileResponse(
        path=str(target_file),
        filename=target_file.name,
        media_type="application/octet-stream",
    )


@router.get("/sessions/{session_id}/stream")
async def stream_session_events(
    session_id: UUID,
    service: SessionService = Depends(get_session_service),
) -> StreamingResponse:
    """
    Open persistent SSE connection to receive all events for a session.

    This endpoint:
    - Opens a persistent SSE connection
    - Streams ALL events for the session (from all queued messages)
    - Stays open until client disconnects

    Use this endpoint ONCE per chat session, not per message.
    """
    logger.info("stream_session_events_request", extra={"session_id": str(session_id)})

    # Verify session exists
    await service.get_session(session_id)

    async def event_generator():
        """Generate SSE events for the entire session."""
        from app.infrastructure.sse.manager import sse_manager

        # Create event queue for this SSE connection
        event_queue: asyncio.Queue = asyncio.Queue()

        try:
            # Register SSE connection with manager
            await sse_manager.register(session_id, event_queue)
            logger.info("sse_stream_registered", extra={"session_id": str(session_id)})

            # Stream events indefinitely until client disconnects
            while True:
                try:
                    # Wait for next event (with timeout for keepalive)
                    event_dict = await asyncio.wait_for(event_queue.get(), timeout=30.0)

                    # Convert dict to SSE format
                    event_type = event_dict.get("event", "message")
                    event_data = event_dict.get("data", "{}")

                    sse_output = f"event: {event_type}\ndata: {event_data}\n\n"
                    yield sse_output

                except asyncio.TimeoutError:
                    # Send keepalive ping every 30 seconds
                    yield f"event: ping\ndata: {json.dumps({'type': 'keepalive'})}\n\n"

        except Exception as e:
            logger.error(
                "sse_stream_error",
                session_id=str(session_id),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        finally:
            # Unregister SSE connection
            await sse_manager.unregister(session_id, event_queue)
            logger.info(
                "sse_stream_unregistered", extra={"session_id": str(session_id)}
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
