"""File information value object."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileInfo:
    """Represents file information for an agent or skill resource.

    This value object encapsulates metadata about files in the filesystem,
    providing a domain-friendly representation separate from filesystem paths.
    """

    path: str
    name: str
    size: int
    is_directory: bool
    modified_at: datetime

    @classmethod
    def from_path(cls, base_path: Path, file_path: Path) -> "FileInfo":
        """Create FileInfo from filesystem path.

        Args:
            base_path: Base directory path (e.g., agent directory)
            file_path: Absolute path to the file or directory

        Returns:
            FileInfo instance with metadata from the filesystem

        Raises:
            OSError: If file stat operation fails
        """
        stat = file_path.stat()
        relative_path = file_path.relative_to(base_path)

        return cls(
            path=str(relative_path),
            name=file_path.name,
            size=stat.st_size if file_path.is_file() else 0,
            is_directory=file_path.is_dir(),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )
