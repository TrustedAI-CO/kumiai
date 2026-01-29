"""Onboarding API endpoints for setting up demo templates."""

import json
import shutil
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.api.dependencies import get_user_profile_service, get_project_service
from app.application.services.user_profile_service import UserProfileService
from app.application.services.project_service import ProjectService
from app.application.dtos.requests import CreateProjectRequest

router = APIRouter()

# Get paths
EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"
SKILLS_EXAMPLES = EXAMPLES_DIR / "skills"
AGENTS_EXAMPLES = EXAMPLES_DIR / "agents"
TEMPLATES_DIR = EXAMPLES_DIR / "templates"


class SetupDemoRequest(BaseModel):
    """Request to setup a demo team."""

    team: Literal["dev", "research", "content"]


class SetupDemoResponse(BaseModel):
    """Response from demo setup."""

    project_name: str
    skills_created: list[str]
    agents_created: list[str]
    message: str


class OnboardingStatusResponse(BaseModel):
    """Onboarding status response."""

    completed: bool
    team: str | None = None


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    profile_service: UserProfileService = Depends(get_user_profile_service),
) -> OnboardingStatusResponse:
    """
    Get onboarding completion status.

    Returns whether the user has completed onboarding and which team they chose.
    """
    profile = await profile_service.get_profile()
    user_settings = profile.get("settings", {})

    return OnboardingStatusResponse(
        completed=user_settings.get("onboarding_completed", False),
        team=user_settings.get("onboarding_team"),
    )


@router.post("/reset")
async def reset_onboarding(
    profile_service: UserProfileService = Depends(get_user_profile_service),
) -> dict:
    """
    Reset onboarding status.

    Allows the user to go through onboarding again.
    """
    profile = await profile_service.get_profile()
    user_settings = profile.get("settings", {})
    user_settings["onboarding_completed"] = False
    user_settings.pop("onboarding_team", None)

    await profile_service.update_profile(user_settings)

    return {"message": "Onboarding reset successfully"}


@router.post("/setup", response_model=SetupDemoResponse)
async def setup_demo(
    request: SetupDemoRequest,
    profile_service: UserProfileService = Depends(get_user_profile_service),
    project_service: ProjectService = Depends(get_project_service),
) -> SetupDemoResponse:
    """
    Set up a demo team with example skills, agents, and project.

    Copies example skills and agents to ~/.kumiai and creates a demo project.
    """
    # Map team names to template files
    template_files = {
        "dev": "dev-team.json",
        "research": "research-team.json",
        "content": "content-team.json",
    }

    template_file = TEMPLATES_DIR / template_files[request.team]

    # Load template
    try:
        with open(template_file) as f:
            template = json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Template file not found: {template_file}"
        )

    # Ensure target directories exist
    skills_dir = Path(settings.skills_dir)
    agents_dir = Path(settings.agents_dir)
    skills_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Copy skills
    skills_created = []
    for skill_name in template["skills"]:
        source = SKILLS_EXAMPLES / skill_name
        target = skills_dir / skill_name

        if source.exists():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            skills_created.append(skill_name)

    # Copy agents
    agents_created = []
    for agent_name in template["agents"]:
        source = AGENTS_EXAMPLES / agent_name
        target = agents_dir / agent_name

        if source.exists():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
            agents_created.append(agent_name)

    # Create demo project with team members
    project_data = template.get("project", {})
    project = await project_service.create_project(
        CreateProjectRequest(
            name=project_data.get("name", "Demo Project"),
            description=project_data.get("description", ""),
            pm_agent_id="product-manager",
            team_member_ids=agents_created,
        )
    )

    # Mark onboarding as completed
    profile = await profile_service.get_profile()
    user_settings = profile.get("settings", {})
    user_settings["onboarding_completed"] = True
    user_settings["onboarding_team"] = request.team

    await profile_service.update_profile(user_settings)

    return SetupDemoResponse(
        project_name=template["project"]["name"],
        skills_created=skills_created,
        agents_created=agents_created,
        message=f"Successfully set up {template['name']}! Skills and agents are ready to use.",
    )
