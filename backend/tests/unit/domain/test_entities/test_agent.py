"""Tests for Agent entity."""

import pytest

from app.core.exceptions import ValidationError
from app.domain.entities.agent import Agent


class TestAgent:
    """Test Agent entity."""

    def test_create_agent_minimal(self):
        """Test creating agent with minimal required fields."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
        )

        assert agent.id == "test-agent"
        assert agent.name == "Test Agent"
        assert agent.file_path == "/agents/test-agent/"
        assert agent.tags == []
        assert agent.skills == []
        assert agent.allowed_tools == []
        assert agent.allowed_mcps == []
        assert agent.icon_color == "#4A90E2"

    def test_create_agent_full(self):
        """Test creating agent with all fields."""
        agent = Agent(
            id="full-agent",
            name="Full Agent",
            file_path="/agents/full-agent/",
            tags=["testing", "automation"],
            skills=["skill-1", "skill-2"],
            allowed_tools=["Read", "Write", "Bash"],
            allowed_mcps=["filesystem", "git"],
            icon_color="#FF5733",
        )

        assert agent.id == "full-agent"
        assert agent.name == "Full Agent"
        assert agent.tags == ["testing", "automation"]
        assert agent.skills == ["skill-1", "skill-2"]
        assert agent.allowed_tools == ["Read", "Write", "Bash"]
        assert agent.allowed_mcps == ["filesystem", "git"]
        assert agent.icon_color == "#FF5733"

    def test_validate_success(self):
        """Test validation passes for valid agent."""
        agent = Agent(
            id="valid-agent",
            name="Valid Agent",
            file_path="/agents/valid-agent/",
        )
        agent.validate()  # Should not raise

    def test_validate_empty_name(self):
        """Test validation fails for empty name."""
        agent = Agent(
            id="test-agent",
            name="",
            file_path="/agents/test-agent/",
        )

        with pytest.raises(ValidationError, match="Agent name cannot be empty"):
            agent.validate()

    def test_validate_whitespace_name(self):
        """Test validation fails for whitespace-only name."""
        agent = Agent(
            id="test-agent",
            name="   ",
            file_path="/agents/test-agent/",
        )

        with pytest.raises(ValidationError, match="Agent name cannot be empty"):
            agent.validate()

    def test_validate_empty_file_path(self):
        """Test validation fails for empty file_path."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="",
        )

        with pytest.raises(ValidationError, match="Agent file_path cannot be empty"):
            agent.validate()

    def test_validate_invalid_icon_color(self):
        """Test validation fails for invalid hex color."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            icon_color="invalid",
        )

        with pytest.raises(
            ValidationError,
            match="Icon color must be a valid hex color",
        ):
            agent.validate()

    def test_validate_short_hex_color(self):
        """Test validation passes for short hex color (#FFF)."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            icon_color="#FFF",
        )
        agent.validate()  # Should not raise

    def test_update_metadata(self):
        """Test updating agent metadata."""
        agent = Agent(
            id="test-agent",
            name="Original Name",
            file_path="/agents/test-agent/",
            tags=["original"],
            icon_color="#000000",
        )

        agent.update_metadata(
            name="Updated Name",
            tags=["new", "tags"],
            skills=["skill-1"],
            allowed_tools=["Read"],
            icon_color="#FFFFFF",
        )

        assert agent.name == "Updated Name"
        assert agent.tags == ["new", "tags"]
        assert agent.skills == ["skill-1"]
        assert agent.allowed_tools == ["Read"]
        assert agent.icon_color == "#FFFFFF"

    def test_update_metadata_partial(self):
        """Test updating only some metadata fields."""
        agent = Agent(
            id="test-agent",
            name="Original Name",
            file_path="/agents/test-agent/",
            tags=["original"],
        )

        agent.update_metadata(name="Updated Name")

        assert agent.name == "Updated Name"
        assert agent.tags == ["original"]  # Unchanged

    def test_add_tag(self):
        """Test adding a tag."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            tags=["existing"],
        )

        agent.add_tag("new-tag")

        assert "new-tag" in agent.tags
        assert "existing" in agent.tags

    def test_add_tag_duplicate(self):
        """Test adding duplicate tag fails."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            tags=["existing"],
        )

        with pytest.raises(ValidationError, match="Tag 'existing' already exists"):
            agent.add_tag("existing")

    def test_add_tag_empty(self):
        """Test adding empty tag fails."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
        )

        with pytest.raises(ValidationError, match="Tag cannot be empty"):
            agent.add_tag("")

    def test_remove_tag(self):
        """Test removing a tag."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            tags=["tag1", "tag2"],
        )

        agent.remove_tag("tag1")

        assert "tag1" not in agent.tags
        assert "tag2" in agent.tags

    def test_remove_tag_nonexistent(self):
        """Test removing nonexistent tag fails."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            tags=["existing"],
        )

        with pytest.raises(ValidationError, match="Tag 'nonexistent' does not exist"):
            agent.remove_tag("nonexistent")

    def test_add_skill(self):
        """Test adding a skill."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            skills=["skill-1"],
        )

        agent.add_skill("skill-2")

        assert "skill-2" in agent.skills
        assert "skill-1" in agent.skills

    def test_add_skill_duplicate(self):
        """Test adding duplicate skill fails."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            skills=["skill-1"],
        )

        with pytest.raises(ValidationError, match="Skill 'skill-1' already exists"):
            agent.add_skill("skill-1")

    def test_remove_skill(self):
        """Test removing a skill."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            skills=["skill-1", "skill-2"],
        )

        agent.remove_skill("skill-1")

        assert "skill-1" not in agent.skills
        assert "skill-2" in agent.skills

    def test_remove_skill_nonexistent(self):
        """Test removing nonexistent skill fails."""
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="/agents/test-agent/",
            skills=["skill-1"],
        )

        with pytest.raises(ValidationError, match="Skill 'nonexistent' does not exist"):
            agent.remove_skill("nonexistent")
