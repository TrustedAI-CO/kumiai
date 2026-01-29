"""Text buffer manager for streaming Claude responses."""

from typing import Dict, List, Optional
from uuid import UUID

from app.core.logging import get_logger
from app.infrastructure.claude.events import ContentBlockEvent, StreamDeltaEvent

logger = get_logger(__name__)


class TextBufferManager:
    """
    Manages text buffering for streaming Claude responses.

    Buffers text deltas per content block and flushes them at appropriate times
    to create complete text blocks.
    """

    def __init__(self):
        """Initialize empty text buffers."""
        self._text_buffers: Dict[int, List[str]] = {}

    def buffer_delta(self, event: StreamDeltaEvent) -> None:
        """
        Buffer a text delta event.

        Args:
            event: Stream delta event containing text chunk
        """
        idx = event.content_index
        if idx not in self._text_buffers:
            self._text_buffers[idx] = []
        self._text_buffers[idx].append(event.content)

    def flush_buffer(
        self,
        idx: int,
        session_id: UUID,
        agent_id: str,
        agent_name: Optional[str],
        response_id: str,
    ) -> Optional[ContentBlockEvent]:
        """
        Flush a specific text buffer and return a content block event.

        Args:
            idx: Content block index to flush
            session_id: Session UUID
            agent_id: Agent ID
            agent_name: Agent name
            response_id: Response ID

        Returns:
            ContentBlockEvent with complete text, or None if buffer is empty
        """
        if idx in self._text_buffers and self._text_buffers[idx]:
            buffer = self._text_buffers[idx]
            complete_text = "".join(buffer)
            logger.debug(
                "flushing_text_block",
                extra={
                    "session_id": str(session_id),
                    "block_length": len(complete_text),
                    "content_index": idx,
                },
            )
            event = ContentBlockEvent(
                session_id=str(session_id),
                content=complete_text,
                block_type="text",
                agent_id=agent_id,
                agent_name=agent_name,
                response_id=response_id,
            )
            del self._text_buffers[idx]
            return event
        return None

    def flush_all_buffers(
        self,
        session_id: UUID,
        agent_id: str,
        agent_name: Optional[str],
        response_id: str,
    ) -> List[ContentBlockEvent]:
        """
        Flush all remaining text buffers.

        Args:
            session_id: Session UUID
            agent_id: Agent ID
            agent_name: Agent name
            response_id: Response ID

        Returns:
            List of ContentBlockEvents with complete text
        """
        events = []
        if self._text_buffers:
            for idx in sorted(self._text_buffers.keys()):
                buffer = self._text_buffers[idx]
                if buffer:
                    complete_text = "".join(buffer)
                    logger.debug(
                        "flushing_final_text_block",
                        extra={
                            "session_id": str(session_id),
                            "block_length": len(complete_text),
                            "content_index": idx,
                        },
                    )
                    events.append(
                        ContentBlockEvent(
                            session_id=str(session_id),
                            content=complete_text,
                            block_type="text",
                            agent_id=agent_id,
                            agent_name=agent_name,
                            response_id=response_id,
                        )
                    )
            self._text_buffers.clear()
        return events

    def clear(self) -> None:
        """Clear all buffers."""
        self._text_buffers.clear()
