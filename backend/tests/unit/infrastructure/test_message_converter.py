"""Tests for Claude SDK message converter."""

from claude_agent_sdk import types

from app.infrastructure.claude.message_converter import convert_message_to_events
from app.infrastructure.claude.events import (
    StreamDeltaEvent,
    ToolUseEvent,
    ToolCompleteEvent,
    MessageStartEvent,
    ErrorEvent,
)


class TestMessageConverter:
    """Test message conversion from Claude SDK types to SSE events."""

    def test_stream_event_with_text_delta(self):
        """StreamEvent with content_block_delta produces StreamDeltaEvent."""
        stream_event = types.StreamEvent(
            uuid="evt-1",
            session_id="claude-session-1",
            event={
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Hello world!"},
            },
        )

        events = convert_message_to_events(stream_event, "session-123")

        assert len(events) == 1
        assert isinstance(events[0], StreamDeltaEvent)
        assert events[0].session_id == "session-123"
        assert events[0].content == "Hello world!"

    def test_stream_event_with_empty_text_delta(self):
        """StreamEvent with empty text produces no events."""
        stream_event = types.StreamEvent(
            uuid="evt-2",
            session_id="claude-session-1",
            event={
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": ""},
            },
        )

        events = convert_message_to_events(stream_event, "session-123")

        assert len(events) == 0

    def test_stream_event_with_tool_use_start(self):
        """StreamEvent with content_block_start for tool produces ToolUseEvent."""
        stream_event = types.StreamEvent(
            uuid="evt-3",
            session_id="claude-session-1",
            event={
                "type": "content_block_start",
                "index": 1,
                "content_block": {
                    "type": "tool_use",
                    "id": "tool-abc123",
                    "name": "read_file",
                    "input": {"file_path": "/path/to/file.txt"},
                },
            },
        )

        events = convert_message_to_events(stream_event, "session-123")

        # Tool use is NOT extracted at start (input may be incomplete)
        # Complete tool use comes from AssistantMessage with full input
        assert len(events) == 0

    def test_stream_event_with_message_stop(self):
        """StreamEvent with message_stop produces NO events (just logged)."""
        stream_event = types.StreamEvent(
            uuid="evt-4", session_id="claude-session-1", event={"type": "message_stop"}
        )

        events = convert_message_to_events(stream_event, "session-123")

        # message_stop is just logged, not used for completion detection
        # Completion is detected via message_delta with stop_reason="end_turn"
        assert len(events) == 0

    def test_stream_event_with_message_start(self):
        """StreamEvent with message_start produces MessageStartEvent."""
        stream_event = types.StreamEvent(
            uuid="evt-start",
            session_id="claude-session-1",
            event={"type": "message_start"},
        )

        events = convert_message_to_events(stream_event, "session-123")
        assert len(events) == 1
        assert isinstance(events[0], MessageStartEvent)

    def test_stream_event_with_content_block_stop(self):
        """StreamEvent with content_block_stop produces ContentBlockStopEvent."""
        from app.infrastructure.claude.events import ContentBlockStopEvent

        stream_event = types.StreamEvent(
            uuid="evt-stop",
            session_id="claude-session-1",
            event={"type": "content_block_stop", "index": 0},
        )

        events = convert_message_to_events(stream_event, "session-123")
        assert len(events) == 1
        assert isinstance(events[0], ContentBlockStopEvent)
        assert events[0].content_index == 0

    def test_stream_event_with_message_delta_without_end_turn(self):
        """StreamEvent with message_delta (no end_turn) produces no events."""
        stream_event = types.StreamEvent(
            uuid="evt-delta",
            session_id="claude-session-1",
            event={"type": "message_delta", "delta": {"stop_reason": "tool_use"}},
        )

        events = convert_message_to_events(stream_event, "session-123")
        # Only end_turn produces completion event, tool_use does not
        assert len(events) == 0

    def test_assistant_message_with_text_block(self):
        """AssistantMessage with TextBlock produces NO events (already streamed)."""
        text_block = types.TextBlock(text="Hello from Claude!")
        assistant_msg = types.AssistantMessage(
            content=[text_block],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        # TextBlocks are skipped - already streamed via content_block_delta
        assert len(events) == 0

    def test_assistant_message_with_multiple_text_blocks(self):
        """AssistantMessage with multiple TextBlocks produces NO events (already streamed)."""
        blocks = [
            types.TextBlock(text="First block. "),
            types.TextBlock(text="Second block."),
        ]
        assistant_msg = types.AssistantMessage(
            content=blocks,
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        # TextBlocks are skipped - already streamed via content_block_delta
        assert len(events) == 0

    def test_assistant_message_with_tool_use_block(self):
        """AssistantMessage with ToolUseBlock produces ToolUseEvent."""
        tool_block = types.ToolUseBlock(
            id="tool-xyz",
            name="write_file",
            input={"file_path": "/tmp/test.txt", "content": "Test"},
        )
        assistant_msg = types.AssistantMessage(
            content=[tool_block],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        assert len(events) == 1
        assert isinstance(events[0], ToolUseEvent)
        assert events[0].tool_use_id == "tool-xyz"
        assert events[0].tool_name == "write_file"

    def test_assistant_message_with_text_and_tool(self):
        """AssistantMessage with TextBlock and ToolUseBlock produces both events."""
        blocks = [
            types.TextBlock(text="Let me read that file."),
            types.ToolUseBlock(
                id="tool-123", name="read_file", input={"file_path": "/path/file.txt"}
            ),
        ]
        assistant_msg = types.AssistantMessage(
            content=blocks,
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        # Only ToolUseEvent - TextBlock is skipped (already streamed)
        assert len(events) == 1
        assert isinstance(events[0], ToolUseEvent)
        assert events[0].tool_name == "read_file"

    def test_assistant_message_with_tool_result_block(self):
        """AssistantMessage with ToolResultBlock produces ToolCompleteEvent."""
        tool_result = types.ToolResultBlock(
            tool_use_id="tool-123", content="File read successfully", is_error=False
        )
        assistant_msg = types.AssistantMessage(
            content=[tool_result],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        assert len(events) == 1
        assert isinstance(events[0], ToolCompleteEvent)
        assert events[0].tool_use_id == "tool-123"

    def test_assistant_message_with_error(self):
        """AssistantMessage with error produces ErrorEvent."""
        assistant_msg = types.AssistantMessage(
            content=[],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error="rate_limit",
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        assert len(events) == 1
        assert isinstance(events[0], ErrorEvent)
        assert "rate_limit" in events[0].error

    def test_user_message_produces_no_events(self):
        """UserMessage produces no events (just logged)."""
        user_msg = types.UserMessage(
            content="Hello!", uuid="msg-123", parent_tool_use_id=None
        )

        events = convert_message_to_events(user_msg, "session-123")

        assert len(events) == 0

    def test_system_message_produces_no_events(self):
        """SystemMessage produces no events (just logged)."""
        system_msg = types.SystemMessage(
            subtype="init", data={"session_id": "test-123", "cwd": "/path"}
        )

        events = convert_message_to_events(system_msg, "session-123")

        assert len(events) == 0

    def test_result_message_produces_no_events(self):
        """ResultMessage produces no events (just logged)."""
        result_msg = types.ResultMessage(
            subtype="success",
            duration_ms=100,
            duration_api_ms=50,
            is_error=False,
            num_turns=1,
            session_id="test-123",
            total_cost_usd=0.001,
            usage={"input_tokens": 10, "output_tokens": 20},
        )

        events = convert_message_to_events(result_msg, "session-123")

        assert len(events) == 0

    def test_unicode_text_handling(self):
        """Messages with Unicode text are handled correctly."""
        stream_event = types.StreamEvent(
            uuid="evt-unicode",
            session_id="claude-session-1",
            event={
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Hello 世界! 🌍"},
            },
        )

        events = convert_message_to_events(stream_event, "session-123")

        assert len(events) == 1
        assert events[0].content == "Hello 世界! 🌍"

    def test_complex_tool_input(self):
        """Tool use with complex nested input structure from AssistantMessage."""
        # Tool use comes from AssistantMessage, not content_block_start
        tool_block = types.ToolUseBlock(
            id="tool-complex",
            name="complex_tool",
            input={
                "nested": {"array": [1, 2, 3], "object": {"key": "value"}},
                "unicode": "测试",
            },
        )
        assistant_msg = types.AssistantMessage(
            content=[tool_block],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        events = convert_message_to_events(assistant_msg, "session-123")

        assert len(events) == 1
        assert isinstance(events[0], ToolUseEvent)
        assert events[0].tool_input["nested"]["array"] == [1, 2, 3]
        assert events[0].tool_input["unicode"] == "测试"
