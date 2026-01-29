"""
Unit tests for ClaudeClient wrapper.

Tests the Claude SDK client wrapper functionality including:
- Connection with timeout
- Query sending
- Message streaming with session ID capture
- Health checking
- Disconnection
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from claude_agent_sdk import ClaudeAgentOptions

from app.infrastructure.claude.client import ClaudeClient
from app.infrastructure.claude.exceptions import (
    ClaudeConnectionError,
    ClaudeExecutionError,
)


@pytest.fixture
def mock_options():
    """Create mock ClaudeAgentOptions."""
    options = MagicMock(spec=ClaudeAgentOptions)
    options.model = "claude-sonnet-4"
    options.cwd = "/test/path"
    return options


@pytest.fixture
def mock_sdk_client():
    """Create mock ClaudeSDKClient."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.query = AsyncMock()
    client.interrupt = AsyncMock()
    client.disconnect = AsyncMock()
    return client


class TestClaudeClient:
    """Tests for ClaudeClient wrapper."""

    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    def test_init(self, mock_sdk_class, mock_options):
        """Test ClaudeClient initialization."""
        mock_sdk_instance = MagicMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options, timeout_seconds=30)

        assert client._options == mock_options
        assert client._timeout_seconds == 30
        assert client._client == mock_sdk_instance
        assert client._session_id is None
        assert client._connected is False
        mock_sdk_class.assert_called_once_with(options=mock_options)

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_connect_success(self, mock_sdk_class, mock_options):
        """Test successful connection with timeout."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.connect = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options, timeout_seconds=30)

        await client.connect()

        assert client._connected is True
        mock_sdk_instance.connect.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_connect_timeout(self, mock_sdk_class, mock_options):
        """Test connection timeout raises ClaudeConnectionError."""

        async def slow_connect():
            await asyncio.sleep(100)

        mock_sdk_instance = AsyncMock()
        # Simulate timeout by making connect hang
        mock_sdk_instance.connect = slow_connect
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options, timeout_seconds=0.1)

        with pytest.raises(ClaudeConnectionError, match="Connection timeout"):
            await client.connect()

        assert client._connected is False

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_connect_failure(self, mock_sdk_class, mock_options):
        """Test connection failure raises ClaudeConnectionError."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.connect = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options, timeout_seconds=30)

        with pytest.raises(ClaudeConnectionError, match="Connection failed"):
            await client.connect()

        assert client._connected is False

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_query_sends_message(self, mock_sdk_class, mock_options):
        """Test query sends message to SDK."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.query = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        await client.query("Hello, Claude!")

        mock_sdk_instance.query.assert_called_once_with("Hello, Claude!")

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_query_failure(self, mock_sdk_class, mock_options):
        """Test query failure raises ClaudeExecutionError."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.query = AsyncMock(side_effect=Exception("Query failed"))
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        with pytest.raises(ClaudeExecutionError, match="Query failed"):
            await client.query("Hello")

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_receive_messages_captures_session_id(
        self, mock_sdk_class, mock_options
    ):
        """Test receive_messages captures session_id from StreamEvent."""
        from claude_agent_sdk import types

        # Create StreamEvent with session_id
        stream_event = types.StreamEvent(
            uuid="evt-1", session_id="test-session-123", event={"type": "message_start"}
        )

        # Create content message
        content_event = types.StreamEvent(
            uuid="evt-2",
            session_id="test-session-123",
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Hello"},
            },
        )

        async def mock_receive():
            yield stream_event
            yield content_event

        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.receive_messages = mock_receive
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        messages = []
        async for message in client.receive_messages():
            messages.append(message)

        assert len(messages) == 2
        assert client.get_session_id() == "test-session-123"

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_receive_messages_without_init(self, mock_sdk_class, mock_options):
        """Test receive_messages without init message."""
        content_message = MagicMock()
        content_message.subtype = "content"

        async def mock_receive():
            yield content_message

        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.receive_messages = mock_receive
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        messages = []
        async for message in client.receive_messages():
            messages.append(message)

        assert len(messages) == 1
        assert client.get_session_id() is None

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_receive_messages_failure(self, mock_sdk_class, mock_options):
        """Test receive_messages failure raises ClaudeExecutionError."""

        async def mock_receive():
            raise Exception("Streaming failed")
            yield  # Make it a generator

        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.receive_messages = mock_receive
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        with pytest.raises(ClaudeExecutionError, match="Message streaming failed"):
            async for _ in client.receive_messages():
                pass

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_interrupt(self, mock_sdk_class, mock_options):
        """Test interrupt calls SDK interrupt."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.interrupt = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        await client.interrupt()

        mock_sdk_instance.interrupt.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_interrupt_failure(self, mock_sdk_class, mock_options):
        """Test interrupt failure raises ClaudeExecutionError."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.interrupt = AsyncMock(
            side_effect=Exception("Interrupt failed")
        )
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        with pytest.raises(ClaudeExecutionError, match="Interrupt failed"):
            await client.interrupt()

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_is_alive_not_connected(self, mock_sdk_class, mock_options):
        """Test is_alive returns False when not connected."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        assert client.is_alive() is False

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_is_alive_subprocess_running(self, mock_sdk_class, mock_options):
        """Test is_alive returns True when subprocess is running."""
        # Create mock subprocess
        mock_process = MagicMock()
        mock_process.returncode = None  # Still running

        mock_transport = MagicMock()
        mock_transport._process = mock_process

        mock_sdk_instance = AsyncMock()
        mock_sdk_instance._transport = mock_transport
        mock_sdk_instance.connect = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)
        await client.connect()

        assert client.is_alive() is True

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_is_alive_subprocess_died(self, mock_sdk_class, mock_options):
        """Test is_alive returns False when subprocess has died."""
        # Create mock subprocess that died
        mock_process = MagicMock()
        mock_process.returncode = 1  # Process exited

        mock_transport = MagicMock()
        mock_transport._process = mock_process

        mock_sdk_instance = AsyncMock()
        mock_sdk_instance._transport = mock_transport
        mock_sdk_instance.connect = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)
        await client.connect()

        assert client.is_alive() is False

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_disconnect(self, mock_sdk_class, mock_options):
        """Test disconnect calls SDK disconnect."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.connect = AsyncMock()
        mock_sdk_instance.disconnect = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)
        await client.connect()

        await client.disconnect()

        assert client._connected is False
        mock_sdk_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_disconnect_when_not_connected(self, mock_sdk_class, mock_options):
        """Test disconnect when not connected doesn't call SDK."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.disconnect = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        await client.disconnect()

        mock_sdk_instance.disconnect.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_disconnect_failure(self, mock_sdk_class, mock_options):
        """Test disconnect failure raises ClaudeExecutionError."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_instance.connect = AsyncMock()
        mock_sdk_instance.disconnect = AsyncMock(
            side_effect=Exception("Disconnect failed")
        )
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)
        await client.connect()

        with pytest.raises(ClaudeExecutionError, match="Disconnect failed"):
            await client.disconnect()

    @pytest.mark.asyncio
    @patch("app.infrastructure.claude.client.ClaudeSDKClient")
    async def test_get_session_id_before_capture(self, mock_sdk_class, mock_options):
        """Test get_session_id returns None before capture."""
        mock_sdk_instance = AsyncMock()
        mock_sdk_class.return_value = mock_sdk_instance

        client = ClaudeClient(mock_options)

        assert client.get_session_id() is None
