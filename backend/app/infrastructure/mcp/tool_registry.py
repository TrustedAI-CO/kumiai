"""Tool registry for validating and managing tool permissions."""

import logging
from typing import List

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for validating tool permissions and assembling tool lists.

    Handles:
    - Base tool validation
    - MCP server tool prefixing (mcp__<server_name>)
    - Common tool injection
    """

    # Built-in tools available to all sessions
    COMMON_TOOLS = ["mcp__common_tools"]

    # Built-in base tools (file operations, etc.)
    BASE_TOOLS = {
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Grep",
        "Glob",
    }

    @staticmethod
    def build_allowed_tools(
        base_tools: List[str],
        mcp_servers: List[str],
        include_common: bool = True,
    ) -> List[str]:
        """
        Build complete allowed tools list from base tools and MCP servers.

        Args:
            base_tools: List of base tool names (Read, Write, etc.)
            mcp_servers: List of MCP server names to enable
            include_common: Whether to include common tools (default: True)

        Returns:
            Complete list of allowed tools with MCP prefixes
        """
        allowed_tools = base_tools.copy()

        # Add MCP servers with mcp__ prefix
        for server_name in mcp_servers:
            tool_name = f"mcp__{server_name}"
            if tool_name not in allowed_tools:
                allowed_tools.append(tool_name)

        # Add common tools if requested
        if include_common:
            for common_tool in ToolRegistry.COMMON_TOOLS:
                if common_tool not in allowed_tools:
                    allowed_tools.append(common_tool)

        logger.debug(f"Built allowed tools list: {len(allowed_tools)} tools")
        logger.debug(f"  Base tools: {base_tools}")
        logger.debug(f"  MCP tools: {[f'mcp__{s}' for s in mcp_servers]}")
        logger.debug(
            f"  Common tools: {ToolRegistry.COMMON_TOOLS if include_common else []}"
        )

        return allowed_tools

    @staticmethod
    def validate_base_tools(tools: List[str]) -> List[str]:
        """
        Validate that base tools are recognized.

        Args:
            tools: List of tool names to validate

        Returns:
            List of valid tools

        Logs warnings for unrecognized tools.
        """
        valid_tools = []
        base_tools_set = ToolRegistry.BASE_TOOLS

        for tool in tools:
            if tool in base_tools_set or tool.startswith("mcp__"):
                valid_tools.append(tool)
            else:
                logger.warning(f"Unrecognized base tool: {tool}")

        return valid_tools

    @staticmethod
    def extract_mcp_servers_from_tools(tools: List[str]) -> List[str]:
        """
        Extract MCP server names from tool list.

        Args:
            tools: List of tools (may include mcp__ prefixed tools)

        Returns:
            List of MCP server names (without mcp__ prefix)
        """
        mcp_servers = []

        for tool in tools:
            if tool.startswith("mcp__"):
                server_name = tool[5:]  # Remove 'mcp__' prefix
                mcp_servers.append(server_name)

        return mcp_servers
