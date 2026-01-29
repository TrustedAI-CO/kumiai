"""Tests for ToolRegistry."""

from app.infrastructure.mcp.tool_registry import ToolRegistry


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_build_allowed_tools_base_only(self):
        """Test building tools list with only base tools."""
        base_tools = ["Read", "Write", "Edit"]
        mcp_servers = []

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=False
        )

        assert result == ["Read", "Write", "Edit"]

    def test_build_allowed_tools_with_mcp_servers(self):
        """Test building tools list with MCP servers."""
        base_tools = ["Read", "Write"]
        mcp_servers = ["github", "jira"]

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=False
        )

        assert "Read" in result
        assert "Write" in result
        assert "mcp__github" in result
        assert "mcp__jira" in result

    def test_build_allowed_tools_with_common_tools(self):
        """Test building tools list includes common tools by default."""
        base_tools = ["Read", "Write"]
        mcp_servers = []

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=True
        )

        assert "Read" in result
        assert "Write" in result
        assert "mcp__common_tools" in result

    def test_build_allowed_tools_without_common_tools(self):
        """Test building tools list can exclude common tools."""
        base_tools = ["Read", "Write"]
        mcp_servers = []

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=False
        )

        assert "Read" in result
        assert "Write" in result
        assert "mcp__common_tools" not in result

    def test_build_allowed_tools_no_duplicates(self):
        """Test that build_allowed_tools doesn't add duplicates."""
        base_tools = ["Read", "Write", "mcp__github"]  # Already has mcp__github
        mcp_servers = ["github", "jira"]

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=False
        )

        # Count occurrences of mcp__github
        github_count = result.count("mcp__github")
        assert github_count == 1

    def test_build_allowed_tools_complete_scenario(self):
        """Test complete scenario with base tools, MCPs, and common tools."""
        base_tools = ["Read", "Write", "Bash"]
        mcp_servers = ["github", "pm_management"]

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=True
        )

        # Should have all base tools
        assert "Read" in result
        assert "Write" in result
        assert "Bash" in result

        # Should have MCP servers with prefix
        assert "mcp__github" in result
        assert "mcp__pm_management" in result

        # Should have common tools
        assert "mcp__common_tools" in result

        # Should have 6 total items
        assert len(result) == 6

    def test_build_allowed_tools_empty_inputs(self):
        """Test building tools list with empty inputs."""
        result = ToolRegistry.build_allowed_tools([], [], include_common=False)

        assert result == []

    def test_build_allowed_tools_empty_base_with_mcps(self):
        """Test building tools list with no base tools but with MCPs."""
        result = ToolRegistry.build_allowed_tools([], ["github"], include_common=False)

        assert result == ["mcp__github"]

    def test_build_allowed_tools_preserves_base_tools_order(self):
        """Test that base tools order is preserved."""
        base_tools = ["Edit", "Read", "Write"]
        mcp_servers = []

        result = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=False
        )

        # First three should be base tools in order
        assert result[0] == "Edit"
        assert result[1] == "Read"
        assert result[2] == "Write"

    def test_build_allowed_tools_mcp_prefix_added_correctly(self):
        """Test that MCP prefix is added correctly to server names."""
        mcp_servers = ["server_one", "server_two"]

        result = ToolRegistry.build_allowed_tools([], mcp_servers, include_common=False)

        assert "mcp__server_one" in result
        assert "mcp__server_two" in result
        assert "server_one" not in result  # Should not have unprefixed version

    def test_validate_base_tools_all_valid(self):
        """Test validating list of all valid base tools."""
        tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]

        result = ToolRegistry.validate_base_tools(tools)

        assert result == tools

    def test_validate_base_tools_with_mcp_tools(self):
        """Test validating list including MCP tools."""
        tools = ["Read", "Write", "mcp__github", "mcp__jira"]

        result = ToolRegistry.validate_base_tools(tools)

        assert result == tools

    def test_validate_base_tools_invalid_tools_filtered(self):
        """Test that invalid tools are filtered out."""
        tools = ["Read", "InvalidTool", "Write", "AnotherInvalid"]

        result = ToolRegistry.validate_base_tools(tools)

        assert "Read" in result
        assert "Write" in result
        assert "InvalidTool" not in result
        assert "AnotherInvalid" not in result

    def test_validate_base_tools_empty_list(self):
        """Test validating empty tools list."""
        result = ToolRegistry.validate_base_tools([])

        assert result == []

    def test_validate_base_tools_all_invalid(self):
        """Test validating list with all invalid tools."""
        tools = ["InvalidTool1", "InvalidTool2"]

        result = ToolRegistry.validate_base_tools(tools)

        assert result == []

    def test_validate_base_tools_mixed_valid_invalid(self):
        """Test validating mixed valid and invalid tools."""
        tools = ["Read", "InvalidTool", "mcp__github", "AnotherInvalid", "Write"]

        result = ToolRegistry.validate_base_tools(tools)

        assert len(result) == 3
        assert "Read" in result
        assert "mcp__github" in result
        assert "Write" in result

    def test_extract_mcp_servers_from_tools(self):
        """Test extracting MCP server names from tool list."""
        tools = ["Read", "Write", "mcp__github", "mcp__jira", "Bash"]

        result = ToolRegistry.extract_mcp_servers_from_tools(tools)

        assert "github" in result
        assert "jira" in result
        assert len(result) == 2

    def test_extract_mcp_servers_no_mcp_tools(self):
        """Test extracting MCP servers when no MCP tools in list."""
        tools = ["Read", "Write", "Edit"]

        result = ToolRegistry.extract_mcp_servers_from_tools(tools)

        assert result == []

    def test_extract_mcp_servers_only_mcp_tools(self):
        """Test extracting MCP servers when only MCP tools in list."""
        tools = ["mcp__github", "mcp__jira", "mcp__pm_management"]

        result = ToolRegistry.extract_mcp_servers_from_tools(tools)

        assert result == ["github", "jira", "pm_management"]

    def test_extract_mcp_servers_empty_list(self):
        """Test extracting MCP servers from empty list."""
        result = ToolRegistry.extract_mcp_servers_from_tools([])

        assert result == []

    def test_extract_mcp_servers_preserves_order(self):
        """Test that MCP server extraction preserves order."""
        tools = ["mcp__third", "mcp__first", "mcp__second"]

        result = ToolRegistry.extract_mcp_servers_from_tools(tools)

        assert result == ["third", "first", "second"]

    def test_extract_mcp_servers_handles_duplicates(self):
        """Test extracting MCP servers with duplicate entries."""
        tools = ["mcp__github", "mcp__jira", "mcp__github"]

        result = ToolRegistry.extract_mcp_servers_from_tools(tools)

        # Should include duplicates (no deduplication)
        assert result == ["github", "jira", "github"]

    def test_common_tools_constant(self):
        """Test that COMMON_TOOLS constant is defined correctly."""
        assert ToolRegistry.COMMON_TOOLS == ["mcp__common_tools"]

    def test_base_tools_constant(self):
        """Test that BASE_TOOLS constant contains expected tools."""
        expected_tools = {"Read", "Write", "Edit", "Bash", "Grep", "Glob"}
        assert ToolRegistry.BASE_TOOLS == expected_tools

    def test_base_tools_constant_is_set(self):
        """Test that BASE_TOOLS is a set for O(1) lookup."""
        assert isinstance(ToolRegistry.BASE_TOOLS, set)

    def test_integration_build_and_extract(self):
        """Test integration between build_allowed_tools and extract_mcp_servers."""
        base_tools = ["Read", "Write"]
        mcp_servers = ["github", "jira"]

        # Build tools list
        built_tools = ToolRegistry.build_allowed_tools(
            base_tools, mcp_servers, include_common=True
        )

        # Extract MCP servers from built list
        extracted_servers = ToolRegistry.extract_mcp_servers_from_tools(built_tools)

        # Should extract the MCP servers we added plus common_tools
        assert "github" in extracted_servers
        assert "jira" in extracted_servers
        assert "common_tools" in extracted_servers

    def test_integration_build_and_validate(self):
        """Test integration between build_allowed_tools and validate_base_tools."""
        base_tools = ["Read", "Write", "InvalidTool"]
        mcp_servers = ["github"]

        # First validate base tools
        valid_base_tools = ToolRegistry.validate_base_tools(base_tools)

        # Then build allowed tools with validated tools
        built_tools = ToolRegistry.build_allowed_tools(
            valid_base_tools, mcp_servers, include_common=False
        )

        # Should have valid tools and MCP tools, but not invalid tool
        assert "Read" in built_tools
        assert "Write" in built_tools
        assert "mcp__github" in built_tools
        assert "InvalidTool" not in built_tools
