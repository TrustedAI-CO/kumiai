"""Fixtures for creating test database models."""

from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Skill as SkillEntity
from app.infrastructure.database.models import (
    Project,
    Session,
    Message,
    ActivityLog,
    UserProfile,
)
from app.domain.value_objects import (
    SessionType,
    SessionStatus,
    MessageRole,
    EventType,
)


# NOTE: character fixture removed - Characters are now file-based (agents)


@pytest.fixture
async def project(db_session: AsyncSession) -> Project:
    """Create a test project with unique name."""
    proj = Project(
        name=f"Test Project {uuid4().hex[:8]}",
        description="Test project description",
        pm_agent_id="test-pm-agent",
        path=f"/test/projects/test_{uuid4().hex[:8]}",
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)
    return proj


@pytest.fixture
async def session(db_session: AsyncSession, project: Project) -> Session:
    """Create a test session."""
    sess = Session(
        agent_id="test-agent",
        project_id=project.id,
        session_type=SessionType.PM.value,
        status=SessionStatus.IDLE.value,
        claude_session_id="test_session_123",
        context={"test": "context"},
    )
    db_session.add(sess)
    await db_session.commit()
    await db_session.refresh(sess)
    return sess


@pytest.fixture
async def message(db_session: AsyncSession, session: Session) -> Message:
    """Create a test message."""
    msg = Message(
        session_id=session.id,
        role=MessageRole.USER.value,
        content="Test message content",
        sequence=0,
        meta={"test": "metadata"},
    )
    db_session.add(msg)
    await db_session.commit()
    await db_session.refresh(msg)
    return msg


@pytest.fixture
def skill(tmp_skills_dir: Path) -> SkillEntity:
    """Create a test skill with file-based storage.

    Args:
        tmp_skills_dir: Temporary skills directory fixture

    Returns:
        Skill entity instance
    """
    skill_id = f"test-skill-{uuid4().hex[:8]}"
    skill_dir = tmp_skills_dir / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create SKILL.md with frontmatter
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        f"""---
name: Test Skill {uuid4().hex[:8]}
description: Test skill description
tags: [test, skill]
icon: terminal
iconColor: "#00FF00"
version: 1.0.0
---

# Test Skill

This is a test skill for testing purposes.
"""
    )

    # Return a Skill entity
    return SkillEntity(
        id=skill_id,
        name=f"Test Skill {uuid4().hex[:8]}",
        file_path=f"/skills/{skill_id}/",
        description="Test skill description",
        tags=["test", "skill"],
        icon="terminal",
        icon_color="#00FF00",
    )


@pytest.fixture
async def activity_log(db_session: AsyncSession, session: Session) -> ActivityLog:
    """Create a test activity log."""
    log = ActivityLog(
        session_id=session.id,
        event_type=EventType.SESSION_CREATED.value,
        event_data={"test": "data"},
    )
    db_session.add(log)
    await db_session.commit()
    await db_session.refresh(log)
    return log


@pytest.fixture
async def user_profile(db_session: AsyncSession) -> UserProfile:
    """Create a test user profile."""
    profile = UserProfile(
        settings={"theme": "dark", "language": "en"},
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile
