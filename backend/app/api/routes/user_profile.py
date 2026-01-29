"""User profile API routes."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_user_profile_service
from app.application.dtos import UpdateUserProfileRequest, UserProfileResponse
from app.application.services import UserProfileService

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    service: UserProfileService = Depends(get_user_profile_service),
):
    """Get the default user profile."""
    profile = await service.get_profile()
    return UserProfileResponse(**profile)


@router.post("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    request: UpdateUserProfileRequest,
    service: UserProfileService = Depends(get_user_profile_service),
):
    """Create or update the user profile."""
    profile = await service.update_profile(
        avatar=request.avatar,
        description=request.description,
        preferences=request.preferences,
    )
    return UserProfileResponse(**profile)
