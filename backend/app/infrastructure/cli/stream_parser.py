"""JSON stream parser for codeagent-wrapper output.

Parses streaming JSON output from codeagent-wrapper backends
and converts to a unified event format compatible with KumiAI's
message handling pipeline.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.infrastructure.cli.config import BACKEND_CODEX, BACKEND_GEMINI


@dataclass
class ParsedEvent:
    """Unified event from any CLI backend."""

    event_type: str  # "text", "tool_use", "tool_result", "error", "complete", "init"
    content: str = ""
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    session_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


def parse_claude_stream_event(data: Dict[str, Any]) -> Optional[ParsedEvent]:
    """Parse Claude CLI stream-json format."""
    event_type = data.get("type", "")

    if event_type == "system":
        session_id = data.get("session_id")
        return ParsedEvent(
            event_type="init",
            session_id=session_id,
            raw=data,
        )

    if event_type == "assistant":
        content_block = data.get("message", {})
        text = ""
        if isinstance(content_block, dict):
            content = content_block.get("content", "")
            if isinstance(content, list):
                text = "".join(
                    block.get("text", "")
                    for block in content
                    if block.get("type") == "text"
                )
            elif isinstance(content, str):
                text = content
        return ParsedEvent(event_type="text", content=text, raw=data)

    if event_type == "content_block_delta":
        delta = data.get("delta", {})
        if delta.get("type") == "text_delta":
            return ParsedEvent(
                event_type="text",
                content=delta.get("text", ""),
                raw=data,
            )

    if event_type == "tool_use":
        return ParsedEvent(
            event_type="tool_use",
            tool_name=data.get("name", ""),
            tool_input=data.get("input", {}),
            raw=data,
        )

    if event_type == "tool_result":
        return ParsedEvent(
            event_type="tool_result",
            tool_result=data.get("content", ""),
            raw=data,
        )

    if event_type == "result":
        return ParsedEvent(
            event_type="complete",
            content=data.get("result", ""),
            raw=data,
        )

    if event_type == "error":
        return ParsedEvent(
            event_type="error",
            content=data.get("error", {}).get("message", str(data)),
            raw=data,
        )

    return None


def parse_gemini_stream_event(data: Dict[str, Any]) -> Optional[ParsedEvent]:
    """Parse Gemini CLI stream-json format.

    Gemini CLI events (with -o stream-json):
    - {"type":"init","session_id":"..."}
    - {"type":"text","role":"model","content":"...","delta":true}
    - {"type":"result","status":"success|error"}
    """
    event_type = data.get("type", "")

    if event_type == "init":
        return ParsedEvent(
            event_type="init",
            session_id=data.get("session_id"),
            raw=data,
        )

    if event_type == "text" and data.get("role") == "model":
        content = data.get("content", "")
        if content:
            return ParsedEvent(event_type="text", content=content, raw=data)
        return None

    if event_type == "error":
        error_payload = data.get("error", data.get("message", "Gemini execution failed"))
        if isinstance(error_payload, dict):
            message = str(error_payload.get("message") or error_payload)
        else:
            message = str(error_payload)
        return ParsedEvent(
            event_type="error",
            content=message,
            raw=data,
        )

    if event_type == "result":
        status = data.get("status", "")
        if status in ("error", "failed"):
            error_payload = data.get("error", "Gemini execution failed")
            if isinstance(error_payload, dict):
                message = str(error_payload.get("message") or error_payload)
            else:
                message = str(error_payload)
            return ParsedEvent(
                event_type="error",
                content=message,
                raw=data,
            )
        return ParsedEvent(
            event_type="complete",
            content=data.get("content", ""),
            raw=data,
        )

    return None


def parse_codex_stream_event(data: Dict[str, Any]) -> Optional[ParsedEvent]:
    """Parse Codex CLI JSON output format.

    Codex events:
    - {"type":"thread.started","thread_id":"..."}
    - {"type":"item.completed","item":{"type":"agent_message","text":"..."}}
    - {"type":"response.output_text.delta","delta":"..."}
    - {"type":"thread.completed","thread_id":"..."}
    - {"type":"turn.completed"}
    """

    def _extract_text(value: Any) -> str:
        """Extract plain text from Codex message payload variants."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "".join(_extract_text(item) for item in value)
        if isinstance(value, dict):
            # Most direct string fields first
            for key in ("text", "delta", "content"):
                extracted = _extract_text(value.get(key))
                if extracted:
                    return extracted

            # Codex message content can be a list of rich blocks
            if isinstance(value.get("content"), list):
                parts: List[str] = []
                for block in value["content"]:
                    if isinstance(block, dict):
                        block_type = block.get("type", "")
                        if block_type in ("output_text", "text", "input_text"):
                            block_text = _extract_text(block.get("text"))
                            if block_text:
                                parts.append(block_text)
                if parts:
                    return "".join(parts)
        return ""

    event_type = data.get("type", "")

    if event_type == "thread.started":
        return ParsedEvent(
            event_type="init",
            session_id=data.get("thread_id"),
            raw=data,
        )

    # Newer Codex stream shape (incremental text chunks)
    if event_type in ("response.output_text.delta", "message.delta"):
        text = _extract_text(data.get("delta"))
        if text:
            return ParsedEvent(event_type="text", content=text, raw=data)
        return None

    if event_type == "item.completed":
        item = data.get("item")
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type in ("agent_message", "assistant_message", "message"):
                text = _extract_text(item)
                if text:
                    return ParsedEvent(event_type="text", content=text, raw=data)
            if item_type == "error":
                error_msg = _extract_text(item.get("message")) or str(item)
                return ParsedEvent(event_type="error", content=error_msg, raw=data)
        return None

    if event_type == "error":
        error_msg = _extract_text(data.get("message")) or str(data)
        return ParsedEvent(event_type="error", content=error_msg, raw=data)

    if event_type == "turn.failed":
        error = data.get("error", {})
        error_msg = _extract_text(error.get("message") if isinstance(error, dict) else error)
        if not error_msg:
            error_msg = str(data)
        return ParsedEvent(event_type="error", content=error_msg, raw=data)

    if event_type in ("thread.completed", "turn.completed"):
        return ParsedEvent(
            event_type="complete",
            content="",
            raw=data,
        )

    # Some wrappers may emit final output in alternate result events.
    if event_type in ("response.completed", "message.completed"):
        text = _extract_text(data.get("output") or data.get("message") or data.get("content"))
        if text:
            return ParsedEvent(event_type="text", content=text, raw=data)
        return ParsedEvent(event_type="complete", content="", raw=data)

    return None


def parse_stream_line(line: str, backend: str = "claude") -> Optional[ParsedEvent]:
    """Parse a single line of streaming JSON output.

    Args:
        line: Raw line from stdout
        backend: Backend type for format-specific parsing

    Returns:
        ParsedEvent if the line was valid JSON, None otherwise
    """
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    # Route to backend-specific parser
    if backend == BACKEND_GEMINI:
        return parse_gemini_stream_event(data)
    if backend == BACKEND_CODEX:
        return parse_codex_stream_event(data)

    # Claude and fallback: try all parsers
    result = parse_claude_stream_event(data)
    if result:
        return result

    # Auto-detect: try Gemini then Codex patterns
    if data.get("role") or data.get("delta") is not None or data.get("status"):
        return parse_gemini_stream_event(data)
    if data.get("thread_id") or (isinstance(data.get("item"), dict)):
        return parse_codex_stream_event(data)

    return None
