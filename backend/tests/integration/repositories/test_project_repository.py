"""Integration tests for ProjectRepository implementation."""

from uuid import uuid4

import pytest

from app.core.exceptions import EntityNotFound
from app.domain.entities import Project
from app.infrastructure.database.repositories.project_repository import (
    ProjectRepositoryImpl,
)


class TestProjectRepositoryImpl:
    """Integration tests for ProjectRepositoryImpl."""

    async def test_create_project(self, project_repo: ProjectRepositoryImpl):
        """Test creating a project."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="A test project",
            path="/projects/test",
        )

        created = await project_repo.create(project)

        assert created.id == project.id
        assert created.name == "Test Project"
        assert created.description == "A test project"
        assert created.path == "/projects/test"
        assert created.pm_agent_id is None
        assert created.pm_session_id is None
        assert created.created_at is not None
        assert created.updated_at is not None

    async def test_create_project_without_pm(self, project_repo: ProjectRepositoryImpl):
        """Test creating a project without PM assignment."""
        # Create project without PM
        project = Project(
            id=uuid4(),
            name="No PM Project",
            description="No PM",
            path="/projects/no_pm",
        )

        created = await project_repo.create(project)

        assert created.pm_agent_id is None
        assert created.pm_session_id is None
        assert not created.has_pm()

    async def test_get_by_id_found(self, project_repo: ProjectRepositoryImpl):
        """Test getting project by ID when it exists."""
        project = Project(
            id=uuid4(), name="FindMe", description="Test", path="/projects/findme"
        )
        await project_repo.create(project)

        retrieved = await project_repo.get_by_id(project.id)

        assert retrieved is not None
        assert retrieved.id == project.id
        assert retrieved.name == "FindMe"

    async def test_get_by_id_not_found(self, project_repo: ProjectRepositoryImpl):
        """Test getting non-existent project returns None."""
        result = await project_repo.get_by_id(uuid4())

        assert result is None

    async def test_get_by_id_excludes_soft_deleted(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test get_by_id excludes soft-deleted projects."""
        project = Project(
            id=uuid4(), name="Deleted", description="Test", path="/projects/deleted"
        )
        await project_repo.create(project)
        await project_repo.delete(project.id)

        result = await project_repo.get_by_id(project.id)
        assert result is None

    async def test_get_all(self, project_repo: ProjectRepositoryImpl):
        """Test getting all projects."""
        # Create 3 projects
        for i in range(3):
            project = Project(
                id=uuid4(),
                name=f"Project{i}",
                description=f"Desc{i}",
                path=f"/projects/p{i}",
            )
            await project_repo.create(project)

        all_projects = await project_repo.get_all()

        assert len(all_projects) >= 3

    async def test_get_all_excludes_deleted_by_default(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test get_all excludes soft-deleted projects by default."""
        project = Project(
            id=uuid4(), name="ToDelete", description="Test", path="/projects/todelete"
        )
        await project_repo.create(project)
        project_id = project.id

        before = await project_repo.get_all()
        before_count = len(before)

        await project_repo.delete(project_id)

        after = await project_repo.get_all()
        after_count = len(after)

        assert after_count == before_count - 1

    async def test_get_all_includes_deleted_when_requested(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test get_all includes soft-deleted when include_deleted=True."""
        project = Project(
            id=uuid4(),
            name="DeletedInclude",
            description="Test",
            path="/projects/deleted_include",
        )
        await project_repo.create(project)
        project_id = project.id

        await project_repo.delete(project_id)

        all_projects = await project_repo.get_all(include_deleted=True)

        deleted_project = next((p for p in all_projects if p.id == project_id), None)
        assert deleted_project is not None

    # NOTE: test_get_by_pm_character_empty removed - get_by_pm_character method no longer exists (agents are file-based)

    async def test_update_project(self, project_repo: ProjectRepositoryImpl):
        """Test updating project."""
        project = Project(
            id=uuid4(),
            name="Original",
            description="Original desc",
            path="/projects/orig",
        )
        await project_repo.create(project)

        # Update via entity business method
        project.update_metadata(name="Updated", description="Updated desc")

        updated = await project_repo.update(project)

        assert updated.name == "Updated"
        assert updated.description == "Updated desc"

    async def test_update_project_metadata(self, project_repo: ProjectRepositoryImpl):
        """Test updating project metadata only."""
        # Create project
        project = Project(
            id=uuid4(), name="Project", description="Test", path="/projects/proj"
        )
        await project_repo.create(project)

        # Update metadata (not PM-related fields to avoid FK issues)
        project.update_metadata(description="Updated description")

        updated = await project_repo.update(project)

        assert updated.description == "Updated description"
        assert not updated.has_pm()

    async def test_update_nonexistent_raises_not_found(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test updating non-existent project raises EntityNotFound."""
        project = Project(
            id=uuid4(), name="Ghost", description="Test", path="/projects/ghost"
        )

        with pytest.raises(EntityNotFound):
            await project_repo.update(project)

    async def test_delete_project(self, project_repo: ProjectRepositoryImpl):
        """Test soft-deleting project."""
        project = Project(
            id=uuid4(), name="ToDelete", description="Test", path="/projects/todelete"
        )
        await project_repo.create(project)

        await project_repo.delete(project.id)

        result = await project_repo.get_by_id(project.id)
        assert result is None

        # But should exist when including deleted
        all_projects = await project_repo.get_all(include_deleted=True)
        deleted_project = next((p for p in all_projects if p.id == project.id), None)
        assert deleted_project is not None

    async def test_delete_nonexistent_raises_not_found(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test deleting non-existent project raises EntityNotFound."""
        with pytest.raises(EntityNotFound):
            await project_repo.delete(uuid4())

    async def test_exists_returns_true_for_existing(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test exists returns True for existing project."""
        project = Project(
            id=uuid4(), name="Exists", description="Test", path="/projects/exists"
        )
        await project_repo.create(project)

        result = await project_repo.exists(project.id)

        assert result is True

    async def test_exists_returns_false_for_nonexistent(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test exists returns False for non-existent project."""
        result = await project_repo.exists(uuid4())

        assert result is False

    async def test_exists_returns_true_for_soft_deleted(
        self, project_repo: ProjectRepositoryImpl
    ):
        """Test exists returns True even for soft-deleted projects."""
        project = Project(
            id=uuid4(),
            name="ExistsDeleted",
            description="Test",
            path="/projects/exists_deleted",
        )
        await project_repo.create(project)
        await project_repo.delete(project.id)

        result = await project_repo.exists(project.id)

        assert result is True
