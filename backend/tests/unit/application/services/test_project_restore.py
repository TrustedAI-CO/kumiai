"""Unit tests for project restore (WORK-02, with mocked repositories)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.exceptions import (
    ProjectNotDeletedError,
    ProjectNotFoundError,
    ProjectPathConflictError,
)
from app.application.services.project_service import ProjectService
from app.core.exceptions import DatabaseError
from app.domain.entities import Project

STAMP = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
PATH = "/Users/dev/.kumiai/projects/demo"


@pytest.fixture
def project_service():
    """Project service with mocked dependencies."""
    return ProjectService(
        project_repo=AsyncMock(),
        session_repo=AsyncMock(),
        task_repo=AsyncMock(),
        agent_repo=AsyncMock(),
    )


def _deleted(service, stamp=STAMP, path=PATH, path_taken=False, project_id=None):
    """Arrange a deleted project that is free to restore."""
    service._project_repo.get_deletion_info.return_value = (stamp, path)
    service._project_repo.is_path_taken.return_value = path_taken
    service._task_repo.restore_by_project.return_value = 1
    service._session_repo.restore_by_project.return_value = 2
    service._project_repo.get_by_id.return_value = Project(
        id=project_id or uuid4(),
        name="demo",
        description=None,
        path=path,
    )


class TestProjectRestore:
    """Restoring a project is the exact mirror of deleting it."""

    # spec: SPEC-work-project-restore R1
    async def test_restore_brings_back_project_and_its_children(self, project_service):
        """The project and the children its deletion hid become visible again."""
        project_id = uuid4()
        _deleted(project_service)

        await project_service.restore_project(project_id)

        project_service._project_repo.restore.assert_awaited_once_with(project_id)
        project_service._task_repo.restore_by_project.assert_awaited_once()
        project_service._session_repo.restore_by_project.assert_awaited_once()

    # spec: SPEC-work-project-restore R2
    async def test_restore_keys_on_the_deletion_timestamp(self, project_service):
        """
        Children are matched by the project's own deletion timestamp.

        This is what keeps a child deleted earlier deleted: the restore only claims rows
        stamped at the exact moment this project was hidden.
        """
        project_id = uuid4()
        _deleted(project_service)

        await project_service.restore_project(project_id)

        assert project_service._task_repo.restore_by_project.await_args.args[1] == STAMP
        assert (
            project_service._session_repo.restore_by_project.await_args.args[1] == STAMP
        )

    # spec: SPEC-work-project-restore R3
    async def test_restoring_a_live_project_is_rejected(self, project_service):
        """A project that was never deleted cannot be restored."""
        project_service._project_repo.get_deletion_info.return_value = (None, PATH)

        with pytest.raises(ProjectNotDeletedError):
            await project_service.restore_project(uuid4())

        project_service._project_repo.restore.assert_not_awaited()
        project_service._task_repo.restore_by_project.assert_not_awaited()
        project_service._session_repo.restore_by_project.assert_not_awaited()

    # spec: SPEC-work-project-restore R3
    async def test_restoring_an_unknown_project_raises_not_found(self, project_service):
        """An id with no row at all is a 404, not a conflict."""
        project_service._project_repo.get_deletion_info.return_value = None

        with pytest.raises(ProjectNotFoundError):
            await project_service.restore_project(uuid4())

        project_service._project_repo.restore.assert_not_awaited()

    # spec: SPEC-work-project-restore R4
    async def test_restore_refuses_when_path_is_taken(self, project_service):
        """A live project holding the path blocks the restore, loudly."""
        _deleted(project_service, path_taken=True)

        with pytest.raises(ProjectPathConflictError) as excinfo:
            await project_service.restore_project(uuid4())

        assert PATH in str(excinfo.value), "the conflict must name the path"
        project_service._project_repo.restore.assert_not_awaited()
        project_service._task_repo.restore_by_project.assert_not_awaited()
        project_service._session_repo.restore_by_project.assert_not_awaited()

    # spec: SPEC-work-project-restore R4
    async def test_path_conflict_check_excludes_the_project_itself(
        self, project_service
    ):
        """The project's own row must not count as the conflict."""
        project_id = uuid4()
        _deleted(project_service)

        await project_service.restore_project(project_id)

        args = project_service._project_repo.is_path_taken.await_args.args
        assert args[0] == PATH
        assert args[1] == project_id


