"""Unit tests for project deletion cascade (WORK-01, with mocked repositories)."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.application.services.exceptions import ProjectNotFoundError
from app.application.services.project_service import ProjectService


@pytest.fixture
def project_service():
    """Project service with mocked dependencies."""
    return ProjectService(
        project_repo=AsyncMock(),
        session_repo=AsyncMock(),
        task_repo=AsyncMock(),
        agent_repo=AsyncMock(),
    )


class TestProjectDeleteCascade:
    """Deleting a project hides its children with it."""

    # spec: SPEC-work-project-delete-cascade R1
    async def test_delete_cascades_to_tasks_and_sessions(self, project_service):
        """A project's live tasks and sessions are deleted along with it."""
        project_id = uuid4()
        project_service._project_repo.exists.return_value = True
        project_service._task_repo.soft_delete_by_project.return_value = 2
        project_service._session_repo.soft_delete_by_project.return_value = 3

        await project_service.delete_project(project_id)

        project_service._task_repo.soft_delete_by_project.assert_awaited_once()
        project_service._session_repo.soft_delete_by_project.assert_awaited_once()
        project_service._project_repo.delete.assert_awaited_once()

        assert (
            project_service._task_repo.soft_delete_by_project.await_args.args[0]
            == project_id
        )
        assert (
            project_service._session_repo.soft_delete_by_project.await_args.args[0]
            == project_id
        )

    # spec: SPEC-work-project-delete-cascade R1
    async def test_delete_uses_one_shared_timestamp(self, project_service):
        """Project and children are stamped with the identical timestamp."""
        project_id = uuid4()
        project_service._project_repo.exists.return_value = True
        project_service._task_repo.soft_delete_by_project.return_value = 1
        project_service._session_repo.soft_delete_by_project.return_value = 1

        await project_service.delete_project(project_id)

        task_stamp = project_service._task_repo.soft_delete_by_project.await_args.args[
            1
        ]
        session_stamp = (
            project_service._session_repo.soft_delete_by_project.await_args.args[1]
        )
        project_stamp = project_service._project_repo.delete.await_args.args[1]

        assert task_stamp == session_stamp == project_stamp
        assert task_stamp.tzinfo is not None, "timestamp must be timezone-aware"

    # spec: SPEC-work-project-delete-cascade R1
    async def test_delete_with_no_children_succeeds(self, project_service):
        """A project with no tasks or sessions deletes cleanly."""
        project_id = uuid4()
        project_service._project_repo.exists.return_value = True
        project_service._task_repo.soft_delete_by_project.return_value = 0
        project_service._session_repo.soft_delete_by_project.return_value = 0

        await project_service.delete_project(project_id)

        project_service._project_repo.delete.assert_awaited_once()

    # spec: SPEC-work-project-delete-cascade R1
    async def test_delete_missing_project_raises(self, project_service):
        """Deleting an unknown project raises and touches no child."""
        project_service._project_repo.exists.return_value = False

        with pytest.raises(ProjectNotFoundError):
            await project_service.delete_project(uuid4())

        project_service._task_repo.soft_delete_by_project.assert_not_awaited()
        project_service._session_repo.soft_delete_by_project.assert_not_awaited()
        project_service._project_repo.delete.assert_not_awaited()

    # spec: SPEC-work-project-delete-cascade R5
    async def test_delete_touches_no_files_on_disk(self, project_service, monkeypatch):
        """Deletion leaves the project's files on disk exactly as they were."""
        import os
        import shutil

        def _fail(*args, **kwargs):  # pragma: no cover - only runs on regression
            raise AssertionError("project deletion must not touch the filesystem")

        monkeypatch.setattr(shutil, "rmtree", _fail)
        monkeypatch.setattr(os, "remove", _fail)
        monkeypatch.setattr(os, "unlink", _fail)

        project_id = uuid4()
        project_service._project_repo.exists.return_value = True
        project_service._task_repo.soft_delete_by_project.return_value = 0
        project_service._session_repo.soft_delete_by_project.return_value = 0

        await project_service.delete_project(project_id)


