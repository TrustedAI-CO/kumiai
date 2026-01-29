"""Tests for AgentLoader."""

import pytest
from unittest.mock import AsyncMock
from app.application.loaders.agent_loader import AgentLoader
from app.domain.entities.agent import Agent
from app.core.exceptions import NotFoundError


@pytest.fixture
def mock_agent_repository():
    """Create mock agent repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return Agent(
        id="test-agent",
        name="Test Agent",
        file_path="/agents/test-agent",
        description="Test agent description",
        allowed_tools=["Read", "Write"],
        allowed_mcps=["github"],
        skills=["planning", "review"],
    )


@pytest.fixture
def agent_loader(mock_agent_repository):
    """Create AgentLoader instance."""
    return AgentLoader(agent_repository=mock_agent_repository)


class TestAgentLoader:
    """Tests for AgentLoader."""

    @pytest.mark.asyncio
    async def test_load_agent(self, agent_loader, mock_agent_repository, sample_agent):
        """Test loading agent entity."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)

        agent = await agent_loader.load_agent("test-agent")

        assert agent == sample_agent
        mock_agent_repository.get_by_id.assert_called_once_with("test-agent")

    @pytest.mark.asyncio
    async def test_load_agent_not_found(self, agent_loader, mock_agent_repository):
        """Test loading agent that doesn't exist."""
        mock_agent_repository.get_by_id = AsyncMock(
            side_effect=NotFoundError("Agent not found")
        )

        with pytest.raises(NotFoundError, match="Agent not found"):
            await agent_loader.load_agent("nonexistent-agent")

    @pytest.mark.asyncio
    async def test_load_agent_content(self, agent_loader, mock_agent_repository):
        """Test loading agent content from CLAUDE.md."""
        expected_content = "Agent personality and instructions"
        mock_agent_repository.load_agent_content = AsyncMock(
            return_value=expected_content
        )

        content = await agent_loader.load_agent_content("test-agent")

        assert content == expected_content
        mock_agent_repository.load_agent_content.assert_called_once_with("test-agent")

    @pytest.mark.asyncio
    async def test_load_agent_content_not_found(
        self, agent_loader, mock_agent_repository
    ):
        """Test loading content for agent that doesn't exist."""
        mock_agent_repository.load_agent_content = AsyncMock(
            side_effect=NotFoundError("Content not found")
        )

        with pytest.raises(NotFoundError, match="Content not found"):
            await agent_loader.load_agent_content("nonexistent-agent")

    @pytest.mark.asyncio
    async def test_create_symlink(
        self, agent_loader, mock_agent_repository, sample_agent, tmp_path
    ):
        """Test creating symlink to agent directory."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)

        # Use tmp_path for safe testing
        target_dir = tmp_path / "agents"
        agent_path = tmp_path / "source" / "test-agent"
        agent_path.mkdir(parents=True)

        # Update sample agent to point to tmp test directory
        sample_agent.file_path = str(agent_path)

        # Mock get_agent_directory to return the agent path
        mock_agent_repository.get_agent_directory = AsyncMock(return_value=agent_path)

        symlink_path = await agent_loader.create_symlink("test-agent", target_dir)

        assert symlink_path == target_dir / "test-agent"
        assert symlink_path.is_symlink()
        assert symlink_path.resolve() == agent_path

    @pytest.mark.asyncio
    async def test_create_symlink_custom_name(
        self, agent_loader, mock_agent_repository, sample_agent, tmp_path
    ):
        """Test creating symlink with custom name."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)

        target_dir = tmp_path / "agents"
        agent_path = tmp_path / "source" / "test-agent"
        agent_path.mkdir(parents=True)

        sample_agent.file_path = str(agent_path)

        symlink_path = await agent_loader.create_symlink(
            "test-agent", target_dir, symlink_name="custom-agent"
        )

        assert symlink_path == target_dir / "custom-agent"
        assert symlink_path.is_symlink()

    @pytest.mark.asyncio
    async def test_create_symlink_replaces_existing(
        self, agent_loader, mock_agent_repository, sample_agent, tmp_path
    ):
        """Test creating symlink replaces existing symlink."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)

        target_dir = tmp_path / "agents"
        target_dir.mkdir(parents=True)

        agent_path = tmp_path / "source" / "test-agent"
        agent_path.mkdir(parents=True)

        sample_agent.file_path = str(agent_path)

        # Mock get_agent_directory to return the agent path
        mock_agent_repository.get_agent_directory = AsyncMock(return_value=agent_path)

        # Create initial symlink
        symlink_path = target_dir / "test-agent"
        symlink_path.symlink_to(tmp_path / "other")

        # Create new symlink (should replace old one)
        new_symlink = await agent_loader.create_symlink("test-agent", target_dir)

        assert new_symlink.is_symlink()
        assert new_symlink.resolve() == agent_path

    @pytest.mark.asyncio
    async def test_create_symlink_creates_target_directory(
        self, agent_loader, mock_agent_repository, sample_agent, tmp_path
    ):
        """Test creating symlink creates target directory if it doesn't exist."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)

        target_dir = tmp_path / "agents" / "deep" / "nested"
        agent_path = tmp_path / "source" / "test-agent"
        agent_path.mkdir(parents=True)

        sample_agent.file_path = str(agent_path)

        symlink_path = await agent_loader.create_symlink("test-agent", target_dir)

        assert target_dir.exists()
        assert symlink_path.is_symlink()

    @pytest.mark.asyncio
    async def test_load_agent_for_session(
        self, agent_loader, mock_agent_repository, sample_agent
    ):
        """Test loading agent with content and symlink for session."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)
        mock_agent_repository.load_agent_content = AsyncMock(
            return_value="Agent content"
        )

        # Test without session_dir (no symlink)
        agent, content, symlink_path = await agent_loader.load_agent_for_session(
            "test-agent"
        )

        assert agent == sample_agent
        assert content == "Agent content"
        assert symlink_path is None

    @pytest.mark.asyncio
    async def test_load_agent_for_session_with_symlink(
        self, agent_loader, mock_agent_repository, sample_agent, tmp_path
    ):
        """Test loading agent with symlink creation."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)
        mock_agent_repository.load_agent_content = AsyncMock(
            return_value="Agent content"
        )

        session_dir = tmp_path / "sessions" / "session123"
        agent_path = tmp_path / "source" / "test-agent"
        agent_path.mkdir(parents=True)

        sample_agent.file_path = str(agent_path)

        agent, content, symlink_path = await agent_loader.load_agent_for_session(
            "test-agent", session_dir=session_dir
        )

        assert agent == sample_agent
        assert content == "Agent content"
        assert symlink_path is not None
        assert symlink_path.is_symlink()
        assert symlink_path == session_dir / "agents" / "test-agent"

    @pytest.mark.asyncio
    async def test_load_agent_for_session_logs_metadata(
        self, agent_loader, mock_agent_repository, sample_agent
    ):
        """Test that load_agent_for_session logs agent metadata."""
        mock_agent_repository.get_by_id = AsyncMock(return_value=sample_agent)
        mock_agent_repository.load_agent_content = AsyncMock(
            return_value="Agent content"
        )

        agent, content, symlink_path = await agent_loader.load_agent_for_session(
            "test-agent"
        )

        # Verify agent has expected metadata
        assert len(agent.skills) == 2
        assert len(agent.allowed_tools) == 2
        assert len(agent.allowed_mcps) == 1
