"""Convert Claude SDK messages to SSE events."""

from typing import List, Any, Union
import logging
import json

from claude_agent_sdk import types

from app.infrastructure.claude.events import (
    StreamDeltaEvent,
    ToolUseEvent,
    ToolCompleteEvent,
    MessageCompleteEvent,
    MessageStartEvent,
    ErrorEvent,
    SSEEvent,
)

logger = logging.getLogger(__name__)


def convert_message_to_events(
    message: Union[types.StreamEvent, types.AssistantMessage, types.UserMessage, Any],
    session_id: str,
    response_id: str | None = None,
    agent_id: str | None = None,
    agent_name: str | None = None,
) -> List[SSEEvent]:
    """
    Convert a Claude SDK message to SSE events.

    Args:
        message: Message from Claude SDK (StreamEvent, AssistantMessage, etc.)
        session_id: Session UUID as string
        response_id: Response ID for grouping related messages
        agent_id: Agent ID for attribution
        agent_name: Agent name for attribution

    Returns:
        List of SSE event objects

    Message Types from Claude SDK:
    - StreamEvent: Incremental streaming updates (content_block_delta, etc.)
    - AssistantMessage: Complete assistant response with content blocks
    - UserMessage: User input (we don't convert these)
    """
    events: List[SSEEvent] = []

    # Handle StreamEvent (most common during streaming)
    if isinstance(message, types.StreamEvent):
        events.extend(_extract_stream_events(message, session_id))

    # Handle AssistantMessage (complete message with all blocks)
    # NOTE: In streaming mode, Claude SDK sends BOTH streaming events AND a final
    # AssistantMessage. We extract tool uses from here (with complete input)
    # but skip text content (already streamed).
    elif isinstance(message, types.AssistantMessage):
        logger.debug(
            "assistant_message_received",
            extra={"session_id": session_id, "content_blocks": len(message.content)},
        )
        # Extract tool uses from complete message (they have full input now)
        events.extend(
            _extract_assistant_message_events(
                message, session_id, response_id, agent_id, agent_name
            )
        )

    # Handle UserMessage (we don't convert these, just log)
    elif isinstance(message, types.UserMessage):
        logger.debug(
            "user_message_received",
            extra={
                "session_id": session_id,
                "content_preview": str(message.content)[:100],
            },
        )

    # Handle SystemMessage (init, system info - just log)
    elif isinstance(message, types.SystemMessage):
        logger.debug(
            "system_message_received",
            extra={
                "session_id": session_id,
                "subtype": getattr(message, "subtype", None),
            },
        )

    # Handle ResultMessage (just log it, completion is detected via message_delta)
    elif isinstance(message, types.ResultMessage):
        logger.debug(
            "result_message_received",
            extra={
                "session_id": session_id,
                "subtype": getattr(message, "subtype", None),
                "is_error": getattr(message, "is_error", False),
            },
        )

    # Unknown message type
    else:
        # Get full type info for debugging
        message_module = type(message).__module__
        message_class = type(message).__name__

        logger.warning(
            "unknown_message_type",
            extra={
                "session_id": session_id,
                "message_type": f"{message_module}.{message_class}",
                "message_str": str(message)[:200],
                "is_stream_event": isinstance(message, types.StreamEvent),
                "is_assistant": isinstance(message, types.AssistantMessage),
                "is_user": isinstance(message, types.UserMessage),
            },
        )

    return events


