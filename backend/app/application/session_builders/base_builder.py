"""Base session builder with common logic."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from claude_agent_sdk import ClaudeAgentOptions

from app.domain.value_objects.session_type import SessionType
from app.infrastructure.mcp.mcp_service import MCPServerService
from app.infrastructure.mcp.server_registry import MCPServerRegistry
from app.infrastructure.mcp.tool_registry import ToolRegistry
from app.application.loaders.agent_loader import AgentLoader
from app.application.loaders.skill_loader import SkillLoader

logger = logging.getLogger(__name__)


@dataclass
class SessionBuildContext:
    """
    Context for building a session.

    Contains all information needed to build ClaudeAgentOptions.
    """

    # Session metadata
    session_type: SessionType
    instance_id: str
    working_dir: Path

    # Agent configuration (optional)
    agent_id: Optional[str] = None

    # Project configuration (optional)
    project_id: Optional[str] = None
    project_path: Optional[Path] = None

    # Model configuration
    model: str = "sonnet"

    # Resume configuration
    resume_session_id: Optional[str] = None

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionBuilder(ABC):
    """
    Abstract base for session builders.

    Implements template method pattern: subclasses implement build_options()
    to create session-type-specific ClaudeAgentOptions.
    """

    def __init__(
        self,
        agent_loader: AgentLoader,
        skill_loader: SkillLoader,
        mcp_service: Optional[MCPServerService] = None,
    ):
        """
        Initialize session builder.

        Args:
            agent_loader: Service for loading agents
            skill_loader: Service for loading skills
            mcp_service: Service for loading MCP configurations
        """
        self.agent_loader = agent_loader
        self.skill_loader = skill_loader
        self.mcp_service = mcp_service or MCPServerService.get_instance()

    @abstractmethod
    async def build_options(self, context: SessionBuildContext) -> ClaudeAgentOptions:
        """
        Build ClaudeAgentOptions for this session type.

        Args:
            context: Build context with session configuration

        Returns:
            ClaudeAgentOptions configured for this session type

        Raises:
            ValidationError: If configuration is invalid
            NotFoundError: If agent/skill not found
        """
        pass

    async def _load_agent_content(
        self, agent_id: str, session_dir: Optional[Path] = None
    ) -> tuple[str, List[str], List[str], List[str]]:
        """
        Load agent content, skills, tools, and MCPs.

        Args:
            agent_id: Agent identifier
            session_dir: Optional session directory for symlinks

        Returns:
            Tuple of (agent_content, allowed_tools, allowed_mcps, skill_descriptions)
        """
        # Load agent with content and create symlink
        agent, content, _ = await self.agent_loader.load_agent_for_session(
            agent_id, session_dir
        )

        # Safety check: ensure agent was loaded
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' not found or returned None")

        # Load skills if agent has any
        skill_descriptions = []
        if agent.skills:
            skill_descriptions = await self.skill_loader.load_skills_for_session(
                agent.skills, session_dir
            )

        return content, agent.allowed_tools, agent.allowed_mcps, skill_descriptions

    def _build_allowed_tools(
        self,
        base_tools: List[str],
        mcp_servers: List[str],
        include_common: bool = True,
    ) -> List[str]:
        """
        Build complete allowed tools list.

        Args:
            base_tools: Base tool names
            mcp_servers: MCP server names
            include_common: Include common tools (default: True)

        Returns:
            Complete list of allowed tools
        """
        return ToolRegistry.build_allowed_tools(base_tools, mcp_servers, include_common)

    def _load_mcp_servers(
        self,
        agent_id: str,
        agent_mcps: List[str],
        include_common: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load MCP server configurations.

        Combines both:
        - In-process MCP servers (from MCPServerRegistry)
        - External MCP servers (from ~/.claude.json via MCPServerService)

        Args:
            agent_id: Agent identifier (for logging)
            agent_mcps: List of MCP server names the agent is allowed to use
            include_common: Include common_tools MCP server (default: True)

        Returns:
            Dictionary mapping server names to their configurations
        """
        mcp_servers = {}

        # 1. Load in-process MCP servers (custom tools)
        # These take precedence over external servers with same name
        internal_server_names = []

        # Always include internal servers that match agent_mcps
        for server_name in agent_mcps:
            internal_server = MCPServerRegistry.get_server(server_name)
            if internal_server:
                mcp_servers[server_name] = internal_server
                internal_server_names.append(server_name)
                logger.debug(
                    f"Loaded in-process MCP server '{server_name}' for {agent_id}"
                )

        # Load common_tools (in-process) if requested
        if include_common:
            common_tools = MCPServerRegistry.get_server("common_tools")
            if common_tools:
                mcp_servers["common_tools"] = common_tools
                internal_server_names.append("common_tools")
                logger.debug(
                    f"Loaded in-process common_tools MCP server for {agent_id}"
                )

        # 2. Load external MCP servers from ~/.claude.json
        # Skip servers we already loaded from registry
        external_mcps = [mcp for mcp in agent_mcps if mcp not in internal_server_names]

        if external_mcps:
            external_servers = self.mcp_service.get_servers_for_agent(
                agent_id, external_mcps
            )
            mcp_servers.update(external_servers)
            logger.debug(
                f"Loaded {len(external_servers)} external MCP servers for {agent_id}: "
                f"{list(external_servers.keys())}"
            )

        logger.info(
            f"Loaded {len(mcp_servers)} total MCP servers for {agent_id}: "
            f"{list(mcp_servers.keys())} "
            f"({len(internal_server_names)} in-process, {len(external_mcps)} external)"
        )

        return mcp_servers

    def _add_resume_if_present(
        self, options_dict: Dict[str, Any], resume_session_id: Optional[str]
    ) -> None:
        """
        Add resume configuration if session ID provided.

        Args:
            options_dict: Options dictionary to modify
            resume_session_id: Optional Claude session ID to resume
        """
        if resume_session_id:
            options_dict["resume"] = resume_session_id
            logger.info(f"Session will resume from: {resume_session_id}")
