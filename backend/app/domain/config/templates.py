"""Project, agent, and skill template configurations."""


def get_project_template(
    project_name: str,
    project_id: str,
    project_path: str,
    created_date: str,
    description: str,
    project_manager: str,
    team_members: str,
) -> str:
    """
    Get the default template for a PROJECT.md file.

    Args:
        project_name: Display name of the project
        project_id: Unique identifier for the project
        project_path: Filesystem path to the project
        created_date: Date when the project was created
        description: Project description
        project_manager: Information about the project manager
        team_members: List of team members

    Returns:
        Template content for the project's PROJECT.md file
    """
    return f"""# {project_name}

**Project ID:** `{project_id}`
**Project Path:** `{project_path}`
**Created:** `{created_date}`

## Description

{description}

## Project Manager

{project_manager}

## Team Members

{team_members}

## Recent Activity

### Tasks Completed
No tasks completed yet

### Active Tasks
No active tasks

### Pending Tasks
No pending tasks
"""


def get_agent_template(agent_name: str, skills: list, allowed_tools: list) -> str:
    """
    Get the default template for a CLAUDE.md file.

    Args:
        agent_name: Name of the agent
        skills: List of skill IDs assigned to the agent
        allowed_tools: List of tool names allowed for the agent

    Returns:
        Template content for the agent's CLAUDE.md body
    """
    skills_section = (
        "\n".join(f"- {skill}" for skill in skills) if skills else "- (none configured)"
    )
    tools_section = (
        "\n".join(f"- {tool}" for tool in allowed_tools)
        if allowed_tools
        else "- (none configured)"
    )

    return f"""
# {agent_name}

Describe the agent's role and responsibilities here.

## Role Description

Provide a detailed description of what this agent does and when to use it.

## Responsibilities

- Responsibility 1
- Responsibility 2
- Responsibility 3

## Communication Style

Describe how this agent communicates (formal, casual, technical, etc.)

## Skills

This agent has access to the following skills:
{skills_section}

## Tools & Capabilities

Allowed tools:
{tools_section}

## Notes

Add any additional notes, warnings, or tips here.
"""


def get_skill_template(skill_name: str, description: str) -> str:
    """
    Get the default template for a SKILL.md file.

    Args:
        skill_name: Name of the skill
        description: Brief description of the skill

    Returns:
        Template content for the skill's SKILL.md body
    """
    return f"""
# {skill_name}

{description}

## Overview

Provide a detailed overview of what this skill does and when to use it.

## Usage

Explain how to use this skill effectively. Include examples if helpful.

### Examples

```
Add code examples or usage patterns here
```

## Prerequisites

List any requirements or setup needed:
- Requirement 1
- Requirement 2

## Best Practices

- Best practice 1
- Best practice 2

## Notes

Add any additional notes, warnings, or tips here.
"""
