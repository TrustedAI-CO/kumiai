"""Common Tools MCP Server.

Provides tools available to all agents for inter-session communication
and collaboration.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any, Dict
import logging
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)


def _error(message: str) -> Dict[str, Any]:
    """Create error response."""
    return {"content": [{"type": "text", "text": f"✗ Error: {message}"}]}


def _find_project_root(file_path: Path) -> Path | None:
    """
    Find project root by searching for .sessions or .git directory.

    Args:
        file_path: Starting path to search from

    Returns:
        Project root path if found, None otherwise
    """
    current = file_path if file_path.is_dir() else file_path.parent

    # Search up to 10 levels
    for _ in range(10):
        if (current / ".sessions").exists() or (current / ".git").exists():
            return current

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return None


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / 1024 / 1024:.1f}MB"


@tool(
    "show_file",
    "Display a file to the user with a preview card. Shows image thumbnails for images, file icons for other types.",
    {"path": str},
)
async def show_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Display a file to the user by creating a preview card in the frontend.

    The frontend will automatically show a thumbnail for images or a file type icon
    for other files. Users can click to view the full file content.

    Use this when you want to:
    - Show a file you've created (image, document, code, etc.)
    - Present results of file generation or manipulation
    - Let the user review a file before taking further action

    Args (from args dict):
        path: Path to the file to display (relative or absolute)

    Returns:
        Success confirmation that file will be displayed
    """
    try:
        # Extract parameters
        file_path_str = args.get("path", "")

        # Validate inputs
        if not file_path_str:
            return _error("No file path provided")

        file_path = Path(file_path_str)

        # Validate file exists
        if not file_path.exists():
            return _error(f"File not found: {file_path_str}")

        if not file_path.is_file():
            return _error(f"Path is not a file: {file_path_str}")

        # Get file info for logging
        file_name = file_path.name
        file_size = file_path.stat().st_size

        logger.info(
            f"[COMMON_TOOLS] Displaying file: {file_path_str} "
            f"({_format_file_size(file_size)})"
        )

        # Return empty response - frontend will detect this tool call and render preview card
        # No need for text output since the file preview is shown inline
        return {"content": [{"type": "text", "text": ""}]}

    except Exception as e:
        logger.error(f"[COMMON_TOOLS] Error displaying file: {e}", exc_info=True)
        return _error(f"Failed to display file: {str(e)}")


@tool(
    "contact_instance",
    "Send a message to another instance to delegate work or request collaboration",
    {
        "instance_id": str,
        "message": str,
    },
)
async def contact_instance(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message to another instance.

    Works with instances in ANY status (initializing, idle, thinking, working).
    Use for: delegating work, providing context, requesting help, or coordinating work.

    Args (from args dict):
        instance_id: ID of the target instance to send message to
        message: Message to send (will appear as user input to the target instance)

    Returns:
        Delivery confirmation
    """
    try:
        # Extract parameters
        target_instance_id = args.get("instance_id", "")
        message = args.get("message", "")

        # Validate inputs
        if not target_instance_id:
            return _error("instance_id is required")

        if not message:
            return _error("message is required")

        # Validate UUID format
        try:
            instance_uuid = UUID(target_instance_id)
        except ValueError:
            return _error(f"Invalid instance_id format: {target_instance_id}")

        # Get sender instance info from context
        from app.infrastructure.mcp.servers.context import get_current_session_info

        sender_info = get_current_session_info()
        source_instance_id = None
        if sender_info and "source_instance_id" in sender_info:
            try:
                source_instance_id = UUID(sender_info["source_instance_id"])
            except (ValueError, TypeError):
                logger.warning(
                    f"[COMMON_TOOLS] Invalid source_instance_id format: {sender_info.get('source_instance_id')}"
                )

        logger.info(
            f"[COMMON_TOOLS] Sending message to instance {target_instance_id[:8]}... "
            f"from sender {str(source_instance_id)[:8] if source_instance_id else 'unknown'}: "
            f"{message[:100]}..."
        )

        # Send message using backend API (fire-and-forget for async execution)
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl
        import asyncio

        # Verify target instance exists
        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            target_instance = await session_repo.get_by_id(instance_uuid)

            if not target_instance:
                return _error(f"Instance {target_instance_id} not found")

        # Fire-and-forget: Create background task to send message
        # This prevents blocking the current session
        if source_instance_id:
            asyncio.create_task(
                _send_message_background(instance_uuid, message, source_instance_id)
            )
        else:
            logger.warning(
                "[COMMON_TOOLS] No source_instance_id available, message won't have attribution"
            )
            asyncio.create_task(
                _send_message_background(
                    instance_uuid, message, UUID("00000000-0000-0000-0000-000000000000")
                )
            )

        logger.info(
            f"[COMMON_TOOLS] Message dispatched to instance {target_instance_id[:8]}"
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""✓ Message dispatched to instance {target_instance_id[:8]}...

Your message is being delivered to the target instance.""",
                }
            ]
        }

    except Exception as e:
        logger.error(
            f"[COMMON_TOOLS] Error sending message to instance: {e}", exc_info=True
        )
        return _error(f"Failed to send message: {str(e)}")


