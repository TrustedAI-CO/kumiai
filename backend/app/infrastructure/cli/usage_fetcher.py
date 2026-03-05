"""Fetch real-time usage/quota data from each CLI provider's internal API.

Ported from craw-empire's credential-tools.ts + usage-cli-tools.ts.
"""

import json
import os
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


@dataclass(frozen=True)
class UsageWindow:
    """A single rate-limit / quota window."""

    label: str
    utilization: float  # 0.0 – 1.0
    resets_at: Optional[str] = None  # ISO 8601


@dataclass(frozen=True)
class UsageResult:
    """Result of fetching usage for one provider."""

    windows: List[UsageWindow] = field(default_factory=list)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Credential readers
# ---------------------------------------------------------------------------

def _read_claude_token() -> Optional[str]:
    """Read Claude OAuth access token from macOS Keychain or credentials file."""
    if platform.system() == "Darwin":
        try:
            raw = subprocess.check_output(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                timeout=3,
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            data = json.loads(raw)
            token = (data.get("claudeAiOauth") or {}).get("accessToken")
            if token:
                return token
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            pass

    creds_path = Path.home() / ".claude" / ".credentials.json"
    if creds_path.exists():
        try:
            data = json.loads(creds_path.read_text())
            token = (data.get("claudeAiOauth") or {}).get("accessToken")
            if token:
                return token
        except (json.JSONDecodeError, OSError):
            pass

    return None


def _read_codex_tokens() -> Optional[Dict[str, str]]:
    """Read Codex (OpenAI) access_token + account_id from ~/.codex/auth.json."""
    auth_path = Path.home() / ".codex" / "auth.json"
    try:
        data = json.loads(auth_path.read_text())
        tokens = data.get("tokens", {})
        access_token = tokens.get("access_token")
        account_id = tokens.get("account_id")
        if access_token and account_id:
            return {"access_token": access_token, "account_id": account_id}
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _read_gemini_creds_from_keychain() -> Optional[Dict[str, Any]]:
    """Read Gemini OAuth creds from macOS Keychain."""
    if platform.system() != "Darwin":
        return None
    try:
        raw = subprocess.check_output(
            ["security", "find-generic-password", "-s", "gemini-cli-oauth", "-a", "main-account", "-w"],
            timeout=3,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        if not raw:
            return None
        stored = json.loads(raw)
        token_data = stored.get("token", {})
        if not token_data.get("accessToken"):
            return None
        return {
            "access_token": token_data["accessToken"],
            "refresh_token": token_data.get("refreshToken", ""),
            "expiry_date": token_data.get("expiresAt", 0),
        }
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None


def _read_gemini_creds_from_file() -> Optional[Dict[str, Any]]:
    """Read Gemini OAuth creds from ~/.gemini/oauth_creds.json."""
    try:
        creds_path = Path.home() / ".gemini" / "oauth_creds.json"
        data = json.loads(creds_path.read_text())
        if data.get("access_token"):
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", ""),
                "expiry_date": data.get("expiry_date", 0),
            }
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _read_gemini_creds() -> Optional[Dict[str, Any]]:
    return _read_gemini_creds_from_keychain() or _read_gemini_creds_from_file()


async def _get_gemini_project_id(token: str) -> Optional[str]:
    """Get Gemini Cloud project ID."""
    env_project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
    if env_project:
        return env_project

    settings_path = Path.home() / ".gemini" / "settings.json"
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text())
            project = data.get("cloudaicompanionProject")
            if project:
                return project
        except (json.JSONDecodeError, OSError):
            pass

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                "https://cloudcode-pa.googleapis.com/v1internal:loadCodeAssist",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "metadata": {
                        "ideType": "GEMINI_CLI",
                        "platform": "PLATFORM_UNSPECIFIED",
                        "pluginType": "GEMINI",
                    }
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("cloudaicompanionProject")
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Usage fetchers
# ---------------------------------------------------------------------------

