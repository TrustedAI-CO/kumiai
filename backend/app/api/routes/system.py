"""System API endpoints for app management."""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.infrastructure.cli.config import AVAILABLE_MODELS, DEFAULT_MODELS
from app.infrastructure.cli.detector import (
    detect_all_backends,
    detect_codeagent_wrapper,
)
from app.infrastructure.database.connection import get_engine
from app.infrastructure.database.models import Base

router = APIRouter()


class CLIBackendResponse(BaseModel):
    """Response for a single CLI backend."""

    name: str
    installed: bool
    version: str | None = None
    path: str | None = None
    default_model: str = ""
    available_models: List[str] = []


class CLIBackendsResponse(BaseModel):
    """Response for all CLI backends."""

    backends: List[CLIBackendResponse]
    codeagent_wrapper_installed: bool
    codeagent_wrapper_version: str | None = None


@router.get("/cli-backends")
async def get_cli_backends() -> CLIBackendsResponse:
    """Get available CLI backends and their installation status."""
    backends = await detect_all_backends()
    wrapper = await detect_codeagent_wrapper()

    return CLIBackendsResponse(
        backends=[
            CLIBackendResponse(
                name=b.name,
                installed=b.installed,
                version=b.version,
                path=b.path,
                default_model=DEFAULT_MODELS.get(b.name, ""),
                available_models=AVAILABLE_MODELS.get(b.name, []),
            )
            for b in backends
        ],
        codeagent_wrapper_installed=wrapper.installed,
        codeagent_wrapper_version=wrapper.version,
    )


@router.get("/version")
async def get_version_info() -> dict:
    """Get version info with last modification timestamps for frontend and backend."""
    import os
    import time

    def get_latest_mtime(directory: Path, extensions: tuple) -> str | None:
        """Find the most recent modification time in a directory."""
        latest = 0.0
        search_dir = directory
        if not search_dir.exists():
            return None
        for root, _, files in os.walk(search_dir):
            for f in files:
                if f.endswith(extensions):
                    mtime = os.path.getmtime(os.path.join(root, f))
                    if mtime > latest:
                        latest = mtime
        if latest == 0.0:
            return None
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest))

    # Find project directories by checking common patterns
    backend_dir = None
    frontend_dir = None
    for candidate in [
        Path(__file__).resolve().parents[3],  # backend/app/api/routes -> backend
    ]:
        if (candidate / "app").exists():
            backend_dir = candidate
            break

    if backend_dir:
        frontend_dir = backend_dir.parent / "frontend"

    backend_version = None
    frontend_version = None

    if backend_dir and backend_dir.exists():
        backend_version = get_latest_mtime(backend_dir / "app", (".py",))

    if frontend_dir and frontend_dir.exists():
        frontend_version = get_latest_mtime(frontend_dir / "src", (".ts", ".tsx"))

    return {
        "backend_version": backend_version,
        "frontend_version": frontend_version,
        "app_version": "2.0.0",
    }


class UsageWindowResponse(BaseModel):
    """A single usage/rate-limit window."""

    label: str
    utilization: float  # 0.0 – 1.0
    resets_at: Optional[str] = None


class LiveUsageEntry(BaseModel):
    """Live usage data for a provider."""

    windows: List[UsageWindowResponse] = []
    error: Optional[str] = None


class LiveUsageResponse(BaseModel):
    """Response for live CLI usage data."""

    usage: Dict[str, LiveUsageEntry]


class RateLimitInfo(BaseModel):
    """Rate limit details for a plan tier."""

    requests_per_minute: Optional[int] = None
    input_tokens_per_minute: Optional[int] = None
    output_tokens_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    tokens_per_day: Optional[int] = None
    reset_window: str = ""


class CLIUsageInfo(BaseModel):
    """Usage information for a single CLI backend."""

    name: str
    installed: bool
    plan: str = "unknown"
    plan_tier: str = ""
    configured_model: str = ""
    auth_status: str = "unknown"
    dashboard_url: str = ""
    rate_limits: Optional[RateLimitInfo] = None
    extra: Dict[str, Any] = {}


class CLIUsageResponse(BaseModel):
    """Response for CLI usage information."""

    backends: List[CLIUsageInfo]


