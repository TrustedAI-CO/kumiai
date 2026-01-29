"""
Test Claude SDK message types to document actual structure.

This test file documents the ACTUAL message types returned by the Claude SDK,
not our assumptions. It serves as both documentation and validation.
"""

from claude_agent_sdk import types


class TestClaudeSDKMessageTypes:
    """Document actual Claude SDK message type structures."""

    def test_stream_event_structure(self):
        """
        StreamEvent contains streaming updates during execution.

        Structure:
        - uuid: str - Unique event identifier
        - session_id: str - Claude session identifier
        - event: dict - Raw Anthropic API stream event (content_block_delta, etc.)
        - parent_tool_use_id: str | None - Parent tool if nested
        """
        # Create a sample StreamEvent
        stream_event = types.StreamEvent(
            uuid="evt-123",
            session_id="session-456",
            event={
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Hello"},
            },
            parent_tool_use_id=None,
        )

        assert stream_event.uuid == "evt-123"
        assert stream_event.session_id == "session-456"
        assert stream_event.event["type"] == "content_block_delta"
        assert stream_event.event["delta"]["text"] == "Hello"
        assert stream_event.parent_tool_use_id is None

    def test_assistant_message_structure(self):
        """
        AssistantMessage contains complete assistant responses.

        Structure:
        - content: list[TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock]
        - model: str - Model identifier
        - parent_tool_use_id: str | None - Parent tool if nested
        - error: Optional[Literal[...]] - Error type if failed
        """
        # Create sample AssistantMessage with TextBlock
        text_block = types.TextBlock(text="Hello, I'm Claude!")

        assistant_msg = types.AssistantMessage(
            content=[text_block],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        assert len(assistant_msg.content) == 1
        assert isinstance(assistant_msg.content[0], types.TextBlock)
        assert assistant_msg.content[0].text == "Hello, I'm Claude!"
        assert assistant_msg.model == "claude-3-5-sonnet-20241022"
        assert assistant_msg.error is None

    def test_assistant_message_with_tool_use(self):
        """AssistantMessage can contain ToolUseBlock for tool execution."""
        text_block = types.TextBlock(text="Let me read that file for you.")
        tool_block = types.ToolUseBlock(
            id="tool-abc123", name="read_file", input={"file_path": "/path/to/file.txt"}
        )

        assistant_msg = types.AssistantMessage(
            content=[text_block, tool_block],
            model="claude-3-5-sonnet-20241022",
            parent_tool_use_id=None,
            error=None,
        )

        assert len(assistant_msg.content) == 2
        assert isinstance(assistant_msg.content[0], types.TextBlock)
        assert isinstance(assistant_msg.content[1], types.ToolUseBlock)
        assert assistant_msg.content[1].id == "tool-abc123"
        assert assistant_msg.content[1].name == "read_file"

    def test_user_message_structure(self):
        """
        UserMessage represents user input or tool results.

        Structure:
        - content: str | list[TextBlock | ...] - Message content
        - uuid: str | None - Message identifier
        - parent_tool_use_id: str | None - Parent tool if tool result
        """
        user_msg = types.UserMessage(
            content="Hello, Claude!", uuid="msg-789", parent_tool_use_id=None
        )

        assert user_msg.content == "Hello, Claude!"
        assert user_msg.uuid == "msg-789"
        assert user_msg.parent_tool_use_id is None

    def test_text_block_structure(self):
        """TextBlock contains simple text content."""
        block = types.TextBlock(text="Hello world!")

        assert block.text == "Hello world!"

    def test_tool_use_block_structure(self):
        """ToolUseBlock contains tool execution request."""
        block = types.ToolUseBlock(
            id="tool-xyz",
            name="write_file",
            input={"file_path": "/tmp/test.txt", "content": "Test content"},
        )

        assert block.id == "tool-xyz"
        assert block.name == "write_file"
        assert block.input["file_path"] == "/tmp/test.txt"

    def test_tool_result_block_structure(self):
        """ToolResultBlock contains tool execution results."""
        # Success result
        success_block = types.ToolResultBlock(
            tool_use_id="tool-xyz", content="File written successfully", is_error=False
        )

        assert success_block.tool_use_id == "tool-xyz"
        assert success_block.content == "File written successfully"
        assert success_block.is_error is False

        # Error result
        error_block = types.ToolResultBlock(
            tool_use_id="tool-abc", content="File not found", is_error=True
        )

        assert error_block.tool_use_id == "tool-abc"
        assert error_block.is_error is True

    def test_stream_event_content_block_delta(self):
        """StreamEvent with content_block_delta for text streaming."""
        event = types.StreamEvent(
            uuid="evt-1",
            session_id="sess-1",
            event={
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "streaming text..."},
            },
        )

        assert event.event["type"] == "content_block_delta"
        assert event.event["delta"]["type"] == "text_delta"
        assert "streaming text..." in event.event["delta"]["text"]

    def test_stream_event_message_start(self):
        """StreamEvent with message_start event."""
        event = types.StreamEvent(
            uuid="evt-2",
            session_id="sess-1",
            event={
                "type": "message_start",
                "message": {
                    "id": "msg_123",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-3-5-sonnet-20241022",
                },
            },
        )

        assert event.event["type"] == "message_start"
        assert event.event["message"]["role"] == "assistant"

    def test_stream_event_content_block_start(self):
        """StreamEvent with content_block_start for text or tool."""
        # Text block start
        text_start = types.StreamEvent(
            uuid="evt-3",
            session_id="sess-1",
            event={
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        )

        assert text_start.event["type"] == "content_block_start"
        assert text_start.event["content_block"]["type"] == "text"

        # Tool use block start
        tool_start = types.StreamEvent(
            uuid="evt-4",
            session_id="sess-1",
            event={
                "type": "content_block_start",
                "index": 1,
                "content_block": {
                    "type": "tool_use",
                    "id": "tool-123",
                    "name": "read_file",
                    "input": {},
                },
            },
        )

        assert tool_start.event["type"] == "content_block_start"
        assert tool_start.event["content_block"]["type"] == "tool_use"

    def test_stream_event_content_block_stop(self):
        """StreamEvent with content_block_stop marks block completion."""
        event = types.StreamEvent(
            uuid="evt-5",
            session_id="sess-1",
            event={"type": "content_block_stop", "index": 0},
        )

        assert event.event["type"] == "content_block_stop"
        assert event.event["index"] == 0

    def test_stream_event_message_delta(self):
        """StreamEvent with message_delta for stop reason."""
        event = types.StreamEvent(
            uuid="evt-6",
            session_id="sess-1",
            event={"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
        )

        assert event.event["type"] == "message_delta"
        assert event.event["delta"]["stop_reason"] == "end_turn"

    def test_stream_event_message_stop(self):
        """StreamEvent with message_stop marks message completion."""
        event = types.StreamEvent(
            uuid="evt-7", session_id="sess-1", event={"type": "message_stop"}
        )

        assert event.event["type"] == "message_stop"

    def test_system_message_structure(self):
        """
        SystemMessage represents system information (init, etc.).

        Structure:
        - subtype: str - System message subtype (e.g., 'init')
        - data: dict - System data (cwd, session_id, tools, etc.)
        """
        # SystemMessage is used for init and system info
        # We don't create these directly, just document the structure
        # that we receive from Claude SDK
        pass

    def test_result_message_structure(self):
        """
        ResultMessage represents execution summary.

        Structure:
        - subtype: str - Result subtype (e.g., 'success', 'error')
        - duration_ms: int - Total execution time
        - is_error: bool - Whether execution failed
        - session_id: str - Claude session ID
        - usage: dict - Token usage statistics
        """
        # ResultMessage is sent at end of execution
        # We don't create these directly, just document the structure
        pass


class TestClaudeSDKMessageTypeUnion:
    """Test that receive_messages returns union of message types."""

    def test_receive_messages_return_type_includes_all_types(self):
        """
        receive_messages() returns:
        UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent

        Our converter must handle all these types.
        """
        # Document the types we need to handle
        valid_types = [
            types.UserMessage,
            types.AssistantMessage,
            types.StreamEvent,
            types.SystemMessage,
            types.ResultMessage,
        ]

        # Verify all types are importable
        for msg_type in valid_types:
            assert msg_type is not None
            assert hasattr(msg_type, "__name__")
