"""CodeAgent Wrapper client for non-Claude CLI backends.

Wraps the codeagent-wrapper binary to support codex, gemini, and opencode
backends with a unified interface compatible with KumiAI's session system.
"""

import asyncio
import codecs
import re
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
        self._in_error_block = False  # Track multi-line error blocks
        self._error_lines: List[str] = []  # Accumulate error block lines

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

    # Chunk reading constants
    _READ_CHUNK_SIZE = 1024
    _FLUSH_INTERVAL_SEC = 0.08  # 80ms - flush timeout for partial lines

    async def receive_messages(self) -> AsyncIterator[dict]:
        """Stream response messages from codeagent-wrapper output.

        Uses chunk-based reading for real-time streaming. Yields both
        stream_delta (incremental) and content_block_stop (flush trigger)
        messages so the executor can buffer deltas and flush periodically.
        """
        # Clear process_ready at the start so we always wait for the NEW subprocess.
        # query() runs concurrently via create_task and will set() this after spawning.
        self._process_ready.clear()

        # Wait for subprocess to be spawned
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

        first_line = True
        self._in_error_block = False
        self._error_lines = []

        decoder = codecs.getincrementaldecoder("utf-8")("replace")
        line_buffer = ""

        while True:
            # Read chunks with timeout for periodic flushing
            timed_out = False
            try:
                raw = await asyncio.wait_for(
                    self._process.stdout.read(self._READ_CHUNK_SIZE),
                    timeout=self._FLUSH_INTERVAL_SEC,
                )
            except asyncio.TimeoutError:
                raw = b""
                timed_out = True

            if raw:
                chunk_text = decoder.decode(raw, final=False)
                line_buffer += chunk_text

                # Process complete lines from the buffer
                while "\n" in line_buffer:
                    line, line_buffer = line_buffer.split("\n", 1)

                    # Try JSON parsing first
                    event = parse_stream_line(line, self._backend)

                    if event is not None:
                        first_line = False
                        if self._in_error_block:
                            error_msg = self._flush_error_block()
                            yield self._make_error_message(error_msg)

                        if event.event_type == "text" and event.content:
                            yield self._make_stream_delta_message(event.content)
                            yield self._make_content_block_stop_message()
                        else:
                            yield self._convert_event_to_message(event)
                        continue

                    # Use stripped for control checks, preserve original for emission
                    stripped = line.strip()
                    if not stripped:
                        continue

                    # Skip first line if it's the echoed query
                    if first_line:
                        first_line = False
                        if self._query_text and stripped.startswith(self._query_text):
                            remainder = stripped[len(self._query_text):]
                            if remainder:
                                yield self._make_stream_delta_message(remainder + "\n")
                                yield self._make_content_block_stop_message()
                            continue

                    if self._is_wrapper_noise(stripped):
                        logger.debug("codeagent_metadata_skipped", line=stripped[:80])
                        continue

                    if self._is_error_block_start(stripped):
                        self._in_error_block = True
                        self._error_lines = [stripped]
                        logger.debug("codeagent_error_block_start", line=stripped[:80])
                        continue

                    if self._in_error_block:
                        if self._is_error_block_content(stripped):
                            self._error_lines.append(stripped)
                            continue
                        else:
                            error_msg = self._flush_error_block()
                            yield self._make_error_message(error_msg)

                    # Emit delta + flush preserving line structure
                    yield self._make_stream_delta_message(line.rstrip("\r") + "\n")
                    yield self._make_content_block_stop_message()

            # Timeout flush: emit partial line content for real-time delivery
            if timed_out and line_buffer and not self._in_error_block:
                partial = line_buffer
                partial_stripped = partial.strip()
                if partial_stripped and not self._is_wrapper_noise(partial_stripped):
                    yield self._make_stream_delta_message(partial)
                    yield self._make_content_block_stop_message()
                    line_buffer = ""

            # EOF detection (only on actual empty read, not timeout)
            if raw == b"" and not timed_out and self._process.returncode is not None:
                break

        # Process remaining decoder buffer
        tail = decoder.decode(b"", final=True)
        if tail:
            line_buffer += tail

        # Process remaining line buffer
        if line_buffer.strip():
            stripped = line_buffer.strip()
            if self._is_error_block_start(stripped):
                self._in_error_block = True
                self._error_lines = [stripped]
            elif not self._is_wrapper_noise(stripped):
                if self._in_error_block:
                    if self._is_error_block_content(stripped):
                        self._error_lines.append(stripped)
                    else:
                        error_msg = self._flush_error_block()
                        yield self._make_error_message(error_msg)
                        yield self._make_stream_delta_message(line_buffer)
                        yield self._make_content_block_stop_message()
                else:
                    yield self._make_stream_delta_message(line_buffer)
                    yield self._make_content_block_stop_message()

        # Flush any remaining error block
        if self._in_error_block and self._error_lines:
            error_msg = self._flush_error_block()
            yield self._make_error_message(error_msg)

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

    # Patterns that indicate the start of an error block from the backend
    _ERROR_BLOCK_START_RE = re.compile(
        r"(?:"
        r"GoogleGenerativeAI(?:Fetch)?Error"  # Gemini errors
        r"|GaxiosError"                        # Google HTTP client errors
        r"|Error:\s"                           # Generic "Error: ..." lines
        r"|FetchError"                         # Node.js fetch errors
        r"|APIError"                           # OpenAI/API errors
        r"|RateLimitError"                     # Rate limit errors
        r"|ServiceUnavailableError"            # Service unavailable
        r"|InternalServerError"                # Server errors
        r"|TimeoutError"                       # Timeout errors
        r"|ECONNREFUSED"                       # Connection refused
        r"|ETIMEDOUT"                          # Connection timeout
        r"|model.*not found"                   # Model not found errors
        r"|quota.*exceeded"                    # Quota exceeded
        r")",
        re.IGNORECASE,
    )

    # Patterns for lines that are part of an ongoing error block
    _ERROR_BLOCK_CONTENT_RE = re.compile(
        r"(?:"
        r'^\s*"[a-zA-Z_]+"\s*:'              # JSON key-value: "error": ...
        r"|^\s*[\{\}\[\]]"                     # JSON structure chars
        r"|^\s+at\s"                           # Stack trace: "    at ..."
        r"|^\s*\d+\s*\|"                       # Source code context in errors
        r"|status.*:\s*\d{3}"                  # HTTP status lines
        r"|statusText"                         # HTTP status text
        r"|headers.*:"                         # HTTP headers
        r"|config.*:"                          # HTTP config
        r"|request.*:"                         # HTTP request
        r"|response.*:"                        # HTTP response
        r"|data.*:"                            # HTTP data
        r"|url.*:"                             # URL lines
        r"|method.*:"                          # HTTP method
        r"|RESOURCE_EXHAUSTED"                 # Google API exhausted
        r"|MODEL_CAPACITY_EXHAUSTED"           # Gemini capacity
        r"|RATE_LIMIT"                         # Rate limit markers
        r"|retry.*after"                       # Retry-after hints
        r"|too many requests"                  # 429 messages
        r"|code.*:\s*\d{3}"                    # "code": 429
        r"|message.*:"                         # "message": "..."
        r")",
        re.IGNORECASE,
    )

    def _is_wrapper_noise(self, line: str) -> bool:
        """Check if line is codeagent-wrapper metadata/noise."""
        if line in self._WRAPPER_NOISE_EXACT:
            return True
        if line.startswith(self._WRAPPER_NOISE_PREFIXES):
            return True
        return False

    def _is_error_block_start(self, line: str) -> bool:
        """Check if line starts a multi-line error block."""
        return bool(self._ERROR_BLOCK_START_RE.search(line))

    def _is_error_block_content(self, line: str) -> bool:
        """Check if line is part of an ongoing error block."""
        return bool(self._ERROR_BLOCK_CONTENT_RE.search(line))

    def _flush_error_block(self) -> str:
        """Flush accumulated error lines and return a user-friendly error message."""
        error_lines = self._error_lines
        raw_error = "\n".join(error_lines)
        self._in_error_block = False
        self._error_lines = []

        logger.warning(
            "codeagent_error_block_detected",
            backend=self._backend,
            error_preview=raw_error[:200],
        )

        # Extract a user-friendly message from the raw error
        # Check for rate limit / capacity errors
        if re.search(
            r"429|RESOURCE_EXHAUSTED|MODEL_CAPACITY_EXHAUSTED|rate.?limit|too many requests",
            raw_error,
            re.IGNORECASE,
        ):
            return "API rate limit exceeded. The model is currently at capacity. Please wait a moment and try again."

        if re.search(r"500|INTERNAL", raw_error, re.IGNORECASE):
            return "The AI backend returned an internal server error. Please try again."

        if re.search(r"503|SERVICE_UNAVAILABLE|UNAVAILABLE", raw_error, re.IGNORECASE):
            return "The AI backend is temporarily unavailable. Please try again later."

        if re.search(r"timeout|ETIMEDOUT|ECONNREFUSED", raw_error, re.IGNORECASE):
            return "Connection to the AI backend timed out. Please try again."

        if re.search(r"not found|NOT_FOUND", raw_error, re.IGNORECASE):
            return "The specified model was not found. Please check the model configuration."

        # Generic fallback - extract the first meaningful line
        first_line = error_lines[0] if error_lines else raw_error.split("\n")[0]
        if len(first_line) > 150:
            first_line = first_line[:150] + "..."
        return f"Backend error: {first_line}"

    def _make_stream_delta_message(self, text: str, content_index: int = 0) -> dict:
        """Create an incremental stream delta message for real-time streaming."""
        return {
            "type": "stream_delta",
            "delta": {"type": "text_delta", "text": text},
            "content_index": content_index,
            "session_id": self._session_id,
        }

    def _make_content_block_stop_message(self, content_index: int = 0) -> dict:
        """Create a content block stop marker to trigger buffer flush."""
        return {
            "type": "content_block_stop",
            "content_index": content_index,
            "session_id": self._session_id,
        }

    def _make_error_message(self, error_text: str) -> dict:
        """Create an error message dict."""
        return {
            "type": "error",
            "error": {"message": error_text},
            "session_id": self._session_id,
        }

    def _make_text_message(self, text: str) -> dict:
        """Create a text message dict."""
        return {
            "type": "assistant",
            "message": {
                "content": [{"type": "text", "text": text}],
            },
            "session_id": self._session_id,
        }