# Known plan rate limits (as of March 2026)
CLAUDE_PLAN_LIMITS: Dict[str, RateLimitInfo] = {
    "max": RateLimitInfo(
        requests_per_minute=None,
        input_tokens_per_minute=None,
        output_tokens_per_minute=None,
        reset_window="5-hour rolling window",
    ),
    "pro": RateLimitInfo(
        requests_per_minute=None,
        input_tokens_per_minute=None,
        output_tokens_per_minute=None,
        reset_window="5-hour rolling window (lower than MAX)",
    ),
    "free": RateLimitInfo(
        requests_per_minute=None,
        input_tokens_per_minute=None,
        output_tokens_per_minute=None,
        reset_window="Daily reset",
    ),
}

CODEX_PLAN_LIMITS: Dict[str, RateLimitInfo] = {
    "plus": RateLimitInfo(
        reset_window="Monthly cycle",
    ),
    "pro": RateLimitInfo(
        reset_window="Monthly cycle (higher limits)",
    ),
}

GEMINI_PLAN_LIMITS: Dict[str, RateLimitInfo] = {
    "free": RateLimitInfo(
        requests_per_minute=15,
        requests_per_day=1500,
        tokens_per_day=1_000_000,
        reset_window="Daily reset (midnight PT)",
    ),
    "paid": RateLimitInfo(
        requests_per_minute=1000,
        requests_per_day=None,
        reset_window="Per-minute reset",
    ),
}


def _get_claude_usage() -> CLIUsageInfo:
    """Gather Claude Code usage info from ~/.claude.json."""
    claude_config = Path.home() / ".claude.json"
    plan = "unknown"
    plan_tier = ""
    auth_status = "not configured"
    configured_model = DEFAULT_MODELS.get("claude", "sonnet")
    extra: Dict[str, Any] = {}
    rate_limits: Optional[RateLimitInfo] = None

    if claude_config.exists():
        try:
            data = json.loads(claude_config.read_text())
            auth_status = "authenticated"

            oauth = data.get("oauthAccount", {})
            billing_type = oauth.get("billingType", "")
            org_name = oauth.get("organizationName", "")
            email = oauth.get("emailAddress", "")

            sub_type = data.get("subscriptionType", "")
            has_sub = data.get("hasAvailableSubscription", False)

            if sub_type == "max":
                plan = "MAX"
                plan_tier = "max"
                rate_limits = CLAUDE_PLAN_LIMITS["max"]
            elif sub_type == "pro":
                plan = "Pro"
                plan_tier = "pro"
                rate_limits = CLAUDE_PLAN_LIMITS["pro"]
            elif billing_type == "stripe_subscription" or has_sub:
                plan = "Pro"
                plan_tier = "pro"
                rate_limits = CLAUDE_PLAN_LIMITS["pro"]
            else:
                plan = "Free"
                plan_tier = "free"
                rate_limits = CLAUDE_PLAN_LIMITS["free"]

            if org_name:
                extra["organization"] = org_name
            if email:
                # Mask email to avoid exposing PII in API responses
                parts = email.split("@")
                if len(parts) == 2 and len(parts[0]) > 1:
                    masked = parts[0][0] + "***@" + parts[1]
                else:
                    masked = "***"
                extra["account"] = masked

            first_token = data.get("claudeCodeFirstTokenDate", "")
            if first_token:
                extra["member_since"] = first_token[:10]

        except (json.JSONDecodeError, OSError):
            pass

    return CLIUsageInfo(
        name="claude",
        installed=True,
        plan=plan,
        plan_tier=plan_tier,
        configured_model=configured_model,
        auth_status=auth_status,
        dashboard_url="https://claude.ai/settings/billing",
        rate_limits=rate_limits,
        extra=extra,
    )


