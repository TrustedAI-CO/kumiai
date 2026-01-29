"""Domain configuration module."""

from .session_roles import RoleConfig, MessageFilterConfig, get_role_config
from .system_prompts import (
    PM_PROMPT,
    SPECIALIST_PROMPT,
    ASSISTANT_PROMPT,
    format_system_prompt,
)

__all__ = [
    "RoleConfig",
    "MessageFilterConfig",
    "get_role_config",
    "PM_PROMPT",
    "SPECIALIST_PROMPT",
    "ASSISTANT_PROMPT",
    "format_system_prompt",
]
