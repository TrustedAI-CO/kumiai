"""Unit tests for FileService."""

import tempfile
from pathlib import Path

import pytest

from app.core.exceptions import FileSystemError, ValidationError
from app.infrastructure.filesystem import FileService


class TestFileService:
    """Test FileService operations."""

    @pytest.fixture
    def file_service(self):
        """Create FileService instance."""
        return FileService()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_validate_path_success(self, file_service, temp_dir):
        """Test path validation with valid path."""
        file_path = "test.json"
        result = file_service.validate_path(temp_dir, file_path)

        # Both paths should resolve to the same location
        expected = (temp_dir / file_path).resolve()
        assert result == expected

    def test_validate_path_traversal_attack(self, file_service, temp_dir):
        """Test path validation blocks traversal attack."""
        file_path = "../../../etc/passwd"

        with pytest.raises(ValidationError) as exc_info:
            file_service.validate_path(temp_dir, file_path)

        assert "outside allowed directory" in str(exc_info.value)

    def test_validate_path_empty(self, file_service, temp_dir):
        """Test path validation rejects empty path."""
        with pytest.raises(ValidationError) as exc_info:
            file_service.validate_path(temp_dir, "")

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_extension_allowed(self, file_service):
        """Test file extension validation with allowed types."""
        for ext in [".json", ".yaml", ".yml", ".txt", ".md"]:
            # Should not raise
            file_service.validate_extension(f"test{ext}")

    def test_validate_extension_not_allowed(self, file_service):
        """Test file extension validation rejects disallowed types."""
        with pytest.raises(ValidationError) as exc_info:
            file_service.validate_extension("test.exe")

        assert "not allowed" in str(exc_info.value)

    def test_validate_extension_no_extension(self, file_service):
        """Test file extension validation rejects files without extension."""
        with pytest.raises(ValidationError) as exc_info:
            file_service.validate_extension("test")

        assert "must have an extension" in str(exc_info.value)

    def test_is_protected_file(self, file_service):
        """Test protected file detection."""
        assert file_service.is_protected_file("agent.json")
        assert file_service.is_protected_file("skill.json")
        assert file_service.is_protected_file("subdir/agent.json")
        assert not file_service.is_protected_file("other.json")

    @pytest.mark.asyncio
    async def test_list_files_empty_directory(self, file_service, temp_dir):
        """Test listing files in empty directory."""
        files = await file_service.list_files(temp_dir)

        assert files == []

    @pytest.mark.asyncio
    async def test_list_files_with_files(self, file_service, temp_dir):
        """Test listing files with content."""
        # Create test files
        (temp_dir / "file1.json").write_text('{"test": 1}')
        (temp_dir / "file2.txt").write_text("test")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file3.yaml").write_text("test: value")

        files = await file_service.list_files(temp_dir)

        # Should include all files and directories
        paths = [f.path for f in files]
        assert "file1.json" in paths
        assert "file2.txt" in paths
        assert "subdir" in paths
        assert str(Path("subdir") / "file3.yaml") in paths

    @pytest.mark.asyncio
    async def test_list_files_nonexistent_directory(self, file_service, temp_dir):
        """Test listing files in nonexistent directory."""
        nonexistent = temp_dir / "nonexistent"
        files = await file_service.list_files(nonexistent)

        assert files == []

    @pytest.mark.asyncio
    async def test_list_files_skips_hidden(self, file_service, temp_dir):
        """Test that hidden files are skipped."""
        (temp_dir / ".hidden").write_text("hidden")
        (temp_dir / "visible.txt").write_text("visible")

        files = await file_service.list_files(temp_dir)
        paths = [f.path for f in files]

        assert "visible.txt" in paths
        assert ".hidden" not in paths

    @pytest.mark.asyncio
    async def test_read_file_success(self, file_service, temp_dir):
        """Test reading file content."""
        test_file = temp_dir / "test.json"
        test_content = '{"key": "value"}'
        test_file.write_text(test_content)

        content, size = await file_service.read_file(test_file)

        assert content == test_content
        assert size == len(test_content)

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, file_service, temp_dir):
        """Test reading nonexistent file."""
        nonexistent = temp_dir / "nonexistent.json"

        with pytest.raises(FileSystemError) as exc_info:
            await file_service.read_file(nonexistent)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_read_file_is_directory(self, file_service, temp_dir):
        """Test reading a directory fails."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        with pytest.raises(FileSystemError) as exc_info:
            await file_service.read_file(subdir)

        assert "not a file" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_write_file_success(self, file_service, temp_dir):
        """Test writing file content."""
        test_file = temp_dir / "test.json"
        test_content = '{"key": "value"}'

        size = await file_service.write_file(test_file, test_content)

        assert size == len(test_content)
        assert test_file.read_text() == test_content

    @pytest.mark.asyncio
    async def test_write_file_creates_directories(self, file_service, temp_dir):
        """Test writing file creates parent directories."""
        test_file = temp_dir / "subdir" / "nested" / "test.json"
        test_content = '{"key": "value"}'

        size = await file_service.write_file(test_file, test_content)

        assert size == len(test_content)
        assert test_file.exists()
        assert test_file.read_text() == test_content

    @pytest.mark.asyncio
    async def test_write_file_overwrites(self, file_service, temp_dir):
        """Test writing file overwrites existing content."""
        test_file = temp_dir / "test.json"
        test_file.write_text("old content")

        new_content = "new content"
        size = await file_service.write_file(test_file, new_content)

        assert size == len(new_content)
        assert test_file.read_text() == new_content

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_service, temp_dir):
        """Test deleting file."""
        test_file = temp_dir / "test.json"
        test_file.write_text("content")

        await file_service.delete_file(test_file)

        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_directory_success(self, file_service, temp_dir):
        """Test deleting directory."""
        test_dir = temp_dir / "subdir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        await file_service.delete_file(test_dir)

        assert not test_dir.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, file_service, temp_dir):
        """Test deleting nonexistent file."""
        nonexistent = temp_dir / "nonexistent.json"

        with pytest.raises(FileSystemError) as exc_info:
            await file_service.delete_file(nonexistent)

        assert "not found" in str(exc_info.value)
