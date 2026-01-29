"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=7892, description="API port")
    api_reload: bool = Field(default=True, description="Enable auto-reload")

    # Database Settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///{kumiai_home}/kumiai.db",
        description="Database connection URL (SQLite by default)",
    )
    db_pool_size: int = Field(default=5, description="Database connection pool size")
    db_max_overflow: int = Field(default=5, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    db_pool_recycle: int = Field(
        default=3600, description="Connection recycle time in seconds"
    )

    # Paths
    kumiai_home: Path = Field(
        default_factory=lambda: Path.home() / ".kumiai",
        description="KumiAI home directory",
    )
    skills_dir: Path = Field(
        default_factory=lambda: Path.home() / ".kumiai" / "skills",
        description="Skills directory",
    )
    agents_dir: Path = Field(
        default_factory=lambda: Path.home() / ".kumiai" / "agents",
        description="Agents directory",
    )
    projects_dir: Path = Field(
        default_factory=lambda: Path.home() / ".kumiai" / "projects",
        description="Projects directory",
    )
    storage_dir: Path = Field(
        default_factory=lambda: Path.home() / ".kumiai" / "storage",
        description="Storage directory for uploaded files",
    )

    # Claude AI Settings
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # Session Settings
    session_timeout: int = Field(default=1800, description="Session timeout in seconds")
    session_cleanup_interval: int = Field(
        default=300, description="Session cleanup interval in seconds"
    )

    # Feature Flags
    enable_mcp: bool = Field(default=True, description="Enable MCP servers")
    enable_custom_tools: bool = Field(default=True, description="Enable custom tools")

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )

    # Environment
    environment: str = Field(default="development", description="Environment name")

    @field_validator(
        "kumiai_home",
        "skills_dir",
        "agents_dir",
        "projects_dir",
        "storage_dir",
        mode="before",
    )
    @classmethod
    def parse_path(cls, v: Union[str, Path]) -> Path:
        """Parse string paths to Path objects."""
        if isinstance(v, str):
            return Path(v).expanduser().resolve()
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v

    def get_database_url(self) -> str:
        """Get database URL with kumiai_home properly interpolated."""
        if "{kumiai_home}" in self.database_url:
            return self.database_url.replace("{kumiai_home}", str(self.kumiai_home))
        return self.database_url


# Global settings instance
settings = Settings()
