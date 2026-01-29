"""Welcome message configurations for different session types."""

from typing import Dict, TypedDict

from app.domain.value_objects import SessionType


class WelcomeMessageConfig(TypedDict):
    """Configuration for a welcome message."""

    content: str
    default_name: str


# Welcome messages for each session type that supports auto-welcome
WELCOME_MESSAGES: Dict[SessionType, WelcomeMessageConfig] = {
    SessionType.PM: {
        "content": "Hello! I'm your PM assistant. What would you like to work on?",
        "default_name": "PM Assistant",
    },
    SessionType.AGENT_ASSISTANT: {
        "content": "Hello! I'm your Agent assistant. I can help you create and manage AI agent definitions. What would you like to do?",
        "default_name": "Agent Assistant",
    },
    SessionType.SKILL_ASSISTANT: {
        "content": "Hello! I'm your Skill assistant. I can help you create and manage skill definitions. What would you like to do?",
        "default_name": "Skill Assistant",
    },
}


def get_welcome_message(session_type: SessionType) -> WelcomeMessageConfig | None:
    """
    Get welcome message configuration for a session type.

    Args:
        session_type: Session type to get welcome message for

    Returns:
        Welcome message config if available, None otherwise
    """
    return WELCOME_MESSAGES.get(session_type)
