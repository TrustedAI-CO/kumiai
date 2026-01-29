"""merge migration heads

Revision ID: ddecbf33ef2e
Revises: 5e22d374774c, add_tool_call_role
Create Date: 2026-01-22 11:59:54.776823

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "ddecbf33ef2e"
down_revision: Union[str, None] = ("5e22d374774c", "add_tool_call_role")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
