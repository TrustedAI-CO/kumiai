"""Credential service for building environment variables from stored credentials."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CredentialService:
    """
    Service for reading stored credentials and producing env var dicts.

    Used by session builders to inject provider credentials
    (Anthropic API key or AWS Bedrock credentials) into ClaudeAgentOptions.env.

    Uses get_repository_session() for self-contained DB access,
    making it safe to use as a singleton in long-lived objects.
    """

    async def get_provider_env(self) -> Dict[str, str]:
        """
        Read stored credentials and return environment variables dict.

        Returns:
            Dict of env vars to pass to ClaudeAgentOptions.env.
            Empty dict if no credentials are configured.
        """
        try:
            from app.infrastructure.database.connection import get_repository_session
            from app.infrastructure.database.repositories import (
                PostgresUserProfileRepository,
            )

            async with get_repository_session() as db:
                repo = PostgresUserProfileRepository(db)
                profile = await repo.get_default_profile()

                if not profile:
                    return {}

                settings = profile.get("settings", {})
                cred_config = settings.get("credentials", {})
                provider = cred_config.get("provider", "anthropic")

                if provider == "anthropic":
                    return self._build_anthropic_env(cred_config)
                elif provider == "bedrock":
                    return self._build_bedrock_env(cred_config)
                else:
                    logger.warning("Unknown provider: %s", provider)
                    return {}

        except Exception as e:
            logger.error("Failed to fetch credentials: %s", str(e))
            return {}

    def _build_anthropic_env(self, cred_config: dict) -> Dict[str, str]:
        """Build env vars for Anthropic Direct provider."""
        api_key = cred_config.get("anthropic_api_key", "")
        if not api_key:
            return {}

        logger.info("Anthropic env prepared")
        return {"ANTHROPIC_API_KEY": api_key}

    def _build_bedrock_env(self, cred_config: dict) -> Dict[str, str]:
        """Build env vars for AWS Bedrock provider."""
        aws = cred_config.get("aws", {})
        access_key = aws.get("aws_access_key_id", "")
        secret_key = aws.get("aws_secret_access_key", "")

        if not access_key or not secret_key:
            logger.warning(
                "Bedrock credentials incomplete: has_access_key=%s, has_secret_key=%s",
                bool(access_key),
                bool(secret_key),
            )
            return {}

        env: Dict[str, str] = {
            "AWS_ACCESS_KEY_ID": access_key,
            "AWS_SECRET_ACCESS_KEY": secret_key,
            "AWS_REGION": aws.get("aws_region", "us-east-1"),
            "AWS_DEFAULT_REGION": aws.get("aws_region", "us-east-1"),
        }

        session_token = aws.get("aws_session_token")
        if session_token:
            env["AWS_SESSION_TOKEN"] = session_token

        logger.info(
            "Bedrock env prepared: region=%s, has_session_token=%s",
            aws.get("aws_region", "us-east-1"),
            bool(session_token),
        )

        return env
