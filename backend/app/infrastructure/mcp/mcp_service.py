"""MCP server service for loading and managing MCP server configurations."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class MCPServerService:
    """
    Service for loading and managing MCP server configurations.

    MCP servers are loaded from ~/.claude.json (Claude Code config).
    This ensures consistency with the Claude SDK MCP server format.
    """

    _instance: Optional["MCPServerService"] = None
    _user_config: Optional[Dict[str, Any]] = None

    def __init__(self):
        """Initialize MCP service with empty cache."""
        self._user_config = None

    @classmethod
    def get_instance(cls) -> "MCPServerService":
        """
        Get singleton instance of MCP service.

        Returns:
            MCPServerService instance
        """
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Initialized MCPServerService singleton")
        return cls._instance

    def _load_user_config(self) -> Dict[str, Any]:
        """
        Load user MCP server configuration from ~/.claude.json.

        Returns:
            Dictionary mapping server names to their configuration.
            Empty dict if file doesn't exist or can't be loaded.
        """
        if self._user_config is None:
            mcp_config_path = Path.home() / ".claude.json"

            if not mcp_config_path.exists():
                logger.warning("~/.claude.json not found, no MCP servers available")
                self._user_config = {}
                return self._user_config

            try:
                config = json.loads(mcp_config_path.read_text(encoding="utf-8"))
                # Extract mcpServers section from the config
                self._user_config = config.get("mcpServers", {})
                logger.info(
                    f"Loaded user MCP config: {len(self._user_config)} servers available"
                )
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load MCP config from {mcp_config_path}: {e}")
                self._user_config = {}

        return self._user_config

    def get_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        Get MCP server configuration by name.

        Args:
            server_name: Name of the MCP server

        Returns:
            Server configuration dict or None if not found
        """
        user_config = self._load_user_config()
        return user_config.get(server_name)

    def get_servers_for_agent(
        self, agent_id: str, allowed_mcp_servers: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get MCP server configurations for an agent.

        Filters the user's MCP servers from ~/.claude.json to only include
        servers that the agent is allowed to use.

        Args:
            agent_id: Agent identifier (for logging)
            allowed_mcp_servers: List of MCP server names allowed for this agent

        Returns:
            Dict mapping server name to server configuration
        """
        if not allowed_mcp_servers:
            return {}

        user_config = self._load_user_config()
        servers = {}

        for server_name in allowed_mcp_servers:
            server_config = user_config.get(server_name)
            if server_config:
                servers[server_name] = server_config
                logger.debug(f"Added MCP server '{server_name}' for agent {agent_id}")
            else:
                logger.warning(
                    f"MCP server '{server_name}' not found in ~/.claude.json for agent {agent_id}"
                )

        if servers:
            logger.info(
                f"Loaded {len(servers)} MCP servers for {agent_id}: {list(servers.keys())}"
            )
        elif allowed_mcp_servers:
            logger.warning(
                f"No MCP servers found for {agent_id}! "
                f"Requested: {allowed_mcp_servers}. Check ~/.claude.json"
            )

        return servers

    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all loaded MCP server configurations.

        Returns:
            Dict mapping server name to server configuration
        """
        return self._load_user_config().copy()

    def list_server_names(self) -> List[str]:
        """
        List all available MCP server names.

        Returns:
            List of server names
        """
        user_config = self._load_user_config()
        return list(user_config.keys())

    def reload(self) -> None:
        """Reload all MCP server configurations from disk."""
        self._user_config = None
        user_config = self._load_user_config()
        logger.info(f"Reloaded {len(user_config)} MCP servers from ~/.claude.json")
