"""
Integration tests for logical vs physical path architecture.

Tests that verify the separation between API-exposed logical paths
and internal filesystem physical paths for agents and skills.
"""

import pytest
from pathlib import Path

from app.infrastructure.filesystem.agent_repository import FileBasedAgentRepository
from app.infrastructure.filesystem.skill_repository import FileBasedSkillRepository
from app.domain.entities.agent import Agent
from app.domain.entities.skill import Skill


class TestPathArchitecture:
    """Test logical vs physical path separation."""

    @pytest.mark.asyncio
    async def test_agent_logical_vs_physical_paths(self, tmp_path):
        """Test that agent API returns logical paths while repository uses physical paths."""
        # Setup
        agents_dir = tmp_path / "agents"
        repo = FileBasedAgentRepository(base_path=agents_dir)

        # Create agent
        agent = Agent(
            id="test-agent",
            name="Test Agent",
            file_path="",  # Empty on creation
            description="Testing path architecture",
            allowed_tools=["Read"],
            allowed_mcps=[],
            skills=[],
        )
        created_agent = await repo.create(agent)

        # API should return logical path
        assert created_agent.file_path == "/agents/test-agent/", (
            "API should return logical path format /agents/{id}/"
        )

        # Logical path should NOT be an absolute filesystem path
        assert not Path(
            created_agent.file_path
        ).is_absolute() or created_agent.file_path.startswith("/agents/"), (
            "Logical path should not expose actual filesystem location"
        )

        # Repository method should return physical path
        physical_path = await repo.get_agent_directory("test-agent")
        assert physical_path.is_absolute(), "Physical path should be absolute"
        assert physical_path.exists(), "Physical directory should exist on filesystem"
        assert physical_path == agents_dir / "test-agent", (
            "Physical path should match repository base_path"
        )

        # Verify CLAUDE.md exists at physical location
        claude_md = physical_path / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md should exist at physical location"

    @pytest.mark.asyncio
    async def test_skill_logical_vs_physical_paths(self, tmp_path):
        """Test that skill API returns logical paths while repository uses physical paths."""
        # Setup
        skills_dir = tmp_path / "skills"
        repo = FileBasedSkillRepository(base_path=skills_dir)

        # Create skill
        skill = Skill(
            id="test-skill",
            name="Test Skill",
            file_path="",  # Empty on creation
            description="Testing path architecture",
        )
        created_skill = await repo.create(skill)

        # API should return logical path
        assert created_skill.file_path == "/skills/test-skill/", (
            "API should return logical path format /skills/{id}/"
        )

        # Logical path should NOT be an absolute filesystem path
        assert not Path(
            created_skill.file_path
        ).is_absolute() or created_skill.file_path.startswith("/skills/"), (
            "Logical path should not expose actual filesystem location"
        )

        # Repository method should return physical path
        physical_path = await repo.get_skill_directory("test-skill")
        assert physical_path.is_absolute(), "Physical path should be absolute"
        assert physical_path.exists(), "Physical directory should exist on filesystem"
        assert physical_path == skills_dir / "test-skill", (
            "Physical path should match repository base_path"
        )

        # Verify SKILL.md exists at physical location
        skill_md = physical_path / "SKILL.md"
        assert skill_md.exists(), "SKILL.md should exist at physical location"

    @pytest.mark.asyncio
    async def test_filesystem_location_independence_agents(self, tmp_path):
        """Test that agent logical paths are independent of filesystem location.

        This verifies that the API contract (logical paths) remains constant
        even when the physical storage location changes.
        """
        # Create two repositories with different base paths
        location_1 = tmp_path / "location1" / "agents"
        location_2 = tmp_path / "location2" / "agents"

        repo_1 = FileBasedAgentRepository(base_path=location_1)
        repo_2 = FileBasedAgentRepository(base_path=location_2)

        # Create same agent in both repositories
        agent = Agent(
            id="portable-agent",
            name="Portable Agent",
            file_path="",
            description="Testing location independence",
            allowed_tools=["Read"],
            allowed_mcps=[],
            skills=[],
        )

        agent_1 = await repo_1.create(agent)
        agent_2 = await repo_2.create(agent)

        # Both should return identical logical paths
        assert agent_1.file_path == agent_2.file_path, (
            "Logical paths must be identical regardless of physical location"
        )
        assert agent_1.file_path == "/agents/portable-agent/", (
            "Logical path should follow standard format"
        )

        # But physical paths should be different
        physical_1 = await repo_1.get_agent_directory("portable-agent")
        physical_2 = await repo_2.get_agent_directory("portable-agent")

        assert physical_1 != physical_2, (
            "Physical paths should differ based on repository configuration"
        )
        assert physical_1 == location_1 / "portable-agent", (
            "Physical path should reflect first repository location"
        )
        assert physical_2 == location_2 / "portable-agent", (
            "Physical path should reflect second repository location"
        )

        # Both physical locations should have CLAUDE.md
        assert (physical_1 / "CLAUDE.md").exists(), (
            "CLAUDE.md should exist at first physical location"
        )
        assert (physical_2 / "CLAUDE.md").exists(), (
            "CLAUDE.md should exist at second physical location"
        )

    @pytest.mark.asyncio
    async def test_filesystem_location_independence_skills(self, tmp_path):
        """Test that skill logical paths are independent of filesystem location."""
        # Create two repositories with different base paths
        location_1 = tmp_path / "location1" / "skills"
        location_2 = tmp_path / "location2" / "skills"

        repo_1 = FileBasedSkillRepository(base_path=location_1)
        repo_2 = FileBasedSkillRepository(base_path=location_2)

        # Create same skill in both repositories
        skill = Skill(
            id="portable-skill",
            name="Portable Skill",
            file_path="",
            description="Testing location independence",
        )

        skill_1 = await repo_1.create(skill)
        skill_2 = await repo_2.create(skill)

        # Both should return identical logical paths
        assert skill_1.file_path == skill_2.file_path, (
            "Logical paths must be identical regardless of physical location"
        )
        assert skill_1.file_path == "/skills/portable-skill/", (
            "Logical path should follow standard format"
        )

        # But physical paths should be different
        physical_1 = await repo_1.get_skill_directory("portable-skill")
        physical_2 = await repo_2.get_skill_directory("portable-skill")

        assert physical_1 != physical_2, (
            "Physical paths should differ based on repository configuration"
        )
        assert (physical_1 / "SKILL.md").exists(), (
            "SKILL.md should exist at first physical location"
        )
        assert (physical_2 / "SKILL.md").exists(), (
            "SKILL.md should exist at second physical location"
        )

    @pytest.mark.asyncio
    async def test_get_all_returns_logical_paths(self, tmp_path):
        """Test that get_all() returns logical paths for all entities."""
        # Setup agent repository
        agents_dir = tmp_path / "agents"
        agent_repo = FileBasedAgentRepository(base_path=agents_dir)

        # Create multiple agents
        for i in range(3):
            agent = Agent(
                id=f"agent-{i}",
                name=f"Agent {i}",
                file_path="",
                description=f"Agent number {i}",
                allowed_tools=["Read"],
                allowed_mcps=[],
                skills=[],
            )
            await agent_repo.create(agent)

        # Get all agents
        all_agents = await agent_repo.get_all()

        # All should have logical paths
        for agent in all_agents:
            assert agent.file_path.startswith("/agents/"), (
                f"Agent {agent.id} should have logical path"
            )
            assert agent.file_path == f"/agents/{agent.id}/", (
                f"Agent {agent.id} should follow logical path format"
            )

        # Setup skill repository
        skills_dir = tmp_path / "skills"
        skill_repo = FileBasedSkillRepository(base_path=skills_dir)

        # Create multiple skills
        for i in range(3):
            skill = Skill(
                id=f"skill-{i}",
                name=f"Skill {i}",
                file_path="",
                description=f"Skill number {i}",
            )
            await skill_repo.create(skill)

        # Get all skills
        all_skills = await skill_repo.get_all()

        # All should have logical paths
        for skill in all_skills:
            assert skill.file_path.startswith("/skills/"), (
                f"Skill {skill.id} should have logical path"
            )
            assert skill.file_path == f"/skills/{skill.id}/", (
                f"Skill {skill.id} should follow logical path format"
            )

    @pytest.mark.asyncio
    async def test_get_by_id_returns_logical_path(self, tmp_path):
        """Test that get_by_id() returns logical path."""
        # Setup
        agents_dir = tmp_path / "agents"
        repo = FileBasedAgentRepository(base_path=agents_dir)

        # Create agent
        agent = Agent(
            id="lookup-test",
            name="Lookup Test",
            file_path="",
            description="Testing lookup",
            allowed_tools=[],
            allowed_mcps=[],
            skills=[],
        )
        await repo.create(agent)

        # Retrieve by ID
        retrieved = await repo.get_by_id("lookup-test")

        # Should have logical path
        assert retrieved.file_path == "/agents/lookup-test/", (
            "Retrieved agent should have logical path"
        )

        # Physical path should still be accessible
        physical = await repo.get_agent_directory("lookup-test")
        assert physical.exists(), "Physical directory should exist"
