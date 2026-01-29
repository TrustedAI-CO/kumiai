"""Fixtures for repository integration tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.project_repository import (
    ProjectRepositoryImpl,
)


# NOTE: character_repo fixture removed - Characters are now file-based (agents)


@pytest.fixture
async def project_repo(db_session: AsyncSession) -> ProjectRepositoryImpl:
    """Create ProjectRepository with test database session."""
    return ProjectRepositoryImpl(db_session)
