"""Unit tests for SkillService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos import SkillDTO
from app.application.services import SkillService
from app.application.services.exceptions import SkillNotFoundError
from app.core.exceptions import NotFoundError, RepositoryError
from app.domain.entities import Skill
from app.domain.repositories import SkillRepository


class TestSkillService:
    """Test SkillService business logic."""

    @pytest.fixture
    def mock_skill_repo(self) -> SkillRepository:
        """Create mock skill repository.

        Returns:
            Mock SkillRepository instance
        """
        repo = MagicMock(spec=SkillRepository)
        # Make all methods async
        repo.create = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_all = AsyncMock()
        repo.get_by_tags = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock()
        repo.exists = AsyncMock()
        repo.get_by_name = AsyncMock()
        repo.load_skill_content = AsyncMock()
        repo.load_supporting_doc = AsyncMock()
        return repo

    @pytest.fixture
    def skill_service(self, mock_skill_repo: SkillRepository) -> SkillService:
        """Create SkillService with mocked repository.

        Args:
            mock_skill_repo: Mock skill repository

        Returns:
            SkillService instance
        """
        return SkillService(skill_repo=mock_skill_repo)

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
            tags=["test"],
            icon="zap",
            icon_color="#4A90E2",
        )

    @pytest.mark.asyncio
    async def test_create_skill_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test creating a skill successfully."""
        mock_skill_repo.create.return_value = sample_skill
        mock_skill_repo.get_by_id.return_value = sample_skill

        result = await skill_service.create_skill(
            name="Test Skill",
            file_path="/skills/test-skill/",
            description="A test skill",
            tags=["test"],
            icon="zap",
            icon_color="#4A90E2",
        )

        assert isinstance(result, SkillDTO)
        assert result.name == "Test Skill"
        assert result.id == "test-skill"
        mock_skill_repo.create.assert_called_once()
        mock_skill_repo.get_by_id.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_create_skill_generates_id_from_path(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test creating skill extracts ID from file_path."""
        # Create a skill with matching ID for get_by_id
        skill_with_correct_id = Skill(
            id="my-new-skill",
            name="My New Skill",
            file_path="/skills/my-new-skill/",
            description="Test",
            tags=[],
            icon="zap",
            icon_color="#4A90E2",
        )
        mock_skill_repo.create.return_value = skill_with_correct_id
        mock_skill_repo.get_by_id.return_value = skill_with_correct_id

        result = await skill_service.create_skill(
            name="My New Skill",
            file_path="/skills/my-new-skill/",
            description="Test",
        )

        # Verify create was called with skill entity
        call_args = mock_skill_repo.create.call_args[0][0]
        assert call_args.id == "my-new-skill"
        assert call_args.file_path == "/skills/my-new-skill/"

        # Verify result
        assert result.id == "my-new-skill"

    @pytest.mark.asyncio
    async def test_create_skill_repository_error(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test create_skill propagates repository errors."""
        mock_skill_repo.create.side_effect = RepositoryError("Skill already exists", {})

        with pytest.raises(RepositoryError, match="Skill already exists"):
            await skill_service.create_skill(name="Test", file_path="/skills/test/")

    @pytest.mark.asyncio
    async def test_get_skill_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test retrieving a skill by ID."""
        mock_skill_repo.get_by_id.return_value = sample_skill

        result = await skill_service.get_skill("test-skill")

        assert isinstance(result, SkillDTO)
        assert result.id == "test-skill"
        assert result.name == "Test Skill"
        mock_skill_repo.get_by_id.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_get_skill_not_found(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test get_skill when repository returns None."""
        mock_skill_repo.get_by_id.return_value = None

        with pytest.raises(SkillNotFoundError, match="Skill test-skill not found"):
            await skill_service.get_skill("test-skill")

    @pytest.mark.asyncio
    async def test_get_skill_propagates_not_found_error(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test get_skill propagates NotFoundError from repository."""
        mock_skill_repo.get_by_id.side_effect = NotFoundError("Not found", {})

        with pytest.raises(NotFoundError):
            await skill_service.get_skill("nonexistent")

    @pytest.mark.asyncio
    async def test_list_skills_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test listing all skills."""
        mock_skill_repo.get_all.return_value = [sample_skill]

        result = await skill_service.list_skills()

        assert len(result) == 1
        assert isinstance(result[0], SkillDTO)
        assert result[0].id == "test-skill"
        mock_skill_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_skills_empty(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test listing skills when none exist."""
        mock_skill_repo.get_all.return_value = []

        result = await skill_service.list_skills()

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_by_tags_or_matching(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test searching skills with OR logic."""
        mock_skill_repo.get_by_tags.return_value = [sample_skill]

        result = await skill_service.search_by_tags(
            tags=["test", "other"], match_all=False
        )

        assert len(result) == 1
        assert result[0].id == "test-skill"
        mock_skill_repo.get_by_tags.assert_called_once_with(
            ["test", "other"], match_all=False
        )

    @pytest.mark.asyncio
    async def test_search_by_tags_and_matching(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test searching skills with AND logic."""
        mock_skill_repo.get_by_tags.return_value = [sample_skill]

        result = await skill_service.search_by_tags(
            tags=["test", "sample"], match_all=True
        )

        assert len(result) == 1
        mock_skill_repo.get_by_tags.assert_called_once_with(
            ["test", "sample"], match_all=True
        )

    @pytest.mark.asyncio
    async def test_update_skill_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test updating a skill."""
        mock_skill_repo.get_by_id.return_value = sample_skill
        updated_skill = Skill(
            id=sample_skill.id,
            name="Updated Name",
            file_path=sample_skill.file_path,
            description="Updated",
            tags=sample_skill.tags,
        )
        mock_skill_repo.update.return_value = updated_skill

        result = await skill_service.update_skill(
            skill_id="test-skill", name="Updated Name"
        )

        assert result.name == "Updated Name"
        mock_skill_repo.get_by_id.assert_called_once_with("test-skill")
        mock_skill_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_skill_propagates_not_found(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test updating non-existent skill propagates NotFoundError."""
        mock_skill_repo.get_by_id.side_effect = NotFoundError("Not found", {})

        with pytest.raises(NotFoundError):
            await skill_service.update_skill(skill_id="nonexistent", name="New Name")

    @pytest.mark.asyncio
    async def test_update_skill_with_tags(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
        sample_skill: Skill,
    ):
        """Test updating skill with new tags."""
        mock_skill_repo.get_by_id.return_value = sample_skill
        updated_skill = Skill(
            id=sample_skill.id,
            name=sample_skill.name,
            file_path=sample_skill.file_path,
            description=sample_skill.description,
            tags=["test", "new", "tags"],
        )
        mock_skill_repo.update.return_value = updated_skill

        result = await skill_service.update_skill(
            skill_id="test-skill", tags=["test", "new", "tags"]
        )

        assert "new" in result.tags
        assert "tags" in result.tags
        assert len(result.tags) == 3

    @pytest.mark.asyncio
    async def test_delete_skill_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test deleting a skill."""
        mock_skill_repo.delete.return_value = None

        await skill_service.delete_skill("test-skill")

        mock_skill_repo.delete.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_delete_skill_propagates_not_found(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test deleting non-existent skill propagates NotFoundError."""
        mock_skill_repo.delete.side_effect = NotFoundError("Not found", {})

        with pytest.raises(NotFoundError):
            await skill_service.delete_skill("nonexistent")

    @pytest.mark.asyncio
    async def test_load_skill_content_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test loading SKILL.md content for AI context."""
        mock_content = "---\nname: Test\n---\n# Test Skill"
        mock_skill_repo.load_skill_content.return_value = mock_content

        result = await skill_service.load_skill_content("test-skill")

        assert result == mock_content
        mock_skill_repo.load_skill_content.assert_called_once_with("test-skill")

    @pytest.mark.asyncio
    async def test_load_skill_content_propagates_not_found(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test loading content for non-existent skill propagates NotFoundError."""
        mock_skill_repo.load_skill_content.side_effect = NotFoundError("Not found", {})

        with pytest.raises(NotFoundError):
            await skill_service.load_skill_content("nonexistent")

    @pytest.mark.asyncio
    async def test_load_supporting_doc_success(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test loading supporting documentation."""
        mock_content = "# Reference Documentation"
        mock_skill_repo.load_supporting_doc.return_value = mock_content

        result = await skill_service.load_supporting_doc("test-skill", "REFERENCE.md")

        assert result == mock_content
        mock_skill_repo.load_supporting_doc.assert_called_once_with(
            "test-skill", "REFERENCE.md"
        )

    @pytest.mark.asyncio
    async def test_load_supporting_doc_propagates_not_found(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test loading non-existent supporting doc propagates NotFoundError."""
        mock_skill_repo.load_supporting_doc.side_effect = NotFoundError(
            "Doc not found", {}
        )

        with pytest.raises(NotFoundError):
            await skill_service.load_supporting_doc("test-skill", "MISSING.md")

    @pytest.mark.asyncio
    async def test_load_supporting_doc_propagates_repository_error(
        self,
        skill_service: SkillService,
        mock_skill_repo: SkillRepository,
    ):
        """Test loading supporting doc with path traversal propagates RepositoryError."""
        mock_skill_repo.load_supporting_doc.side_effect = RepositoryError(
            "Invalid path", {}
        )

        with pytest.raises(RepositoryError, match="Invalid path"):
            await skill_service.load_supporting_doc("test-skill", "../../../etc/passwd")