def _extract_stream_events(
    stream_event: types.StreamEvent, session_id: str
) -> List[SSEEvent]:
    """
    Extract events from StreamEvent.

    StreamEvent.event contains the raw Anthropic API stream event with types:
    - message_start: Message begins
    - content_block_start: New content block (text or tool)
    - content_block_delta: Incremental text update
    - content_block_stop: Content block completed
    - message_delta: Message metadata (stop_reason)
    - message_stop: Message completed

    NOTE: Claude SDK can send multiple content blocks with different indices in parallel!
    """
    events: List[SSEEvent] = []
    event_data = stream_event.event
    event_type = event_data.get("type")
    content_index = event_data.get("index", 0)  # Get content block index

    logger.debug(
        "stream_event_received",
        extra={
            "session_id": session_id,
            "event_type": event_type,
            "stream_session_id": stream_event.session_id,
        },
    )

    # Handle content_block_delta (text streaming and tool input streaming)
    if event_type == "content_block_delta":
        delta = event_data.get("delta", {})
        delta_type = delta.get("type")

        if delta_type == "text_delta":
            text = delta.get("text", "")
            if text:
                events.append(
                    StreamDeltaEvent(
                        session_id=session_id,
                        content=text,
                        content_index=content_index,  # Add index to event
                    )
                )
                logger.debug(
                    "text_delta_extracted",
                    extra={
                        "session_id": session_id,
                        "text_length": len(text),
                        "content_index": content_index,
                    },
                )

        elif delta_type == "input_json_delta":
            # Tool input is being streamed - we'll collect it when block completes
            logger.debug(
                "tool_input_delta_received",
                extra={
                    "session_id": session_id,
                    "partial_json": delta.get("partial_json", ""),
                },
            )

    # Handle content_block_start
    elif event_type == "content_block_start":
        content_block = event_data.get("content_block", {})
        block_type = content_block.get("type")

        if block_type == "tool_use":
            # Don't extract tool use here - input is empty at start
            # We'll get it from the complete AssistantMessage with full input
            logger.debug(
                "tool_use_block_started",
                extra={
                    "session_id": session_id,
                    "tool_id": content_block.get("id"),
                    "tool_name": content_block.get("name"),
                },
            )

    # Handle content_block_stop (triggers text buffer flush)
    elif event_type == "content_block_stop":
        # This signals end of a content block (text or tool)
        # Create a marker event to trigger executor buffer flush for this specific index
        from app.infrastructure.claude.events import ContentBlockStopEvent

        events.append(
            ContentBlockStopEvent(session_id=session_id, content_index=content_index)
        )
        logger.debug(
            "content_block_stop_received",
            extra={"session_id": session_id, "content_index": content_index},
        )

    # Handle message_start (clear buffers for new message)
    elif event_type == "message_start":
        events.append(MessageStartEvent(session_id=session_id))
        logger.debug("message_start_received", extra={"session_id": session_id})

    # Handle message_delta (check stop_reason to detect conversation end)
    elif event_type == "message_delta":
        delta = event_data.get("delta", {})
        stop_reason = delta.get("stop_reason")

        logger.debug(
            "message_delta_received",
            extra={"session_id": session_id, "stop_reason": stop_reason},
        )

        # Only mark conversation complete when stop_reason is 'end_turn'
        # 'tool_use' means Claude is waiting for tool results, more messages coming
        if stop_reason == "end_turn":
            events.append(MessageCompleteEvent(session_id=session_id))
            logger.info(
                "conversation_complete_detected",
                extra={"session_id": session_id, "stop_reason": stop_reason},
            )

    # Log message_stop for debugging (not used for completion detection)
    elif event_type == "message_stop":
        logger.debug("message_stop_received", extra={"session_id": session_id})

    return events


def _extract_assistant_message_events(
    assistant_msg: types.AssistantMessage,
    session_id: str,
    response_id: str | None = None,
    agent_id: str | None = None,
    agent_name: str | None = None,
) -> List[SSEEvent]:
    """
    Extract events from complete AssistantMessage.

    AssistantMessage.content contains list of:
    - TextBlock: Simple text content (SKIP - already streamed)
    - ToolUseBlock: Tool execution request (EXTRACT - has complete input)
    - ToolResultBlock: Tool execution result
    - ThinkingBlock: Internal reasoning (if enabled)
    """
    events: List[SSEEvent] = []

    # Handle error in assistant message
    if assistant_msg.error:
        events.append(
            ErrorEvent(
                session_id=session_id,
                error=f"Assistant error: {assistant_msg.error}",
                error_type=assistant_msg.error,
            )
        )
        return events

    # Process content blocks
    for block in assistant_msg.content:
        # TextBlock - SKIP (already streamed via content_block_delta)
        if isinstance(block, types.TextBlock):
            logger.debug(
                "text_block_skipped",
                extra={
                    "session_id": session_id,
                    "reason": "Already streamed",
                    "text_length": len(block.text) if block.text else 0,
                },
            )

        # ToolUseBlock - extract tool use WITH COMPLETE INPUT
        elif isinstance(block, types.ToolUseBlock):
            events.append(
                ToolUseEvent(
                    session_id=session_id,
                    tool_use_id=block.id,
                    tool_name=block.name,
                    tool_input=block.input,
                    response_id=response_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                )
            )
            logger.debug(
                "tool_use_block_extracted",
                extra={
                    "session_id": session_id,
                    "tool_name": block.name,
                    "has_input": bool(block.input),
                },
            )

        # ToolResultBlock - extract tool completion with result
        elif isinstance(block, types.ToolResultBlock):
            # Convert result content to string for transmission
            result_str = None
            if block.content is not None:
                if isinstance(block.content, str):
                    result_str = block.content
                elif isinstance(block.content, list):
                    # List of content blocks - join them
                    result_str = json.dumps(block.content)
                else:
                    result_str = str(block.content)

            events.append(
                ToolCompleteEvent(
                    session_id=session_id,
                    tool_use_id=block.tool_use_id,
                    result=result_str,
                    is_error=block.is_error or False,
                )
            )
            logger.debug(
                "tool_result_block_extracted",
                extra={
                    "session_id": session_id,
                    "tool_use_id": block.tool_use_id,
                    "has_result": result_str is not None,
                    "is_error": block.is_error,
                },
            )

        # ThinkingBlock - ignore for now (internal reasoning)
        elif isinstance(block, types.ThinkingBlock):
            logger.debug("thinking_block_ignored", extra={"session_id": session_id})

        # Unknown block type
        else:
            logger.warning(
                "unknown_content_block",
                extra={"session_id": session_id, "block_type": type(block).__name__},
            )

    return events