async def fetch_claude_usage() -> UsageResult:
    """Fetch Claude usage from Anthropic OAuth usage API."""
    token = _read_claude_token()
    if not token:
        return UsageResult(error="unauthenticated")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.anthropic.com/api/oauth/usage",
                headers={
                    "Authorization": f"Bearer {token}",
                    "anthropic-beta": "oauth-2025-04-20",
                },
            )
            if resp.status_code != 200:
                return UsageResult(error=f"http_{resp.status_code}")

            data = resp.json()
            label_map = {
                "five_hour": "5-hour",
                "seven_day": "7-day",
                "seven_day_sonnet": "7-day Sonnet",
                "seven_day_opus": "7-day Opus",
            }
            windows: List[UsageWindow] = []
            for key, label in label_map.items():
                entry = data.get(key)
                if entry and isinstance(entry, dict):
                    util_raw = entry.get("utilization", 0)
                    windows.append(UsageWindow(
                        label=label,
                        utilization=round(util_raw) / 100,  # API returns 0-100
                        resets_at=entry.get("resets_at"),
                    ))
            return UsageResult(windows=windows)
    except Exception:
        return UsageResult(error="unavailable")


async def fetch_codex_usage() -> UsageResult:
    """Fetch Codex/OpenAI usage from ChatGPT backend API."""
    tokens = _read_codex_tokens()
    if not tokens:
        return UsageResult(error="unauthenticated")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://chatgpt.com/backend-api/wham/usage",
                headers={
                    "Authorization": f"Bearer {tokens['access_token']}",
                    "ChatGPT-Account-Id": tokens["account_id"],
                },
            )
            if resp.status_code != 200:
                return UsageResult(error=f"http_{resp.status_code}")

            data = resp.json()
            rate_limit = data.get("rate_limit", {})
            windows: List[UsageWindow] = []

            pw = rate_limit.get("primary_window")
            if pw:
                reset_ts = pw.get("reset_at")
                windows.append(UsageWindow(
                    label="5-hour",
                    utilization=(pw.get("used_percent", 0)) / 100,
                    resets_at=_ts_to_iso(reset_ts) if reset_ts else None,
                ))

            sw = rate_limit.get("secondary_window")
            if sw:
                reset_ts = sw.get("reset_at")
                windows.append(UsageWindow(
                    label="7-day",
                    utilization=(sw.get("used_percent", 0)) / 100,
                    resets_at=_ts_to_iso(reset_ts) if reset_ts else None,
                ))

            return UsageResult(windows=windows)
    except Exception:
        return UsageResult(error="unavailable")


async def fetch_gemini_usage() -> UsageResult:
    """Fetch Gemini usage from Google Cloud internal API."""
    creds = _read_gemini_creds()
    if not creds:
        return UsageResult(error="unauthenticated")

    token = creds["access_token"]
    project_id = await _get_gemini_project_id(token)
    if not project_id:
        return UsageResult(error="unavailable")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"project": project_id},
            )
            if resp.status_code != 200:
                return UsageResult(error=f"http_{resp.status_code}")

            data = resp.json()
            windows: List[UsageWindow] = []
            for bucket in data.get("buckets", []):
                model_id = bucket.get("modelId", "Quota")
                if model_id.endswith("_vertex"):
                    continue
                remaining = bucket.get("remainingFraction", 1.0)
                windows.append(UsageWindow(
                    label=model_id,
                    utilization=round((1 - remaining) * 100) / 100,
                    resets_at=bucket.get("resetTime"),
                ))
            return UsageResult(windows=windows)
    except Exception:
        return UsageResult(error="unavailable")


async def fetch_all_usage() -> Dict[str, UsageResult]:
    """Fetch usage for all providers in parallel."""
    import asyncio
    results = await asyncio.gather(
        fetch_claude_usage(),
        fetch_codex_usage(),
        fetch_gemini_usage(),
        return_exceptions=True,
    )

    providers = ["claude", "codex", "gemini"]
    usage: Dict[str, UsageResult] = {}
    for name, result in zip(providers, results):
        if isinstance(result, Exception):
            usage[name] = UsageResult(error="unavailable")
        else:
            usage[name] = result
    return usage


def _ts_to_iso(ts: int) -> str:
    """Convert Unix timestamp (seconds) to ISO 8601 string."""
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
