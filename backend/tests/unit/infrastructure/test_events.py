"""Tests for SSE event types."""

import json

from app.infrastructure.claude.events import (
    StreamDeltaEvent,
    ToolUseEvent,
    ToolCompleteEvent,
    MessageCompleteEvent,
    ResultEvent,
    ErrorEvent,
)


class TestStreamDeltaEvent:
    """Tests for StreamDeltaEvent."""

    def test_create_event(self):
        """Test creating a stream delta event."""
        event = StreamDeltaEvent(session_id="test-session", content="Hello world")

        assert event.session_id == "test-session"
        assert event.content == "Hello world"
        assert event.type == "stream_delta"

    def test_to_sse_format(self):
        """Test converting to SSE format."""
        event = StreamDeltaEvent(session_id="test-session", content="Hello")

        sse = event.to_sse()

        assert sse["event"] == "stream_delta"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"
        assert data["content"] == "Hello"

    def test_to_sse_with_special_characters(self):
        """Test SSE format with special characters in content."""
        event = StreamDeltaEvent(
            session_id="test-session", content='Line 1\nLine 2\n"quoted"'
        )

        sse = event.to_sse()
        data = json.loads(sse["data"])

        # JSON encoding should handle special chars
        assert data["content"] == 'Line 1\nLine 2\n"quoted"'

    def test_to_sse_with_unicode(self):
        """Test SSE format with unicode content."""
        event = StreamDeltaEvent(session_id="test-session", content="Hello 世界 🌍")

        sse = event.to_sse()
        data = json.loads(sse["data"])

        assert data["content"] == "Hello 世界 🌍"


class TestToolUseEvent:
    """Tests for ToolUseEvent."""

    def test_create_event(self):
        """Test creating a tool use event."""
        event = ToolUseEvent(
            session_id="test-session",
            tool_use_id="tool-123",
            tool_name="read_file",
            tool_input={"file_path": "/test/file.txt"},
        )

        assert event.session_id == "test-session"
        assert event.tool_use_id == "tool-123"
        assert event.tool_name == "read_file"
        assert event.tool_input == {"file_path": "/test/file.txt"}
        assert event.type == "tool_use"

    def test_to_sse_format(self):
        """Test converting to SSE format."""
        event = ToolUseEvent(
            session_id="test-session",
            tool_use_id="tool-123",
            tool_name="bash",
            tool_input={"command": "ls -la"},
        )

        sse = event.to_sse()

        assert sse["event"] == "tool_use"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"
        assert data["tool_use_id"] == "tool-123"
        assert data["tool_name"] == "bash"
        assert data["tool_input"]["command"] == "ls -la"

    def test_to_sse_with_complex_input(self):
        """Test SSE format with complex tool input."""
        event = ToolUseEvent(
            session_id="test-session",
            tool_use_id="tool-123",
            tool_name="complex_tool",
            tool_input={
                "nested": {"key": "value"},
                "array": [1, 2, 3],
                "string": "test",
            },
        )

        sse = event.to_sse()
        data = json.loads(sse["data"])

        assert data["tool_input"]["nested"]["key"] == "value"
        assert data["tool_input"]["array"] == [1, 2, 3]


class TestToolCompleteEvent:
    """Tests for ToolCompleteEvent."""

    def test_create_event(self):
        """Test creating a tool complete event."""
        event = ToolCompleteEvent(session_id="test-session", tool_use_id="tool-123")

        assert event.session_id == "test-session"
        assert event.tool_use_id == "tool-123"
        assert event.type == "tool_complete"

    def test_to_sse_format(self):
        """Test converting to SSE format."""
        event = ToolCompleteEvent(session_id="test-session", tool_use_id="tool-123")

        sse = event.to_sse()

        assert sse["event"] == "tool_complete"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"
        assert data["tool_use_id"] == "tool-123"


class TestMessageCompleteEvent:
    """Tests for MessageCompleteEvent."""

    def test_create_event(self):
        """Test creating a message complete event."""
        event = MessageCompleteEvent(session_id="test-session")

        assert event.session_id == "test-session"
        assert event.type == "message_complete"

    def test_to_sse_format(self):
        """Test converting to SSE format."""
        event = MessageCompleteEvent(session_id="test-session")

        sse = event.to_sse()

        assert sse["event"] == "message_complete"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"


class TestResultEvent:
    """Tests for ResultEvent."""

    def test_create_event(self):
        """Test creating a result event."""
        event = ResultEvent(
            session_id="test-session", result="Task completed successfully"
        )

        assert event.session_id == "test-session"
        assert event.result == "Task completed successfully"
        assert event.type == "result"

    def test_to_sse_format(self):
        """Test converting to SSE format."""
        event = ResultEvent(session_id="test-session", result="All done!")

        sse = event.to_sse()

        assert sse["event"] == "result"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"
        assert data["result"] == "All done!"


class TestErrorEvent:
    """Tests for ErrorEvent."""

    def test_create_event_with_message_only(self):
        """Test creating an error event with just message."""
        event = ErrorEvent(session_id="test-session", error="Something went wrong")

        assert event.session_id == "test-session"
        assert event.error == "Something went wrong"
        assert event.error_type is None
        assert event.type == "error"

    def test_create_event_with_type(self):
        """Test creating an error event with error type."""
        event = ErrorEvent(
            session_id="test-session",
            error="Connection failed",
            error_type="ClaudeConnectionError",
        )

        assert event.session_id == "test-session"
        assert event.error == "Connection failed"
        assert event.error_type == "ClaudeConnectionError"

    def test_to_sse_format_without_type(self):
        """Test SSE format without error type."""
        event = ErrorEvent(session_id="test-session", error="Error occurred")

        sse = event.to_sse()

        assert sse["event"] == "error"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"
        assert data["error"] == "Error occurred"
        assert "error_type" not in data

    def test_to_sse_format_with_type(self):
        """Test SSE format with error type."""
        event = ErrorEvent(
            session_id="test-session",
            error="Execution failed",
            error_type="ClaudeExecutionError",
        )

        sse = event.to_sse()

        assert sse["event"] == "error"
        data = json.loads(sse["data"])
        assert data["session_id"] == "test-session"
        assert data["error"] == "Execution failed"
        assert data["error_type"] == "ClaudeExecutionError"


class TestEventTypeFields:
    """Tests for event type discrimination."""

    def test_all_events_have_type_field(self):
        """Test that all events have a type field."""
        events = [
            StreamDeltaEvent("s1", "content"),
            ToolUseEvent("s1", "t1", "tool", {}),
            ToolCompleteEvent("s1", "t1"),
            MessageCompleteEvent("s1"),
            ResultEvent("s1", "result"),
            ErrorEvent("s1", "error"),
        ]

        for event in events:
            assert hasattr(event, "type")
            assert event.type is not None

    def test_all_events_have_to_sse_method(self):
        """Test that all events have to_sse method."""
        events = [
            StreamDeltaEvent("s1", "content"),
            ToolUseEvent("s1", "t1", "tool", {}),
            ToolCompleteEvent("s1", "t1"),
            MessageCompleteEvent("s1"),
            ResultEvent("s1", "result"),
            ErrorEvent("s1", "error"),
        ]

        for event in events:
            assert hasattr(event, "to_sse")
            assert callable(event.to_sse)

    def test_all_sse_outputs_have_event_and_data(self):
        """Test that all SSE outputs have event and data fields."""
        events = [
            StreamDeltaEvent("s1", "content"),
            ToolUseEvent("s1", "t1", "tool", {}),
            ToolCompleteEvent("s1", "t1"),
            MessageCompleteEvent("s1"),
            ResultEvent("s1", "result"),
            ErrorEvent("s1", "error"),
        ]

        for event in events:
            sse = event.to_sse()
            assert "event" in sse
            assert "data" in sse
            # Data should be valid JSON
            assert isinstance(json.loads(sse["data"]), dict)

    def test_all_sse_data_includes_session_id(self):
        """Test that all SSE data includes session_id."""
        events = [
            StreamDeltaEvent("test-session", "content"),
            ToolUseEvent("test-session", "t1", "tool", {}),
            ToolCompleteEvent("test-session", "t1"),
            MessageCompleteEvent("test-session"),
            ResultEvent("test-session", "result"),
            ErrorEvent("test-session", "error"),
        ]

        for event in events:
            sse = event.to_sse()
            data = json.loads(sse["data"])
            assert data["session_id"] == "test-session"
