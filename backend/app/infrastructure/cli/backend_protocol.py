"""CLI Backend protocol defining the interface for all AI CLI backends."""

from typing import AsyncIterator, Optional, Protocol, runtime_checkable


@runtime_checkable
class CLIBackend(Protocol):
    """Protocol for AI CLI backends (Claude SDK, codeagent-wrapper, etc.).

    All backend implementations must conform to this interface.
    ClaudeClient already satisfies this protocol.
    CodeAgentWrapperClient implements it for codex/gemini/opencode.
    """

    @property
    def backend_type(self) -> str:
        """Return the backend type identifier (e.g., 'claude', 'codex', 'gemini')."""
        ...

    async def connect(self) -> None:
        """Establish connection to the backend."""
        ...

    async def query(self, message: str) -> None:
        """Send a query message to the backend."""
        ...

    async def receive_messages(self) -> AsyncIterator[dict]:
        """Stream response messages from the backend."""
        ...

    async def interrupt(self) -> None:
        """Interrupt current execution."""
        ...

    async def disconnect(self) -> None:
        """Disconnect and cleanup."""
        ...

    def is_alive(self) -> bool:
        """Check if the backend process is still alive."""
        ...

    def get_session_id(self) -> Optional[str]:
        """Get the session ID (synchronous)."""
        ...

    async def get_session_id_async(self, timeout: float = 5.0) -> Optional[str]:
        """Get the session ID, waiting for it to be available."""
        ...
