"""Tests for AssistantBuilder."""

import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.application.session_builders.assistant_builder import AssistantSessionBuilder
from app.application.session_builders.base_builder import SessionBuildContext
from app.domain.value_objects.session_type import SessionType
from app.domain.entities.agent import Agent


@pytest.fixture
def mock_agent_loader():
    """Create mock agent loader."""
    loader = MagicMock()

    # Mock load_agent_for_session
    mock_agent = Agent(
        id="test-assistant",
        name="Test Assistant Agent",
        file_path="/path/to/agent",
        description="Test Assistant",
        allowed_tools=["Read", "Write"],
        allowed_mcps=["common_tools"],
        skills=["general_assistance"],
    )
    loader.load_agent_for_session = AsyncMock(
        return_value=(
            mock_agent,
            "Assistant personality content",
            Path("/tmp/agents/test-assistant"),
        )
    )
    return loader


@pytest.fixture
def mock_skill_loader():
    """Create mock skill loader."""
    loader = MagicMock()
    loader.load_skills_for_session = AsyncMock(
        return_value=["### General Assistance skill\nHelps with various tasks"]
    )
    return loader


@pytest.fixture
def mock_mcp_service():
    """Create mock MCP service."""
    service = MagicMock()
    service.get_servers_for_agent = MagicMock(
        return_value={
            "common_tools": {"command": "common-mcp", "args": []},
        }
    )
    return service


@pytest.fixture
def assistant_builder(mock_agent_loader, mock_skill_loader, mock_mcp_service):
    """Create AssistantBuilder instance."""
    return AssistantSessionBuilder(
        agent_loader=mock_agent_loader,
        skill_loader=mock_skill_loader,
        mcp_service=mock_mcp_service,
    )