@tool(
    "get_session_info",
    "Get information about the current session (your own identity and context)",
    {},
)
async def get_session_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current session's information.

    Returns your session ID, agent info, project association, status, and context.
    Useful for understanding your own identity and current state.

    Args (from args dict):
        None

    Returns:
        Dict with session metadata including ID, agent, project, status, and context
    """
    try:
        # Get current session info from context
        from app.infrastructure.mcp.servers.context import get_current_session_info

        sender_info = get_current_session_info()
        if not sender_info:
            return _error("Unable to determine current session context")

        source_instance_id_str = sender_info.get("source_instance_id")
        if not source_instance_id_str:
            return _error("Unable to determine session ID")

        try:
            source_instance_id = UUID(source_instance_id_str)
        except ValueError as e:
            return _error(f"Invalid session ID format: {e}")

        # Retrieve full session details from database
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            session = await session_repo.get_by_id(source_instance_id)

            if not session:
                return _error(f"Session {source_instance_id} not found")

        logger.info(
            f"[COMMON_TOOLS] Retrieved session info for {str(source_instance_id)[:8]}"
        )

        # Build response with all relevant session info
        result_lines = ["📋 Session Information", ""]
        result_lines.append(f"**Session ID:** {session.id}")
        result_lines.append(f"**Agent ID:** {session.agent_id}")
        result_lines.append(f"**Session Type:** {session.session_type.value}")
        result_lines.append(f"**Status:** {session.status.value}")

        if session.project_id:
            result_lines.append(f"**Project ID:** {session.project_id}")
        else:
            result_lines.append("**Project ID:** None (not associated with a project)")

        result_lines.append("")
        result_lines.append("**Context:**")

        if session.context:
            # Show kanban stage
            kanban_stage = session.context.get("kanban_stage", "N/A")
            result_lines.append(f"  • Kanban Stage: {kanban_stage}")

            # Show task description
            task_description = session.context.get(
                "task_description"
            ) or session.context.get("description")
            if task_description:
                result_lines.append(f"  • Task Description: {task_description}")

            # Show spawned_by if exists
            spawned_by = session.context.get("spawned_by")
            if spawned_by:
                result_lines.append(f"  • Spawned By: {spawned_by}")

            # Show other context keys (limit to avoid overwhelming output)
            other_keys = [
                k
                for k in session.context.keys()
                if k
                not in ["kanban_stage", "task_description", "description", "spawned_by"]
            ]
            if other_keys:
                result_lines.append(
                    f"  • Other Context Keys: {', '.join(other_keys[:5])}"
                )
                if len(other_keys) > 5:
                    result_lines.append(f"    (and {len(other_keys) - 5} more...)")
        else:
            result_lines.append("  No context data")

        result_lines.append("")
        result_lines.append("**Timestamps:**")
        result_lines.append(f"  • Created: {session.created_at}")
        result_lines.append(f"  • Updated: {session.updated_at}")

        if session.error_message:
            result_lines.append("")
            result_lines.append(f"**⚠️ Error Message:** {session.error_message}")

        return {
            "content": [{"type": "text", "text": "\n".join(result_lines)}],
            "session_id": str(session.id),
            "agent_id": session.agent_id,
            "session_type": session.session_type.value,
            "status": session.status.value,
            "project_id": str(session.project_id) if session.project_id else None,
            "context": session.context,
        }

    except Exception as e:
        logger.error(f"[COMMON_TOOLS] Error getting session info: {e}", exc_info=True)
        return _error(f"Failed to get session info: {str(e)}")


@tool(
    "contact_pm",
    "Send a message to the Project Manager (PM) of your project",
    {
        "message": str,
    },
)
async def contact_pm(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message to your project's PM.

    Automatically finds and contacts the latest PM session in your project.
    Use this to report progress, ask for guidance, or request additional context.

    Args (from args dict):
        message: Message to send to the PM (will appear as user input to the PM)

    Returns:
        Delivery confirmation with PM instance ID
    """
    try:
        # Extract parameters
        message = args.get("message", "")

        # Validate inputs
        if not message:
            return _error("message is required")

        # Get current session info from context
        from app.infrastructure.mcp.servers.context import get_current_session_info

        sender_info = get_current_session_info()
        if not sender_info:
            return _error("Unable to determine current session context")

        source_instance_id_str = sender_info.get("source_instance_id")
        project_id_str = sender_info.get("project_id")

        if not source_instance_id_str:
            return _error("Unable to determine source instance ID")

        if not project_id_str:
            return _error("This session is not associated with a project")

        # Parse UUIDs
        try:
            source_instance_id = UUID(source_instance_id_str)
            project_id = UUID(project_id_str)
        except ValueError as e:
            return _error(f"Invalid UUID format in session context: {e}")

        # Find the latest PM session in this project
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)

            # Verify source session exists
            source_session = await session_repo.get_by_id(source_instance_id)
            if not source_session:
                return _error(f"Source session {source_instance_id} not found")

            # Get latest PM session
            pm_session = await session_repo.get_latest_pm_session(project_id)
            if not pm_session:
                return _error(f"No PM session found in project {project_id}")

        pm_instance_id = pm_session.id

        logger.info(
            f"[COMMON_TOOLS] Sending message to PM {str(pm_instance_id)[:8]}... "
            f"from specialist {str(source_instance_id)[:8]}: {message[:100]}..."
        )

        # Send message using background task
        import asyncio

        asyncio.create_task(
            _send_message_background(pm_instance_id, message, source_instance_id)
        )

        logger.info(
            f"[COMMON_TOOLS] Message dispatched to PM {str(pm_instance_id)[:8]}"
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""✓ Message dispatched to Project Manager (PM instance {str(pm_instance_id)[:8]}...)

Your message is being delivered to the PM.""",
                }
            ]
        }

    except Exception as e:
        logger.error(f"[COMMON_TOOLS] Error sending message to PM: {e}", exc_info=True)
        return _error(f"Failed to send message to PM: {str(e)}")


@tool(
    "remind",
    "Schedule a reminder message to be sent back to you after a delay",
    {
        "delay_seconds": int,
        "message": str,
    },
)
async def remind(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule a reminder message to yourself after a delay.

    Use this when you need to check on something later, such as:
    - Waiting for a build to complete
    - Checking deployment status after some time
    - Following up on a long-running task
    - Polling for external process completion

    Args (from args dict):
        delay_seconds: How many seconds to wait before sending the reminder (1-86400)
        message: The reminder message to send back to yourself

    Returns:
        Confirmation that reminder is scheduled
    """
    try:
        # Extract parameters
        delay_seconds = args.get("delay_seconds", 60)
        message = args.get("message", "")

        # Validate inputs
        if not message:
            return _error("message is required")

        if not isinstance(delay_seconds, int):
            return _error("delay_seconds must be an integer")

        if delay_seconds < 1:
            return _error("delay_seconds must be at least 1 second")

        if delay_seconds > 86400:  # 24 hours
            return _error("delay_seconds cannot exceed 24 hours (86400 seconds)")

        # Get current session info from context
        from app.infrastructure.mcp.servers.context import get_current_session_info

        sender_info = get_current_session_info()
        if not sender_info:
            return _error("Unable to determine current session context")

        source_instance_id_str = sender_info.get("source_instance_id")
        if not source_instance_id_str:
            return _error("Unable to determine session ID")

        # Parse UUID
        try:
            source_instance_id = UUID(source_instance_id_str)
        except ValueError as e:
            return _error(f"Invalid session ID format: {e}")

        # Verify session exists
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import SessionRepositoryImpl

        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            session = await session_repo.get_by_id(source_instance_id)

            if not session:
                return _error(f"Session {source_instance_id} not found")

        logger.info(
            f"[COMMON_TOOLS] Scheduling reminder for session {str(source_instance_id)[:8]} "
            f"in {delay_seconds}s: {message[:50]}..."
        )

        # Schedule the reminder as a background task
        import asyncio

        asyncio.create_task(
            _send_reminder_background(source_instance_id, delay_seconds, message)
        )

        # Human-readable time format
        if delay_seconds < 60:
            time_str = f"{delay_seconds} second{'s' if delay_seconds != 1 else ''}"
        elif delay_seconds < 3600:
            minutes = delay_seconds // 60
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = delay_seconds // 3600
            minutes = (delay_seconds % 3600) // 60
            time_str = (
                f"{hours}h {minutes}m"
                if minutes > 0
                else f"{hours} hour{'s' if hours != 1 else ''}"
            )

        logger.info(
            f"[COMMON_TOOLS] Reminder scheduled for session {str(source_instance_id)[:8]} "
            f"in {time_str}"
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"⏰ Reminder scheduled for {time_str} from now\n\n"
                        f"Message: {message}\n\n"
                        f"You'll receive this reminder automatically. Continue with other work."
                    ),
                }
            ]
        }

    except Exception as e:
        logger.error(f"[COMMON_TOOLS] Error scheduling reminder: {e}", exc_info=True)
        return _error(f"Failed to schedule reminder: {str(e)}")