def _get_codex_usage() -> CLIUsageInfo:
    """Gather Codex CLI usage info from ~/.codex/config.toml."""
    import shutil as sh

    if not sh.which("codex"):
        return CLIUsageInfo(name="codex", installed=False, auth_status="not installed")

    configured_model = DEFAULT_MODELS.get("codex", "")
    extra: Dict[str, Any] = {}

    codex_config = Path.home() / ".codex" / "config.toml"
    if codex_config.exists():
        try:
            content = codex_config.read_text()
            for line in content.splitlines():
                line = line.strip()
                if (
                    line.startswith("model")
                    and "=" in line
                    and not line.startswith("model_")
                ):
                    configured_model = line.split("=", 1)[1].strip().strip('"')
                if line.startswith("model_reasoning_effort"):
                    extra["reasoning_effort"] = line.split("=", 1)[1].strip().strip('"')
        except OSError:
            pass

    return CLIUsageInfo(
        name="codex",
        installed=True,
        plan="ChatGPT",
        plan_tier="subscription",
        configured_model=configured_model,
        auth_status="authenticated",
        dashboard_url="https://platform.openai.com/usage",
        rate_limits=CODEX_PLAN_LIMITS.get("pro"),
        extra=extra,
    )


def _get_gemini_usage() -> CLIUsageInfo:
    """Gather Gemini CLI usage info."""
    import shutil as sh

    if not sh.which("gemini"):
        return CLIUsageInfo(name="gemini", installed=False, auth_status="not installed")

    configured_model = DEFAULT_MODELS.get("gemini", "")
    extra: Dict[str, Any] = {}
    plan_tier = "free"

    gemini_settings = Path.home() / ".config" / "gemini" / "settings.json"
    if gemini_settings.exists():
        try:
            data = json.loads(gemini_settings.read_text())
            if "model" in data:
                configured_model = data["model"]
        except (json.JSONDecodeError, OSError):
            pass

    return CLIUsageInfo(
        name="gemini",
        installed=True,
        plan="Google AI",
        plan_tier=plan_tier,
        configured_model=configured_model,
        auth_status="authenticated",
        dashboard_url="https://aistudio.google.com/apikey",
        rate_limits=GEMINI_PLAN_LIMITS.get(plan_tier),
        extra=extra,
    )


def _get_opencode_usage() -> CLIUsageInfo:
    """Gather OpenCode usage info."""
    import shutil as sh

    if not sh.which("opencode"):
        return CLIUsageInfo(
            name="opencode", installed=False, auth_status="not installed"
        )

    return CLIUsageInfo(
        name="opencode",
        installed=True,
        plan="Open Source",
        plan_tier="oss",
        configured_model="",
        auth_status="configured",
        dashboard_url="",
    )


@router.get("/cli-usage")
async def get_cli_usage() -> CLIUsageResponse:
    """Get usage and configuration info for all CLI backends."""
    backends = [
        _get_claude_usage(),
        _get_codex_usage(),
        _get_gemini_usage(),
        _get_opencode_usage(),
    ]
    return CLIUsageResponse(backends=backends)


@router.get("/cli-usage/live")
async def get_live_cli_usage() -> LiveUsageResponse:
    """Fetch real-time usage data from each CLI provider's API."""
    from app.infrastructure.cli.usage_fetcher import fetch_all_usage

    raw = await fetch_all_usage()
    usage: Dict[str, LiveUsageEntry] = {}
    for provider, result in raw.items():
        usage[provider] = LiveUsageEntry(
            windows=[
                UsageWindowResponse(
                    label=w.label,
                    utilization=w.utilization,
                    resets_at=w.resets_at,
                )
                for w in result.windows
            ],
            error=result.error,
        )
    return LiveUsageResponse(usage=usage)


@router.post("/reset")
async def reset_app() -> dict:
    """
    Reset the application to initial state.

    This will delete all data except projects:
    - Database (kumiai.db)
    - Skills directory
    - Agents directory
    - User settings

    Projects directory will be preserved.
    """
    try:
        # Remove database
        db_path = Path(settings.kumiai_home) / "kumiai.db"
        if db_path.exists():
            db_path.unlink()

        # Remove skills directory
        skills_dir = Path(settings.skills_dir)
        if skills_dir.exists():
            shutil.rmtree(skills_dir)

        # Remove agents directory
        agents_dir = Path(settings.agents_dir)
        if agents_dir.exists():
            shutil.rmtree(agents_dir)

        # Note: Projects directory is NOT deleted
        # projects_dir = Path(settings.projects_dir)

        # Recreate database tables
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        return {
            "message": "Application reset successfully. Database, skills, and agents have been deleted. Projects preserved."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset application: {str(e)}"
        )
