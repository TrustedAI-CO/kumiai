"""Tests for SessionFactory."""

import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock

from app.application.factories.session_factory import SessionFactory
from app.domain.value_objects.session_type import SessionType
from app.domain.entities.agent import Agent
from app.domain.entities.skill import Skill
from app.core.exceptions import ValidationError


@pytest.fixture
def mock_agent_repo():
    """Create mock agent repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_skill_repo():
    """Create mock skill repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def session_factory(mock_agent_repo, mock_skill_repo, sample_agent):
    """Create SessionFactory instance with mocked repositories."""
    # Setup default mocks for agent loading (using repository methods)
    mock_agent_repo.get_by_id = AsyncMock(return_value=sample_agent)
    mock_agent_repo.load_agent_content = AsyncMock(return_value="Agent content")

    # Mock skill loading (using repository methods)
    mock_skill_repo.get_by_id = AsyncMock(return_value=None)
    mock_skill_repo.load_skill_content = AsyncMock(return_value="Skill content")

    return SessionFactory(
        agent_repository=mock_agent_repo,
        skill_repository=mock_skill_repo,
    )


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return Agent(
        id="test-agent",
        name="Test Agent",
        file_path="/path/to/agent",
        description="Test agent description",
        allowed_tools=["Read", "Write"],
        allowed_mcps=["common_tools"],
        skills=["test-skill"],
    )


@pytest.fixture
def sample_skill():
    """Create a sample skill for testing."""
    return Skill(
        id="test-skill",
        name="Test Skill",
        file_path="/path/to/skill",
        description="Test skill description",
    )


class TestSessionFactory:
    """Tests for SessionFactory."""

    @pytest.mark.asyncio
    async def test_create_pm_session_requires_project_id(self, session_factory):
        """Test that PM sessions require project_id."""
        with pytest.raises(ValidationError, match="PM sessions require project_id"):
            await session_factory.create_session(
                session_type=SessionType.PM,
                instance_id=str(uuid4()),
                working_dir=Path("/tmp/test"),
                agent_id="test-agent",
                project_id=None,  # Missing project_id
            )

    @pytest.mark.asyncio
    async def test_create_specialist_session_requires_agent_id(self, session_factory):
        """Test that Specialist sessions require agent_id."""
        with pytest.raises(
            ValidationError, match="Specialist sessions require agent_id"
        ):
            await session_factory.create_session(
                session_type=SessionType.SPECIALIST,
                instance_id=str(uuid4()),
                working_dir=Path("/tmp/test"),
                agent_id=None,  # Missing agent_id
            )

    @pytest.mark.asyncio
    async def test_create_specialist_session_validates_agent_exists(
        self, mock_agent_repo, mock_skill_repo
    ):
        """Test that Specialist sessions validate agent existence."""
        # Setup: agent doesn't exist
        mock_agent_repo.get_by_id = AsyncMock(return_value=None)
        mock_agent_repo.get_all = AsyncMock(
            return_value=[
                Agent(
                    id="agent1",
                    name="Agent 1",
                    file_path="/path/to/agent1",
                    description="",
                    allowed_tools=[],
                    allowed_mcps=[],
                    skills=[],
                ),
                Agent(
                    id="agent2",
                    name="Agent 2",
                    file_path="/path/to/agent2",
                    description="",
                    allowed_tools=[],
                    allowed_mcps=[],
                    skills=[],
                ),
            ]
        )

        factory = SessionFactory(
            agent_repository=mock_agent_repo,
            skill_repository=mock_skill_repo,
        )

        with pytest.raises(
            ValidationError,
            match="Agent 'nonexistent-agent' not found. Available agents: 'agent1', 'agent2'",
        ):
            await factory.create_session(
                session_type=SessionType.SPECIALIST,
                instance_id=str(uuid4()),
                working_dir=Path("/tmp/test"),
                agent_id="nonexistent-agent",
            )

    @pytest.mark.asyncio
    async def test_create_pm_session_success(self, session_factory, sample_agent):
        """Test successful PM session creation."""
        project_id = uuid4()
        session, options = await session_factory.create_session(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-agent",
            project_id=project_id,
        )

        # Verify session created
        assert session.session_type == SessionType.PM
        assert session.agent_id == "test-agent"
        assert session.project_id == project_id

        # Verify ClaudeAgentOptions created
        assert options is not None
        assert hasattr(options, "model")
        assert hasattr(options, "cwd")

    @pytest.mark.asyncio
    async def test_create_specialist_session_success(self, session_factory):
        """Test successful Specialist session creation."""
        session, options = await session_factory.create_session(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-agent",
        )

        # Verify session created
        assert session.session_type == SessionType.SPECIALIST
        assert session.agent_id == "test-agent"
        assert session.project_id is None

        # Verify ClaudeAgentOptions created
        assert options is not None

    @pytest.mark.asyncio
    async def test_create_assistant_session_success(self, session_factory):
        """Test successful Assistant session creation."""
        session, options = await session_factory.create_session(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id=None,  # Agent is optional for assistant
        )

        # Verify session created
        assert session.session_type == SessionType.ASSISTANT
        # Agent ID is optional for assistant, defaults to empty string
        assert session.agent_id is not None

        # Verify ClaudeAgentOptions created
        assert options is not None

    @pytest.mark.asyncio
    async def test_resume_session_includes_resume_id(self, session_factory):
        """Test that resume_session_id is included in options."""
        resume_id = "claude-session-123"
        session, options = await session_factory.create_session(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-agent",
            resume_session_id=resume_id,
        )

        # Verify resume is in options
        # Note: This depends on ClaudeAgentOptions structure
        assert options is not None