async def _send_reminder_background(session_id: UUID, delay_seconds: int, message: str):
    """
    Background task to wait and send reminder message.

    Args:
        session_id: Target session to send reminder to (same as caller)
        delay_seconds: How long to wait before sending
        message: Reminder message content
    """
    import asyncio

    try:
        logger.info(
            f"[COMMON_TOOLS] Waiting {delay_seconds}s before sending reminder to {str(session_id)[:8]}"
        )
        await asyncio.sleep(delay_seconds)

        logger.info(
            f"[COMMON_TOOLS] Sending reminder to {str(session_id)[:8]}: {message[:50]}..."
        )

        # Update session status to WORKING (wake up idle sessions)
        from app.application.services.session_service import SessionService
        from app.infrastructure.database.repositories import ProjectRepositoryImpl
        from app.infrastructure.filesystem.agent_repository import (
            FileBasedAgentRepository,
        )
        from app.infrastructure.database.connection import get_repository_session
        from pathlib import Path

        async with get_repository_session() as db_session:
            session_service = SessionService(
                session_repo=SessionRepositoryImpl(db_session),
                project_repo=ProjectRepositoryImpl(db_session),
                agent_repo=FileBasedAgentRepository(Path("data/agents")),
            )
            await session_service.transition_to_working(session_id)

        # Send reminder message through executor
        from app.api.dependencies import get_session_executor

        executor = get_session_executor()
        await executor.enqueue(
            session_id=session_id,
            message=message,
            sender_name="System Reminder",
            sender_session_id=None,
        )

        logger.info(f"[COMMON_TOOLS] Reminder delivered to {str(session_id)[:8]}")

    except Exception as e:
        logger.error(f"[COMMON_TOOLS] Failed to deliver reminder: {e}", exc_info=True)


