"""Claude SDK hooks for context injection and status tracking."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Store execution references for status updates
# Maps Claude SDK session_id -> {"execution": ..., "project_id": ..., "source_instance_id": ...}
_execution_registry: Dict[str, Dict[str, Any]] = {}

# Maps our internal UUID session_id -> {"execution": ..., "project_id": ..., "source_instance_id": ...} (for lazy registration)
# This allows hooks to register themselves when they first fire
_pending_executions: Dict[str, Dict[str, Any]] = {}


async def inject_session_context_hook(
    input_data: Dict[str, Any], tool_use_id: str, context: Any
) -> Dict[str, Any]:
    """
    Auto-inject session_id and project_id into PM management tools.

    This hook intercepts tool calls and automatically injects the current
    Claude SDK session_id and associated project_id. These parameters are not
    exposed in the tool schema, so agents cannot provide them - they're always
    injected by this hook.

    Args:
        input_data: Hook input data containing tool_name, tool_input, session_id, etc.
        tool_use_id: Tool use identifier
        context: Hook context (unused in Python SDK)

    Returns:
        Hook response with updatedInput containing injected session_id and project_id
    """
    logger.debug(
        f"[HOOK] Called with event: {input_data.get('hook_event_name')}, "
        f"tool: {input_data.get('tool_name')}"
    )

    # Only process PreToolUse events
    if input_data.get("hook_event_name") != "PreToolUse":
        return {}

    # Get session_id from hook context (provided by Claude SDK)
    session_id = input_data.get("session_id")
    if not session_id:
        logger.error("[HOOK] ✗ No session_id in hook input, cannot inject!")
        logger.error(f"[HOOK] Available keys: {list(input_data.keys())}")
        return {}

    # Get project_id and source_instance_id from execution registry
    project_id = await _get_project_id_from_session(session_id)
    source_instance_id = await _get_source_instance_id_from_session(session_id)

    if not project_id:
        logger.warning(f"[HOOK] No project_id found for session {session_id}")
        tool_name = input_data.get("tool_name", "")
        if "spawn_instance" in tool_name:
            logger.error("[HOOK] spawn_instance requires project_id but none found!")

    if not source_instance_id:
        logger.warning(f"[HOOK] No source_instance_id found for session {session_id}")

    tool_input = input_data.get("tool_input", {})

    logger.info(
        f"[HOOK] ✓ Auto-injecting project_id: {project_id}, "
        f"source_instance_id: {source_instance_id} into {input_data.get('tool_name')}"
    )

    # Inject project_id and source_instance_id into tool input
    # Merge with existing tool_input to preserve any other parameters
    updated_input = {**tool_input}

    if project_id:
        updated_input["project_id"] = str(project_id)
    else:
        logger.error(
            f"[HOOK] No project_id to inject for {input_data.get('tool_name')}"
        )

    if source_instance_id:
        updated_input["source_instance_id"] = str(source_instance_id)
    else:
        logger.error(
            f"[HOOK] No source_instance_id to inject for {input_data.get('tool_name')}"
        )

    return {
        "hookSpecificOutput": {
            "hookEventName": input_data["hook_event_name"],
            "permissionDecision": "allow",
            "updatedInput": updated_input,
        }
    }


async def _get_project_id_from_session(session_id: str) -> str | None:
    """
    Get project_id from Claude SDK session_id.

    This function uses a multi-tier lookup strategy:
    1. Check main execution registry (fast path)
    2. Check pending execution registry
    3. Fallback to database query using internal session ID

    Args:
        session_id: Claude SDK session ID

    Returns:
        Project ID UUID string or None if not found
    """
    try:
        # Fast path: Check main registry
        if session_id in _execution_registry:
            project_id = _execution_registry[session_id].get("project_id")
            if project_id:
                logger.debug(
                    f"[HOOK] Found project_id {project_id} in main registry for session {session_id}"
                )
                return str(project_id)

        # Check pending registry (might not have been moved yet)
        for internal_id, entry in _pending_executions.items():
            execution = entry["execution"]
            project_id = entry.get("project_id")

            # Try to match by Claude SDK session ID
            try:
                client = getattr(execution, "client", None)
                if client:
                    exec_sdk_id = await client.get_session_id_async(timeout=2.0)
                    if exec_sdk_id == session_id and project_id:
                        logger.debug(
                            f"[HOOK] Found project_id {project_id} in pending registry for session {session_id}"
                        )
                        return str(project_id)
            except Exception as e:
                logger.debug(f"[HOOK] Error checking pending execution: {e}")
                continue

        # Fallback: Query database using execution's internal session_id
        # First, try to find the execution to get internal session_id
        execution = await _get_or_register_execution(session_id)
        if execution:
            internal_session_id = execution.session_id
            logger.info(
                f"[HOOK] Falling back to database query for session {internal_session_id}"
            )

            from uuid import UUID

            from app.infrastructure.database.repositories.session_repository import (
                SessionRepositoryImpl,
            )
            from app.infrastructure.database.session import get_repository_session

            async with get_repository_session() as db:
                session_repo = SessionRepositoryImpl(db)
                session_entity = await session_repo.get_by_id(
                    UUID(str(internal_session_id))
                )
                if session_entity and session_entity.project_id:
                    logger.info(
                        f"[HOOK] Found project_id {session_entity.project_id} from database"
                    )
                    return str(session_entity.project_id)

        logger.warning(f"Could not find project_id for Claude session {session_id}")
        return None

    except Exception as e:
        logger.error(f"Error getting project_id for session {session_id}: {e}")
        return None


async def _get_source_instance_id_from_session(session_id: str) -> str | None:
    """
    Get source_instance_id from Claude SDK session_id.

    This function uses a multi-tier lookup strategy:
    1. Check main execution registry (fast path)
    2. Check pending execution registry
    3. Fallback to using the execution's internal session_id

    Args:
        session_id: Claude SDK session ID

    Returns:
        Source instance ID UUID string or None if not found
    """
    try:
        # Fast path: Check main registry
        if session_id in _execution_registry:
            source_instance_id = _execution_registry[session_id].get(
                "source_instance_id"
            )
            if source_instance_id:
                logger.debug(
                    f"[HOOK] Found source_instance_id {source_instance_id} in main registry for session {session_id}"
                )
                return str(source_instance_id)

        # Check pending registry (might not have been moved yet)
        for internal_id, entry in _pending_executions.items():
            execution = entry["execution"]
            source_instance_id = entry.get("source_instance_id")

            # Try to match by Claude SDK session ID
            try:
                client = getattr(execution, "client", None)
                if client:
                    exec_sdk_id = await client.get_session_id_async(timeout=2.0)
                    if exec_sdk_id == session_id and source_instance_id:
                        logger.debug(
                            f"[HOOK] Found source_instance_id {source_instance_id} in pending registry for session {session_id}"
                        )
                        return str(source_instance_id)
            except Exception as e:
                logger.debug(f"[HOOK] Error checking pending execution: {e}")
                continue

        # Fallback: Use execution's internal session_id as source_instance_id
        execution = await _get_or_register_execution(session_id)
        if execution:
            internal_session_id = execution.session_id
            logger.info(
                f"[HOOK] Using internal session_id {internal_session_id} as source_instance_id"
            )
            return str(internal_session_id)

        logger.warning(
            f"Could not find source_instance_id for Claude session {session_id}"
        )
        return None

    except Exception as e:
        logger.error(f"Error getting source_instance_id for session {session_id}: {e}")
        return None


def register_pending_execution(
    internal_session_id: str,
    execution: Any,
    project_id: str | None = None,
    source_instance_id: str | None = None,
) -> None:
    """
    Register execution with internal UUID session ID and optional context.

    This is called before Claude SDK session ID is available.
    Hooks will lazily move this to the main registry when they first fire.

    Args:
        internal_session_id: Our internal UUID session ID
        execution: Execution object
        project_id: Project UUID string (optional)
        source_instance_id: Source instance UUID string (optional, usually same as internal_session_id)
    """
    _pending_executions[internal_session_id] = {
        "execution": execution,
        "project_id": project_id,
        "source_instance_id": source_instance_id,
    }
    logger.info(
        f"[HOOK REGISTRY] Registered pending execution for internal session {internal_session_id} "
        f"with project_id: {project_id}, source_instance_id: {source_instance_id}"
    )


def register_execution(
    claude_sdk_session_id: str,
    execution: Any,
    project_id: str | None = None,
    source_instance_id: str | None = None,
) -> None:
    """
    Register an execution instance with Claude SDK session ID for hooks.

    Args:
        claude_sdk_session_id: Claude SDK session ID
        execution: Execution object
        project_id: Project UUID string (optional)
        source_instance_id: Source instance UUID string (optional)
    """
    _execution_registry[claude_sdk_session_id] = {
        "execution": execution,
        "project_id": project_id,
        "source_instance_id": source_instance_id,
    }
    logger.info(
        f"[HOOK REGISTRY] Registered execution for Claude SDK session {claude_sdk_session_id} "
        f"with project_id: {project_id}, source_instance_id: {source_instance_id}. "
        f"Registry now has: {list(_execution_registry.keys())}"
    )


def unregister_execution(internal_session_id: str) -> None:
    """Unregister an execution instance by internal session ID."""
    # Remove from pending
    if internal_session_id in _pending_executions:
        del _pending_executions[internal_session_id]
        logger.debug(
            f"[HOOK REGISTRY] Unregistered pending execution for session {internal_session_id}"
        )

    # Remove from main registry (need to find by execution object)
    # Since we don't have the Claude SDK ID here, remove all entries with this execution
    to_remove = []
    for sdk_id, entry in _execution_registry.items():
        exec_obj = entry["execution"]
        if str(exec_obj.session_id) == internal_session_id:
            to_remove.append(sdk_id)

    for sdk_id in to_remove:
        del _execution_registry[sdk_id]
        logger.debug(
            f"[HOOK REGISTRY] Unregistered execution for Claude SDK session {sdk_id}"
        )


async def _eagerly_register_from_pending(claude_sdk_session_id: str) -> Any:
    """
    Eagerly register pending execution using Claude SDK session ID.

    Called from hooks that fire BEFORE any response messages are received
    (like UserPromptSubmit). At this point, the client hasn't captured the
    session_id yet, but the hook provides it directly.

    Returns:
        Execution object or None if not found in pending registry
    """
    # Already registered?
    if claude_sdk_session_id in _execution_registry:
        return _execution_registry[claude_sdk_session_id]["execution"]

    # Check if ANY pending execution exists (should only be one during creation)
    # Since this is called during the first message, there should be exactly one
    # pending execution - the one we just created.
    if _pending_executions:
        # Get the first (and should be only) pending execution
        internal_id, entry = next(iter(_pending_executions.items()))
        execution = entry["execution"]
        project_id = entry.get("project_id")
        source_instance_id = entry.get("source_instance_id")

        # Register it with the Claude SDK session ID
        register_execution(
            claude_sdk_session_id, execution, project_id, source_instance_id
        )
        del _pending_executions[internal_id]

        logger.info(
            f"[HOOK REGISTRY] Eagerly registered pending execution "
            f"{internal_id} with Claude SDK ID {claude_sdk_session_id}, "
            f"project_id: {project_id}, source_instance_id: {source_instance_id}"
        )
        return execution

    logger.error(
        f"[HOOK] ✗ Session {claude_sdk_session_id} not found! "
        f"Registry: {list(_execution_registry.keys())}, "
        f"Pending: {list(_pending_executions.keys())}"
    )
    return None


async def _get_or_register_execution(claude_sdk_session_id: str) -> Any:
    """
    Get execution from registry, or lazily register if pending.

    When hooks first fire, the Claude SDK session ID is available but
    execution may still be in pending registry. This function moves it
    to the main registry.

    Returns:
        Execution object or None if not found
    """
    # Already registered?
    if claude_sdk_session_id in _execution_registry:
        return _execution_registry[claude_sdk_session_id]["execution"]

    # Check if any pending executions can be registered
    # We need to find which pending execution corresponds to this Claude SDK session
    # The execution object has access to the client which knows the Claude SDK session ID
    for internal_id, entry in list(_pending_executions.items()):
        execution = entry["execution"]
        project_id = entry.get("project_id")
        source_instance_id = entry.get("source_instance_id")

        # Try to get Claude SDK session ID from execution's client
        try:
            client = getattr(execution, "client", None)
            if client:
                # Wait for session_id to be captured (with timeout)
                exec_sdk_id = await client.get_session_id_async(timeout=2.0)
                if exec_sdk_id == claude_sdk_session_id:
                    # Found it! Move to main registry with project_id and source_instance_id
                    register_execution(
                        claude_sdk_session_id, execution, project_id, source_instance_id
                    )
                    del _pending_executions[internal_id]
                    logger.info(
                        f"[HOOK REGISTRY] Lazily registered pending execution "
                        f"{internal_id} with Claude SDK ID {claude_sdk_session_id}, "
                        f"project_id: {project_id}, source_instance_id: {source_instance_id}"
                    )
                    return execution
        except Exception as e:
            logger.debug(f"[HOOK REGISTRY] Error checking execution: {e}")
            continue

    logger.error(
        f"[HOOK] ✗ Session {claude_sdk_session_id} not found! "
        f"Registry: {list(_execution_registry.keys())}, "
        f"Pending: {list(_pending_executions.keys())}"
    )
    return None


async def user_prompt_submit_hook(
    input_data: Dict[str, Any], tool_use_id: str, context: Any
) -> Dict[str, Any]:
    """
    Hook: UserPromptSubmit
    Fires when user submits a prompt (before Claude processes it).

    Use this to mark the session as PROCESSING.
    """
    claude_sdk_session_id = input_data.get("session_id")
    logger.info(f"[HOOK] UserPromptSubmit for session {claude_sdk_session_id}")

    # This hook fires BEFORE Claude processes the message, so the client
    # hasn't received any response messages yet. But we DO have the Claude SDK
    # session ID from the hook input! Use it to eagerly register from pending.
    execution = await _eagerly_register_from_pending(claude_sdk_session_id)

    # Mark as processing and update database + broadcast status
    if execution:
        execution.is_processing = True
        logger.info(
            f"[HOOK] Set is_processing=True for session {claude_sdk_session_id}"
        )

        # Update session status in database and broadcast
        from app.infrastructure.claude.state.session_status_manager import (
            session_status_manager,
        )

        await session_status_manager.update_to_working(execution.session_id)

    # Allow prompt to proceed
    return {}


# Delay for tool completion before interrupting (in seconds)
TOOL_COMPLETION_DELAY_SEC = 1.0


async def ask_user_question_pre_hook(
    input_data: Dict[str, Any], tool_use_id: str, context: Any
) -> Dict[str, Any]:
    """
    Hook: PreToolUse for askuserquestion
    Fires BEFORE AskUserQuestion tool executes.

    Allows the tool to execute (so questions are sent to frontend),
    then schedules interrupt after tool completes.
    """
    tool_name = input_data.get("tool_name", "")

    if tool_name == "AskUserQuestion":
        session_id = input_data.get("session_id")
        logger.info(f"[ASK_USER] AskUserQuestion detected for session {session_id}")

        # Allow the tool to execute first (so questions reach the frontend)
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            }
        }

        # Schedule interrupt to happen after tool completes
        import asyncio

        execution = await _get_or_register_execution(session_id)
        if execution:

            async def interrupt_after_delay():
                # Delay to let tool complete and avoid race condition
                logger.info(
                    f"[ASK_USER] Starting {TOOL_COMPLETION_DELAY_SEC}s delay for {session_id}"
                )
                await asyncio.sleep(TOOL_COMPLETION_DELAY_SEC)
                logger.info(
                    f"[ASK_USER] Delay complete, attempting interrupt for {session_id}"
                )
                try:
                    await execution.client.interrupt()
                    logger.info(f"[ASK_USER] Interrupt call completed for {session_id}")

                    # Update session status to IDLE
                    execution.is_processing = False
                    from app.infrastructure.claude.state.session_status_manager import (
                        session_status_manager,
                    )

                    await session_status_manager.reset_to_idle(execution.session_id)
                    logger.info(
                        f"[ASK_USER] Session {session_id} interrupted and set to IDLE"
                    )

                except Exception as e:
                    logger.error(
                        f"[ASK_USER] Failed to interrupt session {session_id}: {e}",
                        exc_info=True,
                    )

            # Create task with exception handling
            def handle_task_done(task):
                if not task.cancelled() and task.exception():
                    logger.error(f"Interrupt task failed: {task.exception()}")

            task = asyncio.create_task(interrupt_after_delay())
            task.add_done_callback(handle_task_done)

        return response

    return {}


async def stop_hook(
    input_data: Dict[str, Any], tool_use_id: str, context: Any
) -> Dict[str, Any]:
    """
    Hook: Stop
    Fires when Claude finishes responding.

    Use this to check queue and mark as IDLE if no more messages.
    """
    session_id = input_data.get("session_id")
    logger.info(f"[HOOK] Stop for session {session_id}")

    # Get or lazily register execution
    execution = await _get_or_register_execution(session_id)

    # Check queue and update processing state
    if execution:
        queue_size = execution.queue.qsize()

        if queue_size == 0:
            execution.is_processing = False
            logger.info(
                f"[HOOK] Set is_processing=False for session {session_id} (queue empty)"
            )

            # Update session status in database and broadcast
            from app.infrastructure.claude.state.session_status_manager import (
                session_status_manager,
            )

            # Use reset_to_idle instead of update_after_execution
            # since we're just updating status during message processing
            await session_status_manager.reset_to_idle(execution.session_id)
        else:
            logger.info(
                f"[HOOK] Keeping is_processing=True for session {session_id} "
                f"(queue has {queue_size} messages)"
            )

    # Allow to proceed
    return {}


async def get_source_instance_id_from_registry(
    claude_sdk_session_id: str,
) -> str | None:
    """
    Get source_instance_id from execution registry for the given Claude SDK session ID.

    This is a synchronous helper that can be called from tools to get the source instance ID.
    For async contexts, use _get_source_instance_id_from_session() instead.

    Args:
        claude_sdk_session_id: Claude SDK session ID

    Returns:
        Source instance ID UUID string or None if not found
    """
    # Check main registry
    if claude_sdk_session_id in _execution_registry:
        return _execution_registry[claude_sdk_session_id].get("source_instance_id")

    # Check pending registry
    for internal_id, entry in _pending_executions.items():
        execution = entry["execution"]
        source_instance_id = entry.get("source_instance_id")

        try:
            client = getattr(execution, "client", None)
            if client:
                exec_sdk_id = await client.get_session_id_async(timeout=2.0)
                if exec_sdk_id == claude_sdk_session_id:
                    return source_instance_id
        except Exception:
            continue

    # Fallback: Try to get from execution object
    execution = await _get_or_register_execution(claude_sdk_session_id)
    if execution:
        return str(execution.session_id)

    return None
