"""PM Management MCP Server.

Provides tools for PM agents to orchestrate project workflows,
spawn sessions, and manage specialist sessions.
"""

from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any, Dict
import logging
from uuid import UUID, uuid4

from app.application.dtos.session_dto import SessionDTO
from app.domain.entities import Session as SessionEntity
from app.domain.value_objects import SessionType, SessionStatus
from app.domain.value_objects.task_status import TaskStatus
from app.infrastructure.database.connection import get_repository_session
from app.infrastructure.database.repositories import SessionRepositoryImpl
from app.infrastructure.database.repositories.task_repository import TaskRepositoryImpl
from app.infrastructure.database.repositories.project_repository import (
    ProjectRepositoryImpl,
)
from app.infrastructure.filesystem.agent_repository import FileBasedAgentRepository

logger = logging.getLogger(__name__)


def _error(message: str) -> Dict[str, Any]:
    """Create error response."""
    return {"content": [{"type": "text", "text": f"✗ Error: {message}"}]}


@tool(
    "spawn_instance",
    "Create a new specialist work instance for a project task",
    {
        "agent_id": str,
        "task_description": str,
        "task_id": str,
    },
)
async def spawn_instance(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new specialist session.

    Args (from args dict):
        agent_id: ID of the specialist agent to spawn (e.g., "backend-dev")
        task_description: Description of what the session should accomplish
        project_id: UUID of the project (auto-injected by hook, not in schema)

    Returns:
        Dict with content array containing session creation confirmation
    """
    try:
        # Extract and validate parameters
        project_id_str = args.get("project_id", "")
        agent_id = args.get("agent_id", "")
        task_description = args.get("task_description", "")
        task_id_str = args.get("task_id", "")

        if not project_id_str:
            return _error("project_id is required")
        if not agent_id:
            return _error("agent_id is required")
        if not task_description:
            return _error("task_description is required")

        try:
            project_id = UUID(project_id_str)
        except ValueError:
            return _error(f"Invalid project_id format: {project_id_str}")

        task_id: UUID | None = None
        if task_id_str:
            try:
                task_id = UUID(task_id_str)
            except ValueError:
                return _error(f"Invalid task_id format: {task_id_str}")

        logger.info(
            f"[PM_TOOLS] Spawning specialist session: "
            f"project={project_id}, agent={agent_id}, task={task_description[:100]}..."
        )

        # Validate agent exists before creating session
        from app.core.config import settings

        agent_repo = FileBasedAgentRepository(settings.agents_dir)
        agent = await agent_repo.get_by_id(agent_id)

        if not agent:
            available_agents = await agent_repo.get_all()
            available_agent_ids = [a.id for a in available_agents]
            error_msg = f"Agent '{agent_id}' not found. Available agents: {', '.join(repr(aid) for aid in available_agent_ids)}"
            logger.warning(f"[PM_TOOLS] {error_msg}")
            return _error(error_msg)

        # Validate task_id belongs to the same project
        if task_id is not None:
            async with get_repository_session() as db:
                task_repo = TaskRepositoryImpl(db)
                task_entity = await task_repo.get_by_id(task_id)
            if task_entity is None:
                return _error(f"Task {task_id} not found")
            if str(task_entity.project_id) != str(project_id):
                return _error(f"Task {task_id} does not belong to project {project_id}")

        # Create session entity
        session_entity = SessionEntity(
            id=uuid4(),
            agent_id=agent_id,
            project_id=project_id,
            session_type=SessionType.SPECIALIST,
            status=SessionStatus.INITIALIZING,
            task_id=task_id,
            context={
                "task_description": task_description,
                "description": task_description,  # Frontend compatibility
                "spawned_by": "pm",
                "kanban_stage": "backlog",
            },
        )

        # Create and commit in independent transaction
        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            created_session = await session_repo.create(session_entity)
            await db.commit()
            new_session = SessionDTO.from_entity(created_session)

        logger.info(
            f"[PM_TOOLS] Created specialist session {new_session.id} "
            f"for agent {agent_id} in project {project_id}"
        )

        task_line = f"\nTask ID: {task_id}" if task_id else ""
        result_text = f"""✓ Specialist session created successfully!

Session ID: {new_session.id}
Agent: {agent_id}
Task: {task_description}{task_line}
Status: {new_session.status}

⚠️  Instance is in {new_session.status} status. Use contact_instance to send the first message and start execution."""

        response: Dict[str, Any] = {
            "content": [{"type": "text", "text": result_text}],
            "session_id": str(new_session.id),
            "agent_id": agent_id,
            "project_id": str(project_id),
        }
        if task_id:
            response["task_id"] = str(task_id)
        return response

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error spawning session: {e}", exc_info=True)
        return _error(f"Failed to spawn session: {str(e)}")


@tool(
    "contact_instance",
    "Send a message to another agent instance",
    {
        "target_instance_id": str,
        "message": str,
    },
)
async def contact_instance(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message to another instance within the same project.

    Args (from args dict):
        target_instance_id: UUID of the instance to send the message to
        message: The message content to send

    Returns:
        Dict with content array containing delivery confirmation
    """
    try:
        # Extract and validate parameters
        target_instance_id_str = args.get("target_instance_id", "")
        message = args.get("message", "")

        if not target_instance_id_str:
            return _error("target_instance_id is required")
        if not message:
            return _error("message is required")

        try:
            target_instance_id = UUID(target_instance_id_str)
        except ValueError as e:
            return _error(f"Invalid UUID format: {e}")

        # Get sender instance info from injected parameters
        # These are auto-injected by the inject_session_context_hook
        source_instance_id_str = args.get("source_instance_id", "")
        project_id_str = args.get("project_id", "")

        source_instance_id = None
        project_id = None

        # Parse source_instance_id
        if source_instance_id_str:
            try:
                source_instance_id = UUID(source_instance_id_str)
                logger.debug(
                    f"[PM_TOOLS] Got source_instance_id from hook injection: {source_instance_id}"
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"[PM_TOOLS] Invalid source_instance_id format: {source_instance_id_str}, error: {e}"
                )

        # Parse project_id
        if project_id_str:
            try:
                project_id = UUID(project_id_str)
                logger.debug(
                    f"[PM_TOOLS] Got project_id from hook injection: {project_id}"
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"[PM_TOOLS] Invalid project_id format: {project_id_str}, error: {e}"
                )

        # Validate required parameters
        if not source_instance_id:
            return _error(
                "Could not determine source instance. The inject_session_context_hook should have provided this."
            )
        if not project_id:
            return _error(
                "Could not determine project. The inject_session_context_hook should have provided this."
            )

        logger.info(
            f"[PM_TOOLS] Contact instance: "
            f"from={source_instance_id}, to={target_instance_id}, message_len={len(message)}"
        )

        # Validate instances exist and are in the same project
        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)

            source_instance = await session_repo.get_by_id(source_instance_id)
            if not source_instance:
                return _error(f"Source instance {source_instance_id} not found")

            target_instance = await session_repo.get_by_id(target_instance_id)
            if not target_instance:
                return _error(f"Target instance {target_instance_id} not found")

            # Validate same project
            if source_instance.project_id != project_id:
                return _error(f"Source instance is not in project {project_id}")
            if target_instance.project_id != project_id:
                return _error(
                    f"Target instance {target_instance_id} is not in project {project_id}"
                )
            if source_instance.project_id != target_instance.project_id:
                return _error(
                    f"Instances are in different projects: "
                    f"{source_instance.project_id} != {target_instance.project_id}"
                )

            # Get sender name for attribution
            sender_name = (
                source_instance.agent_id.replace("-", " ").title()
                if source_instance.agent_id
                else "PM"
            )

        # Update target session status to WORKING using SessionService
        from app.application.services.session_service import SessionService
        from app.infrastructure.database.repositories import ProjectRepositoryImpl
        from app.infrastructure.filesystem.agent_repository import (
            FileBasedAgentRepository,
        )
        from pathlib import Path

        async with get_repository_session() as db_session:
            session_service = SessionService(
                session_repo=SessionRepositoryImpl(db_session),
                project_repo=ProjectRepositoryImpl(db_session),
                agent_repo=FileBasedAgentRepository(Path("data/agents")),
            )
            await session_service.transition_to_working(target_instance_id)

        # Lazy import to avoid circular dependency
        from app.api.dependencies import get_session_executor

        # Enqueue message for delivery to target instance
        executor = get_session_executor()
        await executor.enqueue(
            session_id=target_instance_id,
            message=message,
            sender_name=sender_name,
            sender_session_id=source_instance_id,
        )

        logger.info(
            f"[PM_TOOLS] Message enqueued for delivery: "
            f"from={source_instance_id} to={target_instance_id}"
        )

        result_text = f"""✓ Message sent to instance {target_instance_id}

From: {sender_name} (Instance: {str(source_instance_id)[:8]})
To: {target_instance.agent_id or "Unknown"} (Instance: {str(target_instance_id)[:8]})
Message: {message[:100]}{"..." if len(message) > 100 else ""}

The message has been queued for delivery and will be processed by the target instance."""

        return {
            "content": [{"type": "text", "text": result_text}],
            "source_instance_id": str(source_instance_id),
            "target_instance_id": str(target_instance_id),
        }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error in contact_instance: {e}", exc_info=True)
        return _error(f"Failed to send message: {str(e)}")


