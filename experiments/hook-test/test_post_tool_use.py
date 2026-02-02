"""
Minimal experiment to test PostToolUse hooks in Claude SDK.
"""

import asyncio
import logging
from typing import Any, Dict

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    create_sdk_mcp_server,
    tool,
)

# Setup logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Define a simple test tool
@tool("test_ask", "Ask the user a test question", {"question": str})
async def test_ask_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Test tool that asks a question."""
    question = args.get("question", "Test question?")
    logger.warning(f"[TOOL] test_ask called with: {question}")
    return {"content": [{"type": "text", "text": f"Question: {question}"}]}


# Create MCP server
test_mcp_server = create_sdk_mcp_server(
    "test_tools",
    tools=[test_ask_tool],
)


# PostToolUse hook
async def post_tool_hook(
    input_data: Dict[str, Any], tool_use_id: str, context: Any
) -> Dict[str, Any]:
    """Hook that fires after tool use."""
    logger.warning(
        f"[HOOK] PostToolUse FIRED! "
        f"event={input_data.get('hook_event_name')}, "
        f"tool={input_data.get('tool_name')}, "
        f"keys={list(input_data.keys())}"
    )
    return {}


async def main():
    """Run the test."""
    logger.warning("=== Starting PostToolUse Hook Test ===")

    # Build options with PostToolUse hook
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
        system_prompt="You are a test assistant. When asked to test, use the test_ask tool.",
        mcp_servers=[test_mcp_server],
        include_partial_messages=True,
        permission_mode="bypassPermissions",
        hooks={
            "PostToolUse": [
                HookMatcher(hooks=[post_tool_hook]),
            ],
        },
    )

    logger.warning("Creating ClaudeSDKClient with PostToolUse hook...")
    client = ClaudeSDKClient(options=options)

    logger.warning("Connecting to Claude...")
    await client.connect()

    logger.warning("Sending message that should trigger tool use...")
    messages = []
    async for message in client.send_message("Use test_ask tool to ask me 'What is your name?'"):
        logger.warning(f"[MESSAGE] {message}")
        messages.append(message)

    logger.warning(f"=== Test Complete. Got {len(messages)} messages ===")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
