"""CLI detection service for discovering installed AI CLI tools."""

import asyncio
import shutil
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.infrastructure.cli.config import (
    ALL_BACKENDS,
    AVAILABLE_MODELS,
    BACKEND_CLAUDE,
    BACKEND_CODEX,
    BACKEND_GEMINI,
    BACKEND_OPENCODE,
    CLIBackendInfo,
    DEFAULT_MODELS,
)

logger = get_logger(__name__)

# CLI command names for each backend
_CLI_COMMANDS: Dict[str, str] = {
    BACKEND_CLAUDE: "claude",
    BACKEND_CODEX: "codex",
    BACKEND_GEMINI: "gemini",
    BACKEND_OPENCODE: "opencode",
}

# Version flags for each CLI
_VERSION_FLAGS: Dict[str, str] = {
    BACKEND_CLAUDE: "--version",
    BACKEND_CODEX: "--version",
    BACKEND_GEMINI: "--version",
    BACKEND_OPENCODE: "--version",
}


async def _get_cli_version(command: str, flag: str) -> Optional[str]:
    """Get the version of a CLI tool."""
    try:
        proc = await asyncio.create_subprocess_exec(
            command,
            flag,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        if proc.returncode == 0:
            return stdout.decode().strip().split("\n")[0]
        return None
    except (FileNotFoundError, asyncio.TimeoutError, OSError):
        return None


async def detect_cli_backend(backend_name: str) -> CLIBackendInfo:
    """Detect a single CLI backend's installation status."""
    command = _CLI_COMMANDS.get(backend_name)
    if not command:
        return CLIBackendInfo(
            name=backend_name,
            installed=False,
            default_model=DEFAULT_MODELS.get(backend_name, ""),
            available_models=AVAILABLE_MODELS.get(backend_name, []),
        )

    path = shutil.which(command)
    version = None

    if path:
        flag = _VERSION_FLAGS.get(backend_name, "--version")
        version = await _get_cli_version(command, flag)

    return CLIBackendInfo(
        name=backend_name,
        installed=path is not None,
        version=version,
        path=path,
        default_model=DEFAULT_MODELS.get(backend_name, ""),
        available_models=AVAILABLE_MODELS.get(backend_name, []),
    )


async def detect_all_backends() -> List[CLIBackendInfo]:
    """Detect all supported CLI backends in parallel."""
    tasks = [detect_cli_backend(name) for name in ALL_BACKENDS]
    results = await asyncio.gather(*tasks)

    for info in results:
        if info.installed:
            logger.info(
                "cli_backend_detected",
                backend=info.name,
                version=info.version,
                path=info.path,
            )
        else:
            logger.debug("cli_backend_not_found", backend=info.name)

    return list(results)


async def detect_codeagent_wrapper() -> CLIBackendInfo:
    """Detect if codeagent-wrapper is installed."""
    path = shutil.which("codeagent-wrapper")
    version = None

    if path:
        version = await _get_cli_version("codeagent-wrapper", "--version")

    return CLIBackendInfo(
        name="codeagent-wrapper",
        installed=path is not None,
        version=version,
        path=path,
    )
