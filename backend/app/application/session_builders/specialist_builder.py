"""Specialist session builder."""

import logging

from claude_agent_sdk import ClaudeAgentOptions

from app.domain.config.system_prompts import SPECIALIST_PROMPT, format_system_prompt
from app.application.session_builders.base_builder import (
    SessionBuilder,
    SessionBuildContext,
)
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class SpecialistSessionBuilder(SessionBuilder):
    """
    Builder for Specialist sessions.

    Specialist sessions:
    - Require agent_id
    - Working directory is session-specific (session_dir)
    - Get agent-specific tools and MCPs
    - Load agent personality and skills
    """

    async def build_options(self, context: SessionBuildContext) -> ClaudeAgentOptions:
        """
        Build ClaudeAgentOptions for Specialist session.

        Args:
            context: Build context

        Returns:
            Configured ClaudeAgentOptions

        Raises:
            ValidationError: If agent_id missing
        """
        # Validate Specialist requirements
        if not context.agent_id:
            raise ValidationError("Specialist sessions require agent_id")

        # Specialist uses session directory for isolation
        working_dir = context.working_dir

        logger.info(
            f"Building Specialist session options for {context.agent_id} "
            f"(working_dir: {working_dir})"
        )

        # Load agent content, tools, MCPs, and skills
        (
            agent_content,
            base_tools,
            agent_mcps,
            skill_descriptions,
        ) = await self._load_agent_content(context.agent_id, working_dir)

        # Build allowed tools (includes mcp__ prefixed tools)
        allowed_tools = self._build_allowed_tools(
            base_tools=base_tools,
            mcp_servers=agent_mcps,
            include_common=True,
        )

        # Load MCP server configurations from ~/.claude.json
        mcp_servers = self._load_mcp_servers(
            agent_id=context.agent_id,
            agent_mcps=agent_mcps,
            include_common=True,
        )

        # Build system prompt with agent personality and skills
        logger.info(f"Building system prompt for {context.agent_id}...")
        system_prompt = await format_system_prompt(
            base_template=SPECIALIST_PROMPT,
            agent_content=agent_content,
            skills_content=skill_descriptions if skill_descriptions else None,
            user_profile=None,  # TODO: Load user profile
            context=None,
        )
        logger.info(
            f"System prompt built for {context.agent_id}: {len(system_prompt)} chars"
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
        }

        # Add resume if present
        self._add_resume_if_present(options_dict, context.resume_session_id)

        # Count MCP tools from allowed_tools
        mcp_tool_count = sum(1 for t in allowed_tools if t.startswith("mcp__"))

        logger.info(
            f"Specialist session options built for {context.agent_id}: "
            f"{len(allowed_tools)} tools ({mcp_tool_count} MCP), "
            f"{len(skill_descriptions)} skills, "
            f"prompt length: {len(system_prompt)} chars"
        )

        return ClaudeAgentOptions(**options_dict)
