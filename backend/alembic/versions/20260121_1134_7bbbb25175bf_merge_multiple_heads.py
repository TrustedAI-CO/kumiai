"""merge_multiple_heads

Revision ID: 7bbbb25175bf
Revises: xyz789abc123, def456ghi789, fix_path_constraint
Create Date: 2026-01-21 11:34:04.692259

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "7bbbb25175bf"
down_revision: Union[str, None] = (
    "xyz789abc123",
    "def456ghi789",
    "fix_path_constraint",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
