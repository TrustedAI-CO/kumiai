"""Assistant session builder."""

import logging

from claude_agent_sdk import ClaudeAgentOptions

from app.domain.config.system_prompts import (
    ASSISTANT_PROMPT,
    AGENT_ASSISTANT_PROMPT,
    SKILL_ASSISTANT_PROMPT,
    format_system_prompt,
)
from app.domain.value_objects.session_type import SessionType
from app.application.session_builders.base_builder import (
    SessionBuilder,
    SessionBuildContext,
)

logger = logging.getLogger(__name__)


class AssistantSessionBuilder(SessionBuilder):
    """
    Builder for Assistant sessions.

    Assistant sessions:
    - May have agent_id (optional)
    - Working directory is project root
    - Get file editing tools + agent-specific tools
    - Simpler configuration for general assistance
    """

    async def build_options(self, context: SessionBuildContext) -> ClaudeAgentOptions:
        """
        Build ClaudeAgentOptions for Assistant session.

        Args:
            context: Build context

        Returns:
            Configured ClaudeAgentOptions
        """
        # Assistant uses project root or working dir
        if context.project_path:
            working_dir = context.project_path
        else:
            working_dir = context.working_dir

        logger.info(f"Building Assistant session options (working_dir: {working_dir})")

        # Load agent content if agent_id provided
        agent_content = None
        skill_descriptions = []
        agent_tools = []
        agent_mcps = []

        if context.agent_id:
            (
                agent_content,
                agent_tools,
                agent_mcps,
                skill_descriptions,
            ) = await self._load_agent_content(context.agent_id, working_dir)

        # Add session-type-specific MCP servers automatically
        if context.session_type == SessionType.AGENT_ASSISTANT:
            if "agent_assistant" not in agent_mcps:
                agent_mcps.append("agent_assistant")
                logger.info(
                    "Auto-added agent_assistant MCP server for AGENT_ASSISTANT session"
                )
        elif context.session_type == SessionType.SKILL_ASSISTANT:
            if "skill_assistant" not in agent_mcps:
                agent_mcps.append("skill_assistant")
                logger.info(
                    "Auto-added skill_assistant MCP server for SKILL_ASSISTANT session"
                )

        # Base file editing tools
        base_tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]

        # Combine with agent-specific tools
        all_tools = base_tools + agent_tools

        # Build allowed tools
        allowed_tools = self._build_allowed_tools(
            base_tools=all_tools,
            mcp_servers=agent_mcps,
            include_common=True,
        )

        # Load MCP server configurations from ~/.claude.json
        mcp_servers = self._load_mcp_servers(
            agent_id=context.agent_id or "assistant",
            agent_mcps=agent_mcps,
            include_common=True,
        )

        # Select appropriate system prompt based on session type
        if context.session_type == SessionType.AGENT_ASSISTANT:
            base_template = AGENT_ASSISTANT_PROMPT
        elif context.session_type == SessionType.SKILL_ASSISTANT:
            base_template = SKILL_ASSISTANT_PROMPT
        else:
            base_template = ASSISTANT_PROMPT

        # Build system prompt
        system_prompt = await format_system_prompt(
            base_template=base_template,
            agent_content=agent_content,
            skills_content=skill_descriptions if skill_descriptions else None,
            user_profile=None,  # TODO: Load user profile
            context={"tools": allowed_tools},
        )

        # Build options dictionary
        options_dict = {
            "model": context.model,
            "cwd": str(working_dir),
            "system_prompt": system_prompt,
            "allowed_tools": allowed_tools,
            "mcp_servers": mcp_servers,
            "include_partial_messages": True,  # Enable streaming
            "permission_mode": "bypassPermissions",
            "hooks": [],  # No hooks for now
        }

        # Add resume if present
        self._add_resume_if_present(options_dict, context.resume_session_id)

        # Count MCP tools
        mcp_tool_count = sum(1 for t in allowed_tools if t.startswith("mcp__"))

        logger.info(
            f"Assistant session options built: {len(allowed_tools)} tools ({mcp_tool_count} MCP), "
            f"prompt length: {len(system_prompt)} chars"
        )

        return ClaudeAgentOptions(**options_dict)
