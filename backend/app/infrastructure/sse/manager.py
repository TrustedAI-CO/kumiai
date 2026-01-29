"""
SSE Manager Service

Manages active Server-Sent Events (SSE) connections for real-time event broadcasting.
Allows SessionExecutor to broadcast events to connected frontend clients.
"""

import asyncio
import logging
from typing import Dict, List, Any
from uuid import UUID

logger = logging.getLogger(__name__)


class SSEManager:
    """Manage active SSE connections for real-time event broadcasting."""

    def __init__(self):
        """Initialize SSE manager with empty connection registry."""
        self._connections: Dict[UUID, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        logger.info("sse_manager_initialized")

    async def register(self, session_id: UUID, event_queue: asyncio.Queue) -> None:
        """
        Register an SSE connection for a session.

        Args:
            session_id: Session UUID
            event_queue: Queue to receive events for this connection
        """
        async with self._lock:
            if session_id not in self._connections:
                self._connections[session_id] = []

            self._connections[session_id].append(event_queue)
            connection_count = len(self._connections[session_id])

            logger.info(
                "sse_connection_registered",
                extra={
                    "session_id": str(session_id),
                    "connection_count": connection_count,
                },
            )

    async def unregister(self, session_id: UUID, event_queue: asyncio.Queue) -> None:
        """
        Unregister an SSE connection.

        Args:
            session_id: Session UUID
            event_queue: Queue to remove
        """
        async with self._lock:
            if session_id in self._connections:
                try:
                    self._connections[session_id].remove(event_queue)
                    connection_count = len(self._connections[session_id])

                    logger.info(
                        "sse_connection_unregistered",
                        extra={
                            "session_id": str(session_id),
                            "remaining_connections": connection_count,
                        },
                    )

                    # Clean up empty connection lists
                    if not self._connections[session_id]:
                        del self._connections[session_id]
                        logger.debug(
                            "sse_connection_list_removed",
                            extra={"session_id": str(session_id)},
                        )

                except ValueError:
                    logger.warning(
                        "sse_unregister_nonexistent",
                        extra={"session_id": str(session_id)},
                    )

    async def broadcast(self, session_id: UUID, event: Dict[str, Any]) -> None:
        """
        Broadcast event to all connected SSE clients for a session.

        Args:
            session_id: Target session UUID
            event: Event dictionary to broadcast
        """
        async with self._lock:
            if session_id not in self._connections:
                logger.debug(
                    "sse_no_connections",
                    extra={"session_id": str(session_id)},
                )
                return

            connection_count = len(self._connections[session_id])
            logger.debug(
                "sse_broadcasting_event",
                extra={
                    "session_id": str(session_id),
                    "event_type": event.get("type", "unknown"),
                    "connection_count": connection_count,
                },
            )

            # Send to all queues
            failed_queues = []
            for queue in self._connections[session_id]:
                try:
                    # Put event without timeout - queue is unbounded so this should be instant
                    # If queue.put() blocks, it means the queue object itself is corrupted
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    # This should never happen with unbounded queue
                    logger.error(
                        "sse_queue_unexpectedly_full",
                        extra={
                            "session_id": str(session_id),
                            "event_type": event.get("type"),
                            "queue_size": queue.qsize(),
                        },
                    )
                    failed_queues.append(queue)
                except Exception as e:
                    logger.error(
                        "sse_broadcast_error",
                        extra={
                            "session_id": str(session_id),
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
                    failed_queues.append(queue)

            # Remove failed queues
            if failed_queues:
                for queue in failed_queues:
                    try:
                        self._connections[session_id].remove(queue)
                    except ValueError:
                        pass

    def get_connection_count(self, session_id: UUID) -> int:
        """
        Get number of active SSE connections for a session.

        Args:
            session_id: Session UUID

        Returns:
            Number of active connections
        """
        if session_id not in self._connections:
            return 0
        return len(self._connections[session_id])

    def has_connections(self, session_id: UUID) -> bool:
        """
        Check if session has any active SSE connections.

        Args:
            session_id: Session UUID

        Returns:
            True if session has active connections, False otherwise
        """
        return self.get_connection_count(session_id) > 0


# Global singleton instance
sse_manager = SSEManager()
