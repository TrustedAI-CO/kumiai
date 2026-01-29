"""Tests for Skill domain entity (file-based)."""

import pytest

from app.core.exceptions import ValidationError
from app.domain.entities.skill import Skill


class TestSkillCreation:
    """Tests for Skill entity creation."""

    def test_create_skill_with_required_fields(self):
        """Test creating a skill with required fields."""
        skill_id = "test-skill"
        name = "Test Skill"
        file_path = "/skills/test-skill"

        skill = Skill(
            id=skill_id,
            name=name,
            file_path=file_path,
        )

        assert skill.id == skill_id
        assert skill.name == name
        assert skill.file_path == file_path
        assert skill.description is None
        assert skill.tags == []
        assert skill.icon == "zap"
        assert skill.icon_color == "#4A90E2"

    def test_create_skill_with_optional_fields(self):
        """Test creating a skill with optional fields."""
        skill = Skill(
            id="python-skill",
            name="Python Skill",
            file_path="/skills/python-skill",
            description="Test description",
            tags=["python", "testing"],
            icon="python",
            icon_color="#3776AB",
        )

        assert skill.description == "Test description"
        assert skill.tags == ["python", "testing"]
        assert skill.icon == "python"
        assert skill.icon_color == "#3776AB"


class TestSkillUpdateMetadata:
    """Tests for updating skill metadata."""

    def test_update_metadata_updates_name(self):
        """Test updating skill name."""
        skill = Skill(
            id="test-skill",
            name="Old Name",
            file_path="/skills/test-skill",
        )

        skill.update_metadata(name="New Name")

        assert skill.name == "New Name"

    def test_update_metadata_updates_description(self):
        """Test updating skill description."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
            description="Old description",
        )

        skill.update_metadata(description="New description")

        assert skill.description == "New description"

    def test_update_metadata_updates_file_path(self):
        """Test updating skill file_path."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/old/path",
        )

        skill.update_metadata(file_path="/new/path")

        assert skill.file_path == "/new/path"

    def test_update_metadata_updates_all_fields(self):
        """Test updating all skill metadata fields."""
        skill = Skill(
            id="test-skill",
            name="Old Name",
            file_path="/old/path",
            description="Old description",
            icon="zap",
            icon_color="#4A90E2",
        )

        skill.update_metadata(
            name="New Name",
            description="New description",
            file_path="/new/path",
            icon="python",
            icon_color="#3776AB",
        )

        assert skill.name == "New Name"
        assert skill.description == "New description"
        assert skill.file_path == "/new/path"
        assert skill.icon == "python"
        assert skill.icon_color == "#3776AB"


class TestSkillAddTag:
    """Tests for adding tags to skills."""

    def test_add_tag_adds_new_tag(self):
        """Test adding a new tag."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
        )

        skill.add_tag("python")

        assert "python" in skill.tags

    def test_add_tag_strips_whitespace(self):
        """Test that adding a tag strips whitespace."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
        )

        skill.add_tag("  python  ")

        assert "python" in skill.tags
        assert "  python  " not in skill.tags

    def test_add_tag_to_existing_tags(self):
        """Test adding a tag when tags already exist."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
            tags=["python"],
        )

        skill.add_tag("testing")

        assert "python" in skill.tags
        assert "testing" in skill.tags
        assert len(skill.tags) == 2

    def test_add_empty_tag_raises_error(self):
        """Test that adding an empty tag raises ValidationError."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
        )

        with pytest.raises(ValidationError, match="Tag cannot be empty"):
            skill.add_tag("")

    def test_add_whitespace_only_tag_raises_error(self):
        """Test that adding a whitespace-only tag raises ValidationError."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
        )

        with pytest.raises(ValidationError, match="Tag cannot be empty"):
            skill.add_tag("   ")

    def test_add_duplicate_tag_raises_error(self):
        """Test that adding a duplicate tag raises ValidationError."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
            tags=["python"],
        )

        with pytest.raises(ValidationError, match="already exists"):
            skill.add_tag("python")


class TestSkillRemoveTag:
    """Tests for removing tags from skills."""

    def test_remove_tag_removes_existing_tag(self):
        """Test removing an existing tag."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
            tags=["python", "testing"],
        )

        skill.remove_tag("python")

        assert "python" not in skill.tags
        assert "testing" in skill.tags

    def test_remove_last_tag(self):
        """Test removing the last tag."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
            tags=["python"],
        )

        skill.remove_tag("python")

        assert skill.tags == []

    def test_remove_nonexistent_tag_raises_error(self):
        """Test that removing a nonexistent tag raises ValidationError."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
            tags=["python"],
        )

        with pytest.raises(ValidationError, match="does not exist"):
            skill.remove_tag("javascript")


class TestSkillValidation:
    """Tests for skill validation."""

    def test_validate_with_valid_skill_passes(self):
        """Test that validation passes for a valid skill."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill",
        )

        # Should not raise any exceptions
        skill.validate()

    def test_validate_empty_name_raises_error(self):
        """Test that validation fails for empty name."""
        skill = Skill(
            id="test-skill",
            name="",
            file_path="/skills/test-skill",
        )

        with pytest.raises(ValidationError, match="name cannot be empty"):
            skill.validate()

    def test_validate_whitespace_only_name_raises_error(self):
        """Test that validation fails for whitespace-only name."""
        skill = Skill(
            id="test-skill",
            name="   ",
            file_path="/skills/test-skill",
        )

        with pytest.raises(ValidationError, match="name cannot be empty"):
            skill.validate()

    def test_validate_empty_file_path_raises_error(self):
        """Test that validation fails for empty file_path."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="",
        )

        with pytest.raises(ValidationError, match="file_path cannot be empty"):
            skill.validate()

    def test_validate_whitespace_only_file_path_raises_error(self):
        """Test that validation fails for whitespace-only file_path."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="   ",
        )

        with pytest.raises(ValidationError, match="file_path cannot be empty"):
            skill.validate()
