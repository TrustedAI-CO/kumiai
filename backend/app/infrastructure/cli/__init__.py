"""Multi-CLI backend infrastructure.

Provides abstraction for multiple AI CLI backends:
- Claude: Uses claude_agent_sdk directly
- Codex/Gemini/OpenCode: Uses codeagent-wrapper
"""

from app.infrastructure.cli.backend_protocol import CLIBackend
from app.infrastructure.cli.codeagent_client import CodeAgentWrapperClient
from app.infrastructure.cli.config import (
    ALL_BACKENDS,
    AVAILABLE_MODELS,
    BACKEND_CLAUDE,
    BACKEND_CODEX,
    BACKEND_GEMINI,
    BACKEND_OPENCODE,
    CODEAGENT_WRAPPER_BACKENDS,
    CLIBackendConfig,
    CLIBackendInfo,
    DEFAULT_MODELS,
)
from app.infrastructure.cli.detector import (
    detect_all_backends,
    detect_cli_backend,
    detect_codeagent_wrapper,
)

__all__ = [
    "CLIBackend",
    "CodeAgentWrapperClient",
    "CLIBackendConfig",
    "CLIBackendInfo",
    "ALL_BACKENDS",
    "AVAILABLE_MODELS",
    "BACKEND_CLAUDE",
    "BACKEND_CODEX",
    "BACKEND_GEMINI",
    "BACKEND_OPENCODE",
    "CODEAGENT_WRAPPER_BACKENDS",
    "DEFAULT_MODELS",
    "detect_all_backends",
    "detect_cli_backend",
    "detect_codeagent_wrapper",
]
