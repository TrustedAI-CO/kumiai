"""
Minimal experiment to test Claude SDK PostToolUse hooks.

This tests if PostToolUse hooks fire and if interrupt() works.
"""

import asyncio
import logging
from typing import Any, Dict

from claude_agent_sdk import (
    Agent,
    create_sdk_mcp_server,
    tool,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Define a simple test tool
@tool("test_tool", "A simple test tool", {"message": str})
async def test_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Simple tool that returns a message."""
    message = args.get("message", "Hello!")
    logger.info(f"[TOOL] test_tool called with message: {message}")
    return {"content": [{"type": "text", "text": f"Tool response: {message}"}]}


# Create MCP server with the tool
mcp_server = create_sdk_mcp_server(
    "test_server",
    tools=[test_tool],
)


# PostToolUse hook
async def post_tool_use_hook(
    input_data: Dict[str, Any], tool_use_id: str, context: Any
) -> Dict[str, Any]:
    """Hook that fires after tool use."""
    logger.warning(
        f"[HOOK] PostToolUse fired! "
        f"tool_name={input_data.get('tool_name')}, "
        f"tool_use_id={tool_use_id}"
    )

    # Try to interrupt if this is our test tool
    if input_data.get("tool_name") == "test_tool":
        logger.warning("[HOOK] Attempting to interrupt execution...")
        # How do we access the client to call interrupt()?
        # Need to investigate this

    return {}


async def main():
    """Run the test."""
    logger.info("=== Starting Hook Test ===")

    # Create agent with hook
    agent = Agent(
        name="TestAgent",
        system_prompt="You are a test agent. When asked to test, use the test_tool.",
        mcp_servers=[mcp_server],
        options={
            "hooks": {
                "PostToolUse": [
                    {
                        "hooks": [post_tool_use_hook],
                    }
                ],
            }
        },
    )

    logger.info("Agent created with PostToolUse hook")

    # Start a conversation
    logger.info("Sending message to agent...")
    result = await agent.send_message("Please use the test_tool with message 'testing hooks'")

    logger.info(f"Agent response: {result}")
    logger.info("=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
