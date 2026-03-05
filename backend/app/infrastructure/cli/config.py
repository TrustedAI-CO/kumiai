"""CLI backend configuration settings."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CLIBackendConfig(BaseSettings):
    """Configuration for multi-CLI backend support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    codeagent_wrapper_path: str = Field(
        default="codeagent-wrapper",
        description="Path to codeagent-wrapper binary",
    )

    connection_timeout_seconds: int = Field(
        default=30,
        description="Maximum time to wait for CLI connection (seconds)",
    )

    execution_timeout_seconds: int = Field(
        default=900,
        description="Maximum time to wait for CLI execution (15 minutes)",
    )

    max_concurrent_sessions: int = Field(
        default=10,
        description="Maximum number of concurrent CLI sessions",
    )

    skip_permissions: bool = Field(
        default=True,
        description="Skip permission prompts for CLI backends",
    )


# Backend type constants
BACKEND_CLAUDE = "claude"
BACKEND_CODEX = "codex"
BACKEND_GEMINI = "gemini"
BACKEND_OPENCODE = "opencode"

ALL_BACKENDS = [BACKEND_CLAUDE, BACKEND_CODEX, BACKEND_GEMINI, BACKEND_OPENCODE]

# Backends that use codeagent-wrapper (everything except Claude)
CODEAGENT_WRAPPER_BACKENDS = [BACKEND_CODEX, BACKEND_GEMINI, BACKEND_OPENCODE]

# Default models per backend
DEFAULT_MODELS: Dict[str, str] = {
    BACKEND_CLAUDE: "sonnet",
    BACKEND_CODEX: "gpt-5.3-codex",
    BACKEND_GEMINI: "gemini-2.5-flash",
    BACKEND_OPENCODE: "",
}

# Available models per backend (as of March 2026)
AVAILABLE_MODELS: Dict[str, List[str]] = {
    BACKEND_CLAUDE: [
        "haiku",
        "sonnet",
        "opus",
    ],
    BACKEND_CODEX: [
        "gpt-5.3-codex",
        "gpt-5.3-codex-spark",
        "gpt-5.1-codex-max",
        "gpt-5-codex-mini",
        "o3",
        "o4-mini",
    ],
    BACKEND_GEMINI: [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ],
    BACKEND_OPENCODE: [],
}


@dataclass(frozen=True)
class CLIBackendInfo:
    """Information about a detected CLI backend."""

    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    default_model: str = ""
    available_models: List[str] = field(default_factory=list)
