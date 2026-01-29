"""Session role configuration."""

from dataclasses import dataclass, field
from typing import List, Optional

from ..value_objects.session_type import SessionType


@dataclass(frozen=True)
class MessageFilterConfig:
    """Message filtering configuration for UI display."""

    show_roles: List[str] = field(default_factory=lambda: ["user", "assistant", "tool"])
    show_agent_names_only: Optional[List[str]] = None
    hide_specialist: bool = False


@dataclass(frozen=True)
class RoleConfig:
    """Configuration for a session role."""

    display_name: str
    icon: str
    message_filter: MessageFilterConfig
    supports_specialists: bool
    auto_save: bool
    auto_save_type: Optional[str] = None
    requires_project: bool = False
    default_working_dir: str = "project_root"  # "project_root" | "session_dir"


# Role configurations
_ROLE_CONFIGS = {
    SessionType.PM: RoleConfig(
        display_name="Project Manager",
        icon="briefcase",
        message_filter=MessageFilterConfig(),
        supports_specialists=False,
        auto_save=False,
        requires_project=True,
        default_working_dir="project_root",
    ),
    SessionType.SPECIALIST: RoleConfig(
        display_name="Specialist",
        icon="users",
        message_filter=MessageFilterConfig(
            show_agent_names_only=None,
            hide_specialist=False,
        ),
        supports_specialists=True,
        auto_save=False,
        default_working_dir="session_dir",
    ),
    SessionType.ASSISTANT: RoleConfig(
        display_name="Assistant",
        icon="message-circle",
        message_filter=MessageFilterConfig(),
        supports_specialists=False,
        auto_save=False,
        default_working_dir="project_root",
    ),
    SessionType.AGENT_ASSISTANT: RoleConfig(
        display_name="Agent Assistant",
        icon="bot",
        message_filter=MessageFilterConfig(),
        supports_specialists=False,
        auto_save=False,
        default_working_dir="project_root",
    ),
    SessionType.SKILL_ASSISTANT: RoleConfig(
        display_name="Skill Assistant",
        icon="zap",
        message_filter=MessageFilterConfig(),
        supports_specialists=False,
        auto_save=False,
        default_working_dir="project_root",
    ),
}


def get_role_config(session_type: SessionType) -> RoleConfig:
    """
    Get role configuration for a session type.

    Args:
        session_type: The session type

    Returns:
        Role configuration

    Raises:
        ValueError: If session type has no configuration
    """
    config = _ROLE_CONFIGS.get(session_type)
    if not config:
        raise ValueError(f"No configuration found for session type: {session_type}")
    return config
