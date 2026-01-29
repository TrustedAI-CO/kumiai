"""Background queue processor for handling batched messages."""

import asyncio
from typing import List, Optional
from uuid import UUID
from collections import defaultdict

from app.core.logging import get_logger
from app.infrastructure.claude.types import QueuedMessage, StopStreamingSignal

logger = get_logger(__name__)


class MessageQueueProcessor:
    """
    Handles background processing of queued messages.

    Responsibilities:
    - Wait for messages with timeout
    - Collect batches of messages
    - Group and merge messages by sender
    - Manage processing state
    """

    def __init__(self):
        """Initialize the queue processor."""
        self._message_queues: dict[UUID, asyncio.Queue] = {}
        self._processing: dict[UUID, bool] = {}

    def ensure_queue_exists(self, session_id: UUID) -> None:
        """Ensure message queue exists for session."""
        if session_id not in self._message_queues:
            self._message_queues[session_id] = asyncio.Queue()
            self._processing[session_id] = False
            logger.info("created_message_queue", extra={"session_id": str(session_id)})

    def get_queue(self, session_id: UUID) -> asyncio.Queue:
        """Get the queue for a session."""
        return self._message_queues.get(session_id)

    def get_queue_size(self, session_id: UUID) -> int:
        """Get current queue size for a session."""
        if session_id in self._message_queues:
            return self._message_queues[session_id].qsize()
        return 0

    def is_processing(self, session_id: UUID) -> bool:
        """Check if session is currently processing."""
        return self._processing.get(session_id, False)

    def set_processing(self, session_id: UUID, value: bool) -> None:
        """Set processing state for session."""
        self._processing[session_id] = value

    async def wait_for_first_message(
        self, session_id: UUID, timeout: float = 300.0
    ) -> Optional[QueuedMessage]:
        """
        Wait for first message in queue with timeout.

        Args:
            session_id: Session UUID
            timeout: Timeout in seconds (default 300s = 5min)

        Returns:
            First queued message, or None if timeout or stop signal
        """
        queue = self._message_queues.get(session_id)
        if not queue:
            return None

        logger.info(
            "queue_processor_waiting_for_message",
            session_id=str(session_id),
            queue_size=queue.qsize(),
        )

        try:
            first_msg = await asyncio.wait_for(queue.get(), timeout=timeout)
            logger.info(
                "queue_processor_received_first_message",
                session_id=str(session_id),
                queue_size_after_get=queue.qsize(),
            )

            # Check if stop signal
            if isinstance(first_msg, StopStreamingSignal):
                logger.warning(
                    "received_stop_signal_as_first_message",
                    extra={"session_id": str(session_id)},
                )
                queue.task_done()
                return None

            return first_msg

        except asyncio.TimeoutError:
            logger.info(
                "queue_processor_timeout", extra={"session_id": str(session_id)}
            )
            return None

    async def collect_message_batch(
        self, session_id: UUID, first_msg: QueuedMessage
    ) -> List[QueuedMessage]:
        """
        Collect all messages currently in queue (batching).

        Args:
            session_id: Session UUID
            first_msg: First message already retrieved from queue

        Returns:
            List of all messages in the batch
        """
        queue = self._message_queues.get(session_id)
        if not queue:
            return [first_msg]

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
            queue_size_after=queue.qsize(),
        )

        return batch_messages

    def group_messages_by_sender(
        self, batch_messages: List[QueuedMessage]
    ) -> dict[str, List[QueuedMessage]]:
        """
        Group messages by sender.

        Args:
            batch_messages: List of queued messages

        Returns:
            Dictionary mapping sender key to list of messages
        """
        grouped_messages = defaultdict(list)
        for queued_msg in batch_messages:
            sender_key = (
                str(queued_msg.sender_session_id)
                if queued_msg.sender_session_id
                else "user"
            )
            grouped_messages[sender_key].append(queued_msg)
        return grouped_messages

    async def clear_queue(self, session_id: UUID) -> int:
        """
        Clear all messages from queue.

        Args:
            session_id: Session UUID

        Returns:
            Number of messages cleared
        """
        if session_id not in self._message_queues:
            return 0

        queue = self._message_queues[session_id]
        queue_size = queue.qsize()

        while not queue.empty():
            try:
                queue.get_nowait()
                queue.task_done()
            except asyncio.QueueEmpty:
                break

        logger.info(
            "message_queue_cleared",
            extra={"session_id": str(session_id), "cleared_messages": queue_size},
        )

        return queue_size
