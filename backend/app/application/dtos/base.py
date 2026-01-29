"""Base DTO classes."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseDTO(BaseModel):
    """Base class for all DTOs."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both alias and field name
    )


class TimestampedDTO(BaseDTO):
    """Base DTO with timestamps."""

    created_at: datetime
    updated_at: datetime


class PaginatedResult(BaseModel, Generic[T]):
    """Generic paginated result wrapper."""

    items: List[T]
    next_cursor: Optional[str] = None
    has_more: bool = False
    total_count: Optional[int] = None
