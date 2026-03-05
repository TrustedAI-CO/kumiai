"""Request DTOs for API endpoints."""

import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_VALID_CLI_BACKENDS = {"claude", "codex", "gemini", "opencode"}
_MODEL_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-._]{0,99}$")


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    agent_id: str = Field(
        ..., max_length=255, description="Agent string ID (e.g., 'product-manager')"
    )
    project_id: Optional[UUID] = Field(
        None, description="UUID of the project (required for PM sessions)"
    )
    session_type: str = Field(
        ...,
        description="Type of session: pm, specialist, assistant, agent_assistant, skill_assistant",
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Initial session context"
    )

    @field_validator("session_type")
    @classmethod
    def validate_session_type(cls, v: str) -> str:
        """Validate session type is one of the allowed values."""
        allowed = [
            "pm",
            "specialist",
            "assistant",
            "agent_assistant",
            "skill_assistant",
        ]
        if v not in allowed:
            raise ValueError(f"session_type must be one of {allowed}")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: Optional[Dict]) -> Dict:
        """Ensure context is a dict."""
        return v or {}


class ExecuteQueryRequest(BaseModel):
    """Request to execute a query in a session."""

    query: str = Field(
        ..., min_length=1, max_length=10000, description="User query to execute"
    )
    stream: bool = Field(default=True, description="Whether to stream the response")


class UpdateSessionStageRequest(BaseModel):
    """Request to update a session's kanban stage."""

    stage: str = Field(..., description="Kanban stage: backlog, active, waiting, done")

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        """Validate stage is one of the allowed values."""
        allowed = ["backlog", "active", "waiting", "done"]
        if v not in allowed:
            raise ValueError(f"stage must be one of {allowed}")
        return v


class CreateProjectRequest(BaseModel):
    """Request to create a new project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Project description"
    )
    path: Optional[str] = Field(
        None,
        description="Filesystem path to the project. If not provided, creates under ~/.kumiai/projects/{sanitized-name}",
    )
    pm_agent_id: Optional[str] = Field(
        None, max_length=255, description="PM agent ID to assign"
    )
    team_member_ids: Optional[list[str]] = Field(
        None, description="List of agent IDs to assign to the project"
    )


class UpdateProjectRequest(BaseModel):
    """Request to update a project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    path: Optional[str] = None
    team_member_ids: Optional[list[str]] = Field(
        None, description="List of agent IDs to assign to the project"
    )


class AssignPMRequest(BaseModel):
    """Request to assign a PM to a project."""

    pm_agent_id: str = Field(..., max_length=255, description="PM agent ID")


class CreateSkillRequest(BaseModel):
    """Request to create a new skill."""

    name: str = Field(..., min_length=1, max_length=255, description="Skill name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Skill description"
    )
    file_path: Optional[str] = Field(
        None,
        description="Path to skill definition file (auto-generated if not provided)",
    )
    tags: Optional[List[str]] = Field(default_factory=list, description="Skill tags")
    # Frontend-specific fields
    id: Optional[str] = Field(None, description="Custom skill ID")
    category: Optional[str] = Field("general", description="Skill category")
    license: Optional[str] = Field("MIT", description="Skill license")
    version: Optional[str] = Field("1.0.0", description="Skill version")
    content: Optional[str] = Field(None, description="Skill content/documentation")
    icon: Optional[str] = Field("zap", description="Icon name")
    iconColor: Optional[str] = Field("#4A90E2", description="Icon background color")


class UpdateSkillRequest(BaseModel):
    """Request to update a skill."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    file_path: Optional[str] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    iconColor: Optional[str] = None


class ImportSkillRequest(BaseModel):
    """Request to import a skill from a source URL or local path."""

    source: str = Field(
        ...,
        min_length=1,
        description="Source URL (GitHub) or local filesystem path to skill directory",
    )
    skill_id: Optional[str] = Field(
        None,
        description="Optional custom skill ID (defaults to directory name from source)",
    )


class CreateAgentRequest(BaseModel):
    """Request to create a new agent."""

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Agent description"
    )
    id: Optional[str] = Field(
        None, description="Custom agent ID (auto-generated from name if not provided)"
    )
    file_path: Optional[str] = Field(
        None, description="Path to agent directory (auto-generated if not provided)"
    )
    cli_backend: Optional[str] = Field(
        "claude", description="CLI backend (claude, codex, gemini, opencode)"
    )
    default_model: Optional[str] = Field(
        "sonnet", description="Default LLM model (backend-specific)"
    )
    tags: Optional[List[str]] = Field(default_factory=list, description="Agent tags")
    skills: Optional[List[str]] = Field(default_factory=list, description="Skill IDs")
    allowed_tools: Optional[List[str]] = Field(
        default_factory=list, description="Allowed tool names"
    )
    allowed_mcps: Optional[List[str]] = Field(
        default_factory=list, description="Allowed MCP server IDs"
    )
    icon_color: Optional[str] = Field("#4A90E2", description="Icon color (hex format)")

    @field_validator("cli_backend")
    @classmethod
    def validate_cli_backend(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_CLI_BACKENDS:
            raise ValueError(f"cli_backend must be one of {_VALID_CLI_BACKENDS}")
        return v

    @field_validator("default_model")
    @classmethod
    def validate_default_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _MODEL_NAME_RE.match(v):
            raise ValueError("default_model contains invalid characters")
        return v


class UpdateAgentRequest(BaseModel):
    """Request to update an agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    cli_backend: Optional[str] = None
    default_model: Optional[str] = None
    tags: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    allowed_tools: Optional[List[str]] = None
    allowed_mcps: Optional[List[str]] = None
    icon_color: Optional[str] = None

    @field_validator("cli_backend")
    @classmethod
    def validate_cli_backend(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_CLI_BACKENDS:
            raise ValueError(f"cli_backend must be one of {_VALID_CLI_BACKENDS}")
        return v

    @field_validator("default_model")
    @classmethod
    def validate_default_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _MODEL_NAME_RE.match(v):
            raise ValueError("default_model contains invalid characters")
        return v


class CreateMessageRequest(BaseModel):
    """Request to create a new message."""

    id: UUID = Field(..., description="Message UUID")
    session_id: UUID = Field(..., description="UUID of the session")
    role: str = Field(
        ..., description="Message role: user, assistant, system, tool_result"
    )
    content: str = Field(..., min_length=1, description="Message content")
    sequence: int = Field(..., ge=0, description="Message sequence number")
    tool_use_id: Optional[str] = Field(
        None, description="Tool use ID for tool result messages"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    # Sender attribution fields
    agent_id: Optional[str] = Field(
        None,
        max_length=255,
        description="Source of truth for which agent sent the message",
    )
    agent_name: Optional[str] = Field(
        None, max_length=255, description="Display name of the sending agent"
    )
    from_instance_id: Optional[UUID] = Field(
        None,
        description="Session ID where message originated (for cross-session routing)",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is one of the allowed values."""
        allowed = ["user", "assistant", "system", "tool_result"]
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v
