"""Repository implementations."""

from app.infrastructure.database.repositories.message_repository import (
    MessageRepositoryImpl,
)
from app.infrastructure.database.repositories.project_repository import (
    ProjectRepositoryImpl,
)
from app.infrastructure.database.repositories.session_repository import (
    SessionRepositoryImpl,
)
from app.infrastructure.database.repositories.user_profile_repository import (
    PostgresUserProfileRepository,
)

# NOTE: SkillRepositoryImpl removed - Skills are now file-based
# See: app.infrastructure.filesystem.FileBasedSkillRepository

# NOTE: CharacterRepositoryImpl removed - Characters are now file-based (agents)
# See: app.infrastructure.filesystem.FileBasedAgentRepository

__all__ = [
    "MessageRepositoryImpl",
    "ProjectRepositoryImpl",
    "SessionRepositoryImpl",
    "PostgresUserProfileRepository",
]
