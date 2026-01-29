"""Agent Assistant Tools MCP Server.

Provides tools for managing AI agent definitions and configurations.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any, Dict
import logging
from pathlib import Path
import yaml
import json

logger = logging.getLogger(__name__)


def _error(message: str) -> Dict[str, Any]:
    """Create error response."""
    return {"content": [{"type": "text", "text": f"✗ Error: {message}"}]}


def _get_agents_dir() -> Path:
    """Get the agents directory path."""
    return Path.home() / ".kumiai" / "agents"


def _get_skills_dir() -> Path:
    """Get the skills directory path."""
    return Path.home() / ".kumiai" / "skills"


def _get_claude_config_path() -> Path:
    """Get the Claude config file path."""
    return Path.home() / ".claude.json"


def _parse_agent_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse agent CLAUDE.md file with YAML frontmatter.

    Returns:
        Dict with 'frontmatter' and 'content' keys
    """
    content = file_path.read_text(encoding="utf-8")

    # Check for YAML frontmatter
    if not content.startswith("---"):
        return {"frontmatter": {}, "content": content}

    # Split frontmatter and content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"frontmatter": {}, "content": content}

    try:
        frontmatter = yaml.safe_load(parts[1])
        body_content = parts[2].strip()
        return {"frontmatter": frontmatter or {}, "content": body_content}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML frontmatter: {e}")
        return {"frontmatter": {}, "content": content}


@tool(
    "init_agent",
    "Initialize a new AI agent with a template CLAUDE.md file that you can then edit",
    {
        "agent_name": str,
    },
)
async def init_agent(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize a new agent with a template CLAUDE.md file.

    Creates the agent directory and a template file that you should then edit
    using the Write or Edit tool to customize the agent's configuration.

    Args (from args dict):
        agent_name: Display name for the agent (e.g., "Research Analyst")
                   Will be converted to agent_id (e.g., "research-analyst")

    Returns:
        Path to the created CLAUDE.md file for editing
    """
    try:
        # Extract parameters
        agent_name = args.get("agent_name", "")

        # Validate inputs
        if not agent_name:
            return _error("agent_name is required")

        # Convert agent_name to agent_id (lowercase-with-hyphens)
        agent_id = agent_name.lower().replace(" ", "-").replace("_", "-")
        # Remove any non-alphanumeric characters except hyphens
        agent_id = "".join(c for c in agent_id if c.isalnum() or c == "-")
        # Remove consecutive hyphens
        while "--" in agent_id:
            agent_id = agent_id.replace("--", "-")
        # Remove leading/trailing hyphens
        agent_id = agent_id.strip("-")

        if not agent_id:
            return _error(
                "agent_name must contain at least some alphanumeric characters"
            )

        # Create agent directory
        agents_dir = _get_agents_dir()
        agent_dir = agents_dir / agent_id

        if agent_dir.exists():
            return _error(f"Agent '{agent_id}' already exists at {agent_dir}")

        agent_dir.mkdir(parents=True, exist_ok=True)

        # Create template CLAUDE.md content
        template_content = f"""---
name: {agent_name}
tags: []
skills: []
allowed_tools: []
allowed_mcps: []
icon_color: "#4A90E2"
---

# {agent_name}

## Role

[Describe the agent's primary role and purpose]

## Personality

[Describe the agent's personality traits and communication style]

## Capabilities

[List what this agent is good at and when to use it]

## Guidelines

[Provide specific guidelines for how this agent should approach tasks]
"""

        # Write CLAUDE.md file
        claude_md_path = agent_dir / "CLAUDE.md"
        claude_md_path.write_text(template_content, encoding="utf-8")

        logger.info(
            f"[AGENT_ASSISTANT] Initialized agent '{agent_id}' at {claude_md_path}"
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""✓ Agent template created successfully

**Agent ID:** {agent_id}
**Agent Name:** {agent_name}
**Path:** {claude_md_path}

The template file has been created. Next steps:

1. Edit the CLAUDE.md file to customize:
   - tags: Add relevant tags like ["research", "coding", "analysis"]
   - skills: Add skill IDs like ["researcher", "code-reviewer"]
   - allowed_tools: Add tools like ["Read", "Write", "WebFetch"]
   - allowed_mcps: Add MCP servers like ["context7"] or leave empty []
   - icon_color: Change the hex color if desired
   - Content: Replace placeholders with actual agent instructions

2. Use the validate_agent tool to check your configuration

The file is ready for editing at: {claude_md_path}""",
                }
            ],
            "path": str(claude_md_path),
            "agent_id": agent_id,
        }

    except Exception as e:
        logger.error(f"[AGENT_ASSISTANT] Error initializing agent: {e}", exc_info=True)
        return _error(f"Failed to initialize agent: {str(e)}")