class TestAssistantBuilder:
    """Tests for AssistantBuilder."""

    @pytest.mark.asyncio
    async def test_works_without_agent_id(self, assistant_builder):
        """Test that Assistant builder works without agent_id (generic assistant)."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id=None,  # No agent
        )

        options = await assistant_builder.build_options(context)

        # Should still create valid options
        assert options is not None
        assert "mcp__common_tools" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_loads_agent_content_if_provided(
        self, assistant_builder, mock_agent_loader
    ):
        """Test that Assistant builder loads agent content when agent_id provided."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-assistant-agent",
        )

        await assistant_builder.build_options(context)

        # Should have called load_agent_for_session
        mock_agent_loader.load_agent_for_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_project_path_as_working_dir(self, assistant_builder):
        """Test that Assistant builder uses project path as working directory."""
        project_path = Path("/projects/my-project")
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            project_path=project_path,
        )

        options = await assistant_builder.build_options(context)

        # Assistant should use project_path, not working_dir
        assert options.cwd == str(project_path)

    @pytest.mark.asyncio
    async def test_fallback_to_working_dir_when_no_project_path(
        self, assistant_builder
    ):
        """Test that Assistant builder falls back to working_dir when no project_path."""
        working_dir = Path("/tmp/test")
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=working_dir,
            project_path=None,  # No project path
        )

        options = await assistant_builder.build_options(context)

        # Should fall back to working_dir
        assert options.cwd == str(working_dir)

    @pytest.mark.asyncio
    async def test_includes_file_editing_tools(self, assistant_builder):
        """Test that Assistant builder includes base file editing tools."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
        )

        options = await assistant_builder.build_options(context)

        # Should have base file editing tools
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools
        assert "Edit" in options.allowed_tools
        assert "Bash" in options.allowed_tools
        assert "Grep" in options.allowed_tools
        assert "Glob" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_agent_tools_when_provided(self, assistant_builder):
        """Test that Assistant builder includes agent-specific tools when agent_id provided."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-assistant-agent",
        )

        options = await assistant_builder.build_options(context)

        # Should have agent's tools in addition to base tools
        assert "Read" in options.allowed_tools
        assert "Write" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_agent_mcps_when_provided(self, assistant_builder):
        """Test that Assistant builder includes agent's MCP servers when agent_id provided."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-assistant-agent",
        )

        options = await assistant_builder.build_options(context)

        # Should have agent's MCPs with prefix
        assert "mcp__common_tools" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_includes_common_tools(self, assistant_builder):
        """Test that Assistant builder includes common tools."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
        )

        options = await assistant_builder.build_options(context)

        # Should have common tools
        assert "mcp__common_tools" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_system_prompt_includes_assistant_template(self, assistant_builder):
        """Test that system prompt includes Assistant-specific template."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
        )

        options = await assistant_builder.build_options(context)

        # Should have Assistant-specific content
        assert "assistant" in options.system_prompt.lower()

    @pytest.mark.asyncio
    async def test_system_prompt_includes_agent_content(self, assistant_builder):
        """Test that system prompt includes agent content when agent_id provided."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-assistant",
        )

        options = await assistant_builder.build_options(context)

        # Should include agent personality
        assert "Assistant personality content" in options.system_prompt

    @pytest.mark.asyncio
    async def test_system_prompt_includes_skills(self, assistant_builder):
        """Test that system prompt includes skill descriptions when agent has skills."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-assistant",
        )

        options = await assistant_builder.build_options(context)

        # Should include skills section
        assert "Available Skills" in options.system_prompt
        assert "General Assistance skill" in options.system_prompt

    @pytest.mark.asyncio
    async def test_system_prompt_without_agent_content(
        self, assistant_builder, mock_agent_loader
    ):
        """Test that system prompt works without agent content (generic assistant)."""
        # Don't call load_agent_for_session for this test
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id=None,  # No agent
        )

        options = await assistant_builder.build_options(context)

        # Should still have valid system prompt with just template
        assert options.system_prompt is not None
        assert len(options.system_prompt) > 0

    @pytest.mark.asyncio
    async def test_mcp_servers_configuration_loaded(
        self, assistant_builder, mock_mcp_service
    ):
        """Test that MCP server configurations are loaded correctly."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id="test-assistant",
        )

        options = await assistant_builder.build_options(context)

        # Should have MCP server configs
        assert options.mcp_servers is not None
        assert "common_tools" in options.mcp_servers

    @pytest.mark.asyncio
    async def test_mcp_servers_empty_without_agent(self, assistant_builder):
        """Test that MCP servers dict is empty when no agent specified."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            agent_id=None,  # No agent
        )

        options = await assistant_builder.build_options(context)

        # Should have empty MCP servers dict (no agent MCPs)
        # Common tools still added via allowed_tools list
        assert "mcp__common_tools" in options.allowed_tools

    @pytest.mark.asyncio
    async def test_resume_session_included_when_provided(self, assistant_builder):
        """Test that resume session ID is included in options when provided."""
        resume_id = "claude-session-def456"
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            resume_session_id=resume_id,
        )

        options = await assistant_builder.build_options(context)

        # Should have resume in options
        assert options is not None

    @pytest.mark.asyncio
    async def test_permission_mode_set_correctly(self, assistant_builder):
        """Test that permission mode is set to bypassPermissions."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
        )

        options = await assistant_builder.build_options(context)

        assert options.permission_mode == "bypassPermissions"

    @pytest.mark.asyncio
    async def test_model_configuration(self, assistant_builder):
        """Test that model is configured from context."""
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=Path("/tmp/test"),
            model="sonnet",
        )

        options = await assistant_builder.build_options(context)

        assert options.model == "sonnet"

    @pytest.mark.asyncio
    async def test_creates_symlink_when_agent_provided(
        self, assistant_builder, mock_agent_loader
    ):
        """Test that symlink is created for agent when agent_id provided."""
        working_dir = Path("/tmp/test")
        context = SessionBuildContext(
            session_type=SessionType.ASSISTANT,
            instance_id=str(uuid4()),
            working_dir=working_dir,
            agent_id="test-assistant",
        )

        await assistant_builder.build_options(context)

        # Should have called load_agent_for_session with working_dir
        call_args = mock_agent_loader.load_agent_for_session.call_args
        # Assistant uses project_path (which defaults to working_dir)
        assert call_args[0][1] == working_dir  # session_dir parameter
