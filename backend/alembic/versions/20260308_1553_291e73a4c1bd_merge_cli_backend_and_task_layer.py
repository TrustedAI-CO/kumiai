"""merge_cli_backend_and_task_layer

Revision ID: 291e73a4c1bd
Revises: 20260305_0000, add_session_summary_20260308
Create Date: 2026-03-08 15:53:22.819217

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "291e73a4c1bd"
down_revision: Union[str, None] = ("20260305_0000", "add_task_layer_20260308")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
