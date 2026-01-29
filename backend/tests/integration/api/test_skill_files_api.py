"""Integration tests for skill file API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestSkillFilesAPI:
    """Test skill file API endpoints."""

    @pytest.fixture
    async def skill_with_files(self, client, tmp_skills_dir):
        """Create a skill with test files in the skill directory."""
        # Create skill via API (it will be created in tmp_skills_dir by the test client)
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": f"Test Skill {uuid4().hex[:8]}",
                "description": "Test skill",
                "tags": ["test"],
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        skill_data = response.json()
        skill_id = skill_data["id"]

        # Construct actual filesystem path using tmp_skills_dir
        skill_path = tmp_skills_dir / skill_id

        # Create test files in the actual skill directory
        (skill_path / "config.json").write_text('{"name": "test"}')
        (skill_path / "config.yaml").write_text("key: value")
        (skill_path / "docs").mkdir()
        (skill_path / "docs" / "readme.md").write_text("# Documentation")

        yield skill_id, skill_path

    @pytest.mark.asyncio
    async def test_list_skill_files(self, client, skill_with_files):
        """Test GET /api/v1/skills/{id}/files."""
        skill_id, temp_path = skill_with_files

        response = await client.get(f"/api/v1/skills/{skill_id}/files")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # Check files are listed (including SKILL.md created by API)
        paths = [f["path"] for f in data]
        assert "SKILL.md" in paths
        assert "config.json" in paths
        assert "config.yaml" in paths
        assert "docs" in paths

    @pytest.mark.asyncio
    async def test_list_skill_files_not_found(self, client):
        """Test listing files for non-existent skill."""
        response = await client.get(f"/api/v1/skills/{uuid4()}/files")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_skill_file_content(self, client, skill_with_files):
        """Test GET /api/v1/skills/{id}/files/content."""
        skill_id, temp_path = skill_with_files

        response = await client.get(
            f"/api/v1/skills/{skill_id}/files/content",
            params={"file_path": "config.yaml"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_path"] == "config.yaml"
        assert "key: value" in data["content"]
        assert data["size"] > 0

    @pytest.mark.asyncio
    async def test_get_skill_file_content_not_found(self, client, skill_with_files):
        """Test getting non-existent file."""
        skill_id, temp_path = skill_with_files

        response = await client.get(
            f"/api/v1/skills/{skill_id}/files/content",
            params={"file_path": "nonexistent.txt"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_skill_file_content_invalid_extension(
        self, client, skill_with_files
    ):
        """Test getting file with invalid extension."""
        skill_id, temp_path = skill_with_files

        # Create file with invalid extension
        (temp_path / "binary.bin").write_text("binary data")

        response = await client.get(
            f"/api/v1/skills/{skill_id}/files/content",
            params={"file_path": "binary.bin"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_skill_file_content_path_traversal(
        self, client, skill_with_files
    ):
        """Test path traversal attack is blocked."""
        skill_id, temp_path = skill_with_files

        response = await client.get(
            f"/api/v1/skills/{skill_id}/files/content",
            params={"file_path": "../../etc/hosts"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_update_skill_file_content(self, client, skill_with_files):
        """Test PUT /api/v1/skills/{id}/files/content."""
        skill_id, temp_path = skill_with_files

        new_content = "updated: configuration"
        response = await client.put(
            f"/api/v1/skills/{skill_id}/files/content",
            json={
                "file_path": "config.yaml",
                "content": new_content,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_path"] == "config.yaml"
        assert data["content"] == new_content

        # Verify file was actually updated
        assert (temp_path / "config.yaml").read_text() == new_content

    @pytest.mark.asyncio
    async def test_update_skill_file_content_create_new(self, client, skill_with_files):
        """Test creating new file."""
        skill_id, temp_path = skill_with_files

        response = await client.put(
            f"/api/v1/skills/{skill_id}/files/content",
            json={
                "file_path": "new_config.json",
                "content": '{"new": "config"}',
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify file was created
        assert (temp_path / "new_config.json").exists()
        assert '{"new": "config"}' in (temp_path / "new_config.json").read_text()

    @pytest.mark.asyncio
    async def test_update_skill_file_content_nested(self, client, skill_with_files):
        """Test creating file in nested directory."""
        skill_id, temp_path = skill_with_files

        response = await client.put(
            f"/api/v1/skills/{skill_id}/files/content",
            json={
                "file_path": "examples/advanced/example.yaml",
                "content": "example: data",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify nested file was created
        nested_file = temp_path / "examples" / "advanced" / "example.yaml"
        assert nested_file.exists()

    @pytest.mark.asyncio
    async def test_update_skill_file_content_invalid_extension(
        self, client, skill_with_files
    ):
        """Test updating file with invalid extension."""
        skill_id, temp_path = skill_with_files

        response = await client.put(
            f"/api/v1/skills/{skill_id}/files/content",
            json={
                "file_path": "malicious.py",
                "content": "import os; os.system('rm -rf /')",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_delete_skill_file(self, client, skill_with_files):
        """Test DELETE /api/v1/skills/{id}/files."""
        skill_id, temp_path = skill_with_files

        # Create a file to delete
        test_file = temp_path / "temp.txt"
        test_file.write_text("temporary")

        response = await client.delete(
            f"/api/v1/skills/{skill_id}/files",
            params={"file_path": "temp.txt"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify file was deleted
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_skill_file_not_found(self, client, skill_with_files):
        """Test deleting non-existent file."""
        skill_id, temp_path = skill_with_files

        response = await client.delete(
            f"/api/v1/skills/{skill_id}/files",
            params={"file_path": "missing.txt"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_skill_file_protected(self, client, skill_with_files):
        """Test deleting protected file is blocked."""
        skill_id, temp_path = skill_with_files

        response = await client.delete(
            f"/api/v1/skills/{skill_id}/files",
            params={"file_path": "SKILL.md"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify file still exists
        assert (temp_path / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_delete_skill_md_protected(self, client, skill_with_files):
        """Test deleting SKILL.md is blocked (file-based system)."""
        skill_id, temp_path = skill_with_files

        # Create SKILL.md
        (temp_path / "SKILL.md").write_text("# Skill")

        response = await client.delete(
            f"/api/v1/skills/{skill_id}/files",
            params={"file_path": "SKILL.md"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Verify file still exists
        assert (temp_path / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_delete_skill_directory(self, client, skill_with_files):
        """Test deleting directory."""
        skill_id, temp_path = skill_with_files

        response = await client.delete(
            f"/api/v1/skills/{skill_id}/files",
            params={"file_path": "docs"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify directory was deleted
        assert not (temp_path / "docs").exists()
