"""Session type value object."""

from enum import Enum


class SessionType(str, Enum):
    """
    Types of agent sessions.

    Session types define the role and behavior of an agent session:
    - PM: Project Manager session (coordinates project work)
    - SPECIALIST: Single specialist agent (focused expertise)
    - ASSISTANT: Interactive assistant (general help)
    - AGENT_ASSISTANT: Agent-based assistant (agent-driven interaction)
    - SKILL_ASSISTANT: Skill-based assistant (skill-driven interaction)
    """

    PM = "pm"
    SPECIALIST = "specialist"
    ASSISTANT = "assistant"
    AGENT_ASSISTANT = "agent_assistant"
    SKILL_ASSISTANT = "skill_assistant"

    def requires_project(self) -> bool:
        """
        Check if this session type requires a project association.

        Returns:
            True if project_id is required, False otherwise

        Examples:
            >>> SessionType.PM.requires_project()
            True
            >>> SessionType.ASSISTANT.requires_project()
            False
        """
        return self == self.PM
