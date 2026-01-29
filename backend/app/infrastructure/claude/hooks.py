"""Claude SDK hooks for context injection."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


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

    # Get project_id from current session
    # We need to look up the session in the database using session_id
    project_id = await _get_project_id_from_session(session_id)
    if not project_id:
        logger.warning(f"[HOOK] No project_id found for session {session_id}")
        # For spawn_instance, project_id is required, so we'll return an error
        # For other tools, they might not need it
        tool_name = input_data.get("tool_name", "")
        if "spawn_instance" in tool_name:
            logger.error("[HOOK] spawn_instance requires project_id but none found!")

    tool_input = input_data.get("tool_input", {})

    logger.info(
        f"[HOOK] ✓ Auto-injecting project_id: {project_id} into {input_data.get('tool_name')}"
    )

    # Inject only project_id into tool input
    # Merge with existing tool_input to preserve any other parameters
    updated_input = {**tool_input}

    if project_id:
        updated_input["project_id"] = str(project_id)
    else:
        logger.error(
            f"[HOOK] No project_id to inject for {input_data.get('tool_name')}"
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

    Args:
        session_id: Claude SDK session ID

    Returns:
        Project ID UUID string or None if not found
    """
    try:
        # Try to get from client manager first (fast path)
        # The client manager maintains a mapping of session_id -> Session entity
        # This is populated when the client is created

        # Fallback: Query database using our internal session_id
        # We need to map Claude SDK session_id -> our internal UUID session_id
        # This requires the client manager to maintain the mapping

        # For now, let's use a simpler approach:
        # Store the mapping in the context variables when the client is created
        from app.infrastructure.mcp.servers.context import get_current_session_info

        session_info = get_current_session_info()
        if session_info and "project_id" in session_info:
            return str(session_info["project_id"])

        logger.warning(f"Could not find project_id for Claude session {session_id}")
        return None

    except Exception as e:
        logger.error(f"Error getting project_id for session {session_id}: {e}")
        return None
