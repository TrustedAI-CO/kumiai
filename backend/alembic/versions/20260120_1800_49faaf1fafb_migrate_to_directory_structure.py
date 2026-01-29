"""Migrate to directory structure

Revision ID: 49faaf1fafb
Revises: 496b2a11770e
Create Date: 2026-01-20 18:00:00.000000

"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "49faaf1fafb"
down_revision: Union[str, None] = "496b2a11770e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate character and skill file paths from file-based to directory-based structure.

    For each character/skill:
    - Old: /path/to/character.json
    - New: /path/to/character/ (directory) with character.json inside
    """
    conn = op.get_bind()

    # Migrate characters
    characters = conn.execute(
        text("SELECT id, file_path FROM characters WHERE deleted_at IS NULL")
    ).fetchall()

    for character_id, file_path in characters:
        if file_path and file_path.strip():
            path = Path(file_path)

            # Only migrate if it's a file path (ends with .json)
            if path.suffix == ".json":
                # New directory path: /path/to/character/
                new_dir_path = path.parent / path.stem

                # Update database to point to directory
                conn.execute(
                    text(
                        "UPDATE characters SET file_path = :new_path WHERE id = :char_id"
                    ),
                    {"new_path": str(new_dir_path) + "/", "char_id": character_id},
                )

                # Note: Actual file movement should be done separately via a script
                # This migration only updates the database paths

    # Migrate skills
    skills = conn.execute(
        text("SELECT id, file_path FROM skills WHERE deleted_at IS NULL")
    ).fetchall()

    for skill_id, file_path in skills:
        if file_path and file_path.strip():
            path = Path(file_path)

            # Only migrate if it's a file path (ends with .json)
            if path.suffix == ".json":
                # New directory path: /path/to/skill/
                new_dir_path = path.parent / path.stem

                # Update database to point to directory
                conn.execute(
                    text(
                        "UPDATE skills SET file_path = :new_path WHERE id = :skill_id"
                    ),
                    {"new_path": str(new_dir_path) + "/", "skill_id": skill_id},
                )


def downgrade() -> None:
    """
    Rollback directory-based structure to file-based structure.

    For each character/skill:
    - Old: /path/to/character/ (directory)
    - New: /path/to/character.json (file)
    """
    conn = op.get_bind()

    # Rollback characters
    characters = conn.execute(
        text("SELECT id, file_path FROM characters WHERE deleted_at IS NULL")
    ).fetchall()

    for character_id, file_path in characters:
        if file_path and file_path.strip():
            path = Path(file_path.rstrip("/"))

            # If it's a directory path, convert back to file
            if not path.suffix:
                new_file_path = path.parent / f"{path.name}.json"

                conn.execute(
                    text(
                        "UPDATE characters SET file_path = :new_path WHERE id = :char_id"
                    ),
                    {"new_path": str(new_file_path), "char_id": character_id},
                )

    # Rollback skills
    skills = conn.execute(
        text("SELECT id, file_path FROM skills WHERE deleted_at IS NULL")
    ).fetchall()

    for skill_id, file_path in skills:
        if file_path and file_path.strip():
            path = Path(file_path.rstrip("/"))

            # If it's a directory path, convert back to file
            if not path.suffix:
                new_file_path = path.parent / f"{path.name}.json"

                conn.execute(
                    text(
                        "UPDATE skills SET file_path = :new_path WHERE id = :skill_id"
                    ),
                    {"new_path": str(new_file_path), "skill_id": skill_id},
                )
