"""Tests for retry policy: RetryClassifier and RetryState."""

import asyncio

from app.infrastructure.claude.execution.retry import RetryClassifier, RetryState
from claude_agent_sdk._errors import (
    CLIJSONDecodeError,
    CLINotFoundError,
    CLIConnectionError,
    ProcessError,
)


# ---------------------------------------------------------------------------
# RetryState
# ---------------------------------------------------------------------------


class TestRetryState:
    def test_can_retry_initially(self):
        state = RetryState(max_retries=3)
        assert state.can_retry() is True

    def test_can_retry_after_exhaustion(self):
        state = RetryState(max_retries=2)
        state.record_attempt()
        state.record_attempt()
        assert state.can_retry() is False

    def test_can_retry_at_boundary(self):
        state = RetryState(max_retries=1)
        assert state.can_retry() is True
        state.record_attempt()
        assert state.can_retry() is False

    def test_get_delay_linear_backoff(self):
        state = RetryState(max_retries=3, backoff_seconds=2.0)
        assert state.get_delay() == 0.0  # attempt=0 before any record
        state.record_attempt()
        assert state.get_delay() == 2.0  # attempt=1
        state.record_attempt()
        assert state.get_delay() == 4.0  # attempt=2

    def test_zero_retries(self):
        state = RetryState(max_retries=0)
        assert state.can_retry() is False


# ---------------------------------------------------------------------------
# RetryClassifier
# ---------------------------------------------------------------------------


class TestRetryClassifier:
    def setup_method(self):
        self.classifier = RetryClassifier()

    def test_json_decode_error_is_retryable(self):
        error = CLIJSONDecodeError("big line", ValueError("too big"))
        decision = self.classifier.classify(error)
        assert decision.retryable is True
        assert "1MB" in decision.corrective_message
        assert decision.error_label == "CLIJSONDecodeError"

    def test_cli_connection_error_is_retryable(self):
        error = CLIConnectionError("pipe broken")
        decision = self.classifier.classify(error)
        assert decision.retryable is True
        assert decision.corrective_message is not None
        assert decision.error_label == "CLIConnectionError"

    def test_cli_not_found_error_is_not_retryable(self):
        # CLINotFoundError is a subclass of CLIConnectionError — must not be retried
        error = CLINotFoundError()
        decision = self.classifier.classify(error)
        assert decision.retryable is False
        assert decision.corrective_message is None
        assert decision.error_label == "CLINotFoundError"

    def test_process_error_non_sigint_is_retryable(self):
        error = ProcessError("crashed", exit_code=1)
        decision = self.classifier.classify(error)
        assert decision.retryable is True
        assert "exit code 1" in decision.corrective_message
        assert decision.error_label == "ProcessError(exit_code=1)"

    def test_process_error_sigint_is_not_retryable(self):
        error = ProcessError("interrupted", exit_code=-2)
        decision = self.classifier.classify(error)
        assert decision.retryable is False
        assert decision.corrective_message is None
        assert decision.error_label == "ProcessError(SIGINT)"

    def test_process_error_unknown_exit_code_is_not_retryable(self):
        error = ProcessError("unknown", exit_code=None)
        decision = self.classifier.classify(error)
        assert decision.retryable is False
        assert decision.error_label == "ProcessError(unknown)"

    def test_cancelled_error_is_not_retryable(self):
        error = asyncio.CancelledError()
        decision = self.classifier.classify(error)
        assert decision.retryable is False
        assert decision.corrective_message is None
        assert decision.error_label == "CancelledError"

    def test_generic_exception_is_not_retryable(self):
        error = RuntimeError("something unexpected")
        decision = self.classifier.classify(error)
        assert decision.retryable is False
        assert decision.corrective_message is None
        assert decision.error_label == "RuntimeError"

    def test_value_error_is_not_retryable(self):
        error = ValueError("bad value")
        decision = self.classifier.classify(error)
        assert decision.retryable is False

    def test_sdk_errors_propagate_directly(self):
        # SDK errors are no longer wrapped — they propagate as-is from client.py
        error = CLIJSONDecodeError("big line", ValueError("too big"))
        decision = self.classifier.classify(error)
        assert decision.retryable is True
