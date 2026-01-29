"""Tests for SKILL.md template generation."""

from pathlib import Path

import pytest

from app.domain.entities import Skill
from app.infrastructure.filesystem import FileBasedSkillRepository


class TestSkillTemplate:
    """Test SKILL.md template generation when creating new skills."""

    @pytest.fixture
    def skill_repository(self, tmp_skills_dir: Path) -> FileBasedSkillRepository:
        """Create FileBasedSkillRepository with temp directory."""
        return FileBasedSkillRepository(base_path=tmp_skills_dir)

    @pytest.mark.asyncio
    async def test_create_skill_generates_valid_template(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test creating a skill generates valid SKILL.md with template."""
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill/",
            description="A test skill for validation",
            tags=["python", "testing"],
            icon="zap",
            icon_color="#4A90E2",
        )

        await skill_repository.create(skill)

        # Verify SKILL.md exists
        skill_md = tmp_skills_dir / "test-skill" / "SKILL.md"
        assert skill_md.exists()

        # Read and verify content
        content = skill_md.read_text(encoding="utf-8")

        # Check frontmatter
        assert content.startswith("---\n")
        assert "name: Test Skill" in content
        assert "description: A test skill for validation" in content
        # Accept both YAML list formats: flow [python, testing] or block - python\n- testing
        assert (
            "tags: [python, testing]" in content
            or "tags:\n- python\n- testing" in content
        )
        assert "icon: zap" in content
        assert "iconColor: '#4A90E2'" in content

        # Check template sections exist
        assert "# Test Skill" in content
        assert "## Overview" in content
        assert "## Usage" in content
        assert "### Examples" in content
        assert "## Prerequisites" in content
        assert "## Best Practices" in content
        assert "## Notes" in content

    @pytest.mark.asyncio
    async def test_template_has_proper_structure(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test template has proper markdown structure."""
        skill = Skill(
            id="structured-skill",
            name="Structured Skill",
            file_path="/skills/structured-skill/",
            description="Testing structure",
            tags=[],
            icon="terminal",
            icon_color="#00FF00",
        )

        await skill_repository.create(skill)

        skill_md = tmp_skills_dir / "structured-skill" / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        # Split into frontmatter and body
        parts = content.split("---\n")
        assert len(parts) >= 3  # Empty before first ---, frontmatter, content

        # Verify body has proper structure (after frontmatter)
        body = parts[2]

        # Check headers are properly formatted (# followed by space)
        assert "\n# Structured Skill\n" in content
        assert "\n## Overview\n" in content
        assert "\n## Usage\n" in content

        # Check example code block markers
        assert "```" in content

        # Check bullet points exist
        assert "- " in content

    @pytest.mark.asyncio
    async def test_template_includes_description_in_body(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test that description from metadata appears in template body."""
        description = "This is a very specific description for testing"
        skill = Skill(
            id="desc-skill",
            name="Description Skill",
            file_path="/skills/desc-skill/",
            description=description,
            tags=[],
            icon="file",
            icon_color="#FF0000",
        )

        await skill_repository.create(skill)

        skill_md = tmp_skills_dir / "desc-skill" / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        # Description should appear both in frontmatter and body
        assert f"description: {description}" in content
        assert description in content.split("---\n")[2]  # In body after frontmatter

    @pytest.mark.asyncio
    async def test_template_validates_with_validation_method(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test that generated template passes YAML frontmatter validation."""
        from app.application.services.skill_service import SkillService

        skill = Skill(
            id="valid-template",
            name="Valid Template Skill",
            file_path="/skills/valid-template/",
            description="Testing validation",
            tags=["test"],
            icon="check",
            icon_color="#00AA00",
        )

        await skill_repository.create(skill)

        skill_md = tmp_skills_dir / "valid-template" / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        # Create a minimal SkillService instance just for validation
        skill_service = SkillService(
            skill_repo=skill_repository,
            file_service=None,  # Not needed for validation
        )

        # Should not raise any validation errors
        skill_service._validate_skill_md_frontmatter(content)

    @pytest.mark.asyncio
    async def test_minimal_skill_without_description(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test template generation works with minimal skill data."""
        skill = Skill(
            id="minimal-skill",
            name="Minimal Skill",
            file_path="/skills/minimal-skill/",
            description=None,  # No description
            tags=[],  # Empty tags
            icon="zap",
            icon_color="#4A90E2",
        )

        await skill_repository.create(skill)

        skill_md = tmp_skills_dir / "minimal-skill" / "SKILL.md"
        assert skill_md.exists()

        content = skill_md.read_text(encoding="utf-8")

        # Should still have valid structure
        assert content.startswith("---\n")
        assert "name: Minimal Skill" in content
        assert "# Minimal Skill" in content
        assert "## Overview" in content

        # Description in frontmatter should be empty string
        assert "description: ''" in content or 'description: ""\n' in content
