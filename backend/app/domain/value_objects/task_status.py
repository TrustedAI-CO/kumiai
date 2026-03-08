"""TaskStatus value object."""

from enum import Enum


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"
