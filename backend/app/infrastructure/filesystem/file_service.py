"""File system service for managing agent and skill files."""

import shutil
from pathlib import Path
from typing import List

import aiofiles

from app.core.exceptions import FileSystemError, ValidationError
from app.domain.value_objects import FileInfo


class FileService:
    """Service for file system operations with security and validation.

    Provides safe file operations with:
    - Path traversal attack prevention
    - File type validation (whitelist)
    - Async I/O operations
    - Error handling with domain exceptions
    """

    # Allowed file extensions for security
    ALLOWED_EXTENSIONS = {".json", ".yaml", ".yml", ".txt", ".md"}

    # Protected files that cannot be deleted
    PROTECTED_FILES = {"agent.json", "skill.json"}

    def validate_path(self, base_path: Path, file_path: str) -> Path:
        """Validate and resolve file path to prevent path traversal attacks.

        Args:
            base_path: Base directory (e.g., agent directory)
            file_path: Relative path provided by user

        Returns:
            Resolved absolute path

        Raises:
            ValidationError: If path is invalid or attempts traversal
        """
        if not file_path or file_path.strip() == "":
            raise ValidationError("File path cannot be empty")

        try:
            # Resolve both paths to absolute
            full_path = (base_path / file_path).resolve()
            base_resolved = base_path.resolve()

            # Check if full_path is within base_path (prevents ../ attacks)
            if not full_path.is_relative_to(base_resolved):
                raise ValidationError(
                    f"Invalid file path: {file_path} is outside allowed directory"
                )

            return full_path

        except (ValueError, OSError) as e:
            raise ValidationError(f"Invalid file path: {str(e)}")

    def validate_extension(self, file_path: str) -> None:
        """Validate file extension against whitelist.

        Args:
            file_path: File path to validate

        Raises:
            ValidationError: If file extension is not allowed
        """
        ext = Path(file_path).suffix.lower()

        if not ext:
            raise ValidationError("File must have an extension")

        if ext not in self.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            raise ValidationError(
                f"File type '{ext}' not allowed. Allowed types: {allowed}"
            )

    def is_protected_file(self, file_path: str) -> bool:
        """Check if file is protected from deletion.

        Args:
            file_path: Relative file path

        Returns:
            True if file is protected
        """
        file_name = Path(file_path).name
        return file_name in self.PROTECTED_FILES

    async def list_files(self, base_path: Path) -> List[FileInfo]:
        """List all files and directories recursively.

        Args:
            base_path: Base directory to list from

        Returns:
            List of FileInfo objects sorted by path

        Raises:
            FileSystemError: If directory cannot be read
        """
        if not base_path.exists():
            return []

        if not base_path.is_dir():
            raise FileSystemError(f"{base_path} is not a directory")

        try:
            files: List[FileInfo] = []

            # Use rglob for recursive traversal
            for path in sorted(base_path.rglob("*")):
                # Skip hidden files and directories (relative to base_path)
                try:
                    relative_path = path.relative_to(base_path)
                    if any(part.startswith(".") for part in relative_path.parts):
                        continue
                except ValueError:
                    # Path is not relative to base_path, skip it
                    continue

                try:
                    info = FileInfo.from_path(base_path, path)
                    files.append(info)
                except OSError:
                    # Skip files that can't be accessed
                    continue

            return files

        except OSError as e:
            raise FileSystemError(f"Failed to list files in {base_path}: {str(e)}")

    async def read_file(self, full_path: Path) -> tuple[str, int]:
        """Read file content asynchronously.

        Args:
            full_path: Absolute path to file

        Returns:
            Tuple of (content, size)

        Raises:
            FileSystemError: If file doesn't exist or can't be read
        """
        if not full_path.exists():
            raise FileSystemError(f"File not found: {full_path}")

        if not full_path.is_file():
            raise FileSystemError(f"Path is not a file: {full_path}")

        try:
            async with aiofiles.open(full_path, mode="r", encoding="utf-8") as f:
                content = await f.read()
                size = full_path.stat().st_size
                return content, size

        except OSError as e:
            raise FileSystemError(f"Failed to read file {full_path}: {str(e)}")

    async def write_file(self, full_path: Path, content: str) -> int:
        """Write file content asynchronously.

        Args:
            full_path: Absolute path to file
            content: Content to write

        Returns:
            File size in bytes

        Raises:
            FileSystemError: If file can't be written
        """
        try:
            # Create parent directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            async with aiofiles.open(full_path, mode="w", encoding="utf-8") as f:
                await f.write(content)

            # Return file size
            return full_path.stat().st_size

        except OSError as e:
            raise FileSystemError(f"Failed to write file {full_path}: {str(e)}")

    async def delete_file(self, full_path: Path) -> None:
        """Delete file or directory.

        Args:
            full_path: Absolute path to file or directory

        Raises:
            FileSystemError: If file/directory doesn't exist or can't be deleted
        """
        if not full_path.exists():
            raise FileSystemError(f"File not found: {full_path}")

        try:
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                raise FileSystemError(f"Cannot delete: {full_path}")

        except OSError as e:
            raise FileSystemError(f"Failed to delete {full_path}: {str(e)}")
