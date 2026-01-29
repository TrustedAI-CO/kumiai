"""Tests for SkillLoader."""

import pytest
from unittest.mock import AsyncMock
from app.application.loaders.skill_loader import SkillLoader
from app.domain.entities.skill import Skill
from app.core.exceptions import NotFoundError


@pytest.fixture
def mock_skill_repository():
    """Create mock skill repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def sample_skill():
    """Create a sample skill for testing."""
    return Skill(
        id="test-skill",
        name="Test Skill",
        file_path="/skills/test-skill",
        description="Test skill description",
    )


@pytest.fixture
def skill_loader(mock_skill_repository):
    """Create SkillLoader instance."""
    return SkillLoader(skill_repository=mock_skill_repository)


class TestSkillLoader:
    """Tests for SkillLoader."""

    @pytest.mark.asyncio
    async def test_load_skill(self, skill_loader, mock_skill_repository, sample_skill):
        """Test loading skill entity."""
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)

        skill = await skill_loader.load_skill("test-skill")

        assert skill == sample_skill
        mock_skill_repository.get_by_id.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_load_skill_not_found(self, skill_loader, mock_skill_repository):
        """Test loading skill that doesn't exist."""
        mock_skill_repository.get_by_id = AsyncMock(
            side_effect=NotFoundError("Skill not found")
        )

        with pytest.raises(NotFoundError, match="Skill not found"):
            await skill_loader.load_skill("nonexistent-skill")

    @pytest.mark.asyncio
    async def test_load_skill_content(self, skill_loader, mock_skill_repository):
        """Test loading skill content from SKILL.md."""
        expected_content = "Skill documentation and usage instructions"
        mock_skill_repository.load_skill_content = AsyncMock(
            return_value=expected_content
        )

        content = await skill_loader.load_skill_content("test-skill")

        assert content == expected_content
        mock_skill_repository.load_skill_content.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_load_skill_content_not_found(
        self, skill_loader, mock_skill_repository
    ):
        """Test loading content for skill that doesn't exist."""
        mock_skill_repository.load_skill_content = AsyncMock(
            side_effect=NotFoundError("Content not found")
        )

        with pytest.raises(NotFoundError, match="Content not found"):
            await skill_loader.load_skill_content("nonexistent-skill")

    @pytest.mark.asyncio
    async def test_load_skill_description(
        self, skill_loader, mock_skill_repository, sample_skill
    ):
        """Test loading formatted skill description for system prompt."""
        skill_content = "This is the full skill documentation that is quite long..."
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)
        mock_skill_repository.load_skill_content = AsyncMock(return_value=skill_content)

        description = await skill_loader.load_skill_description("test-skill")

        # Should contain skill name
        assert "Test Skill" in description
        # Should contain skill description
        assert "Test skill description" in description
        # Should contain documentation reference
        assert "skills/test-skill/SKILL.md" in description
        # Should contain content preview
        assert skill_content in description

    @pytest.mark.asyncio
    async def test_load_skill_description_truncates_long_content(
        self, skill_loader, mock_skill_repository, sample_skill
    ):
        """Test that skill description truncates content over 500 chars."""
        long_content = "a" * 600  # 600 characters
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)
        mock_skill_repository.load_skill_content = AsyncMock(return_value=long_content)

        description = await skill_loader.load_skill_description("test-skill")

        # Should truncate and add ellipsis
        assert "..." in description
        # Should not contain full content
        assert long_content not in description

    @pytest.mark.asyncio
    async def test_load_skill_description_no_description(
        self, skill_loader, mock_skill_repository
    ):
        """Test skill description when skill has no description field."""
        skill_no_desc = Skill(
            id="no-desc-skill",
            name="No Desc Skill",
            file_path="/skills/no-desc-skill",
            description=None,  # No description
        )
        mock_skill_repository.get_by_id = AsyncMock(return_value=skill_no_desc)
        mock_skill_repository.load_skill_content = AsyncMock(return_value="Content")

        description = await skill_loader.load_skill_description("no-desc-skill")

        # Should use default message
        assert "No description provided" in description

    @pytest.mark.asyncio
    async def test_create_symlink(
        self, skill_loader, mock_skill_repository, sample_skill, tmp_path
    ):
        """Test creating symlink to skill directory."""
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)

        # Use tmp_path for safe testing
        target_dir = tmp_path / "skills"
        skill_path = tmp_path / "source" / "test-skill"
        skill_path.mkdir(parents=True)

        # Update sample skill to point to tmp test directory
        sample_skill.file_path = str(skill_path)

        # Mock get_skill_directory to return the skill path
        mock_skill_repository.get_skill_directory = AsyncMock(return_value=skill_path)

        symlink_path = await skill_loader.create_symlink("test-skill", target_dir)

        assert symlink_path == target_dir / "test-skill"
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == skill_path

    @pytest.mark.asyncio
    async def test_create_symlink_custom_name(
        self, skill_loader, mock_skill_repository, sample_skill, tmp_path
    ):
        """Test creating symlink with custom name."""
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)

        target_dir = tmp_path / "skills"
        skill_path = tmp_path / "source" / "test-skill"
        skill_path.mkdir(parents=True)

        sample_skill.file_path = str(skill_path)

        # Mock get_skill_directory to return the skill path
        mock_skill_repository.get_skill_directory = AsyncMock(return_value=skill_path)

        symlink_path = await skill_loader.create_symlink(
            "test-skill", target_dir, symlink_name="custom-skill"
        )

        assert symlink_path == target_dir / "custom-skill"
        assert symlink_path.is_symlink()

    @pytest.mark.asyncio
    async def test_create_symlink_replaces_existing(
        self, skill_loader, mock_skill_repository, sample_skill, tmp_path
    ):
        """Test creating symlink replaces existing symlink."""
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)

        target_dir = tmp_path / "skills"
        target_dir.mkdir(parents=True)

        skill_path = tmp_path / "source" / "test-skill"
        skill_path.mkdir(parents=True)

        sample_skill.file_path = str(skill_path)

        # Mock get_skill_directory to return the skill path
        mock_skill_repository.get_skill_directory = AsyncMock(return_value=skill_path)

        # Create initial symlink
        symlink_path = target_dir / "test-skill"
        symlink_path.symlink_to(tmp_path / "other")

        # Create new symlink (should replace old one)
        new_symlink = await skill_loader.create_symlink("test-skill", target_dir)

        assert new_symlink.is_symlink()
        assert new_symlink.resolve() == skill_path

    @pytest.mark.asyncio
    async def test_create_symlink_creates_target_directory(
        self, skill_loader, mock_skill_repository, sample_skill, tmp_path
    ):
        """Test creating symlink creates target directory if it doesn't exist."""
        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)

        target_dir = tmp_path / "skills" / "deep" / "nested"
        skill_path = tmp_path / "source" / "test-skill"
        skill_path.mkdir(parents=True)

        sample_skill.file_path = str(skill_path)

        # Mock get_skill_directory to return the skill path
        mock_skill_repository.get_skill_directory = AsyncMock(return_value=skill_path)

        symlink_path = await skill_loader.create_symlink("test-skill", target_dir)

        assert target_dir.exists()
        assert symlink_path.is_symlink()

    @pytest.mark.asyncio
    async def test_load_skills_for_session(
        self, skill_loader, mock_skill_repository, sample_skill
    ):
        """Test loading multiple skills for session."""
        skill1 = sample_skill
        skill2 = Skill(
            id="another-skill",
            name="Another Skill",
            file_path="/skills/another-skill",
            description="Another description",
        )

        mock_skill_repository.get_by_id = AsyncMock(side_effect=[skill1, skill2])
        mock_skill_repository.load_skill_content = AsyncMock(
            return_value="Skill content"
        )

        descriptions = await skill_loader.load_skills_for_session(
            ["test-skill", "another-skill"]
        )

        assert len(descriptions) == 2
        assert "Test Skill" in descriptions[0]
        assert "Another Skill" in descriptions[1]

    @pytest.mark.asyncio
    async def test_load_skills_for_session_with_symlinks(
        self, skill_loader, mock_skill_repository, sample_skill, tmp_path
    ):
        """Test loading skills with symlink creation."""
        session_dir = tmp_path / "sessions" / "session123"
        skill_path = tmp_path / "source" / "test-skill"
        skill_path.mkdir(parents=True)

        sample_skill.file_path = str(skill_path)

        mock_skill_repository.get_by_id = AsyncMock(return_value=sample_skill)
        mock_skill_repository.get_skill_directory = AsyncMock(return_value=skill_path)
        mock_skill_repository.load_skill_content = AsyncMock(
            return_value="Skill content"
        )

        descriptions = await skill_loader.load_skills_for_session(
            ["test-skill"], session_dir=session_dir
        )

        assert len(descriptions) == 1
        # Verify symlink was created
        symlink_path = session_dir / "skills" / "test-skill"
        assert symlink_path.is_symlink()

    @pytest.mark.asyncio
    async def test_load_skills_for_session_handles_errors_gracefully(
        self, skill_loader, mock_skill_repository
    ):
        """Test that load_skills_for_session continues on error."""
        # First skill succeeds, second fails, third succeeds
        skill1 = Skill(
            id="skill1",
            name="Skill 1",
            file_path="/skills/skill1",
            description="Desc 1",
        )
        skill3 = Skill(
            id="skill3",
            name="Skill 3",
            file_path="/skills/skill3",
            description="Desc 3",
        )

        mock_skill_repository.get_by_id = AsyncMock(
            side_effect=[
                skill1,
                NotFoundError("Skill not found"),
                skill3,
            ]
        )
        mock_skill_repository.load_skill_content = AsyncMock(return_value="Content")

        descriptions = await skill_loader.load_skills_for_session(
            ["skill1", "skill2", "skill3"]
        )

        # Should have loaded 2 out of 3 skills
        assert len(descriptions) == 2
        assert "Skill 1" in descriptions[0]
        assert "Skill 3" in descriptions[1]

    @pytest.mark.asyncio
    async def test_load_skills_for_session_empty_list(self, skill_loader):
        """Test loading skills with empty list."""
        descriptions = await skill_loader.load_skills_for_session([])

        assert descriptions == []
