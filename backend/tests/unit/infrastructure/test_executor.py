"""Tests for SessionExecutor."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.infrastructure.claude.executor import SessionExecutor
from app.infrastructure.claude.exceptions import (
    ClaudeExecutionError,
    ClientNotFoundError,
)
from app.infrastructure.claude.events import (
    ContentBlockEvent,
    MessageCompleteEvent,
)
from app.infrastructure.database.models import Session
from app.domain.value_objects import SessionType


@pytest.fixture
def mock_client_manager():
    """Create mock ClaudeClientManager."""
    manager = Mock()
    manager.get_client = AsyncMock()
    manager.create_client = AsyncMock()
    manager.create_client_from_session = AsyncMock()
    return manager


@pytest.fixture
def executor(mock_client_manager):
    """Create SessionExecutor with mocked client manager."""
    return SessionExecutor(client_manager=mock_client_manager)


@pytest.fixture
def mock_claude_client():
    """Create mock ClaudeClient."""
    client = Mock()
    client.query = AsyncMock()
    client.receive_messages = AsyncMock()
    client.get_session_id = Mock(return_value="claude-session-123")
    return client


@pytest.fixture
def mock_session_entity():
    """Create mock Session entity."""
    session = Mock(spec=Session)
    session.id = uuid4()
    session.session_type = SessionType.ASSISTANT
    session.agent_id = "test-agent"
    session.project_id = None
    return session


class TestSessionExecutor:
    """Tests for SessionExecutor.execute()."""

    @pytest.mark.asyncio
    async def test_execute_with_existing_client(
        self, executor, mock_client_manager, mock_claude_client
    ):
        """Test execute uses existing client if available."""
        session_id = uuid4()

        # Mock existing client
        mock_client_manager.get_client.return_value = mock_claude_client

        # Mock message stream with actual Claude SDK type
        from claude_agent_sdk import types

        test_message = types.StreamEvent(
            uuid="evt-1",
            session_id="claude-session-1",
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Hello"},
            },
        )

        async def mock_stream():
            yield test_message

        mock_claude_client.receive_messages = mock_stream

        # Execute
        events = []
        async for event in executor.execute(
            session_id=session_id,
            user_message="Test message",
            agent_id="test-agent",
            project_path=".",
        ):
            events.append(event)

        # Verify
        mock_client_manager.get_client.assert_called_once_with(session_id)
        mock_client_manager.create_client.assert_not_called()
        mock_claude_client.query.assert_called_once_with("Test message")

        # Executor buffers deltas and emits ContentBlockEvent at completion
        assert len(events) == 1
        assert isinstance(events[0], ContentBlockEvent)
        assert events[0].content == "Hello"
        assert events[0].block_type == "text"

    @pytest.mark.asyncio
    async def test_execute_creates_client_if_not_exists(
        self,
        executor,
        mock_client_manager,
        mock_claude_client,
        mock_session_entity,
        tmp_path,
    ):
        """Test execute creates client lazily if it doesn't exist."""
        session_id = uuid4()
        mock_session_entity.id = session_id

        # Mock client not found, then created
        mock_client_manager.get_client.side_effect = ClientNotFoundError(
            "Client not found"
        )
        mock_client_manager.create_client_from_session.return_value = mock_claude_client

        # Mock message stream with actual Claude SDK type
        from claude_agent_sdk import types

        test_message = types.StreamEvent(
            uuid="evt-2",
            session_id="claude-session-2",
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Created!"},
            },
        )

        async def mock_stream():
            yield test_message

        mock_claude_client.receive_messages = mock_stream

        # Mock database session repository
        with patch(
            "app.infrastructure.database.connection.get_repository_session"
        ) as mock_get_repo:
            mock_db = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_session_entity)
            mock_get_repo.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.infrastructure.database.repositories.SessionRepositoryImpl"
            ) as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Execute
                events = []
                async for event in executor.execute(
                    session_id=session_id,
                    user_message="Test message",
                    agent_id="test-agent",
                    project_path=str(tmp_path),
                    resume_session_id="old-session-123",
                ):
                    events.append(event)

        # Verify client creation
        mock_client_manager.create_client_from_session.assert_called_once()
        call_args = mock_client_manager.create_client_from_session.call_args
        assert call_args.kwargs["session"] == mock_session_entity
        assert call_args.kwargs["resume_session"] == "old-session-123"

        assert len(events) == 1
        assert events[0].content == "Created!"

    @pytest.mark.asyncio
    async def test_execute_streams_multiple_events(
        self, executor, mock_client_manager, mock_claude_client
    ):
        """Test execute streams multiple events."""
        session_id = uuid4()
        mock_client_manager.get_client.return_value = mock_claude_client

        # Mock multiple messages with actual Claude SDK types
        from claude_agent_sdk import types

        message1 = types.StreamEvent(
            uuid="evt-3",
            session_id="claude-session-3",
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Hello "},
            },
        )

        message2 = types.StreamEvent(
            uuid="evt-4",
            session_id="claude-session-3",
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "world!"},
            },
        )

        message3 = types.StreamEvent(
            uuid="evt-5",
            session_id="claude-session-3",
            event={"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
        )

        message4 = types.StreamEvent(
            uuid="evt-6", session_id="claude-session-3", event={"type": "message_stop"}
        )

        async def mock_stream():
            yield message1
            yield message2
            yield message3
            yield message4

        mock_claude_client.receive_messages = mock_stream

        # Execute
        events = []
        async for event in executor.execute(
            session_id=session_id,
            user_message="Test",
            agent_id="test-agent",
        ):
            events.append(event)

        # Should have 2 events: 1 buffered content block + 1 completion
        # (text deltas are buffered and emitted as single ContentBlockEvent)
        assert len(events) == 2
        assert isinstance(events[0], ContentBlockEvent)
        assert events[0].content == "Hello world!"  # Buffered from both deltas
        assert events[0].block_type == "text"
        assert isinstance(events[1], MessageCompleteEvent)

    @pytest.mark.asyncio
    async def test_execute_handles_empty_message_stream(
        self, executor, mock_client_manager, mock_claude_client
    ):
        """Test execute handles empty message stream."""
        session_id = uuid4()
        mock_client_manager.get_client.return_value = mock_claude_client

        async def mock_empty_stream():
            # Empty stream
            return
            yield  # Make it async generator

        mock_claude_client.receive_messages = mock_empty_stream

        # Execute
        events = []
        async for event in executor.execute(
            session_id=session_id,
            user_message="Test",
            agent_id="test-agent",
        ):
            events.append(event)

        # Should have no events
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_execute_raises_on_client_creation_failure(
        self, executor, mock_client_manager, mock_session_entity
    ):
        """Test execute raises error if client creation fails."""
        session_id = uuid4()
        mock_session_entity.id = session_id

        # Mock client not found
        mock_client_manager.get_client.side_effect = ClientNotFoundError(
            "Client not found"
        )

        # Mock client creation failure
        mock_client_manager.create_client_from_session.side_effect = Exception(
            "Connection failed"
        )

        # Mock database session repository
        with patch(
            "app.infrastructure.database.connection.get_repository_session"
        ) as mock_get_repo:
            mock_db = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_session_entity)
            mock_get_repo.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.infrastructure.database.repositories.SessionRepositoryImpl"
            ) as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Execute should raise
                with pytest.raises(ClaudeExecutionError) as exc_info:
                    async for _ in executor.execute(
                        session_id=session_id,
                        user_message="Test",
                        agent_id="test-agent",
                    ):
                        pass

        assert "Failed to create client" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_on_query_failure(
        self, executor, mock_client_manager, mock_claude_client
    ):
        """Test execute raises error if query fails."""
        session_id = uuid4()
        mock_client_manager.get_client.return_value = mock_claude_client

        # Mock query failure
        mock_claude_client.query.side_effect = Exception("Query failed")

        # Execute should raise
        with pytest.raises(ClaudeExecutionError) as exc_info:
            async for _ in executor.execute(
                session_id=session_id,
                user_message="Test",
                agent_id="test-agent",
            ):
                pass

        assert "Execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_on_streaming_failure(
        self, executor, mock_client_manager, mock_claude_client
    ):
        """Test execute raises error if streaming fails."""
        session_id = uuid4()
        mock_client_manager.get_client.return_value = mock_claude_client

        # Mock streaming failure
        async def mock_failing_stream():
            raise Exception("Streaming error")
            yield  # Make it async generator

        mock_claude_client.receive_messages = mock_failing_stream

        # Execute should raise
        with pytest.raises(ClaudeExecutionError) as exc_info:
            async for _ in executor.execute(
                session_id=session_id,
                user_message="Test",
                agent_id="test-agent",
            ):
                pass

        assert "Execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_with_different_project_paths(
        self,
        executor,
        mock_client_manager,
        mock_claude_client,
        mock_session_entity,
        tmp_path,
    ):
        """Test execute uses correct project path."""
        session_id = uuid4()
        mock_session_entity.id = session_id
        custom_path = tmp_path / "custom"
        custom_path.mkdir()

        mock_client_manager.get_client.side_effect = ClientNotFoundError(
            "Client not found"
        )
        mock_client_manager.create_client_from_session.return_value = mock_claude_client

        async def mock_stream():
            return
            yield

        mock_claude_client.receive_messages = mock_stream

        # Mock database session repository
        with patch(
            "app.infrastructure.database.connection.get_repository_session"
        ) as mock_get_repo:
            mock_db = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_session_entity)
            mock_get_repo.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.infrastructure.database.repositories.SessionRepositoryImpl"
            ) as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Execute with custom project path
                async for _ in executor.execute(
                    session_id=session_id,
                    user_message="Test",
                    agent_id="test-agent",
                    project_path=str(custom_path),
                ):
                    pass

        # Verify project path passed to create_client_from_session
        call_args = mock_client_manager.create_client_from_session.call_args
        assert str(call_args.kwargs["project_path"]) == str(custom_path)

    @pytest.mark.asyncio
    async def test_execute_with_resume_session(
        self, executor, mock_client_manager, mock_claude_client, mock_session_entity
    ):
        """Test execute passes resume_session to client creation."""
        session_id = uuid4()
        mock_session_entity.id = session_id

        mock_client_manager.get_client.side_effect = ClientNotFoundError(
            "Client not found"
        )
        mock_client_manager.create_client_from_session.return_value = mock_claude_client

        async def mock_stream():
            return
            yield

        mock_claude_client.receive_messages = mock_stream

        # Mock database session repository
        with patch(
            "app.infrastructure.database.connection.get_repository_session"
        ) as mock_get_repo:
            mock_db = AsyncMock()
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_session_entity)
            mock_get_repo.return_value.__aenter__.return_value = mock_db

            with patch(
                "app.infrastructure.database.repositories.SessionRepositoryImpl"
            ) as mock_repo_class:
                mock_repo_class.return_value = mock_repo

                # Execute with resume session
                async for _ in executor.execute(
                    session_id=session_id,
                    user_message="Test",
                    agent_id="test-agent",
                    resume_session_id="resume-123",
                ):
                    pass

        # Verify resume_session passed
        call_args = mock_client_manager.create_client_from_session.call_args
        assert call_args.kwargs["resume_session"] == "resume-123"


class TestGetClaudeSessionId:
    """Tests for get_claude_session_id()."""

    @pytest.mark.asyncio
    async def test_get_session_id_with_existing_client(
        self, executor, mock_client_manager, mock_claude_client
    ):
        """Test getting session ID from existing client."""
        session_id = uuid4()
        mock_client_manager.get_client.return_value = mock_claude_client
        mock_claude_client.get_session_id.return_value = "claude-session-123"

        result = await executor.get_claude_session_id(session_id)

        assert result == "claude-session-123"
        mock_client_manager.get_client.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_session_id_without_client(self, executor, mock_client_manager):
        """Test getting session ID when client doesn't exist."""
        session_id = uuid4()
        mock_client_manager.get_client.side_effect = ClientNotFoundError(
            "Client not found"
        )

        result = await executor.get_claude_session_id(session_id)

        assert result is None
