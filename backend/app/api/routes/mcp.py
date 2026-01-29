"""MCP (Model Context Protocol) API endpoints."""

import json
from pathlib import Path
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class McpServerDTO(BaseModel):
    """MCP Server data transfer object."""

    id: str
    name: str
    command: str
    description: str


@router.get(
    "/mcp/servers",
    response_model=List[McpServerDTO],
    summary="List MCP servers",
    description="Retrieve a list of available MCP servers from Claude Code config",
)
async def list_mcp_servers() -> List[McpServerDTO]:
    """
    List all available MCP servers.

    Automatically discovers MCP servers from the user's Claude Code configuration
    file at ~/.claude.json.

    Returns:
        List of MCP servers configured in Claude Code
    """
    mcp_config_path = Path.home() / ".claude.json"

    if not mcp_config_path.exists():
        logger.warning("~/.claude.json not found, returning empty list")
        return []

    try:
        config_text = mcp_config_path.read_text(encoding="utf-8")
        config = json.loads(config_text)
        mcp_servers = config.get("mcpServers", {})

        # Convert to DTOs
        result = []
        for server_id, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                continue

            # Extract command based on server type
            command = ""
            server_type = server_config.get("type", "stdio")

            if server_type == "stdio":
                # Build command from command + args
                cmd = server_config.get("command", "")
                args = server_config.get("args", [])
                if cmd:
                    if args:
                        command = f"{cmd} {' '.join(str(arg) for arg in args)}"
                    else:
                        command = cmd
            elif server_type == "http":
                # For HTTP servers, use the URL as command
                command = server_config.get("url", "")

            # Extract name and description
            name = server_config.get("name", server_id)
            description = server_config.get("description", "")

            result.append(
                McpServerDTO(
                    id=server_id,
                    name=name,
                    command=command,
                    description=description,
                )
            )

        logger.info(f"Discovered {len(result)} MCP servers from ~/.claude.json")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ~/.claude.json: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to load MCP config: {e}")
        return []