class TestRestoreRaceOnPath:
    """The unique index is the real arbiter when the check-then-write race is lost."""

    # spec: SPEC-work-project-restore R4
    async def test_losing_the_path_race_is_a_conflict_not_a_server_error(
        self, project_service
    ):
        """
        A concurrent restore that slips past is_path_taken must still read as a conflict.

        is_path_taken is a read followed by a write, so another restore can take the
        path in between. The partial unique index rejects the loser. That is the caller
        losing a race, not the server breaking, so it must not surface as a 500 telling
        them to retry something that cannot succeed.
        """
        _deleted(project_service)
        project_service._project_repo.restore.side_effect = DatabaseError(
            "Failed to restore project: UNIQUE constraint failed: "
            "idx_projects_path_unique"
        )

        with pytest.raises(ProjectPathConflictError):
            await project_service.restore_project(uuid4())

    # spec: SPEC-work-project-restore R4
    async def test_an_unrelated_database_failure_still_propagates(
        self, project_service
    ):
        """Only the path index maps to a conflict; real faults stay faults."""
        _deleted(project_service)
        project_service._project_repo.restore.side_effect = DatabaseError(
            "disk I/O error"
        )

        with pytest.raises(DatabaseError):
            await project_service.restore_project(uuid4())


class TestRestoreByProjectQuery:
    """The bulk restore matches on the exact stamp and returns sessions stopped."""

    # spec: SPEC-work-project-restore R2
    @pytest.mark.parametrize(
        "repo_module,repo_class",
        [
            (
                "app.infrastructure.database.repositories.session_repository",
                "SessionRepositoryImpl",
            ),
            (
                "app.infrastructure.database.repositories.task_repository",
                "TaskRepositoryImpl",
            ),
        ],
    )
    async def test_restore_matches_only_the_exact_timestamp(
        self, repo_module, repo_class
    ):
        """
        A child deleted at any other moment stays deleted.

        Equality on deleted_at — not `IS NOT NULL` — is the whole mechanism. An earlier
        stamp simply does not match, so separately-discarded work is never resurrected.
        """
        import importlib

        module = importlib.import_module(repo_module)
        repo = getattr(module, repo_class)(AsyncMock())

        db = repo._session
        result = AsyncMock()
        result.rowcount = 1
        db.execute.return_value = result

        await repo.restore_by_project(uuid4(), STAMP)

        compiled = str(db.execute.await_args.args[0])
        assert "deleted_at = " in compiled, compiled
        assert "IS NOT NULL" not in compiled.upper(), (
            "restore must match the exact deletion stamp, not any deleted row: "
            f"{compiled}"
        )

    # spec: SPEC-work-project-restore R5
    async def test_restored_sessions_come_back_stopped(self):
        """A session that was running when deleted is not restored as running."""
        from app.infrastructure.database.repositories.session_repository import (
            SessionRepositoryImpl,
        )

        repo = SessionRepositoryImpl(AsyncMock())
        db = repo._session
        result = AsyncMock()
        result.rowcount = 1
        db.execute.return_value = result

        await repo.restore_by_project(uuid4(), STAMP)

        compiled = str(db.execute.await_args.args[0]).lower()
        assert "status" in compiled, (
            "restore must reset a running status; a session cannot come back WORKING "
            f"when nothing is executing it: {compiled}"
        )

    # spec: SPEC-work-project-restore R2
    async def test_a_different_stamp_is_not_matched(self):
        """Sanity: the query is parameterised by the stamp it is given."""
        from app.infrastructure.database.repositories.task_repository import (
            TaskRepositoryImpl,
        )

        repo = TaskRepositoryImpl(AsyncMock())
        db = repo._session
        result = AsyncMock()
        result.rowcount = 0
        db.execute.return_value = result

        other = STAMP - timedelta(days=30)
        count = await repo.restore_by_project(uuid4(), other)

        assert count == 0
