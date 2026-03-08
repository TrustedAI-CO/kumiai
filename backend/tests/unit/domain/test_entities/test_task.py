"""Tests for Task domain entity."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationError
from app.domain.entities.task import Task
from app.domain.value_objects.task_status import TaskStatus


class TestTaskCreation:
    """Tests for Task entity creation."""

    def test_create_task_with_required_fields(self):
        task_id = uuid4()
        project_id = uuid4()

        task = Task(
            id=task_id,
            project_id=project_id,
            name="Implement auth flow",
        )

        assert task.id == task_id
        assert task.project_id == project_id
        assert task.name == "Implement auth flow"
        assert task.description is None
        assert task.status == TaskStatus.OPEN
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_create_task_with_all_fields(self):
        task = Task(
            id=uuid4(),
            project_id=uuid4(),
            name="Full task",
            description="A detailed description",
            status=TaskStatus.IN_PROGRESS,
        )

        assert task.description == "A detailed description"
        assert task.status == TaskStatus.IN_PROGRESS


class TestTaskValidation:
    """Tests for Task.validate() method."""

    def test_empty_name_raises_validation_error(self):
        task = Task(id=uuid4(), project_id=uuid4(), name="")

        with pytest.raises(ValidationError) as exc_info:
            task.validate()

        assert "name" in str(exc_info.value).lower()

    def test_whitespace_only_name_raises_validation_error(self):
        task = Task(id=uuid4(), project_id=uuid4(), name="   ")

        with pytest.raises(ValidationError):
            task.validate()

    def test_valid_task_passes_validation(self):
        task = Task(id=uuid4(), project_id=uuid4(), name="Valid task")

        task.validate()  # Should not raise


class TestTaskStatusTransitions:
    """Tests for Task status transition methods."""

    def test_start_from_open(self):
        task = Task(id=uuid4(), project_id=uuid4(), name="Task", status=TaskStatus.OPEN)
        initial_updated_at = task.updated_at

        task.start()

        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at >= initial_updated_at

    def test_complete_from_in_progress(self):
        task = Task(
            id=uuid4(),
            project_id=uuid4(),
            name="Task",
            status=TaskStatus.IN_PROGRESS,
        )

        task.complete()

        assert task.status == TaskStatus.DONE

    def test_archive(self):
        for status in [TaskStatus.OPEN, TaskStatus.DONE]:
            task = Task(id=uuid4(), project_id=uuid4(), name="Task", status=status)
            task.archive()
            assert task.status == TaskStatus.ARCHIVED

    def test_reopen_from_done(self):
        task = Task(id=uuid4(), project_id=uuid4(), name="Task", status=TaskStatus.DONE)

        task.reopen()

        assert task.status == TaskStatus.OPEN

    def test_update_metadata(self):
        task = Task(id=uuid4(), project_id=uuid4(), name="Old name")
        initial_updated_at = task.updated_at

        task.update_metadata(name="New name", description="New desc")

        assert task.name == "New name"
        assert task.description == "New desc"
        assert task.updated_at >= initial_updated_at

    def test_update_metadata_partial(self):
        task = Task(
            id=uuid4(),
            project_id=uuid4(),
            name="Original",
            description="Original desc",
        )

        task.update_metadata(name="Updated")

        assert task.name == "Updated"
        assert task.description == "Original desc"