async def _send_message_background(
    session_id: UUID, message: str, source_instance_id: UUID
):
    """
    Background task to send message to target instance.

    This runs asynchronously to avoid blocking the caller.
    Uses SessionExecutor.enqueue() to trigger actual execution.
    """
    try:
        from app.api.dependencies import get_session_executor
        from app.infrastructure.database.connection import get_repository_session
        from app.infrastructure.database.repositories import (
            SessionRepositoryImpl,
            ProjectRepositoryImpl,
        )
        from app.application.services.session_service import SessionService
        from app.infrastructure.filesystem.agent_repository import (
            FileBasedAgentRepository,
        )
        from pathlib import Path

        # Get source instance info for attribution
        sender_name = "Unknown Instance"
        sender_agent_id = None
        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            source_instance = await session_repo.get_by_id(source_instance_id)
            if source_instance:
                # Get agent_id and name for attribution
                sender_agent_id = source_instance.agent_id
                sender_name = source_instance.agent_id.replace("-", " ").title()

        # Update target session status to WORKING using SessionService
        async with get_repository_session() as db_session:
            session_service = SessionService(
                session_repo=SessionRepositoryImpl(db_session),
                project_repo=ProjectRepositoryImpl(db_session),
                agent_repo=FileBasedAgentRepository(Path("data/agents")),
            )
            await session_service.transition_to_working(session_id)

        # Get the executor singleton and enqueue the message
        executor = get_session_executor()
        await executor.enqueue(
            session_id=session_id,
            message=message,
            sender_name=sender_name,
            sender_session_id=source_instance_id,
            sender_agent_id=sender_agent_id,
        )

        logger.info(
            f"[COMMON_TOOLS] Message enqueued for instance {str(session_id)[:8]} "
            f"from {sender_name}"
        )

    except Exception as e:
        logger.error(
            f"[COMMON_TOOLS] Background message delivery failed: {e}", exc_info=True
        )


# Create the MCP server with common tools
common_tools_server = create_sdk_mcp_server(
    name="common_tools",
    version="1.0.0",
    tools=[show_file, get_session_info, contact_instance, contact_pm, remind],
)
