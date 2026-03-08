"""Unit tests for PM management MCP tools — Task-aware features."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(result: Dict[str, Any]) -> bool:
    """Return True if result content does not start with ✗ Error."""
    text = result["content"][0]["text"]
    return not text.startswith("✗ Error")


def _error_text(result: Dict[str, Any]) -> str:
    return result["content"][0]["text"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_id():
    return str(uuid4())


@pytest.fixture
def task_id():
    return str(uuid4())


@pytest.fixture
def session_id():
    return str(uuid4())


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


class TestCreateTask:
    """Tests for the create_task PM tool."""

    @pytest.mark.asyncio
    async def test_creates_task_with_name_only(self, project_id):
        from app.infrastructure.mcp.servers.pm_management import (
            create_task as _create_task,
        )

        create_task = _create_task.handler

        fake_task_id = uuid4()

        mock_task = MagicMock()
        mock_task.id = fake_task_id
        mock_task.name = "Build auth module"
        mock_task.status = MagicMock(value="open")

        mock_task_dto = MagicMock()
        mock_task_dto.id = fake_task_id
        mock_task_dto.name = "Build auth module"
        mock_task_dto.status = "open"

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
            patch(
                "app.infrastructure.mcp.servers.pm_management.ProjectRepositoryImpl"
            ) as MockProjectRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_project_repo = AsyncMock()
            mock_project = MagicMock()
            mock_project_repo.get_by_id = AsyncMock(return_value=mock_project)
            MockProjectRepo.return_value = mock_project_repo

            mock_task_repo = AsyncMock()
            mock_task_repo.create = AsyncMock(return_value=mock_task)
            MockTaskRepo.return_value = mock_task_repo

            result = await create_task(
                {"project_id": project_id, "name": "Build auth module"}
            )

        assert _ok(result)
        assert "Build auth module" in _error_text(result)
        assert str(fake_task_id) in _error_text(result)
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_requires_name(self, project_id):
        from app.infrastructure.mcp.servers.pm_management import (
            create_task as _create_task,
        )

        create_task = _create_task.handler

        result = await create_task({"project_id": project_id, "name": ""})

        assert not _ok(result)
        assert "name" in _error_text(result).lower()

    @pytest.mark.asyncio
    async def test_requires_project_id(self):
        from app.infrastructure.mcp.servers.pm_management import (
            create_task as _create_task,
        )

        create_task = _create_task.handler

        result = await create_task({"name": "Some task"})

        assert not _ok(result)
        assert "project_id" in _error_text(result).lower()

    @pytest.mark.asyncio
    async def test_error_when_project_not_found(self, project_id):
        from app.infrastructure.mcp.servers.pm_management import (
            create_task as _create_task,
        )

        create_task = _create_task.handler

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch("app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"),
            patch(
                "app.infrastructure.mcp.servers.pm_management.ProjectRepositoryImpl"
            ) as MockProjectRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_project_repo = AsyncMock()
            mock_project_repo.get_by_id = AsyncMock(return_value=None)
            MockProjectRepo.return_value = mock_project_repo

            result = await create_task({"project_id": project_id, "name": "Task"})

        assert not _ok(result)
        assert "not found" in _error_text(result).lower()


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------


class TestListTasks:
    """Tests for the list_tasks PM tool."""

    @pytest.mark.asyncio
    async def test_lists_tasks_for_project(self, project_id):
        from app.infrastructure.mcp.servers.pm_management import (
            list_tasks as _list_tasks,
        )

        list_tasks = _list_tasks.handler

        task1 = MagicMock()
        task1.id = uuid4()
        task1.name = "Alpha"
        task1.status = MagicMock(value="open")
        task1.description = None

        task2 = MagicMock()
        task2.id = uuid4()
        task2.name = "Beta"
        task2.status = MagicMock(value="in_progress")
        task2.description = "Some desc"

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_task_repo = AsyncMock()
            mock_task_repo.get_by_project_id = AsyncMock(return_value=[task1, task2])
            MockTaskRepo.return_value = mock_task_repo

            result = await list_tasks({"project_id": project_id})

        assert _ok(result)
        text = _error_text(result)
        assert "Alpha" in text
        assert "Beta" in text
        assert "tasks" in result

    @pytest.mark.asyncio
    async def test_empty_task_list(self, project_id):
        from app.infrastructure.mcp.servers.pm_management import (
            list_tasks as _list_tasks,
        )

        list_tasks = _list_tasks.handler

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_task_repo = AsyncMock()
            mock_task_repo.get_by_project_id = AsyncMock(return_value=[])
            MockTaskRepo.return_value = mock_task_repo

            result = await list_tasks({"project_id": project_id})

        assert _ok(result)
        assert "no tasks" in _error_text(result).lower()

    @pytest.mark.asyncio
    async def test_requires_project_id(self):
        from app.infrastructure.mcp.servers.pm_management import (
            list_tasks as _list_tasks,
        )

        list_tasks = _list_tasks.handler

        result = await list_tasks({})

        assert not _ok(result)


# ---------------------------------------------------------------------------
# update_task_status
# ---------------------------------------------------------------------------


class TestUpdateTaskStatus:
    """Tests for the update_task_status PM tool."""

    @pytest.mark.asyncio
    async def test_updates_status_successfully(self, project_id, task_id):
        from app.infrastructure.mcp.servers.pm_management import (
            update_task_status as _update_task_status,
        )

        update_task_status = _update_task_status.handler

        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.name = "My Task"
        mock_task.status = MagicMock(value="open")
        mock_task.project_id = project_id

        updated_task = MagicMock()
        updated_task.id = task_id
        updated_task.name = "My Task"
        updated_task.status = MagicMock(value="in_progress")

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_task_repo = AsyncMock()
            mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
            mock_task_repo.update = AsyncMock(return_value=updated_task)
            MockTaskRepo.return_value = mock_task_repo

            result = await update_task_status(
                {
                    "project_id": project_id,
                    "task_id": task_id,
                    "new_status": "in_progress",
                }
            )

        assert _ok(result)
        assert "in_progress" in _error_text(result)

    @pytest.mark.asyncio
    async def test_rejects_invalid_status(self, project_id, task_id):
        from app.infrastructure.mcp.servers.pm_management import (
            update_task_status as _update_task_status,
        )

        update_task_status = _update_task_status.handler

        result = await update_task_status(
            {
                "project_id": project_id,
                "task_id": task_id,
                "new_status": "flying",
            }
        )

        assert not _ok(result)
        assert "invalid" in _error_text(result).lower()

    @pytest.mark.asyncio
    async def test_requires_task_id(self, project_id):
        from app.infrastructure.mcp.servers.pm_management import (
            update_task_status as _update_task_status,
        )

        update_task_status = _update_task_status.handler

        result = await update_task_status(
            {"project_id": project_id, "new_status": "done"}
        )

        assert not _ok(result)

    @pytest.mark.asyncio
    async def test_error_when_task_not_found(self, project_id, task_id):
        from app.infrastructure.mcp.servers.pm_management import (
            update_task_status as _update_task_status,
        )

        update_task_status = _update_task_status.handler

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_task_repo = AsyncMock()
            mock_task_repo.get_by_id = AsyncMock(return_value=None)
            MockTaskRepo.return_value = mock_task_repo

            result = await update_task_status(
                {
                    "project_id": project_id,
                    "task_id": task_id,
                    "new_status": "done",
                }
            )

        assert not _ok(result)
        assert "not found" in _error_text(result).lower()


# ---------------------------------------------------------------------------
# spawn_instance — task_id support
# ---------------------------------------------------------------------------


class TestSpawnInstanceWithTask:
    """Tests for spawn_instance with optional task_id binding."""

    @pytest.mark.asyncio
    async def test_spawn_without_task_id_still_works(self, project_id):
        """Backward compatibility: spawn_instance without task_id should work."""
        from app.infrastructure.mcp.servers.pm_management import (
            spawn_instance as _spawn_instance,
        )

        spawn_instance = _spawn_instance.handler

        fake_session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = fake_session_id
        mock_session.status = MagicMock(value="initializing")
        mock_session.task_id = None

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.SessionRepositoryImpl"
            ) as MockSessionRepo,
            patch(
                "app.infrastructure.mcp.servers.pm_management.FileBasedAgentRepository"
            ) as MockAgentRepo,
            patch("app.infrastructure.mcp.servers.pm_management.SessionDTO") as MockDTO,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_agent_repo = AsyncMock()
            mock_agent = MagicMock()
            mock_agent_repo.get_by_id = AsyncMock(return_value=mock_agent)
            MockAgentRepo.return_value = mock_agent_repo

            mock_session_repo = AsyncMock()
            mock_session_repo.create = AsyncMock(return_value=mock_session)
            MockSessionRepo.return_value = mock_session_repo

            mock_dto = MagicMock()
            mock_dto.id = fake_session_id
            mock_dto.status = "initializing"
            MockDTO.from_entity = MagicMock(return_value=mock_dto)

            result = await spawn_instance(
                {
                    "project_id": project_id,
                    "agent_id": "backend-dev",
                    "task_description": "Implement login flow",
                }
            )

        assert _ok(result)

    @pytest.mark.asyncio
    async def test_spawn_with_task_id_binds_session(self, project_id, task_id):
        """spawn_instance with task_id should create session with task_id set."""
        from app.infrastructure.mcp.servers.pm_management import (
            spawn_instance as _spawn_instance,
        )

        spawn_instance = _spawn_instance.handler

        fake_session_id = uuid4()
        mock_session = MagicMock()
        mock_session.id = fake_session_id
        mock_session.status = MagicMock(value="initializing")
        mock_session.task_id = task_id

        mock_task = MagicMock()
        mock_task.project_id = project_id

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.SessionRepositoryImpl"
            ) as MockSessionRepo,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
            patch(
                "app.infrastructure.mcp.servers.pm_management.FileBasedAgentRepository"
            ) as MockAgentRepo,
            patch("app.infrastructure.mcp.servers.pm_management.SessionDTO") as MockDTO,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_agent_repo = AsyncMock()
            mock_agent = MagicMock()
            mock_agent_repo.get_by_id = AsyncMock(return_value=mock_agent)
            MockAgentRepo.return_value = mock_agent_repo

            mock_task_repo = AsyncMock()
            mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
            MockTaskRepo.return_value = mock_task_repo

            mock_session_repo = AsyncMock()
            mock_session_repo.create = AsyncMock(return_value=mock_session)
            MockSessionRepo.return_value = mock_session_repo

            mock_dto = MagicMock()
            mock_dto.id = fake_session_id
            mock_dto.status = "initializing"
            MockDTO.from_entity = MagicMock(return_value=mock_dto)

            result = await spawn_instance(
                {
                    "project_id": project_id,
                    "agent_id": "backend-dev",
                    "task_description": "Implement login flow",
                    "task_id": task_id,
                }
            )

        assert _ok(result)
        # Verify task_id appears in the response
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_spawn_with_task_id_from_wrong_project_fails(
        self, project_id, task_id
    ):
        """spawn_instance with task_id from different project should fail."""
        from app.infrastructure.mcp.servers.pm_management import (
            spawn_instance as _spawn_instance,
        )

        spawn_instance = _spawn_instance.handler

        wrong_project_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.project_id = wrong_project_id  # different project

        with (
            patch(
                "app.infrastructure.mcp.servers.pm_management.get_repository_session"
            ) as mock_session_ctx,
            patch(
                "app.infrastructure.mcp.servers.pm_management.TaskRepositoryImpl"
            ) as MockTaskRepo,
            patch(
                "app.infrastructure.mcp.servers.pm_management.FileBasedAgentRepository"
            ) as MockAgentRepo,
        ):
            mock_db = AsyncMock()
            mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_agent_repo = AsyncMock()
            mock_agent = MagicMock()
            mock_agent_repo.get_by_id = AsyncMock(return_value=mock_agent)
            MockAgentRepo.return_value = mock_agent_repo

            mock_task_repo = AsyncMock()
            mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
            MockTaskRepo.return_value = mock_task_repo

            result = await spawn_instance(
                {
                    "project_id": project_id,
                    "agent_id": "backend-dev",
                    "task_description": "Implement login flow",
                    "task_id": task_id,
                }
            )

        assert not _ok(result)
        assert "project" in _error_text(result).lower()