@tool(
    "list_agents",
    "List all available AI agents with their configurations",
    {},
)
async def list_agents(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all agents in ~/.kumiai/agents/ directory.

    Returns:
        List of agents with their configurations
    """
    try:
        agents_dir = _get_agents_dir()

        if not agents_dir.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No agents directory found. Create your first agent to get started.",
                    }
                ]
            }

        # Find all agent directories with CLAUDE.md
        agents = []
        for agent_path in sorted(agents_dir.iterdir()):
            if not agent_path.is_dir():
                continue

            claude_md = agent_path / "CLAUDE.md"
            if not claude_md.exists():
                continue

            try:
                parsed = _parse_agent_file(claude_md)
                frontmatter = parsed["frontmatter"]

                agents.append(
                    {
                        "id": agent_path.name,
                        "name": frontmatter.get("name", agent_path.name),
                        "tags": frontmatter.get("tags", []),
                        "skills": frontmatter.get("skills", []),
                        "allowed_tools": frontmatter.get("allowed_tools", []),
                        "allowed_mcps": frontmatter.get("allowed_mcps", []),
                        "icon_color": frontmatter.get("icon_color", "#4A90E2"),
                        "path": str(claude_md),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to parse agent {agent_path.name}: {e}")
                continue

        if not agents:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No agents found in ~/.kumiai/agents/",
                    }
                ]
            }

        # Format output
        result_lines = [f"📋 Found {len(agents)} agent(s):", ""]

        for agent in agents:
            result_lines.append(f"### {agent['name']} (`{agent['id']}`)")
            result_lines.append(f"**Path:** {agent['path']}")

            if agent["tags"]:
                result_lines.append(f"**Tags:** {', '.join(agent['tags'])}")

            if agent["skills"]:
                result_lines.append(f"**Skills:** {', '.join(agent['skills'])}")

            if agent["allowed_tools"]:
                result_lines.append(
                    f"**Allowed Tools:** {', '.join(agent['allowed_tools'])}"
                )

            if agent["allowed_mcps"]:
                result_lines.append(
                    f"**Allowed MCPs:** {', '.join(agent['allowed_mcps'])}"
                )

            result_lines.append(f"**Icon Color:** {agent['icon_color']}")
            result_lines.append("")

        logger.info(f"[AGENT_ASSISTANT] Listed {len(agents)} agents")

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "agents": agents,
        }

    except Exception as e:
        logger.error(f"[AGENT_ASSISTANT] Error listing agents: {e}", exc_info=True)
        return _error(f"Failed to list agents: {str(e)}")


@tool(
    "validate_agent",
    "Validate an agent's configuration and check for issues",
    {
        "agent_id": str,
    },
)
async def validate_agent(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an agent's configuration.

    Checks:
    - CLAUDE.md file exists and is readable
    - YAML frontmatter is valid
    - Required fields are present
    - Skills exist
    - Tools are valid
    - MCPs are available

    Args (from args dict):
        agent_id: Agent identifier to validate

    Returns:
        Validation results with any issues found
    """
    try:
        agent_id = args.get("agent_id", "")

        if not agent_id:
            return _error("agent_id is required")

        agents_dir = _get_agents_dir()
        agent_dir = agents_dir / agent_id

        if not agent_dir.exists():
            return _error(f"Agent '{agent_id}' not found")

        claude_md = agent_dir / "CLAUDE.md"
        if not claude_md.exists():
            return _error(f"CLAUDE.md not found for agent '{agent_id}'")

        # Parse the file
        try:
            parsed = _parse_agent_file(claude_md)
            frontmatter = parsed["frontmatter"]
            content = parsed["content"]
        except Exception as e:
            return _error(f"Failed to parse CLAUDE.md: {str(e)}")

        issues = []
        warnings = []

        # Check required fields
        if not frontmatter.get("name"):
            issues.append("Missing required field: 'name'")

        # Check tags format
        tags = frontmatter.get("tags", [])
        if not isinstance(tags, list):
            issues.append("'tags' must be a list")

        # Check skills format and existence
        skills = frontmatter.get("skills", [])
        if not isinstance(skills, list):
            issues.append("'skills' must be a list")
        else:
            skills_dir = _get_skills_dir()
            if skills_dir.exists():
                for skill_id in skills:
                    skill_path = skills_dir / skill_id / "SKILL.md"
                    if not skill_path.exists():
                        warnings.append(
                            f"Skill '{skill_id}' not found in ~/.kumiai/skills/"
                        )

        # Check allowed_tools format
        allowed_tools = frontmatter.get("allowed_tools", [])
        if not isinstance(allowed_tools, list):
            issues.append("'allowed_tools' must be a list")

        # Check allowed_mcps format and availability
        allowed_mcps = frontmatter.get("allowed_mcps", [])
        if not isinstance(allowed_mcps, list):
            issues.append("'allowed_mcps' must be a list")
        else:
            # Check against ~/.claude.json
            claude_config = _get_claude_config_path()
            if claude_config.exists():
                try:
                    config = json.loads(claude_config.read_text(encoding="utf-8"))
                    available_mcps = list(config.get("mcpServers", {}).keys())

                    for mcp_name in allowed_mcps:
                        if mcp_name not in available_mcps:
                            warnings.append(
                                f"MCP '{mcp_name}' not found in ~/.claude.json"
                            )
                except Exception as e:
                    warnings.append(f"Could not read ~/.claude.json: {str(e)}")

        # Check icon_color format
        icon_color = frontmatter.get("icon_color", "#4A90E2")
        if not isinstance(icon_color, str) or not icon_color.startswith("#"):
            warnings.append("'icon_color' should be a hex color code (e.g., '#904AE2')")

        # Check content
        if not content or len(content.strip()) < 50:
            warnings.append(
                "Agent content is very short. Consider adding more detailed instructions."
            )

        # Build response
        result_lines = [f"✓ Validation complete for agent '{agent_id}'", ""]

        if issues:
            result_lines.append("**❌ Issues Found:**")
            for issue in issues:
                result_lines.append(f"  - {issue}")
            result_lines.append("")

        if warnings:
            result_lines.append("**⚠️ Warnings:**")
            for warning in warnings:
                result_lines.append(f"  - {warning}")
            result_lines.append("")

        if not issues and not warnings:
            result_lines.append("✓ No issues found. Agent configuration is valid.")

        result_lines.append("")
        result_lines.append("**Configuration Summary:**")
        result_lines.append(f"- Name: {frontmatter.get('name', 'N/A')}")
        result_lines.append(f"- Tags: {len(tags)} tag(s)")
        result_lines.append(f"- Skills: {len(skills)} skill(s)")
        result_lines.append(f"- Allowed Tools: {len(allowed_tools)} tool(s)")
        result_lines.append(f"- Allowed MCPs: {len(allowed_mcps)} MCP(s)")
        result_lines.append(f"- Content Length: {len(content)} characters")

        logger.info(
            f"[AGENT_ASSISTANT] Validated agent '{agent_id}': "
            f"{len(issues)} issue(s), {len(warnings)} warning(s)"
        )

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    except Exception as e:
        logger.error(f"[AGENT_ASSISTANT] Error validating agent: {e}", exc_info=True)
        return _error(f"Failed to validate agent: {str(e)}")


@tool(
    "list_available_skills",
    "List all available skills from ~/.kumiai/skills/ that can be used in agent configurations",
    {},
)
async def list_available_skills(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all skills in ~/.kumiai/skills/ directory.

    Shows skills that can be specified in agent's skills field.

    Returns:
        List of available skill IDs with their names and descriptions
    """
    try:
        skills_dir = _get_skills_dir()

        if not skills_dir.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No skills directory found. Skills can be created in ~/.kumiai/skills/",
                    }
                ]
            }

        # Find all skill directories with SKILL.md
        skills = []
        for skill_path in sorted(skills_dir.iterdir()):
            if not skill_path.is_dir():
                continue

            skill_md = skill_path / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                parsed = _parse_agent_file(
                    skill_md
                )  # Reuse the parser for YAML frontmatter
                frontmatter = parsed["frontmatter"]

                skills.append(
                    {
                        "id": skill_path.name,
                        "name": frontmatter.get("name", skill_path.name),
                        "description": frontmatter.get("description", ""),
                        "tags": frontmatter.get("tags", []),
                        "icon": frontmatter.get("icon", "zap"),
                        "iconColor": frontmatter.get("iconColor", "#4A90E2"),
                        "path": str(skill_md),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to parse skill {skill_path.name}: {e}")
                continue

        if not skills:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No skills found in ~/.kumiai/skills/",
                    }
                ]
            }

        # Format output
        result_lines = [f"⚡ Available Skills ({len(skills)}):", ""]

        for skill in skills:
            result_lines.append(f"### {skill['name']} (`{skill['id']}`)")

            if skill["description"]:
                result_lines.append(f"{skill['description']}")

            if skill["tags"]:
                result_lines.append(f"**Tags:** {', '.join(skill['tags'])}")

            result_lines.append(f"**Icon:** {skill['icon']} ({skill['iconColor']})")
            result_lines.append(f"**Path:** {skill['path']}")
            result_lines.append("")

        result_lines.append("---")
        result_lines.append("")
        result_lines.append("**Usage:**")
        result_lines.append(
            "Add skill IDs to the `skills` field in your agent's YAML frontmatter:"
        )
        result_lines.append("```yaml")
        skill_ids = [s["id"] for s in skills[:3]]
        result_lines.append(f"skills: [{', '.join(skill_ids)}]")
        result_lines.append("```")

        logger.info(f"[AGENT_ASSISTANT] Listed {len(skills)} skills")

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "skills": [
                {"id": s["id"], "name": s["name"], "description": s["description"]}
                for s in skills
            ],
        }

    except Exception as e:
        logger.error(f"[AGENT_ASSISTANT] Error listing skills: {e}", exc_info=True)
        return _error(f"Failed to list skills: {str(e)}")


@tool(
    "list_available_tools",
    "List all available tools that can be used in agent configurations",
    {},
)
async def list_available_tools(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List available tools from the system.

    Shows built-in tools that can be specified in agent's allowed_tools field.

    Returns:
        List of available tool names and descriptions
    """
    try:
        # Common built-in tools available in the system
        # These are the tools typically available in Claude Code
        builtin_tools = [
            {"name": "Read", "description": "Read files from the filesystem"},
            {"name": "Write", "description": "Write files to the filesystem"},
            {"name": "Edit", "description": "Edit existing files"},
            {"name": "Bash", "description": "Execute bash commands"},
            {"name": "Glob", "description": "Find files using glob patterns"},
            {"name": "Grep", "description": "Search for text in files"},
            {"name": "WebFetch", "description": "Fetch content from URLs"},
            {"name": "WebSearch", "description": "Search the web"},
            {
                "name": "Task",
                "description": "Launch specialized agents for complex tasks",
            },
        ]

        result_lines = [f"🔧 Available Built-in Tools ({len(builtin_tools)}):", ""]

        for tool in builtin_tools:
            result_lines.append(f"### {tool['name']}")
            result_lines.append(f"{tool['description']}")
            result_lines.append("")

        result_lines.append("---")
        result_lines.append("")
        result_lines.append("**Usage:**")
        result_lines.append(
            "Add these tool names to the `allowed_tools` field in your agent's YAML frontmatter:"
        )
        result_lines.append("```yaml")
        result_lines.append("allowed_tools: [Read, Write, WebFetch]")
        result_lines.append("```")

        logger.info("[AGENT_ASSISTANT] Listed available tools")

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "tools": [t["name"] for t in builtin_tools],
        }

    except Exception as e:
        logger.error(f"[AGENT_ASSISTANT] Error listing tools: {e}", exc_info=True)
        return _error(f"Failed to list tools: {str(e)}")


@tool(
    "list_available_mcps",
    "List all available MCP servers from ~/.claude.json that can be used in agent configurations",
    {},
)
async def list_available_mcps(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List available MCP servers from ~/.claude.json.

    Shows MCP servers that can be specified in agent's allowed_mcps field.

    Returns:
        List of available MCP server names and their configurations
    """
    try:
        claude_config_path = _get_claude_config_path()

        if not claude_config_path.exists():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No ~/.claude.json file found. MCP servers are configured in this file.",
                    }
                ]
            }

        # Read and parse config
        try:
            config = json.loads(claude_config_path.read_text(encoding="utf-8"))
        except Exception as e:
            return _error(f"Failed to parse ~/.claude.json: {str(e)}")

        mcp_servers = config.get("mcpServers", {})

        if not mcp_servers:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No MCP servers found in ~/.claude.json",
                    }
                ]
            }

        result_lines = [f"🔌 Available MCP Servers ({len(mcp_servers)}):", ""]

        for server_name, server_config in sorted(mcp_servers.items()):
            result_lines.append(f"### {server_name}")

            if isinstance(server_config, dict):
                command = server_config.get("command", "N/A")
                args = server_config.get("args", [])

                result_lines.append(f"**Command:** `{command}`")

                if args:
                    args_str = " ".join(str(arg) for arg in args)
                    result_lines.append(f"**Args:** `{args_str}`")

                env = server_config.get("env", {})
                if env:
                    result_lines.append(f"**Environment Variables:** {len(env)} var(s)")
            else:
                result_lines.append(f"**Config:** {server_config}")

            result_lines.append("")

        result_lines.append("---")
        result_lines.append("")
        result_lines.append("**Usage:**")
        result_lines.append(
            "Add these MCP server names to the `allowed_mcps` field in your agent's YAML frontmatter:"
        )
        result_lines.append("```yaml")
        result_lines.append(
            f"allowed_mcps: [{', '.join(list(mcp_servers.keys())[:3])}]"
        )
        result_lines.append("```")
        result_lines.append("")
        result_lines.append("Or use an empty list if no MCPs are needed:")
        result_lines.append("```yaml")
        result_lines.append("allowed_mcps: []")
        result_lines.append("```")

        logger.info(f"[AGENT_ASSISTANT] Listed {len(mcp_servers)} MCP servers")

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "mcps": list(mcp_servers.keys()),
        }

    except Exception as e:
        logger.error(f"[AGENT_ASSISTANT] Error listing MCPs: {e}", exc_info=True)
        return _error(f"Failed to list MCPs: {str(e)}")


# Create the MCP server with agent assistant tools
agent_assistant_server = create_sdk_mcp_server(
    name="agent_assistant_tools",
    version="1.0.0",
    tools=[
        init_agent,
        list_agents,
        validate_agent,
        list_available_skills,
        list_available_tools,
        list_available_mcps,
    ],
)
