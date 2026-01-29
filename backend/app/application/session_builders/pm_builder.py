"""PM session builder."""

import logging

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

from app.domain.config.system_prompts import PM_PROMPT, format_system_prompt
from app.application.session_builders.base_builder import (
    SessionBuilder,
    SessionBuildContext,
)
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class PMSessionBuilder(SessionBuilder):
    """
    Builder for PM (Project Manager) sessions.

    PM sessions:
    - Require project_id
    - Working directory is project root
    - Get PM management tools
    - Can optionally have agent personality
    """

    async def build_options(self, context: SessionBuildContext) -> ClaudeAgentOptions:
        """
        Build ClaudeAgentOptions for PM session.

        Args:
            context: Build context

        Returns:
            Configured ClaudeAgentOptions

        Raises:
            ValidationError: If project_id missing
        """
        # Validate PM requirements
        if not context.project_id:
            raise ValidationError("PM sessions require project_id")

        # Determine working directory (project root for PM)
        if context.project_path:
            working_dir = context.project_path
        else:
            working_dir = context.working_dir

        logger.info(f"Building PM session options (working_dir: {working_dir})")

        # Load agent content if agent_id provided
        agent_content = None
        skill_descriptions = []
        base_tools = []
        agent_mcps = []

        if context.agent_id:
            (
                agent_content,
                base_tools,
                agent_mcps,
                skill_descriptions,
            ) = await self._load_agent_content(context.agent_id, working_dir)

        # PM always gets pm_management MCP
        pm_mcps = ["pm_management"]
        all_mcps = pm_mcps + agent_mcps

        # Build allowed tools (includes mcp__ prefixed tools)
        allowed_tools = self._build_allowed_tools(
            base_tools=base_tools,
            mcp_servers=all_mcps,
            include_common=True,
        )

        # Load MCP server configurations from ~/.claude.json
        mcp_servers = self._load_mcp_servers(
            agent_id=context.agent_id or "pm",
            agent_mcps=all_mcps,
            include_common=True,
        )

        # Build system prompt
        system_prompt = await format_system_prompt(
            base_template=PM_PROMPT,
            agent_content=agent_content,
            skills_content=skill_descriptions if skill_descriptions else None,
            user_profile=None,  # TODO: Load user profile
            context={"tools": allowed_tools},
        )

        # Import hook for project_id injection
        from app.infrastructure.claude.hooks import inject_session_context_hook

        # Build options dictionary
        options_dict = {
            "model": context.model,
            "cwd": str(working_dir),
            "system_prompt": system_prompt,
            "allowed_tools": allowed_tools,
            "mcp_servers": mcp_servers,
            "include_partial_messages": True,  # Enable streaming
            "permission_mode": "bypassPermissions",
            "hooks": {
                "PreToolUse": [
                    # Auto-inject project_id for all PM management tools
                    HookMatcher(
                        matcher=".*pm_management__.*",
                        hooks=[inject_session_context_hook],
                    )
                ]
            },
        }

        # Add resume if present
        self._add_resume_if_present(options_dict, context.resume_session_id)

        # Count MCP tools from allowed_tools
        mcp_tool_count = sum(1 for t in allowed_tools if t.startswith("mcp__"))

        logger.info(
            f"PM session options built: {len(allowed_tools)} tools ({mcp_tool_count} MCP), "
            f"prompt length: {len(system_prompt)} chars"
        )

        return ClaudeAgentOptions(**options_dict)
