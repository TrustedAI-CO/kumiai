"""Skill Assistant Tools MCP Server.

Provides tools for managing skill definitions.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any, Dict
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


def _error(message: str) -> Dict[str, Any]:
    """Create error response."""
    return {"content": [{"type": "text", "text": f"✗ Error: {message}"}]}


def _get_skills_dir() -> Path:
    """Get the skills directory path."""
    return Path.home() / ".kumiai" / "skills"


def _parse_skill_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse skill SKILL.md file with YAML frontmatter.

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
    "init_skill",
    "Initialize a new skill with a template SKILL.md file that you can then edit",
    {
        "skill_name": str,
    },
)
async def init_skill(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize a new skill with a template SKILL.md file.

    Creates the skill directory and a template file that you should then edit
    using the Write or Edit tool to customize the skill's definition.

    Args (from args dict):
        skill_name: Display name for the skill (e.g., "Backend Development")
                   Will be converted to skill_id (e.g., "backend-development")

    Returns:
        Path to the created SKILL.md file for editing
    """
    try:
        # Extract parameters
        skill_name = args.get("skill_name", "")

        # Validate inputs
        if not skill_name:
            return _error("skill_name is required")

        # Convert skill_name to skill_id (lowercase-with-hyphens)
        skill_id = skill_name.lower().replace(" ", "-").replace("_", "-")
        # Remove any non-alphanumeric characters except hyphens
        skill_id = "".join(c for c in skill_id if c.isalnum() or c == "-")
        # Remove consecutive hyphens
        while "--" in skill_id:
            skill_id = skill_id.replace("--", "-")
        # Remove leading/trailing hyphens
        skill_id = skill_id.strip("-")

        if not skill_id:
            return _error(
                "skill_name must contain at least some alphanumeric characters"
            )

        # Create skill directory
        skills_dir = _get_skills_dir()
        skill_dir = skills_dir / skill_id

        if skill_dir.exists():
            return _error(f"Skill '{skill_id}' already exists at {skill_dir}")

        skill_dir.mkdir(parents=True, exist_ok=True)

        # Create template SKILL.md content
        template_content = f"""---
name: {skill_name}
description: Brief description of what this skill does
tags: []
icon: zap
iconColor: "#4A90E2"
---

# {skill_name}

[Provide a comprehensive description of this skill]

## What I Do

- [Capability 1]
- [Capability 2]
- [Capability 3]

## When to Use This Skill

[Describe scenarios where this skill is most useful]

## Example Tasks

- "[Example task 1]"
- "[Example task 2]"
- "[Example task 3]"

## Best Practices

- [Best practice 1]
- [Best practice 2]
- [Best practice 3]

## Related Skills

- [Related skill 1]
- [Related skill 2]
"""

        # Write SKILL.md file
        skill_md_path = skill_dir / "SKILL.md"
        skill_md_path.write_text(template_content, encoding="utf-8")

        logger.info(
            f"[SKILL_ASSISTANT] Initialized skill '{skill_id}' at {skill_md_path}"
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""✓ Skill template created successfully

**Skill ID:** {skill_id}
**Skill Name:** {skill_name}
**Path:** {skill_md_path}

The template file has been created. Next steps:

1. Edit the SKILL.md file to customize:
   - description: Brief description of the skill
   - tags: Add relevant tags like ["backend", "api", "python"]
   - icon: Icon name (e.g., "server", "code", "database")
   - iconColor: Change the hex color if desired
   - Content: Replace placeholders with actual skill documentation

2. Use the validate_skill tool to check your configuration

The file is ready for editing at: {skill_md_path}""",
                }
            ],
            "path": str(skill_md_path),
            "skill_id": skill_id,
        }

    except Exception as e:
        logger.error(f"[SKILL_ASSISTANT] Error initializing skill: {e}", exc_info=True)
        return _error(f"Failed to initialize skill: {str(e)}")


@tool(
    "validate_skill",
    "Validate a skill's configuration and check for issues",
    {
        "skill_id": str,
    },
)
async def validate_skill(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a skill's configuration.

    Checks:
    - SKILL.md file exists and is readable
    - YAML frontmatter is valid
    - Required fields are present
    - Field formats are correct

    Args (from args dict):
        skill_id: Skill identifier to validate

    Returns:
        Validation results with any issues found
    """
    try:
        skill_id = args.get("skill_id", "")

        if not skill_id:
            return _error("skill_id is required")

        skills_dir = _get_skills_dir()
        skill_dir = skills_dir / skill_id

        if not skill_dir.exists():
            return _error(f"Skill '{skill_id}' not found")

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return _error(f"SKILL.md not found for skill '{skill_id}'")

        # Parse the file
        try:
            parsed = _parse_skill_file(skill_md)
            frontmatter = parsed["frontmatter"]
            content = parsed["content"]
        except Exception as e:
            return _error(f"Failed to parse SKILL.md: {str(e)}")

        issues = []
        warnings = []

        # Check required fields
        if not frontmatter.get("name"):
            issues.append("Missing required field: 'name'")

        # Check description
        description = frontmatter.get("description", "")
        if not description:
            warnings.append("Missing 'description' field")
        elif len(description) < 20:
            warnings.append("Description is very short. Consider adding more detail.")

        # Check tags format
        tags = frontmatter.get("tags", [])
        if not isinstance(tags, list):
            issues.append("'tags' must be a list")

        # Check icon
        icon = frontmatter.get("icon", "zap")
        if not isinstance(icon, str):
            warnings.append("'icon' should be a string")

        # Check iconColor format
        icon_color = frontmatter.get("iconColor", "#4A90E2")
        if not isinstance(icon_color, str) or not icon_color.startswith("#"):
            warnings.append("'iconColor' should be a hex color code (e.g., '#904AE2')")

        # Check content
        if not content or len(content.strip()) < 100:
            warnings.append(
                "Skill content is very short. Consider adding more detailed documentation."
            )

        # Check for template placeholders
        if "[" in content and "]" in content:
            warnings.append(
                "Content contains template placeholders like '[...]'. Consider replacing them with actual content."
            )

        # Build response
        result_lines = [f"✓ Validation complete for skill '{skill_id}'", ""]

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
            result_lines.append("✓ No issues found. Skill configuration is valid.")

        result_lines.append("")
        result_lines.append("**Configuration Summary:**")
        result_lines.append(f"- Name: {frontmatter.get('name', 'N/A')}")
        result_lines.append(
            f"- Description: {description[:100]}{'...' if len(description) > 100 else ''}"
        )
        result_lines.append(f"- Tags: {len(tags)} tag(s)")
        result_lines.append(f"- Icon: {icon} ({icon_color})")
        result_lines.append(f"- Content Length: {len(content)} characters")

        logger.info(
            f"[SKILL_ASSISTANT] Validated skill '{skill_id}': "
            f"{len(issues)} issue(s), {len(warnings)} warning(s)"
        )

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    except Exception as e:
        logger.error(f"[SKILL_ASSISTANT] Error validating skill: {e}", exc_info=True)
        return _error(f"Failed to validate skill: {str(e)}")


# Create the MCP server with skill assistant tools
skill_assistant_server = create_sdk_mcp_server(
    name="skill_assistant_tools",
    version="1.0.0",
    tools=[
        init_skill,
        validate_skill,
    ],
)
