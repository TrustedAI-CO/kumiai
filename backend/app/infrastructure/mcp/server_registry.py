"""Registry for in-process MCP servers."""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MCPServerRegistry:
    """
    Registry for in-process MCP servers.

    Manages SDK MCP servers (created with create_sdk_mcp_server) that provide
    custom tools for Claude Agent SDK. These are different from external MCP
    servers loaded from ~/.claude.json.
    """

    _servers: Dict[str, Any] = {}
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Lazy load servers to avoid circular imports."""
        if cls._initialized:
            return

        try:
            from .servers import (
                pm_management_server,
                common_tools_server,
                agent_assistant_server,
                skill_assistant_server,
            )

            cls._servers = {
                "pm_management": pm_management_server,
                "common_tools": common_tools_server,
                "agent_assistant": agent_assistant_server,
                "skill_assistant": skill_assistant_server,
            }
            cls._initialized = True
            logger.info(
                f"[MCP_REGISTRY] Initialized with {len(cls._servers)} in-process servers: "
                f"{list(cls._servers.keys())}"
            )
        except ImportError as e:
            logger.error(f"[MCP_REGISTRY] Failed to load MCP servers: {e}")
            cls._servers = {}
            cls._initialized = True

    @classmethod
    def get_server(cls, name: str) -> Any:
        """
        Get a single in-process MCP server by name.

        Args:
            name: Server name (e.g., "pm_management")

        Returns:
            MCP server instance or None if not found
        """
        cls._ensure_initialized()
        server = cls._servers.get(name)
        if server:
            logger.debug(f"[MCP_REGISTRY] Retrieved server: {name}")
        else:
            logger.debug(
                f"[MCP_REGISTRY] Server not found in in-process registry: {name}"
            )
        return server

    @classmethod
    def get_servers_for_agent(cls, server_names: List[str]) -> Dict[str, Any]:
        """
        Get multiple in-process MCP servers by name.

        Args:
            server_names: List of server names to retrieve

        Returns:
            Dict mapping server names to server instances
        """
        cls._ensure_initialized()
        servers = {
            name: cls._servers[name] for name in server_names if name in cls._servers
        }

        if len(servers) != len(server_names):
            missing = set(server_names) - set(servers.keys())
            logger.debug(
                f"[MCP_REGISTRY] Some servers not found in in-process registry: {missing}. "
                f"Available in-process: {list(cls._servers.keys())}"
            )

        logger.info(
            f"[MCP_REGISTRY] Retrieved {len(servers)} servers for agent: "
            f"{list(servers.keys())}"
        )
        return servers

    @classmethod
    def list_servers(cls) -> List[str]:
        """
        List all available in-process MCP server names.

        Returns:
            List of server names
        """
        cls._ensure_initialized()
        return list(cls._servers.keys())

    @classmethod
    def reload(cls) -> None:
        """Force reload of all servers (useful for testing)."""
        cls._initialized = False
        cls._servers = {}
        cls._ensure_initialized()
        logger.info("[MCP_REGISTRY] Reloaded all servers")
