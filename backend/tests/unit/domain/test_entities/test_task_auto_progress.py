"""Unit tests for task auto-progression when sessions go WORKING."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.value_objects.task_status import TaskStatus
from app.infrastructure.claude.state.session_status_manager import SessionStatusManager


@pytest.fixture
def manager():
    return SessionStatusManager()


def _make_task(status: TaskStatus, task_id=None, project_id=None):
    task = MagicMock()
    task.id = task_id or uuid4()
    task.project_id = project_id or uuid4()
    task.status = status
    return task


def _make_session(task_id=None, project_id=None):
    from app.domain.value_objects import SessionStatus

    session = MagicMock()
    session.id = uuid4()
    session.task_id = task_id
    session.project_id = project_id or uuid4()
    session.status = SessionStatus.IDLE
    session.error_message = None
    session.sync_kanban_stage = MagicMock()
    return session


@pytest.mark.asyncio
async def test_open_task_moves_to_in_progress_when_session_starts(manager):
    """Task in OPEN status moves to IN_PROGRESS when any session goes WORKING."""
    session_id = uuid4()
    task_id = uuid4()
    project_id = uuid4()

    session = _make_session(task_id=task_id, project_id=project_id)
    task = _make_task(TaskStatus.OPEN, task_id=task_id, project_id=project_id)

    with (
        patch(
            "app.infrastructure.claude.state.session_status_manager.get_repository_session"
        ) as mock_repo_session,
        patch(
            "app.infrastructure.claude.state.session_status_manager.sse_manager"
        ) as mock_sse,
    ):
        # First call: session repo context
        session_db = AsyncMock()
        session_repo = AsyncMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        session_repo.update = AsyncMock()

        # Second call: task repo context
        task_db = AsyncMock()
        task_repo_impl = AsyncMock()
        task_repo_impl.get_by_id = AsyncMock(return_value=task)
        task_repo_impl.update = AsyncMock()

        # Mock context managers
        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_db)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        task_ctx = AsyncMock()
        task_ctx.__aenter__ = AsyncMock(return_value=task_db)
        task_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_session.side_effect = [session_ctx, task_ctx]

        with (
            patch(
                "app.infrastructure.claude.state.session_status_manager.SessionRepositoryImpl",
                return_value=session_repo,
            ),
            patch(
                "app.infrastructure.claude.state.session_status_manager.TaskRepositoryImpl",
                return_value=task_repo_impl,
            ),
        ):
            mock_sse.broadcast = AsyncMock()
            await manager.update_to_working(session_id)

    task.start.assert_called_once()
    task_repo_impl.update.assert_called_once_with(task)


@pytest.mark.asyncio
async def test_in_progress_task_not_changed(manager):
    """Task already IN_PROGRESS is left unchanged."""
    session_id = uuid4()
    task_id = uuid4()
    project_id = uuid4()

    session = _make_session(task_id=task_id, project_id=project_id)
    task = _make_task(TaskStatus.IN_PROGRESS, task_id=task_id, project_id=project_id)

    with (
        patch(
            "app.infrastructure.claude.state.session_status_manager.get_repository_session"
        ) as mock_repo_session,
        patch(
            "app.infrastructure.claude.state.session_status_manager.sse_manager"
        ) as mock_sse,
    ):
        session_db = AsyncMock()
        session_repo = AsyncMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        session_repo.update = AsyncMock()

        task_db = AsyncMock()
        task_repo_impl = AsyncMock()
        task_repo_impl.get_by_id = AsyncMock(return_value=task)
        task_repo_impl.update = AsyncMock()

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_db)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        task_ctx = AsyncMock()
        task_ctx.__aenter__ = AsyncMock(return_value=task_db)
        task_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_session.side_effect = [session_ctx, task_ctx]

        with (
            patch(
                "app.infrastructure.claude.state.session_status_manager.SessionRepositoryImpl",
                return_value=session_repo,
            ),
            patch(
                "app.infrastructure.claude.state.session_status_manager.TaskRepositoryImpl",
                return_value=task_repo_impl,
            ),
        ):
            mock_sse.broadcast = AsyncMock()
            await manager.update_to_working(session_id)

    task.start.assert_not_called()
    task_repo_impl.update.assert_not_called()


@pytest.mark.asyncio
async def test_done_task_not_changed(manager):
    """Task in DONE status is never auto-progressed."""
    session_id = uuid4()
    task_id = uuid4()
    project_id = uuid4()

    session = _make_session(task_id=task_id, project_id=project_id)
    task = _make_task(TaskStatus.DONE, task_id=task_id, project_id=project_id)

    with (
        patch(
            "app.infrastructure.claude.state.session_status_manager.get_repository_session"
        ) as mock_repo_session,
        patch(
            "app.infrastructure.claude.state.session_status_manager.sse_manager"
        ) as mock_sse,
    ):
        session_db = AsyncMock()
        session_repo = AsyncMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        session_repo.update = AsyncMock()

        task_db = AsyncMock()
        task_repo_impl = AsyncMock()
        task_repo_impl.get_by_id = AsyncMock(return_value=task)
        task_repo_impl.update = AsyncMock()

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_db)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        task_ctx = AsyncMock()
        task_ctx.__aenter__ = AsyncMock(return_value=task_db)
        task_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_session.side_effect = [session_ctx, task_ctx]

        with (
            patch(
                "app.infrastructure.claude.state.session_status_manager.SessionRepositoryImpl",
                return_value=session_repo,
            ),
            patch(
                "app.infrastructure.claude.state.session_status_manager.TaskRepositoryImpl",
                return_value=task_repo_impl,
            ),
        ):
            mock_sse.broadcast = AsyncMock()
            await manager.update_to_working(session_id)

    task.start.assert_not_called()
    task_repo_impl.update.assert_not_called()


@pytest.mark.asyncio
async def test_archived_task_not_changed(manager):
    """Task in ARCHIVED status is never auto-progressed."""
    session_id = uuid4()
    task_id = uuid4()
    project_id = uuid4()

    session = _make_session(task_id=task_id, project_id=project_id)
    task = _make_task(TaskStatus.ARCHIVED, task_id=task_id, project_id=project_id)

    with (
        patch(
            "app.infrastructure.claude.state.session_status_manager.get_repository_session"
        ) as mock_repo_session,
        patch(
            "app.infrastructure.claude.state.session_status_manager.sse_manager"
        ) as mock_sse,
    ):
        session_db = AsyncMock()
        session_repo = AsyncMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        session_repo.update = AsyncMock()

        task_db = AsyncMock()
        task_repo_impl = AsyncMock()
        task_repo_impl.get_by_id = AsyncMock(return_value=task)
        task_repo_impl.update = AsyncMock()

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_db)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        task_ctx = AsyncMock()
        task_ctx.__aenter__ = AsyncMock(return_value=task_db)
        task_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_session.side_effect = [session_ctx, task_ctx]

        with (
            patch(
                "app.infrastructure.claude.state.session_status_manager.SessionRepositoryImpl",
                return_value=session_repo,
            ),
            patch(
                "app.infrastructure.claude.state.session_status_manager.TaskRepositoryImpl",
                return_value=task_repo_impl,
            ),
        ):
            mock_sse.broadcast = AsyncMock()
            await manager.update_to_working(session_id)

    task.start.assert_not_called()
    task_repo_impl.update.assert_not_called()


@pytest.mark.asyncio
async def test_session_without_task_id_skips_task_update(manager):
    """Sessions with no task_id do not trigger any task query."""
    session_id = uuid4()
    session = _make_session(task_id=None)

    with (
        patch(
            "app.infrastructure.claude.state.session_status_manager.get_repository_session"
        ) as mock_repo_session,
        patch(
            "app.infrastructure.claude.state.session_status_manager.sse_manager"
        ) as mock_sse,
        patch(
            "app.infrastructure.claude.state.session_status_manager.TaskRepositoryImpl"
        ) as MockTaskRepo,
    ):
        session_db = AsyncMock()
        session_repo = AsyncMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        session_repo.update = AsyncMock()

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_db)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_session.return_value = session_ctx

        with patch(
            "app.infrastructure.claude.state.session_status_manager.SessionRepositoryImpl",
            return_value=session_repo,
        ):
            mock_sse.broadcast = AsyncMock()
            await manager.update_to_working(session_id)

    MockTaskRepo.assert_not_called()


@pytest.mark.asyncio
async def test_task_not_found_does_not_crash(manager):
    """If task is deleted between session load and task load, no error propagates."""
    session_id = uuid4()
    task_id = uuid4()
    project_id = uuid4()

    session = _make_session(task_id=task_id, project_id=project_id)

    with (
        patch(
            "app.infrastructure.claude.state.session_status_manager.get_repository_session"
        ) as mock_repo_session,
        patch(
            "app.infrastructure.claude.state.session_status_manager.sse_manager"
        ) as mock_sse,
    ):
        session_db = AsyncMock()
        session_repo = AsyncMock()
        session_repo.get_by_id = AsyncMock(return_value=session)
        session_repo.update = AsyncMock()

        task_db = AsyncMock()
        task_repo_impl = AsyncMock()
        task_repo_impl.get_by_id = AsyncMock(return_value=None)  # Task not found
        task_repo_impl.update = AsyncMock()

        session_ctx = AsyncMock()
        session_ctx.__aenter__ = AsyncMock(return_value=session_db)
        session_ctx.__aexit__ = AsyncMock(return_value=False)

        task_ctx = AsyncMock()
        task_ctx.__aenter__ = AsyncMock(return_value=task_db)
        task_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_session.side_effect = [session_ctx, task_ctx]

        with (
            patch(
                "app.infrastructure.claude.state.session_status_manager.SessionRepositoryImpl",
                return_value=session_repo,
            ),
            patch(
                "app.infrastructure.claude.state.session_status_manager.TaskRepositoryImpl",
                return_value=task_repo_impl,
            ),
        ):
            mock_sse.broadcast = AsyncMock()
            # Should not raise
            await manager.update_to_working(session_id)

    task_repo_impl.update.assert_not_called()
