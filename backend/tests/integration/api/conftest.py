"""Configuration and fixtures for integration API tests."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.api import dependencies
from app.api.dependencies import get_agent_service, get_skill_service
from app.application.services import SkillService
from app.application.services.agent_service import AgentService
from app.core.dependencies import get_db
from app.domain.entities.agent import Agent
from app.infrastructure.filesystem import FileBasedSkillRepository
from app.infrastructure.filesystem.agent_repository import FileBasedAgentRepository
from app.main import app


@pytest.fixture
async def client(db_session, tmp_skills_dir, tmp_agents_dir):
    """Create async HTTP client for API tests with test database override.

    This fixture overrides the FastAPI get_db dependency to use the test
    database session, ensuring that API endpoints interact with test data.
    It also overrides the skill and agent repositories to use temporary directories.
    """
    # Clear singleton cache before test
    dependencies._skill_repository = None
    dependencies._agent_repository = None

    # Override the database dependency to use test session
    async def override_get_db():
        yield db_session

    # Override the skill service to use test repository
    async def override_get_skill_service():
        return SkillService(
            skill_repo=FileBasedSkillRepository(base_path=tmp_skills_dir)
        )

    # Override the agent service to use test repository
    async def override_get_agent_service():
        return AgentService(
            agent_repo=FileBasedAgentRepository(base_path=tmp_agents_dir)
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_skill_service] = override_get_skill_service
    app.dependency_overrides[get_agent_service] = override_get_agent_service

    # Create async client with ASGI transport
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clean up dependency overrides and singleton cache
    app.dependency_overrides.clear()
    dependencies._skill_repository = None
    dependencies._agent_repository = None


@pytest.fixture
def tmp_agents_dir(tmp_path):
    """Create temporary directory for agent tests."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    return agents_dir


@pytest.fixture
async def agent(tmp_agents_dir):
    """Create a test agent."""
    agent_repo = FileBasedAgentRepository(base_path=tmp_agents_dir)
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        file_path="/agents/test-agent/",
        tags=["python", "testing"],
        skills=["test-skill"],
        allowed_tools=["Read", "Write"],
        allowed_mcps=[],
        icon_color="#4A90E2",
    )
    await agent_repo.create(agent)
    return agent
