"""Tests for Project domain entity."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.domain.entities.project import Project


class TestProjectCreation:
    """Tests for Project entity creation."""

    def test_create_project_with_required_fields(self):
        """Test creating a project with required fields."""
        project_id = uuid4()
        name = "Test Project"
        description = "Test description"

        project = Project(
            id=project_id,
            name=name,
            description=description,
            path="/path/to/project",
        )

        assert project.id == project_id
        assert project.name == name
        assert project.description == description
        assert project.path == "/path/to/project"
        assert project.pm_agent_id is None
        assert project.pm_session_id is None
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    def test_create_project_with_pm(self):
        """Test creating a project with PM assigned."""
        project_id = uuid4()
        pm_agent_id = uuid4()
        pm_session_id = uuid4()

        project = Project(
            id=project_id,
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_agent_id=pm_agent_id,
            pm_session_id=pm_session_id,
        )

        assert project.pm_agent_id == pm_agent_id
        assert project.pm_session_id == pm_session_id


class TestProjectAssignPM:
    """Tests for Project.assign_pm() method."""

    def test_assign_pm_sets_both_ids(self):
        """Test that assign_pm sets both agent and session IDs."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
        )
        agent_id = uuid4()
        session_id = uuid4()
        initial_updated_at = project.updated_at

        project.assign_pm(agent_id, session_id)

        assert project.pm_agent_id == agent_id
        assert project.pm_session_id == session_id
        assert project.updated_at > initial_updated_at

    def test_assign_pm_replaces_existing_pm(self):
        """Test that assign_pm replaces existing PM assignment."""
        old_agent_id = "old-pm-agent"
        old_session_id = uuid4()
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_agent_id=old_agent_id,
            pm_session_id=old_session_id,
        )

        new_agent_id = "new-pm-agent"
        new_session_id = uuid4()
        project.assign_pm(new_agent_id, new_session_id)

        assert project.pm_agent_id == new_agent_id
        assert project.pm_session_id == new_session_id


class TestProjectRemovePM:
    """Tests for Project.remove_pm() method."""

    def test_remove_pm_clears_both_ids(self):
        """Test that remove_pm clears both agent and session IDs."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_session_id=uuid4(),
        )
        initial_updated_at = project.updated_at

        project.remove_pm()

        assert project.pm_agent_id is None
        assert project.pm_session_id is None
        assert project.updated_at > initial_updated_at

    def test_remove_pm_when_no_pm_assigned(self):
        """Test remove_pm when no PM is assigned."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
        )

        # Should not raise
        project.remove_pm()
        assert project.pm_agent_id is None
        assert project.pm_session_id is None


class TestProjectHasPM:
    """Tests for Project.has_pm() method."""

    def test_has_pm_returns_true_when_both_assigned(self):
        """Test has_pm returns True when both PM fields are set."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_session_id=uuid4(),
        )

        assert project.has_pm() is True

    def test_has_pm_returns_false_when_neither_assigned(self):
        """Test has_pm returns False when neither PM field is set."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
        )

        assert project.has_pm() is False

    def test_has_pm_returns_false_when_only_agent_assigned(self):
        """Test has_pm returns False when only agent is assigned."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
        )

        assert project.has_pm() is False

    def test_has_pm_returns_false_when_only_session_assigned(self):
        """Test has_pm returns False when only session is assigned without agent."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_agent_id=None,
            pm_session_id=uuid4(),
        )

        assert project.has_pm() is False


class TestProjectUpdateMetadata:
    """Tests for Project.update_metadata() method."""

    def test_update_metadata_updates_name(self):
        """Test update_metadata updates project name."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Old Name",
            description="Test",
            path="/path/to/project",
        )
        initial_updated_at = project.updated_at

        project.update_metadata(name="New Name")

        assert project.name == "New Name"
        assert project.description == "Test"
        assert project.updated_at > initial_updated_at

    def test_update_metadata_updates_description(self):
        """Test update_metadata updates project description."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Old Description",
            path="/path/to/project",
        )

        project.update_metadata(description="New Description")

        assert project.name == "Test Project"
        assert project.description == "New Description"

    def test_update_metadata_updates_both(self):
        """Test update_metadata updates both name and description."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Old Name",
            description="Old Description",
            path="/path/to/project",
        )

        project.update_metadata(name="New Name", description="New Description")

        assert project.name == "New Name"
        assert project.description == "New Description"

    def test_update_metadata_with_none_values_does_nothing(self):
        """Test update_metadata with None values doesn't change anything."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test Description",
            path="/path/to/project",
        )

        project.update_metadata(name=None, description=None)

        assert project.name == "Test Project"
        assert project.description == "Test Description"

    def test_update_metadata_with_no_args_does_nothing(self):
        """Test update_metadata with no arguments doesn't change anything."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test Description",
            path="/path/to/project",
        )
        initial_updated_at = project.updated_at

        project.update_metadata()

        assert project.name == "Test Project"
        assert project.description == "Test Description"
        assert project.updated_at >= initial_updated_at


class TestProjectValidation:
    """Tests for Project.validate() method."""

    def test_validate_with_valid_project_passes(self):
        """Test validate passes with valid project data."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test",
            path="/path/to/project",
        )

        # Should not raise
        project.validate()

    def test_validate_with_pm_assigned_passes(self):
        """Test validate passes with PM assigned."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_session_id=uuid4(),
        )

        # Should not raise
        project.validate()

    def test_validate_empty_name_raises_error(self):
        """Test validate raises error for empty name."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="",
            description="Test",
            path="/path/to/project",
        )

        with pytest.raises(ValidationError) as exc_info:
            project.validate()

        assert "Project name cannot be empty" in str(exc_info.value)

    def test_validate_whitespace_only_name_raises_error(self):
        """Test validate raises error for whitespace-only name."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="   ",
            description="Test",
            path="/path/to/project",
        )

        with pytest.raises(ValidationError) as exc_info:
            project.validate()

        assert "Project name cannot be empty" in str(exc_info.value)

    def test_validate_empty_path_raises_error(self):
        """Test validate raises error for empty path."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="",
        )

        with pytest.raises(ValidationError) as exc_info:
            project.validate()

        assert "Project path cannot be empty" in str(exc_info.value)

    def test_validate_whitespace_only_path_raises_error(self):
        """Test validate raises error for whitespace-only path."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="   ",
        )

        with pytest.raises(ValidationError) as exc_info:
            project.validate()

        assert "Project path cannot be empty" in str(exc_info.value)

    def test_validate_inconsistent_pm_agent_only_raises_error(self):
        """Test validate raises error when only PM agent is set."""
        project = Project(
            id=uuid4(),
            pm_agent_id="test-pm",
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_session_id=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            project.validate()

        assert "pm_agent_id and pm_session_id must both be set" in str(exc_info.value)

    def test_validate_inconsistent_pm_session_only_raises_error(self):
        """Test validate raises error when only PM session is set."""
        project = Project(
            id=uuid4(),
            name="Test Project",
            description="Test",
            path="/path/to/project",
            pm_agent_id=None,
            pm_session_id=uuid4(),
        )

        with pytest.raises(ValidationError) as exc_info:
            project.validate()

        assert "pm_agent_id and pm_session_id must both be set" in str(exc_info.value)
