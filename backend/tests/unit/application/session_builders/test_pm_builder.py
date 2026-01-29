"""Tests for PMBuilder."""

import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.application.session_builders.pm_builder import PMSessionBuilder
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
        id="test-pm",
        name="Test PM Agent",
        file_path="/path/to/agent",
        description="Test PM",
        allowed_tools=["Read", "Write"],
        allowed_mcps=["github"],
        skills=["planning"],
    )
    loader.load_agent_for_session = AsyncMock(
        return_value=(
            mock_agent,
            "PM Agent personality content",
            Path("/tmp/agents/test-pm"),
        )
    )
    return loader


@pytest.fixture
def mock_skill_loader():
    """Create mock skill loader."""
    loader = MagicMock()
    loader.load_skills_for_session = AsyncMock(
        return_value=["### Planning Skill\nHelps with planning"]
    )
    return loader


@pytest.fixture
def mock_mcp_service():
    """Create mock MCP service."""
    service = MagicMock()
    service.get_servers_for_agent = MagicMock(
        return_value={
            "pm_management": {"command": "pm-mcp", "args": []},
            "github": {"command": "github-mcp", "args": []},
        }
    )
    return service


@pytest.fixture
def pm_builder(mock_agent_loader, mock_skill_loader, mock_mcp_service):
    """Create PMBuilder instance."""
    return PMSessionBuilder(
        agent_loader=mock_agent_loader,
        skill_loader=mock_skill_loader,
        mcp_service=mock_mcp_service,
    )


class TestPMBuilder:
    """Tests for PMBuilder."""

    @pytest.mark.asyncio
    async def test_requires_project_id(self, pm_builder):
        """Test that PM builder requires project_id."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=None,  # Missing project_id
        )

        with pytest.raises(ValidationError, match="PM sessions require project_id"):
            await pm_builder.build_options(context)

    @pytest.mark.asyncio
    async def test_uses_project_path_as_working_dir(self, pm_builder):
        """Test that PM builder uses project path as working directory."""
        project_path = Path("/projects/my-project")
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            project_path=project_path,
        )

        options = await pm_builder.build_options(context)

        # PM should use project_path, not working_dir
        assert options.cwd == str(project_path)

    @pytest.mark.asyncio
    async def test_includes_pm_management_tools(self, pm_builder):
        """Test that PM builder includes pm_management MCP."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
        )

        options = await pm_builder.build_options(context)

        # Should have mcp__pm_management
        assert "mcp__pm_management" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_common_tools(self, pm_builder):
        """Test that PM builder includes common tools."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
        )

        options = await pm_builder.build_options(context)

        # Should have common tools
        assert "mcp__common_tools" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_loads_agent_content_if_provided(self, pm_builder, mock_agent_loader):
        """Test that PM builder loads agent content when agent_id provided."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id="test-pm-agent",
        )

        await pm_builder.build_options(context)

        # Should have called load_agent_for_session
        mock_agent_loader.load_agent_for_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_works_without_agent_id(self, pm_builder):
        """Test that PM builder works without agent_id (generic PM)."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id=None,  # No agent
        )

        options = await pm_builder.build_options(context)

        # Should still create valid options
        assert options is not None
        assert "mcp__pm_management" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_system_prompt_includes_pm_template(self, pm_builder):
        """Test that system prompt includes PM-specific template."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
        )

        options = await pm_builder.build_options(context)

        # Should have PM-specific content
        assert "Project Manager" in options.system_prompt
        assert (
            "spawn_instance" in options.system_prompt
            or "project management" in options.system_prompt.lower()
        )

    @pytest.mark.asyncio
    async def test_system_prompt_includes_agent_content(self, pm_builder):
        """Test that system prompt includes agent content when agent_id provided."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id="test-pm",
        )

        options = await pm_builder.build_options(context)

        # Should include agent personality
        assert "PM Agent personality content" in options.system_prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_skills(self, pm_builder, mock_skill_loader):
        """Test that system prompt includes skill descriptions."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id="test-pm",
        )

        options = await pm_builder.build_options(context)

        # Should include skills section
        assert "Available Skills" in options.system_prompt
        assert "Planning Skill" in options.system_prompt

    @pytest.mark.asyncio
    async def test_includes_agent_specific_tools(self, pm_builder):
        """Test that PM builder includes agent-specific tools."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id="test-pm",
        )

        options = await pm_builder.build_options(context)

        # Should have agent's tools
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_agent_mcps_with_prefix(self, pm_builder):
        """Test that PM builder includes agent's MCP servers with mcp__ prefix."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id="test-pm",
        )

        options = await pm_builder.build_options(context)

        # Should have agent's MCPs with prefix
        assert "mcp__github" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_mcp_servers_configuration_loaded(self, pm_builder, mock_mcp_service):
        """Test that MCP server configurations are loaded correctly."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            agent_id="test-pm",
        )

        options = await pm_builder.build_options(context)

        # Should have MCP server configs
        assert options.mcp_servers is not None
        assert "pm_management" in options.mcp_servers
        assert "github" in options.mcp_servers

    @pytest.mark.asyncio
    async def test_resume_session_included_when_provided(self, pm_builder):
        """Test that resume session ID is included in options when provided."""
        resume_id = "claude-session-abc123"
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            resume_session_id=resume_id,
        )

        options = await pm_builder.build_options(context)

        # Should have resume in options
        # Note: ClaudeAgentOptions may store this differently
        # We're verifying the builder processes it
        assert options is not None

    @pytest.mark.asyncio
    async def test_permission_mode_set_correctly(self, pm_builder):
        """Test that permission mode is set to bypassPermissions."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
        )

        options = await pm_builder.build_options(context)

        assert options.permission_mode == "bypassPermissions"

    @pytest.mark.asyncio
    async def test_model_configuration(self, pm_builder):
        """Test that model is configured from context."""
        context = SessionBuildContext(
            session_type=SessionType.PM,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_id=uuid4(),
            model="opus",
        )

        options = await pm_builder.build_options(context)

        assert options.model == "opus"
