"""API credentials management routes."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_user_profile_service
from app.application.services import UserProfileService

router = APIRouter()


class AWSCredentials(BaseModel):
    """AWS credentials input."""

    aws_access_key_id: str = Field(..., min_length=1)
    aws_secret_access_key: str = Field(..., min_length=1)
    aws_session_token: Optional[str] = None
    aws_region: str = Field(default="us-east-1")


class CredentialsConfigRequest(BaseModel):
    """Request to save credentials configuration."""

    provider: Literal["anthropic", "bedrock"] = "anthropic"
    anthropic_api_key: Optional[str] = None
    aws_credentials: Optional[AWSCredentials] = None


class CredentialsConfigResponse(BaseModel):
    """Response with masked credentials."""

    provider: str
    anthropic_configured: bool = False
    anthropic_api_key_masked: Optional[str] = None
    aws_configured: bool = False
    aws_access_key_id_masked: Optional[str] = None
    aws_region: Optional[str] = None
    has_session_token: bool = False


def _mask_key(key: str) -> Optional[str]:
    """Mask a key, showing only first 4 and last 4 characters."""
    if not key:
        return None
    if len(key) <= 8:
        return key[:2] + "..." + key[-2:]
    return key[:4] + "..." + key[-4:]


def _build_response(cred_config: dict) -> CredentialsConfigResponse:
    """Build a masked response from stored credentials config."""
    provider = cred_config.get("provider", "anthropic")

    # Anthropic
    anthropic_key = cred_config.get("anthropic_api_key", "")
    anthropic_configured = bool(anthropic_key)

    # AWS
    aws = cred_config.get("aws", {})
    access_key = aws.get("aws_access_key_id", "")
    aws_configured = bool(access_key and aws.get("aws_secret_access_key"))

    return CredentialsConfigResponse(
        provider=provider,
        anthropic_configured=anthropic_configured,
        anthropic_api_key_masked=_mask_key(anthropic_key) if anthropic_key else None,
        aws_configured=aws_configured,
        aws_access_key_id_masked=_mask_key(access_key) if access_key else None,
        aws_region=aws.get("aws_region"),
        has_session_token=bool(aws.get("aws_session_token")),
    )


@router.get("/settings/credentials", response_model=CredentialsConfigResponse)
async def get_credentials_config(
    service: UserProfileService = Depends(get_user_profile_service),
):
    """Get current credentials configuration (secrets masked)."""
    profile = await service.get_profile()
    settings = profile.get("settings", {})
    cred_config = settings.get("credentials", {})
    return _build_response(cred_config)


@router.post("/settings/credentials", response_model=CredentialsConfigResponse)
async def save_credentials_config(
    request: CredentialsConfigRequest,
    service: UserProfileService = Depends(get_user_profile_service),
):
    """Save credentials configuration."""
    cred_settings: dict = {
        "provider": request.provider,
    }

    if request.anthropic_api_key:
        cred_settings["anthropic_api_key"] = request.anthropic_api_key

    if request.aws_credentials:
        cred_settings["aws"] = {
            "aws_access_key_id": request.aws_credentials.aws_access_key_id,
            "aws_secret_access_key": request.aws_credentials.aws_secret_access_key,
            "aws_session_token": request.aws_credentials.aws_session_token,
            "aws_region": request.aws_credentials.aws_region,
        }

    await service.update_profile(settings={"credentials": cred_settings})

    return _build_response(cred_settings)


@router.delete("/settings/credentials")
async def clear_credentials(
    service: UserProfileService = Depends(get_user_profile_service),
):
    """Clear stored credentials."""
    await service.update_profile(settings={"credentials": {"provider": "anthropic"}})
    return {"status": "cleared"}
