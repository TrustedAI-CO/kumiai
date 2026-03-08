"""Retry policy for recoverable session execution errors."""

import asyncio
from dataclasses import dataclass, field


@dataclass
class RetryDecision:
    retryable: bool
    corrective_message: str | None
    error_label: str


@dataclass
class RetryState:
    max_retries: int
    backoff_seconds: float = 1.0
    attempt: int = field(default=0, init=False)

    def can_retry(self) -> bool:
        return self.attempt < self.max_retries

    def record_attempt(self) -> None:
        self.attempt += 1

    def get_delay(self) -> float:
        return self.backoff_seconds * self.attempt


class RetryClassifier:
    """Classifies exceptions as retryable or not, with corrective messages."""

    def classify(self, error: Exception) -> RetryDecision:
        # Import here to avoid circular imports and keep SDK dependency local
        from claude_agent_sdk._errors import (
            CLIJSONDecodeError,
            CLINotFoundError,
            CLIConnectionError,
            ProcessError,
        )

        # CancelledError must never be retried — caller should re-raise
        if isinstance(error, asyncio.CancelledError):
            return RetryDecision(
                retryable=False,
                corrective_message=None,
                error_label="CancelledError",
            )

        if isinstance(error, CLIJSONDecodeError):
            return RetryDecision(
                retryable=True,
                corrective_message=(
                    "[System] The previous tool call returned data exceeding the 1MB "
                    "JSON buffer limit. Please use a more targeted approach — read "
                    "specific line ranges, use grep/head/tail to filter output, or "
                    "break the task into smaller steps."
                ),
                error_label="CLIJSONDecodeError",
            )

        # Check CLINotFoundError before CLIConnectionError (it's a subclass)
        if isinstance(error, CLINotFoundError):
            return RetryDecision(
                retryable=False,
                corrective_message=None,
                error_label="CLINotFoundError",
            )

        if isinstance(error, CLIConnectionError):
            return RetryDecision(
                retryable=True,
                corrective_message=(
                    "[System] The connection to the Claude Code process was lost. "
                    "The session has been resumed. Please continue from where you left off."
                ),
                error_label="CLIConnectionError",
            )

        if isinstance(error, ProcessError):
            exit_code = getattr(error, "exit_code", None)
            # SIGINT (exit code -2) — not retryable, handled separately
            if exit_code == -2:
                return RetryDecision(
                    retryable=False,
                    corrective_message=None,
                    error_label="ProcessError(SIGINT)",
                )
            # Unknown exit code — not retryable
            if exit_code is None:
                return RetryDecision(
                    retryable=False,
                    corrective_message=None,
                    error_label="ProcessError(unknown)",
                )
            return RetryDecision(
                retryable=True,
                corrective_message=(
                    f"[System] The Claude Code process exited unexpectedly "
                    f"(exit code {exit_code}). The session has been resumed. "
                    "Please continue from where you left off."
                ),
                error_label=f"ProcessError(exit_code={exit_code})",
            )

        return RetryDecision(
            retryable=False,
            corrective_message=None,
            error_label=type(error).__name__,
        )
