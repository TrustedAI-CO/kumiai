"""User profile DTOs."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseDTO


class UserProfileResponse(BaseDTO):
    """User profile response DTO."""

    id: UUID
    avatar: Optional[str] = Field(None, description="Avatar identifier or URL")
    description: Optional[str] = Field(None, description="User description")
    preferences: Optional[dict] = Field(None, description="User preferences")


class UpdateUserProfileRequest(BaseDTO):
    """Update user profile request DTO."""

    avatar: Optional[str] = Field(None, description="Avatar identifier or URL")
    description: Optional[str] = Field(None, description="User description")
    preferences: Optional[dict] = Field(None, description="User preferences")
