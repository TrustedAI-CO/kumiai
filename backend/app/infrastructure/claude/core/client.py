"""
Claude SDK client wrapper.

Wraps the claude_agent_sdk.ClaudeSDKClient with additional functionality:
- Session ID capture from init messages
- Timeout protection
- Health monitoring
- Structured logging
"""

import asyncio
from typing import AsyncIterator, AsyncIterable, Optional, Union

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from app.core.logging import get_logger
from app.infrastructure.claude.exceptions import (
    ClaudeConnectionError,
    ClaudeExecutionError,
)

logger = get_logger(__name__)


class ClaudeClient:
    """
    Wrapper for ClaudeSDKClient with enhanced functionality.

    Provides session ID capture, timeout protection, and health monitoring
    for Claude SDK operations.
    """

    def __init__(self, options: ClaudeAgentOptions, timeout_seconds: int = 30) -> None:
        """
        Initialize Claude client wrapper.

        Args:
            options: Configuration options for Claude SDK
            timeout_seconds: Connection timeout in seconds (default: 30)
        """
        self._options = options
        self._timeout_seconds = timeout_seconds
        self._client = ClaudeSDKClient(options=options)
        self._session_id: Optional[str] = None
        self._connected = False

        logger.info(
            "claude_client_initialized",
            model=getattr(options, "model", None),
            cwd=getattr(options, "cwd", None),
        )

    async def connect(self) -> None:
        """
        Connect to Claude SDK with timeout protection.

        Raises:
            ClaudeConnectionError: If connection fails or times out
        """
        try:
            logger.info("claude_sdk_connecting", timeout=self._timeout_seconds)

            await asyncio.wait_for(
                self._client.connect(),
                timeout=self._timeout_seconds,
            )

            self._connected = True
            logger.info("claude_sdk_connected")

        except asyncio.TimeoutError as e:
            logger.error(
                "claude_connection_timeout",
                timeout=self._timeout_seconds,
            )
            raise ClaudeConnectionError(
                f"Connection timeout after {self._timeout_seconds} seconds"
            ) from e
        except Exception as e:
            logger.error(
                "claude_connection_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ClaudeConnectionError(f"Connection failed: {e}") from e

    async def query(self, message: Union[str, AsyncIterable[dict[str, any]]]) -> None:
        """
        Send a query message to Claude.

        Args:
            message: Message text to send, or async iterable of message dicts
                    for streaming input

        Raises:
            ClaudeExecutionError: If query fails
        """
        try:
            if isinstance(message, str):
                logger.debug("claude_query_sent", message_length=len(message))
            else:
                logger.debug("claude_streaming_query_sent")
            await self._client.query(message)

        except Exception as e:
            logger.error(
                "claude_query_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ClaudeExecutionError(f"Query failed: {e}") from e

    async def receive_messages(self) -> AsyncIterator[dict]:
        """
        Stream response messages from Claude.

        Automatically captures session_id from StreamEvent.

        Yields:
            Message objects from Claude SDK (StreamEvent, AssistantMessage, etc.)

        Raises:
            ClaudeExecutionError: If message streaming fails
        """

        try:
            async for message in self._client.receive_messages():
                # Debug logging to understand message structure
                message_type = type(message).__name__

                # Capture session_id from first message (init message)
                if not self._session_id:
                    # Try multiple ways to get session_id
                    captured_session_id = None

                    # Method 1: message.session_id (direct attribute)
                    if hasattr(message, "session_id"):
                        captured_session_id = message.session_id
                        logger.info(
                            "session_id_found_as_attribute",
                            session_id=captured_session_id,
                            message_type=message_type,
                        )

                    # Method 2: message.data['session_id'] (legacy way)
                    if not captured_session_id:
                        session_data = getattr(message, "data", {})
                        if isinstance(session_data, dict):
                            captured_session_id = session_data.get("session_id")
                            if captured_session_id:
                                logger.info(
                                    "session_id_found_in_data",
                                    session_id=captured_session_id,
                                    message_type=message_type,
                                )

                    # Log first few messages to help debug
                    logger.info(
                        "message_received_for_session_capture",
                        message_type=message_type,
                        has_session_id_attr=hasattr(message, "session_id"),
                        has_data_attr=hasattr(message, "data"),
                        session_id_captured=bool(captured_session_id),
                    )

                    if captured_session_id:
                        self._session_id = captured_session_id
                        logger.info(
                            "session_id_captured",
                            session_id=captured_session_id,
                        )

                yield message

        except Exception as e:
            logger.error(
                "claude_receive_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ClaudeExecutionError(f"Message streaming failed: {e}") from e

    async def interrupt(self) -> None:
        """
        Interrupt current Claude execution.

        Note: After interrupt, the client should be recreated as it enters
        a broken state (pattern from legacy implementation).

        Raises:
            ClaudeExecutionError: If interrupt fails
        """
        try:
            logger.info("claude_interrupt_requested")
            await self._client.interrupt()
            logger.info("claude_interrupt_completed")

        except Exception as e:
            logger.error(
                "claude_interrupt_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ClaudeExecutionError(f"Interrupt failed: {e}") from e

    def is_alive(self) -> bool:
        """
        Check if the Claude SDK subprocess is still alive.

        Returns:
            bool: True if subprocess is running, False otherwise
        """
        if not self._connected:
            return False

        # Check subprocess health via transport
        if hasattr(self._client, "_transport"):
            transport = self._client._transport
            if hasattr(transport, "_process") and transport._process:
                process = transport._process
                if hasattr(process, "returncode"):
                    if process.returncode is not None:
                        logger.warning(
                            "claude_subprocess_died",
                            returncode=process.returncode,
                        )
                        return False

        return True

    async def disconnect(self) -> None:
        """
        Disconnect and cleanup Claude SDK client.

        Raises:
            ClaudeExecutionError: If disconnect fails
        """
        try:
            if self._connected:
                logger.info("claude_disconnecting")
                await self._client.disconnect()
                self._connected = False
                logger.info("claude_disconnected")

        except Exception as e:
            logger.error(
                "claude_disconnect_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ClaudeExecutionError(f"Disconnect failed: {e}") from e

    def get_session_id(self) -> Optional[str]:
        """
        Get the captured Claude session ID.

        Returns:
            Optional[str]: Session ID if captured, None otherwise
        """
        return self._session_id