@tool(
    "list_team_members",
    "View available team members assigned to the current project",
    {},
)
async def list_team_members(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List team members assigned to the project.

    Args (from args dict):
        project_id: UUID of the project (auto-injected by hook, not in schema)

    Returns:
        Dict with content array containing team member details
    """
    try:
        # Extract project_id from context
        project_id_str = args.get("project_id", "")

        if not project_id_str:
            return _error("project_id is required")

        try:
            project_id = UUID(project_id_str)
        except ValueError:
            return _error(f"Invalid project_id format: {project_id_str}")

        logger.info(f"[PM_TOOLS] Listing team members for project: {project_id}")

        # Get project to retrieve team_member_ids
        from app.infrastructure.database.repositories import ProjectRepositoryImpl
        from app.infrastructure.filesystem.agent_repository import (
            FileBasedAgentRepository,
        )
        from app.core.config import settings

        async with get_repository_session() as db:
            project_repo = ProjectRepositoryImpl(db)
            project = await project_repo.get_by_id(project_id)

            if not project:
                return _error(f"Project {project_id} not found")

            # Get team member IDs from project
            team_member_ids = project.team_member_ids or []

            if not team_member_ids:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "No team members assigned to this project yet.\n\nUse the project settings to assign agents to this project.",
                        }
                    ]
                }

            # Load agent details from filesystem
            agent_repo = FileBasedAgentRepository(settings.agents_dir)
            team_members = []

            for agent_id in team_member_ids:
                agent = await agent_repo.get_by_id(agent_id)
                if agent:
                    team_members.append(
                        {
                            "id": agent.id,
                            "name": agent.name,
                            "description": agent.description or "No description",
                        }
                    )

            # Format response
            if not team_members:
                result_text = (
                    "No valid team members found (agents may have been deleted)."
                )
            else:
                result_text = f"**Team Members ({len(team_members)}):**\n\n"
                for member in team_members:
                    result_text += f"• **({member['id']}) {member['name']}:** {member['description']}\n"

            return {
                "content": [{"type": "text", "text": result_text}],
                "team_members": team_members,
            }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error listing team members: {e}", exc_info=True)
        return _error(f"Failed to list team members: {str(e)}")


@tool(
    "get_project_status",
    "View all instances and their current stages in the project",
    {},
)
async def get_project_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get status of all sessions/instances in the project.

    Args (from args dict):
        project_id: UUID of the project (auto-injected by hook, not in schema)

    Returns:
        Dict with content array containing project status overview
    """
    try:
        # Extract and validate project_id
        project_id_str = args.get("project_id", "")
        if not project_id_str:
            return _error("project_id is required (should be auto-injected)")

        try:
            project_id = UUID(project_id_str)
        except ValueError:
            return _error(f"Invalid project_id format: {project_id_str}")

        logger.info(f"[PM_TOOLS] Getting project status for project {project_id}")

        # Query all sessions for this project
        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)

            # Get all sessions for the project
            from app.infrastructure.database.repositories.project_repository import (
                ProjectRepositoryImpl,
            )

            project_repo = ProjectRepositoryImpl(db)
            project_entity = await project_repo.get_by_id(project_id)

            if not project_entity:
                return _error(f"Project {project_id} not found")

            # Get all sessions in the project
            all_sessions = await session_repo.get_by_project_id(project_id)

        # Organize sessions by type and stage
        pm_sessions = []
        specialist_sessions = []

        for session in all_sessions:
            session_info = {
                "id": str(session.id),
                "agent_id": session.agent_id or "Unknown",
                "status": (
                    session.status.value
                    if hasattr(session.status, "value")
                    else str(session.status)
                ),
                "stage": (
                    session.context.get("kanban_stage", "unknown")
                    if session.context
                    else "unknown"
                ),
                "description": (
                    session.context.get("description", "No description")
                    if session.context
                    else "No description"
                ),
            }

            if session.session_type == SessionType.PM:
                pm_sessions.append(session_info)
            else:
                specialist_sessions.append(session_info)

        # Format response
        result_text = f"**Project Status: {project_entity.name}**\n\n"

        if pm_sessions:
            result_text += f"**PM Sessions ({len(pm_sessions)}):**\n"
            for pm in pm_sessions:
                result_text += (
                    f"• {pm['agent_id']} (ID: {pm['id']}) - Status: {pm['status']}\n"
                )
            result_text += "\n"

        if specialist_sessions:
            result_text += f"**Specialist Sessions ({len(specialist_sessions)}):**\n"
            # Group by stage
            stages = {}
            for session in specialist_sessions:
                stage = session["stage"]
                if stage not in stages:
                    stages[stage] = []
                stages[stage].append(session)

            for stage, sessions in sorted(stages.items()):
                result_text += f"\n**{stage.upper()}:**\n"
                for session in sessions:
                    result_text += f"  • {session['agent_id']} (ID: {session['id']}) - {session['status']}\n"
                    if session["description"]:
                        result_text += f"    Task: {session['description'][:80]}{'...' if len(session['description']) > 80 else ''}\n"
        else:
            result_text += "No specialist sessions yet.\n\nUse `spawn_instance` to create work instances."

        return {
            "content": [{"type": "text", "text": result_text}],
            "project_id": str(project_id),
            "pm_sessions": pm_sessions,
            "specialist_sessions": specialist_sessions,
        }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error getting project status: {e}", exc_info=True)
        return _error(f"Failed to get project status: {str(e)}")


