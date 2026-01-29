"""Message API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_message_service
from app.application.dtos.base import PaginatedResult
from app.application.dtos.message_dto import MessageDTO
from app.application.dtos.requests import CreateMessageRequest
from app.application.services import MessageService
from app.core.logging import get_logger
from app.domain.entities import Message
from app.domain.value_objects import MessageRole

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=PaginatedResult[MessageDTO],
    summary="Get messages for a session",
    description="Retrieve messages for a session with cursor-based pagination",
)
async def get_session_messages(
    session_id: UUID,
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of messages per page"
    ),
    cursor: Optional[str] = Query(
        None, description="Cursor for pagination (ISO timestamp)"
    ),
    service: MessageService = Depends(get_message_service),
) -> PaginatedResult[MessageDTO]:
    """
    Get messages for a session with cursor-based pagination.

    Args:
        session_id: Session UUID
        limit: Maximum number of messages to return (default: 50, max: 100)
        cursor: Optional cursor for pagination (ISO timestamp of last message)
        service: Message service (injected)

    Returns:
        Paginated result with messages ordered by created_at timestamp

    Raises:
        404: Session not found
        400: Invalid cursor format
    """
    return await service.get_messages(session_id, limit=limit, cursor=cursor)


@router.get(
    "/messages/{message_id}",
    response_model=MessageDTO,
    summary="Get message by ID",
    description="Retrieve a specific message by its UUID",
)
async def get_message(
    message_id: UUID,
    service: MessageService = Depends(get_message_service),
) -> MessageDTO:
    """
    Get message by ID.

    Args:
        message_id: Message UUID
        service: Message service (injected)

    Returns:
        Message details

    Raises:
        404: Message not found
    """
    return await service.get_message(message_id)


@router.post(
    "/messages",
    response_model=MessageDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Save a single message",
    description="Save a single message to a session",
)
async def save_message(
    request: CreateMessageRequest,
    service: MessageService = Depends(get_message_service),
) -> MessageDTO:
    """
    Save a single message.

    Args:
        request: Message creation request
        service: Message service (injected)

    Returns:
        Saved message

    Raises:
        404: Session not found
        400: Validation error
    """
    logger.info(
        "save_message_request",
        session_id=str(request.session_id),
        role=request.role,
        sequence=request.sequence,
    )
    # Convert request to domain entity
    message = Message(
        id=request.id,
        session_id=request.session_id,
        role=MessageRole(request.role),
        content=request.content,
        sequence=request.sequence,
        tool_use_id=request.tool_use_id,
        metadata=request.metadata or {},
        agent_id=request.agent_id,
        agent_name=request.agent_name,
        from_instance_id=request.from_instance_id,
    )
    result = await service.save_message(message)
    return result  # Service already returns MessageDTO


@router.post(
    "/messages/batch",
    response_model=List[MessageDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Batch save messages",
    description="Save multiple messages in a single transaction",
)
async def save_batch_messages(
    requests: List[CreateMessageRequest],
    service: MessageService = Depends(get_message_service),
) -> List[MessageDTO]:
    """
    Batch save messages.

    Args:
        requests: List of message creation requests
        service: Message service (injected)

    Returns:
        List of saved messages

    Raises:
        404: Session not found for any message
        400: Validation error
    """
    logger.info(
        "save_batch_messages_request",
        count=len(requests),
        session_ids=list(set(str(r.session_id) for r in requests)),
    )
    # Convert requests to domain entities
    messages = [
        Message(
            id=req.id,
            session_id=req.session_id,
            role=MessageRole(req.role),
            content=req.content,
            sequence=req.sequence,
            tool_use_id=req.tool_use_id,
            metadata=req.metadata or {},
            agent_id=req.agent_id,
            agent_name=req.agent_name,
            from_instance_id=req.from_instance_id,
        )
        for req in requests
    ]
    results = await service.save_batch(messages)
    return results  # Service already returns List[MessageDTO]


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a message",
    description="Soft-delete a message",
)
async def delete_message(
    message_id: UUID,
    service: MessageService = Depends(get_message_service),
) -> None:
    """
    Delete a message (soft delete).

    Args:
        message_id: Message UUID
        service: Message service (injected)

    Raises:
        404: Message not found
    """
    logger.info("delete_message_request", message_id=str(message_id))
    await service.delete_message(message_id)
