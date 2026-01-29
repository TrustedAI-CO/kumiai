"""Root conftest.py for pytest configuration and shared fixtures."""

import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.infrastructure.database.models import Base

# Add tests directory to sys.path so we can import fixtures
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

# Import model fixtures to make them available to all tests
from fixtures.model_fixtures import (  # noqa: F401, E402
    activity_log,
    message,
    project,
    session,
    skill,
    user_profile,
)

# Test database URL (use separate test database)
TEST_DATABASE_URL = settings.database_url.replace("/kumiai_db", "/kumiai_test_db")


async def create_enums(conn):
    """Create ENUM types in the database.

    This is needed because the ENUM monkey-patch in alembic/env.py
    prevents automatic ENUM creation when using Base.metadata.create_all().
    """
    enum_definitions = [
        """
        DO $$ BEGIN
            CREATE TYPE session_type AS ENUM ('pm', 'specialist', 'assistant');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE session_status AS ENUM (
                'initializing', 'idle', 'thinking', 'working',
                'waiting', 'completed', 'error', 'cancelled', 'interrupted'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system', 'tool_result');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
        """
        DO $$ BEGIN
            CREATE TYPE event_type AS ENUM (
                'session_created', 'session_started', 'session_completed',
                'session_failed', 'message_sent', 'tool_executed',
                'project_created', 'project_updated'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """,
    ]

    for enum_sql in enum_definitions:
        await conn.execute(text(enum_sql))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable connection pooling for tests
    )

    # Create ENUMs and tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await create_enums(conn)  # Create ENUMs before tables
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session.

    Each test gets a fresh session that is rolled back after the test.
    Uses a SAVEPOINT to ensure all changes are rolled back even if committed.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    async_session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    async with async_session_maker() as session:
        yield session

    # Rollback the outer transaction to undo all changes
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


# File-based skill test fixtures
@pytest.fixture
def tmp_skills_dir(tmp_path: Path) -> Path:
    """
    Create temporary skills directory for file-based skill tests.

    Args:
        tmp_path: Pytest's temporary path fixture

    Returns:
        Path to temporary skills directory
    """
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    return skills_dir


@pytest.fixture
def sample_skill_md() -> str:
    """
    Sample SKILL.md content with YAML frontmatter.

    Returns:
        SKILL.md content string
    """
    return """---
name: Test Skill
description: A test skill for testing purposes
tags: [test, sample]
icon: zap
iconColor: "#4A90E2"
version: 1.0.0
---

# Test Skill

This is a test skill for testing purposes.

## Usage

Use this skill to test the file-based skill system.

## Examples

```python
# Example usage
print("Hello from test skill!")
```
"""


@pytest.fixture
def test_skill_data() -> dict:
    """
    Sample skill data for creating test skills.

    Returns:
        Dictionary with skill data
    """
    return {
        "name": "Test Skill",
        "description": "A test skill for testing purposes",
        "file_path": "/skills/test-skill/",
        "tags": ["test", "sample"],
        "version": "1.0.0",
        "icon": "zap",
        "icon_color": "#4A90E2",
    }
