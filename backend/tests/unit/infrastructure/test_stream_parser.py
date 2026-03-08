"""Tests for non-Claude stream parser compatibility."""

import json

from app.infrastructure.cli.stream_parser import (
    parse_codex_stream_event,
    parse_gemini_stream_event,
    parse_stream_line,
)


class TestCodexStreamParser:
    """Ensure Codex wrapper events are parsed into unified ParsedEvent objects."""

    def test_thread_started_maps_to_init(self):
        event = parse_codex_stream_event(
            {"type": "thread.started", "thread_id": "thread-123"}
        )
        assert event is not None
        assert event.event_type == "init"
        assert event.session_id == "thread-123"

    def test_item_completed_agent_message_text(self):
        event = parse_codex_stream_event(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "hello"},
            }
        )
        assert event is not None
        assert event.event_type == "text"
        assert event.content == "hello"

    def test_item_completed_message_content_output_text(self):
        event = parse_codex_stream_event(
            {
                "type": "item.completed",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "Hello"},
                        {"type": "output_text", "text": " world"},
                    ],
                },
            }
        )
        assert event is not None
        assert event.event_type == "text"
        assert event.content == "Hello world"

    def test_response_output_text_delta_maps_to_text(self):
        event = parse_codex_stream_event(
            {"type": "response.output_text.delta", "delta": "Hello "}
        )
        assert event is not None
        assert event.event_type == "text"
        assert event.content == "Hello "

    def test_error_and_turn_failed_map_to_error(self):
        error_event = parse_codex_stream_event(
            {"type": "error", "message": "Reconnecting... 2/5"}
        )
        assert error_event is not None
        assert error_event.event_type == "error"
        assert "Reconnecting" in error_event.content

        turn_failed_event = parse_codex_stream_event(
            {"type": "turn.failed", "error": {"message": "stream disconnected"}}
        )
        assert turn_failed_event is not None
        assert turn_failed_event.event_type == "error"
        assert turn_failed_event.content == "stream disconnected"

    def test_turn_completed_maps_to_complete(self):
        event = parse_codex_stream_event({"type": "turn.completed"})
        assert event is not None
        assert event.event_type == "complete"

    def test_parse_stream_line_routes_to_codex_parser(self):
        line = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "ok"}],
                },
            }
        )
        event = parse_stream_line(line, backend="codex")
        assert event is not None
        assert event.event_type == "text"
        assert event.content == "ok"


class TestGeminiStreamParser:
    """Ensure Gemini wrapper events are parsed into unified ParsedEvent objects."""

    def test_text_and_result_success(self):
        text_event = parse_gemini_stream_event(
            {"type": "text", "role": "model", "content": "hello"}
        )
        assert text_event is not None
        assert text_event.event_type == "text"
        assert text_event.content == "hello"

        result_event = parse_gemini_stream_event(
            {"type": "result", "status": "success", "content": ""}
        )
        assert result_event is not None
        assert result_event.event_type == "complete"

    def test_error_type_event_with_capacity_message(self):
        error_event = parse_gemini_stream_event(
            {
                "type": "error",
                "message": "No capacity available for model gemini-2.5-pro on the server",
            }
        )
        assert error_event is not None
        assert error_event.event_type == "error"
        assert "No capacity available" in error_event.content

    def test_result_error_with_dict_payload(self):
        error_event = parse_gemini_stream_event(
            {
                "type": "result",
                "status": "error",
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "No capacity available for model gemini-2.5-pro on the server",
                },
            }
        )
        assert error_event is not None
        assert error_event.event_type == "error"
        assert "No capacity available" in error_event.content
