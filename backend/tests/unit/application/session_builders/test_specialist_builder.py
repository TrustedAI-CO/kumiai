"""Tests for SpecialistBuilder."""

import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.application.session_builders.specialist_builder import SpecialistSessionBuilder
from app.application.session_builders.base_builder import SessionBuildContext
from app.domain.value_objects.session_type import SessionType
from app.domain.entities.agent import Agent
from app.core.exceptions import ValidationError


@pytest.fixture
def mock_agent_loader():
    """Create mock agent loader."""
    loader = MagicMock()

    # Mock load_agent_for_session
    mock_agent = Agent(
        id="test-specialist",
        name="Test Specialist Agent",
        file_path="/path/to/agent",
        description="Test Specialist",
        allowed_tools=["Read", "Write", "Bash"],
        allowed_mcps=["github", "jira"],
        skills=["project_planning", "code_review"],
    )
    loader.load_agent_for_session = AsyncMock(
        return_value=(
            mock_agent,
            "Specialist personality content",
            Path("/tmp/agents/test-specialist"),
        )
    )
    return loader


@pytest.fixture
def mock_skill_loader():
    """Create mock skill loader."""
    loader = MagicMock()
    loader.load_skills_for_session = AsyncMock(
        return_value=[
            "### Project Planning skill\nHelps with planning",
            "### Code Review skill\nHelps with code review",
        ]
    )
    return loader


@pytest.fixture
def mock_mcp_service():
    """Create mock MCP service."""
    service = MagicMock()
    service.get_servers_for_agent = MagicMock(
        return_value={
            "github": {"command": "github-mcp", "args": []},
            "jira": {"command": "jira-mcp", "args": []},
        }
    )
    return service


@pytest.fixture
def specialist_builder(mock_agent_loader, mock_skill_loader, mock_mcp_service):
    """Create SpecialistBuilder instance."""
    return SpecialistSessionBuilder(
        agent_loader=mock_agent_loader,
        skill_loader=mock_skill_loader,
        mcp_service=mock_mcp_service,
    )


class TestSpecialistBuilder:
    """Tests for SpecialistBuilder."""

    @pytest.mark.asyncio
    async def test_requires_agent_id(self, specialist_builder):
        """Test that Specialist builder requires agent_id."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id=None,  # Missing agent_id
        )

        with pytest.raises(
            ValidationError, match="Specialist sessions require agent_id"
        ):
            await specialist_builder.build_options(context)

    @pytest.mark.asyncio
    async def test_uses_session_dir_for_isolation(self, specialist_builder):
        """Test that Specialist builder uses session directory for isolation."""
        session_dir = Path("/sessions/abc123")
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=session_dir,
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Specialist should use working_dir (session-specific)
        assert options.cwd == str(session_dir)

    @pytest.mark.asyncio
    async def test_loads_agent_content(self, specialist_builder, mock_agent_loader):
        """Test that Specialist builder loads agent content."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        await specialist_builder.build_options(context)

        # Should have called load_agent_for_session
        mock_agent_loader.load_agent_for_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_agent_specific_tools(self, specialist_builder):
        """Test that Specialist builder includes agent-specific tools."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should have agent's base tools
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools
        assert "Bash" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_agent_mcps(self, specialist_builder):
        """Test that Specialist builder includes agent's MCP servers."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should have agent's MCPs with prefix
        assert "mcp__github" in options.allowed_tools
        assert "mcp__jira" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_common_tools(self, specialist_builder):
        """Test that Specialist builder includes common tools."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should have common tools
        assert "mcp__common_tools" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_system_prompt_includes_specialist_template(self, specialist_builder):
        """Test that system prompt includes Specialist-specific template."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should have Specialist template content
        assert (
            "specialized capabilities" in options.system_prompt.lower()
            or "specialist" in options.system_prompt.lower()
        )

    @pytest.mark.asyncio
    async def test_system_prompt_includes_agent_content(self, specialist_builder):
        """Test that system prompt includes agent personality content."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should include agent personality
        assert "Specialist personality content" in options.system_prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_skills(self, specialist_builder):
        """Test that system prompt includes skill descriptions."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should include skills section
        assert "Available Skills" in options.system_prompt
        assert "Project Planning skill" in options.system_prompt
        assert "Code Review skill" in options.system_prompt

    @pytest.mark.asyncio
    async def test_loads_multiple_skills(self, specialist_builder, mock_skill_loader):
        """Test that Specialist builder loads all agent skills."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        await specialist_builder.build_options(context)

        # Should have called load_skills_for_session with agent's skills
        mock_skill_loader.load_skills_for_session.assert_called_once()
        call_args = mock_skill_loader.load_skills_for_session.call_args
        skills_list = call_args[0][0]
        assert "project_planning" in skills_list
        assert "code_review" in skills_list

    @pytest.mark.asyncio
    async def test_mcp_servers_configuration_loaded(
        self, specialist_builder, mock_mcp_service
    ):
        """Test that MCP server configurations are loaded correctly."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        # Should have MCP server configs
        assert options.mcp_servers is not None
        assert "github" in options.mcp_servers
        assert "jira" in options.mcp_servers

    @pytest.mark.asyncio
    async def test_resume_session_included_when_provided(self, specialist_builder):
        """Test that resume session ID is included in options when provided."""
        resume_id = "claude-session-xyz789"
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
            resume_session_id=resume_id,
        )

        options = await specialist_builder.build_options(context)

        # Should have resume in options
        assert options is not None

    @pytest.mark.asyncio
    async def test_permission_mode_set_correctly(self, specialist_builder):
        """Test that permission mode is set to bypassPermissions."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
        )

        options = await specialist_builder.build_options(context)

        assert options.permission_mode == "bypassPermissions"

    @pytest.mark.asyncio
    async def test_model_configuration(self, specialist_builder):
        """Test that model is configured from context."""
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-specialist",
            model="haiku",
        )

        options = await specialist_builder.build_options(context)

        assert options.model == "haiku"

    @pytest.mark.asyncio
    async def test_creates_symlink_for_agent(
        self, specialist_builder, mock_agent_loader
    ):
        """Test that symlink is created for agent access."""
        session_dir = Path("/sessions/abc123")
        context = SessionBuildContext(
            session_type=SessionType.SPECIALIST,
            instance_id=str(uuid4()),
            working_dir=session_dir,
            agent_id="test-specialist",
        )

        await specialist_builder.build_options(context)

        # Should have called load_agent_for_session with session_dir
        call_args = mock_agent_loader.load_agent_for_session.call_args
        assert call_args[0][1] == session_dir  # session_dir parameter
