"""Integration tests for FileBasedSkillRepository."""

from pathlib import Path

import pytest

from app.core.exceptions import NotFoundError, RepositoryError
from app.domain.entities import Skill
from app.infrastructure.filesystem import FileBasedSkillRepository


class TestFileBasedSkillRepository:
    """Test file-based skill repository operations."""

    @pytest.fixture
    def skill_repository(self, tmp_skills_dir: Path) -> FileBasedSkillRepository:
        """Create FileBasedSkillRepository with temp directory.

        Args:
            tmp_skills_dir: Temporary skills directory fixture

        Returns:
            FileBasedSkillRepository instance
        """
        return FileBasedSkillRepository(base_path=tmp_skills_dir)

    @pytest.fixture
    def sample_skill(self) -> Skill:
        """Create sample skill entity.

        Returns:
            Skill entity instance
        """
        return Skill(
            id="test-skill",
            name="Test Skill",
            file_path="/skills/test-skill/",
            description="A test skill",
            tags=["test", "sample"],
            icon="zap",
            icon_color="#4A90E2",
        )

    @pytest.mark.asyncio
    async def test_create_skill_success(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test creating a skill creates SKILL.md with frontmatter."""
        created_skill = await skill_repository.create(sample_skill)

        assert created_skill.id == sample_skill.id
        assert created_skill.name == sample_skill.name
        # NOTE: version field removed - filesystem handles versioning

        # Verify SKILL.md was created
        skill_md = skill_repository.base_path / sample_skill.id / "SKILL.md"
        assert skill_md.exists()

        # Verify frontmatter
        content = skill_md.read_text()
        assert "---" in content
        assert "name: Test Skill" in content
        # NOTE: version field removed - filesystem handles versioning
        assert "tags:" in content
        assert "icon: zap" in content

    @pytest.mark.asyncio
    async def test_create_skill_duplicate_fails(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test creating duplicate skill fails."""
        await skill_repository.create(sample_skill)

        # Try to create again
        with pytest.raises(RepositoryError, match="already exists"):
            await skill_repository.create(sample_skill)

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test retrieving skill by ID."""
        await skill_repository.create(sample_skill)

        retrieved = await skill_repository.get_by_id(sample_skill.id)

        assert retrieved.id == sample_skill.id
        assert retrieved.name == sample_skill.name
        assert "test" in retrieved.tags

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self, skill_repository: FileBasedSkillRepository
    ):
        """Test retrieving non-existent skill raises NotFoundError."""
        with pytest.raises(NotFoundError, match="Skill.*not found"):
            await skill_repository.get_by_id("nonexistent-skill")

    @pytest.mark.asyncio
    async def test_get_all_skills(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test listing all skills."""
        # Create multiple skills
        await skill_repository.create(sample_skill)

        skill2 = Skill(
            id="test-skill-2",
            name="Test Skill 2",
            file_path="/skills/test-skill-2/",
            description="Another test skill",
            tags=["test"],
        )
        await skill_repository.create(skill2)

        # Get all skills
        skills = await skill_repository.get_all()

        assert len(skills) == 2
        skill_ids = [s.id for s in skills]
        assert "test-skill" in skill_ids
        assert "test-skill-2" in skill_ids

    @pytest.mark.asyncio
    async def test_get_all_excludes_deleted(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test get_all excludes soft-deleted skills."""
        await skill_repository.create(sample_skill)

        # Soft delete
        await skill_repository.delete(sample_skill.id)

        # Should not appear in get_all
        skills = await skill_repository.get_all()
        assert len(skills) == 0

    @pytest.mark.asyncio
    async def test_update_skill_success(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test updating skill metadata."""
        await skill_repository.create(sample_skill)

        # Update skill
        sample_skill.update_metadata(
            name="Updated Test Skill", description="Updated description"
        )
        updated = await skill_repository.update(sample_skill)

        assert updated.name == "Updated Test Skill"
        assert updated.description == "Updated description"

        # Verify SKILL.md was updated
        skill_md = skill_repository.base_path / sample_skill.id / "SKILL.md"
        content = skill_md.read_text()
        assert "name: Updated Test Skill" in content
        # NOTE: version field removed - filesystem handles versioning

    @pytest.mark.asyncio
    async def test_update_skill_not_found(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test updating non-existent skill fails."""
        with pytest.raises(NotFoundError):
            await skill_repository.update(sample_skill)

    @pytest.mark.asyncio
    async def test_delete_skill_soft_delete(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test soft delete renames directory with .deleted suffix."""
        await skill_repository.create(sample_skill)

        await skill_repository.delete(sample_skill.id)

        # Original directory should not exist
        skill_dir = skill_repository.base_path / sample_skill.id
        assert not skill_dir.exists()

        # Deleted directory should exist
        deleted_dir = skill_repository.base_path / f"{sample_skill.id}.deleted"
        assert deleted_dir.exists()
        assert (deleted_dir / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_delete_skill_not_found(
        self, skill_repository: FileBasedSkillRepository
    ):
        """Test deleting non-existent skill raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await skill_repository.delete("nonexistent-skill")

    @pytest.mark.asyncio
    async def test_exists_true(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test exists returns True for existing skill."""
        await skill_repository.create(sample_skill)

        assert await skill_repository.exists(sample_skill.id) is True

    @pytest.mark.asyncio
    async def test_exists_false(self, skill_repository: FileBasedSkillRepository):
        """Test exists returns False for non-existent skill."""
        assert await skill_repository.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_exists_false_for_deleted(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test exists returns False for soft-deleted skill."""
        await skill_repository.create(sample_skill)
        await skill_repository.delete(sample_skill.id)

        assert await skill_repository.exists(sample_skill.id) is False

    @pytest.mark.asyncio
    async def test_get_by_name_success(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test retrieving skill by name."""
        await skill_repository.create(sample_skill)

        found = await skill_repository.get_by_name("Test Skill")

        assert found is not None
        assert found.id == sample_skill.id
        assert found.name == "Test Skill"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(
        self, skill_repository: FileBasedSkillRepository
    ):
        """Test get_by_name returns None for non-existent name."""
        found = await skill_repository.get_by_name("Nonexistent Skill")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_tags_single_tag(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test searching skills by single tag."""
        await skill_repository.create(sample_skill)

        # Create another skill with different tags
        skill2 = Skill(
            id="skill-2",
            name="Skill 2",
            file_path="/skills/skill-2/",
            description="Another skill",
            tags=["other", "sample"],
        )
        await skill_repository.create(skill2)

        # Search by "test" tag
        results = await skill_repository.get_by_tags(["test"], match_all=False)

        assert len(results) == 1
        assert results[0].id == sample_skill.id

    @pytest.mark.asyncio
    async def test_get_by_tags_or_matching(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test searching skills with OR logic (match_all=False)."""
        await skill_repository.create(sample_skill)

        skill2 = Skill(
            id="skill-2",
            name="Skill 2",
            file_path="/skills/skill-2/",
            description="Another skill",
            tags=["other", "sample"],
        )
        await skill_repository.create(skill2)

        # Search for "test" OR "other" (should match both)
        results = await skill_repository.get_by_tags(["test", "other"], match_all=False)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_tags_and_matching(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test searching skills with AND logic (match_all=True)."""
        await skill_repository.create(sample_skill)

        skill2 = Skill(
            id="skill-2",
            name="Skill 2",
            file_path="/skills/skill-2/",
            description="Another skill",
            tags=["other", "sample"],
        )
        await skill_repository.create(skill2)

        # Search for "test" AND "sample" (should match only sample_skill)
        results = await skill_repository.get_by_tags(["test", "sample"], match_all=True)

        assert len(results) == 1
        assert results[0].id == sample_skill.id

    @pytest.mark.asyncio
    async def test_get_by_tags_no_matches(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test searching with tags that match no skills."""
        await skill_repository.create(sample_skill)

        results = await skill_repository.get_by_tags(["nonexistent"], match_all=False)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_load_skill_content_success(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test loading SKILL.md content for AI context."""
        await skill_repository.create(sample_skill)

        # Add body content to SKILL.md
        skill_md = skill_repository.base_path / sample_skill.id / "SKILL.md"
        content = skill_md.read_text()
        content += "\n# Test Skill\n\nThis is the skill documentation."
        skill_md.write_text(content)

        # Load content
        loaded_content = await skill_repository.load_skill_content(sample_skill.id)

        assert "---" in loaded_content  # Has frontmatter
        assert "name: Test Skill" in loaded_content
        assert "# Test Skill" in loaded_content
        assert "skill documentation" in loaded_content

    @pytest.mark.asyncio
    async def test_load_skill_content_not_found(
        self, skill_repository: FileBasedSkillRepository
    ):
        """Test loading content for non-existent skill."""
        with pytest.raises(NotFoundError):
            await skill_repository.load_skill_content("nonexistent")

    @pytest.mark.asyncio
    async def test_load_supporting_doc_success(
        self,
        skill_repository: FileBasedSkillRepository,
        sample_skill: Skill,
        tmp_skills_dir: Path,
    ):
        """Test loading supporting documentation."""
        await skill_repository.create(sample_skill)

        # Create supporting doc
        skill_dir = tmp_skills_dir / sample_skill.id
        doc_file = skill_dir / "REFERENCE.md"
        doc_file.write_text("# Reference\n\nReference documentation.")

        # Load doc
        content = await skill_repository.load_supporting_doc(
            sample_skill.id, "REFERENCE.md"
        )

        assert "# Reference" in content
        assert "Reference documentation" in content

    @pytest.mark.asyncio
    async def test_load_supporting_doc_nested(
        self,
        skill_repository: FileBasedSkillRepository,
        sample_skill: Skill,
        tmp_skills_dir: Path,
    ):
        """Test loading nested supporting documentation."""
        await skill_repository.create(sample_skill)

        # Create nested doc structure
        skill_dir = tmp_skills_dir / sample_skill.id
        nested_dir = skill_dir / "docs" / "api"
        nested_dir.mkdir(parents=True, exist_ok=True)
        doc_file = nested_dir / "endpoints.md"
        doc_file.write_text("# API Endpoints\n\nEndpoint docs.")

        # Load nested doc
        content = await skill_repository.load_supporting_doc(
            sample_skill.id, "docs/api/endpoints.md"
        )

        assert "# API Endpoints" in content

    @pytest.mark.asyncio
    async def test_load_supporting_doc_not_found(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test loading non-existent supporting doc."""
        await skill_repository.create(sample_skill)

        with pytest.raises(NotFoundError, match="not found"):
            await skill_repository.load_supporting_doc(
                sample_skill.id, "NONEXISTENT.md"
            )

    @pytest.mark.asyncio
    async def test_load_supporting_doc_path_traversal_blocked(
        self, skill_repository: FileBasedSkillRepository, sample_skill: Skill
    ):
        """Test path traversal attempts are blocked."""
        await skill_repository.create(sample_skill)

        with pytest.raises(RepositoryError, match="Invalid path"):
            await skill_repository.load_supporting_doc(
                sample_skill.id, "../../../etc/passwd"
            )

    @pytest.mark.asyncio
    async def test_parse_skill_md_valid_frontmatter(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test parsing SKILL.md with valid YAML frontmatter."""
        # Create skill directory with SKILL.md
        skill_dir = tmp_skills_dir / "parse-test"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: Parse Test
description: Testing parsing
tags: [parse, test]
icon: test
iconColor: "#FF0000"
---

# Parse Test Skill

Body content here.
"""
        )

        # Parse the skill - pass the SKILL.md path, not the directory
        metadata = skill_repository._parse_skill_md(skill_md)

        assert metadata["name"] == "Parse Test"
        assert metadata["description"] == "Testing parsing"
        assert metadata["tags"] == ["parse", "test"]
        assert metadata["icon"] == "test"
        assert metadata["iconColor"] == "#FF0000"
        # NOTE: version field removed - filesystem handles versioning

    @pytest.mark.asyncio
    async def test_parse_skill_md_missing_required_fields(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test parsing SKILL.md with missing required fields."""
        skill_dir = tmp_skills_dir / "invalid-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
tags: [test]
---

# Invalid Skill
"""
        )

        # Should raise error for missing name
        with pytest.raises(RepositoryError, match="Missing required field"):
            skill_repository._parse_skill_md(skill_md)

    @pytest.mark.asyncio
    async def test_parse_skill_md_no_frontmatter(
        self, skill_repository: FileBasedSkillRepository, tmp_skills_dir: Path
    ):
        """Test parsing SKILL.md without frontmatter uses defaults."""
        skill_dir = tmp_skills_dir / "no-frontmatter"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# Skill Without Frontmatter\n\nJust content.")

        # Should create metadata with defaults
        metadata = skill_repository._parse_skill_md(skill_md)

        assert metadata["name"] == "No Frontmatter"  # Uses directory name, title-cased
        assert metadata["description"] == ""
        assert metadata["tags"] == []
