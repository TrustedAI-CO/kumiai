"""
Claude SDK configuration settings.

Provides configuration for Claude SDK client infrastructure using Pydantic settings.
API keys are managed by the Claude SDK via environment variables, not explicitly in code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ClaudeSettings(BaseSettings):
    """
    Configuration for Claude SDK client infrastructure.

    The Claude SDK manages API keys automatically via:
    - ANTHROPIC_API_KEY environment variable
    - ~/.claude.json configuration file

    This settings class focuses on infrastructure-level configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Timeout settings
    connection_timeout_seconds: int = 30
    """Maximum time to wait for Claude SDK connection (seconds)."""

    execution_timeout_seconds: int = 900
    """Maximum time to wait for Claude execution (15 minutes)."""

    # Concurrency settings
    max_concurrent_sessions: int = 10
    """Maximum number of concurrent Claude sessions allowed."""

    # Default model
    default_model: str = "sonnet"
    """Default Claude model if agent doesn't specify one."""