@tool(
    "update_instance_stage",
    "Move an instance through workflow stages (backlog → in_progress → review → done → cancelled)",
    {
        "instance_id": str,
        "new_stage": str,
        "reason": str,
    },
)
async def update_instance_stage(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the kanban stage of an instance.

    Args (from args dict):
        instance_id: UUID of the instance to update
        new_stage: New stage (backlog, in_progress, review, done, cancelled)
        reason: Optional reason for the stage change (required for 'cancelled')
        project_id: UUID of the project (auto-injected by hook, not in schema)

    Returns:
        Dict with content array containing update confirmation
    """
    try:
        # Extract and validate parameters
        instance_id_str = args.get("instance_id", "")
        new_stage = args.get("new_stage", "").lower()
        reason = args.get("reason", "")
        project_id_str = args.get("project_id", "")

        if not instance_id_str:
            return _error("instance_id is required")
        if not new_stage:
            return _error("new_stage is required")
        if not project_id_str:
            return _error("project_id is required (should be auto-injected)")

        # Validate stage
        valid_stages = ["backlog", "in_progress", "review", "done", "cancelled"]
        if new_stage not in valid_stages:
            return _error(
                f"Invalid stage '{new_stage}'. Must be one of: {', '.join(valid_stages)}"
            )

        # Require reason for cancelled stage
        if new_stage == "cancelled" and not reason:
            return _error("reason is required when cancelling an instance")

        try:
            instance_id = UUID(instance_id_str)
            project_id = UUID(project_id_str)
        except ValueError as e:
            return _error(f"Invalid UUID format: {e}")

        logger.info(f"[PM_TOOLS] Updating instance {instance_id} to stage {new_stage}")

        # Update session in database
        async with get_repository_session() as db:
            session_repo = SessionRepositoryImpl(db)
            session_entity = await session_repo.get_by_id(instance_id)

            if not session_entity:
                return _error(f"Instance {instance_id} not found")

            # Validate instance is in the same project
            if session_entity.project_id != project_id:
                return _error(f"Instance {instance_id} is not in project {project_id}")

            # Update the kanban stage in context
            if not session_entity.context:
                session_entity.context = {}

            old_stage = session_entity.context.get("kanban_stage", "unknown")
            old_status = session_entity.status
            session_entity.context["kanban_stage"] = new_stage

            # Handle special stages that affect session status
            if new_stage == "cancelled":
                session_entity.status = SessionStatus.CANCELLED
                session_entity.context["cancelled_by"] = "pm"
                session_entity.context["cancellation_reason"] = reason
                session_entity.context["cancelled_at"] = (
                    __import__("datetime").datetime.now().isoformat()
                )
            elif new_stage == "done":
                # Mark as done when moved to done
                if session_entity.status not in [
                    SessionStatus.DONE,
                    SessionStatus.CANCELLED,
                ]:
                    session_entity.status = SessionStatus.DONE
            elif new_stage == "in_progress":
                # Mark as working when moved to in_progress
                if session_entity.status == SessionStatus.INITIALIZING:
                    session_entity.status = SessionStatus.WORKING

            # Update in database
            await session_repo.update(session_entity)
            await db.commit()

        # Build result message
        status_changed = old_status != session_entity.status
        result_text = f"""✓ Instance stage updated successfully!

Instance: {session_entity.agent_id or "Unknown"} (ID: {str(instance_id)[:8]}...)
Stage: {old_stage} → {new_stage}"""

        if status_changed:
            result_text += f"\nStatus: {old_status.value if hasattr(old_status, 'value') else str(old_status)} → {session_entity.status.value if hasattr(session_entity.status, 'value') else str(session_entity.status)}"

        if new_stage == "cancelled":
            result_text += f"\nReason: {reason}"

        result_text += f"\n\nThe instance is now in the '{new_stage}' stage."

        return {
            "content": [{"type": "text", "text": result_text}],
            "instance_id": str(instance_id),
            "old_stage": old_stage,
            "new_stage": new_stage,
        }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error updating instance stage: {e}", exc_info=True)
        return _error(f"Failed to update instance stage: {str(e)}")


@tool(
    "create_task",
    "Create a new task in the current project",
    {
        "name": str,
        "description": str,
    },
)
async def create_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a task that groups related sessions toward a shared goal.

    Args (from args dict):
        name: Task name (required, non-empty)
        description: Optional longer description of the task
        project_id: UUID of the project (auto-injected by hook)

    Returns:
        Dict with content array containing task creation confirmation
    """
    try:
        project_id_str = args.get("project_id", "")
        name = args.get("name", "").strip()
        description = args.get("description", "") or None

        if not project_id_str:
            return _error("project_id is required (should be auto-injected)")
        if not name:
            return _error("name is required and must not be empty")

        try:
            project_id = UUID(project_id_str)
        except ValueError:
            return _error(f"Invalid project_id format: {project_id_str}")

        async with get_repository_session() as db:
            project_repo = ProjectRepositoryImpl(db)
            project = await project_repo.get_by_id(project_id)
            if project is None:
                return _error(f"Project {project_id} not found")

            task_repo = TaskRepositoryImpl(db)
            from app.domain.entities.task import Task as TaskEntity

            task_entity = TaskEntity(
                id=uuid4(),
                project_id=project_id,
                name=name,
                description=description,
            )
            task_entity.validate()
            created = await task_repo.create(task_entity)
            await db.commit()

        logger.info(f"[PM_TOOLS] Created task {created.id} in project {project_id}")

        result_text = f"""✓ Task created successfully!

Task ID: {created.id}
Name: {created.name}
Status: {created.status.value if hasattr(created.status, "value") else str(created.status)}

Use spawn_instance with task_id={created.id} to bind sessions to this task."""

        return {
            "content": [{"type": "text", "text": result_text}],
            "task_id": str(created.id),
            "project_id": str(project_id),
        }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error creating task: {e}", exc_info=True)
        return _error(f"Failed to create task: {str(e)}")


@tool(
    "list_tasks",
    "List all tasks in the current project with their status",
    {},
)
async def list_tasks(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all tasks in the project, grouped by status.

    Args (from args dict):
        project_id: UUID of the project (auto-injected by hook)

    Returns:
        Dict with content array containing task list
    """
    try:
        project_id_str = args.get("project_id", "")
        if not project_id_str:
            return _error("project_id is required (should be auto-injected)")

        try:
            project_id = UUID(project_id_str)
        except ValueError:
            return _error(f"Invalid project_id format: {project_id_str}")

        async with get_repository_session() as db:
            task_repo = TaskRepositoryImpl(db)
            tasks = await task_repo.get_by_project_id(project_id)

        if not tasks:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "No tasks found for this project.\n\nUse create_task to add tasks and organize your work.",
                    }
                ],
                "tasks": [],
            }

        # Group by status
        grouped: Dict[str, list] = {}
        for task in tasks:
            status = (
                task.status.value if hasattr(task.status, "value") else str(task.status)
            )
            grouped.setdefault(status, []).append(task)

        result_text = f"**Tasks ({len(tasks)}):**\n"
        status_order = ["open", "in_progress", "done", "archived"]
        for status in status_order:
            if status not in grouped:
                continue
            result_text += f"\n**{status.upper()} ({len(grouped[status])}):**\n"
            for task in grouped[status]:
                desc = (
                    f" — {task.description[:60]}..."
                    if task.description and len(task.description) > 60
                    else (f" — {task.description}" if task.description else "")
                )
                result_text += f"  • [{task.id}] {task.name}{desc}\n"

        task_list = [
            {
                "id": str(t.id),
                "name": t.name,
                "status": (
                    t.status.value if hasattr(t.status, "value") else str(t.status)
                ),
                "description": t.description,
            }
            for t in tasks
        ]

        return {
            "content": [{"type": "text", "text": result_text}],
            "tasks": task_list,
        }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error listing tasks: {e}", exc_info=True)
        return _error(f"Failed to list tasks: {str(e)}")


_VALID_TASK_STATUSES = ["open", "in_progress", "done", "archived"]


@tool(
    "update_task_status",
    "Move a task through workflow statuses (open → in_progress → done → archived)",
    {
        "task_id": str,
        "new_status": str,
    },
)
async def update_task_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the status of a task.

    Args (from args dict):
        task_id: UUID of the task to update
        new_status: Target status — one of: open, in_progress, done, archived
        project_id: UUID of the project (auto-injected by hook)

    Returns:
        Dict with content array containing update confirmation
    """
    try:
        task_id_str = args.get("task_id", "")
        new_status = args.get("new_status", "").lower().strip()

        if not task_id_str:
            return _error("task_id is required")
        if not new_status:
            return _error("new_status is required")
        if new_status not in _VALID_TASK_STATUSES:
            return _error(
                f"Invalid status '{new_status}'. Must be one of: {', '.join(_VALID_TASK_STATUSES)}"
            )

        try:
            task_id = UUID(task_id_str)
        except ValueError:
            return _error(f"Invalid task_id format: {task_id_str}")

        async with get_repository_session() as db:
            task_repo = TaskRepositoryImpl(db)
            task_entity = await task_repo.get_by_id(task_id)
            if task_entity is None:
                return _error(f"Task {task_id} not found")

            old_status = (
                task_entity.status.value
                if hasattr(task_entity.status, "value")
                else str(task_entity.status)
            )
            task_entity.status = TaskStatus(new_status)
            updated = await task_repo.update(task_entity)
            await db.commit()

        logger.info(
            f"[PM_TOOLS] Updated task {task_id} status: {old_status} → {new_status}"
        )

        result_text = f"""✓ Task status updated!

Task: {updated.name} [{task_id}]
Status: {old_status} → {new_status}"""

        return {
            "content": [{"type": "text", "text": result_text}],
            "task_id": str(task_id),
            "old_status": old_status,
            "new_status": new_status,
        }

    except Exception as e:
        logger.error(f"[PM_TOOLS] Error updating task status: {e}", exc_info=True)
        return _error(f"Failed to update task status: {str(e)}")


# Create the MCP server with PM management tools
pm_management_server = create_sdk_mcp_server(
    name="pm_management",
    version="1.0.0",
    tools=[
        spawn_instance,
        contact_instance,
        list_team_members,
        get_project_status,
        update_instance_stage,
        create_task,
        list_tasks,
        update_task_status,
    ],
)