class TestProjectDeleteStopsRunningAgents:
    """Live agents are stopped before the project is hidden (R3, R4)."""

    @staticmethod
    def _session(session_id):
        session = Mock()
        session.id = session_id
        return session

    @staticmethod
    def _patch_executor(monkeypatch, executor):
        """Stub the lazily-imported get_session_executor used by the service."""
        import app.api.dependencies as dependencies

        monkeypatch.setattr(dependencies, "get_session_executor", lambda: executor)

    # spec: SPEC-work-project-delete-cascade R3
    async def test_running_agents_are_interrupted(self, project_service, monkeypatch):
        """Agents still running for the project are stopped."""
        running_id, idle_id = uuid4(), uuid4()

        executor = Mock()
        executor.is_processing.side_effect = lambda sid: sid == running_id
        executor.interrupt = AsyncMock()
        self._patch_executor(monkeypatch, executor)

        project_service._project_repo.exists.return_value = True
        project_service._session_repo.get_by_project_id.return_value = [
            self._session(running_id),
            self._session(idle_id),
        ]
        project_service._task_repo.soft_delete_by_project.return_value = 0
        project_service._session_repo.soft_delete_by_project.return_value = 2

        await project_service.delete_project(uuid4())

        executor.interrupt.assert_awaited_once_with(running_id)

    # spec: SPEC-work-project-delete-cascade R3
    async def test_agents_are_interrupted_before_the_project_is_hidden(
        self, project_service, monkeypatch
    ):
        """The interrupt happens before any row is stamped deleted."""
        running_id = uuid4()
        order = []

        executor = Mock()
        executor.is_processing.return_value = True
        executor.interrupt = AsyncMock(
            side_effect=lambda sid: order.append("interrupt")
        )
        self._patch_executor(monkeypatch, executor)

        project_service._project_repo.exists.return_value = True
        project_service._session_repo.get_by_project_id.return_value = [
            self._session(running_id)
        ]
        project_service._task_repo.soft_delete_by_project.side_effect = (
            lambda *a: order.append("delete_tasks") or 0
        )
        project_service._session_repo.soft_delete_by_project.side_effect = (
            lambda *a: order.append("delete_sessions") or 0
        )
        project_service._project_repo.delete.side_effect = lambda *a: order.append(
            "delete_project"
        )

        await project_service.delete_project(uuid4())

        assert order[0] == "interrupt", f"interrupt must come first, got {order}"
        assert "delete_project" in order

    # spec: SPEC-work-project-delete-cascade R4
    async def test_failed_interrupt_does_not_abort_the_delete(
        self, project_service, monkeypatch
    ):
        """An agent that cannot be stopped does not leave a half-deleted project."""
        executor = Mock()
        executor.is_processing.return_value = True
        executor.interrupt = AsyncMock(side_effect=RuntimeError("session is gone"))
        self._patch_executor(monkeypatch, executor)

        project_service._project_repo.exists.return_value = True
        project_service._session_repo.get_by_project_id.return_value = [
            self._session(uuid4())
        ]
        project_service._task_repo.soft_delete_by_project.return_value = 0
        project_service._session_repo.soft_delete_by_project.return_value = 1

        await project_service.delete_project(uuid4())

        project_service._project_repo.delete.assert_awaited_once()

    # spec: SPEC-work-project-delete-cascade R4
    async def test_one_failed_interrupt_does_not_stop_the_others(
        self, project_service, monkeypatch
    ):
        """Interrupt failures are isolated per session."""
        bad_id, good_id = uuid4(), uuid4()

        async def _interrupt(sid):
            if sid == bad_id:
                raise RuntimeError("unresponsive")

        executor = Mock()
        executor.is_processing.return_value = True
        executor.interrupt = AsyncMock(side_effect=_interrupt)
        self._patch_executor(monkeypatch, executor)

        project_service._project_repo.exists.return_value = True
        project_service._session_repo.get_by_project_id.return_value = [
            self._session(bad_id),
            self._session(good_id),
        ]
        project_service._task_repo.soft_delete_by_project.return_value = 0
        project_service._session_repo.soft_delete_by_project.return_value = 2

        await project_service.delete_project(uuid4())

        assert executor.interrupt.await_count == 2
        project_service._project_repo.delete.assert_awaited_once()

    # spec: SPEC-work-project-delete-cascade R4
    async def test_executor_unavailable_does_not_abort_the_delete(
        self, project_service, monkeypatch
    ):
        """If the executor cannot be reached at all, the delete still completes."""
        import app.api.dependencies as dependencies

        def _boom():
            raise RuntimeError("executor not wired")

        monkeypatch.setattr(dependencies, "get_session_executor", _boom)

        project_service._project_repo.exists.return_value = True
        project_service._session_repo.get_by_project_id.return_value = []
        project_service._task_repo.soft_delete_by_project.return_value = 0
        project_service._session_repo.soft_delete_by_project.return_value = 0

        await project_service.delete_project(uuid4())

        project_service._project_repo.delete.assert_awaited_once()


class TestSoftDeleteByProjectQuery:
    """The bulk soft-delete only touches children that are still live (R2)."""

    # spec: SPEC-work-project-delete-cascade R2
    @pytest.mark.parametrize(
        "repo_module,repo_class,model_name",
        [
            (
                "app.infrastructure.database.repositories.session_repository",
                "SessionRepositoryImpl",
                "Session",
            ),
            (
                "app.infrastructure.database.repositories.task_repository",
                "TaskRepositoryImpl",
                "Task",
            ),
        ],
    )
    async def test_bulk_update_excludes_already_deleted_children(
        self, repo_module, repo_class, model_name
    ):
        """
        A child deleted earlier keeps its original timestamp.

        The guarantee is carried by the WHERE clause: the bulk UPDATE only matches rows
        whose deleted_at IS NULL, so a previously-deleted child is never restamped with
        the project's timestamp. That distinction is what makes a later restore able to
        tell "hidden by this delete" from "already deleted".
        """
        import importlib

        from datetime import datetime, timezone

        module = importlib.import_module(repo_module)
        repo_cls = getattr(module, repo_class)

        db_session = AsyncMock()
        result = AsyncMock()
        result.rowcount = 1
        db_session.execute.return_value = result

        repo = repo_cls(db_session)
        stamp = datetime.now(timezone.utc)
        project_id = uuid4()

        await repo.soft_delete_by_project(project_id, stamp)

        db_session.execute.assert_awaited_once()
        stmt = db_session.execute.await_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))

        assert "deleted_at IS NULL" in compiled, (
            "bulk soft-delete must skip children that are already deleted, "
            f"got: {compiled}"
        )
        assert model_name.lower() in compiled.lower()

    # spec: SPEC-work-project-delete-cascade R1
    async def test_bulk_update_returns_affected_count(self):
        """The bulk delete reports how many children it hid."""
        from datetime import datetime, timezone

        from app.infrastructure.database.repositories.session_repository import (
            SessionRepositoryImpl,
        )

        db_session = AsyncMock()
        result = AsyncMock()
        result.rowcount = 7
        db_session.execute.return_value = result

        repo = SessionRepositoryImpl(db_session)
        count = await repo.soft_delete_by_project(uuid4(), datetime.now(timezone.utc))

        assert count == 7
