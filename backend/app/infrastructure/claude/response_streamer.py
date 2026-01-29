"""Claude response streaming handler."""

from typing import AsyncIterator
from uuid import UUID

from app.core.logging import get_logger
from app.infrastructure.claude.events import (
    SSEEvent,
    ContentBlockStopEvent,
    MessageStartEvent,
    StreamDeltaEvent,
    MessageCompleteEvent,
)
from app.infrastructure.claude.text_buffer_manager import TextBufferManager

logger = get_logger(__name__)


class ClaudeResponseStreamer:
    """
    Handles streaming of Claude API responses and conversion to SSE events.

    Responsibilities:
    - Convert Claude SDK stream events to our SSE events
    - Buffer text deltas per content block
    - Flush complete text blocks at appropriate times
    - Handle message start/complete events
    """

    async def stream_and_convert(
        self,
        raw_stream: AsyncIterator,
        session_id: UUID,
        agent_id: str,
        agent_name: str | None,
    ) -> AsyncIterator[SSEEvent]:
        """
        Stream Claude responses and convert to SSE events.

        Args:
            raw_stream: Raw Claude SDK stream
            session_id: Session UUID
            agent_id: Agent identifier
            agent_name: Agent display name

        Yields:
            SSEEvent objects for broadcasting
        """
        buffer_manager = TextBufferManager()
        response_id = None

        try:
            async for event in raw_stream:
                logger.debug(
                    "received_stream_event",
                    extra={
                        "session_id": str(session_id),
                        "event_type": type(event).__name__,
                    },
                )

                # Handle text deltas - buffer them
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
                        response_id or "unknown",
                    )
                    if flushed_event:
                        yield flushed_event
                    yield event
                    continue

                # Track response ID from message start
                if isinstance(event, MessageStartEvent):
                    response_id = event.response_id
                    yield event
                    continue

                # Flush remaining buffers on message complete
                if isinstance(event, MessageCompleteEvent):
                    for remaining_event in buffer_manager.flush_all_buffers(
                        session_id, agent_id, agent_name, response_id or "unknown"
                    ):
                        yield remaining_event
                    buffer_manager.clear()
                    yield event
                    continue

                # Pass through all other events
                yield event

        except Exception as e:
            logger.error(
                "stream_processing_error",
                extra={
                    "session_id": str(session_id),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

    async def cleanup_streaming(
        self,
        session_id: UUID,
        buffer_manager: TextBufferManager,
        agent_id: str,
        agent_name: str | None,
        response_id: str,
    ) -> list[SSEEvent]:
        """
        Clean up streaming resources and flush remaining buffers.

        Args:
            session_id: Session UUID
            buffer_manager: Text buffer manager to flush
            agent_id: Agent identifier
            agent_name: Agent display name
            response_id: Response identifier

        Returns:
            List of remaining SSE events from flushed buffers
        """
        events = []

        # Flush all remaining text buffers
        for event in buffer_manager.flush_all_buffers(
            session_id, agent_id, agent_name, response_id
        ):
            events.append(event)

        buffer_manager.clear()

        logger.info(
            "streaming_cleanup_complete",
            extra={
                "session_id": str(session_id),
                "flushed_events": len(events),
            },
        )

        return events
