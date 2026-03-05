"""CodeAgent Wrapper client for non-Claude CLI backends.

Wraps the codeagent-wrapper binary to support codex, gemini, and opencode
backends with a unified interface compatible with KumiAI's session system.
"""

import asyncio
import uuid
from collections.abc import AsyncIterable
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Union

from app.core.logging import get_logger
from app.infrastructure.cli.config import (
    BACKEND_CLAUDE,
    CODEAGENT_WRAPPER_BACKENDS,
    CLIBackendConfig,
)
from app.infrastructure.cli.stream_parser import ParsedEvent, parse_stream_line

logger = get_logger(__name__)


class CodeAgentClientError(Exception):
    """Error from CodeAgent wrapper client."""


class CodeAgentWrapperClient:
    """Client that uses codeagent-wrapper for non-Claude backends.

    Supports codex, gemini, and opencode by spawning codeagent-wrapper
    as a subprocess and parsing its streaming JSON output.
    """

    def __init__(
        self,
        backend: str,
        model: Optional[str] = None,
        cwd: Optional[Path] = None,
        system_prompt: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None,
        config: Optional[CLIBackendConfig] = None,
    ) -> None:
        if backend == BACKEND_CLAUDE:
            raise ValueError(
                "Claude backend should use claude_agent_sdk, not codeagent-wrapper"
            )
        if backend not in CODEAGENT_WRAPPER_BACKENDS:
            raise ValueError(
                f"Unsupported backend: {backend}. "
                f"Supported: {CODEAGENT_WRAPPER_BACKENDS}"
            )

        self._backend = backend
        self._model = model
        self._cwd = cwd or Path.cwd()
        self._system_prompt = system_prompt
        self._allowed_tools = allowed_tools or []
        self._config = config or CLIBackendConfig()

        self._process: Optional[asyncio.subprocess.Process] = None
        self._session_id: Optional[str] = str(uuid.uuid4())
        self._connected = False
        self._session_id_ready = asyncio.Event()
        self._process_ready = asyncio.Event()  # Set when subprocess is spawned
        self._pending_query: Optional[str] = None
        self._query_text: Optional[str] = None  # Store query text to filter echo

        logger.info(
            "codeagent_client_initialized",
            backend=backend,
            model=model,
            cwd=str(cwd),
        )

    @property
    def backend_type(self) -> str:
        """Return the backend type identifier."""
        return self._backend

    async def connect(self) -> None:
        """Mark client as connected (subprocess created on first query)."""
        self._connected = True
        self._session_id_ready.set()
        logger.info("codeagent_client_connected", backend=self._backend)

    async def query(self, message: Union[str, AsyncIterable]) -> None:
        """Send a query by spawning codeagent-wrapper subprocess.

        Args:
            message: The task/query string, or an async iterable of message dicts
                     (for compatibility with Execution's streaming interface).
                     When an async iterable is given, the first message's text is
                     extracted and used as the query.
        """
        if not self._connected:
            raise CodeAgentClientError("Client not connected")

        # Extract text from async iterable (Execution passes _message_generator)
        if isinstance(message, str):
            query_text = message
        else:
            query_text = await self._extract_text_from_stream(message)

        # Clear (not replace) process_ready so receive_messages() which may already
        # hold a reference to this event will correctly wait for the new set()
        self._process_ready.clear()

        # Kill existing process if still running
        if self._process and self._process.returncode is None:
            self._process.kill()
            await self._process.wait()

        self._query_text = query_text  # Store for echo filtering
        cmd = self._build_command(query_text)

        logger.info(
            "codeagent_spawning",
            backend=self._backend,
            cmd=" ".join(cmd[:5]) + "...",
        )

        env = self._build_env()

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
            cwd=str(self._cwd),
            env=env,
        )

        self._pending_query = message
        self._process_ready.set()  # Signal that subprocess is ready for reading

    async def receive_messages(self) -> AsyncIterator[dict]:
        """Stream response messages from codeagent-wrapper output.

        Yields message dicts compatible with KumiAI's event processing.
        """
        # Wait for subprocess to be spawned (query() runs concurrently via create_task)
        try:
            await asyncio.wait_for(self._process_ready.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            logger.error("codeagent_process_ready_timeout", backend=self._backend)
            yield {"type": "error", "error": {"message": "Subprocess failed to start within 30s"}}
            return

        if not self._process or not self._process.stdout:
            return

        # Yield an init event with session_id
        yield {
            "type": "init",
            "session_id": self._session_id,
            "data": {"session_id": self._session_id},
        }

        # codeagent-wrapper output format (non-JSON / plain text mode):
        #   Line 1: echo of the query text (skip)
        #   Middle lines: actual response content (keep)
        #   "---": separator (skip)
        #   "SESSION_ID: xxx": metadata (skip, extract session info)
        first_line = True
        async for raw_line in self._process.stdout:
            line = raw_line.decode("utf-8", errors="replace")
            event = parse_stream_line(line, self._backend)

            if event is None:
                # Non-JSON output - filter codeagent-wrapper metadata
                stripped = line.strip()
                if not stripped:
                    continue

                # Skip first line if it's the echoed query
                if first_line:
                    first_line = False
                    if self._query_text and stripped.startswith(self._query_text):
                        # First line contains echo + possibly start of response
                        remainder = stripped[len(self._query_text):]
                        if remainder:
                            yield self._make_text_message(remainder)
                        continue

                # Skip codeagent-wrapper banner and metadata lines
                if self._is_wrapper_noise(stripped):
                    logger.debug(
                        "codeagent_metadata_skipped",
                        line=stripped[:80],
                    )
                    continue

                yield self._make_text_message(stripped)
                continue

            first_line = False
            yield self._convert_event_to_message(event)

        # Wait for process to finish
        await self._process.wait()

        # stderr is merged into stdout via STDOUT redirect
        if self._process.returncode != 0:
            logger.warning(
                "codeagent_nonzero_exit",
                backend=self._backend,
                returncode=self._process.returncode,
            )

        # Yield completion event
        yield {
            "type": "result",
            "result": "",
            "session_id": self._session_id,
        }

    async def interrupt(self) -> None:
        """Interrupt current execution by killing the subprocess."""
        if self._process and self._process.returncode is None:
            logger.info("codeagent_interrupting", backend=self._backend)
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
                await self._process.wait()
            logger.info("codeagent_interrupted", backend=self._backend)

    async def disconnect(self) -> None:
        """Disconnect and cleanup subprocess."""
        await self.interrupt()
        self._connected = False
        logger.info("codeagent_disconnected", backend=self._backend)

    def is_alive(self) -> bool:
        """Check if the client is still operational.

        For CodeAgent, each query spawns a new subprocess, so a completed
        process does NOT mean the client is dead. The client remains alive
        as long as it's connected.
        """
        return self._connected

    def get_session_id(self) -> Optional[str]:
        """Get the session ID (synchronous)."""
        return self._session_id

    async def get_session_id_async(self, timeout: float = 5.0) -> Optional[str]:
        """Get the session ID, waiting if necessary."""
        if self._session_id:
            return self._session_id
        try:
            await asyncio.wait_for(self._session_id_ready.wait(), timeout=timeout)
            return self._session_id
        except asyncio.TimeoutError:
            return None

    def _build_command(self, message: str) -> List[str]:
        """Build the codeagent-wrapper command."""
        cmd = [self._config.codeagent_wrapper_path]
        cmd.extend(["--backend", self._backend])

        if self._model:
            cmd.extend(["--model", self._model])

        if self._config.skip_permissions:
            cmd.append("--skip-permissions")

        if self._system_prompt:
            # Write system prompt to a temp file and use --prompt-file
            # For now, prepend to message
            pass

        cmd.append(message)
        cmd.append(str(self._cwd))

        return cmd

    async def _extract_text_from_stream(self, stream: AsyncIterable) -> str:
        """Extract query text from the first message in an async stream.

        The Execution class passes an async generator of message dicts.
        Each dict has the shape: {"type": "user", "message": {"role": "user", "content": ...}}
        We extract the text content from the first message.
        """
        async for msg in stream:
            # msg is a dict from Execution._format_message
            content = msg.get("message", {}).get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Extract text from content blocks
                parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        parts.append(block)
                return "\n".join(parts) if parts else ""
            return str(content)
        return ""

    def _build_env(self) -> Optional[Dict[str, str]]:
        """Build environment variables for the subprocess."""
        import os

        env = os.environ.copy()
        # codeagent-wrapper picks up config from its own config file
        # and environment variables
        return env

    def _convert_event_to_message(self, event: ParsedEvent) -> dict:
        """Convert a ParsedEvent to a message dict for KumiAI."""
        if event.event_type == "text":
            return self._make_text_message(event.content)

        if event.event_type == "tool_use":
            return {
                "type": "tool_use",
                "name": event.tool_name,
                "input": event.tool_input or {},
                "session_id": self._session_id,
            }

        if event.event_type == "tool_result":
            return {
                "type": "tool_result",
                "content": event.tool_result or "",
                "session_id": self._session_id,
            }

        if event.event_type == "error":
            return {
                "type": "error",
                "error": {"message": event.content},
                "session_id": self._session_id,
            }

        if event.event_type == "complete":
            return {
                "type": "result",
                "result": event.content,
                "session_id": self._session_id,
            }

        # Default: wrap as text
        return self._make_text_message(str(event.raw))

    # Lines from codeagent-wrapper stderr/banner that should be filtered
    _WRAPPER_NOISE_PREFIXES = (
        "[codeagent-wrapper]",
        "Backend:",
        "Command:",
        "PID:",
        "Log:",
        "SESSION_ID:",
        "Attempt ",  # Retry messages like "Attempt 1 failed with status 429"
        "    at ",   # Stack trace lines
    )
    _WRAPPER_NOISE_EXACT = {"---"}

    def _is_wrapper_noise(self, line: str) -> bool:
        """Check if line is codeagent-wrapper metadata/noise."""
        if line in self._WRAPPER_NOISE_EXACT:
            return True
        if line.startswith(self._WRAPPER_NOISE_PREFIXES):
            return True
        return False

    def _make_text_message(self, text: str) -> dict:
        """Create a text message dict."""
        return {
            "type": "assistant",
            "message": {
                "content": [{"type": "text", "text": text}],
            },
            "session_id": self._session_id,
        }
