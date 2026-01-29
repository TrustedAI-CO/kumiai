"""Integration tests for skill API endpoints."""

from uuid import uuid4

import pytest
from fastapi import status


class TestSkillsAPI:
    """Test skill API endpoints."""

    @pytest.mark.asyncio
    async def test_create_skill_success(self, client, tmp_skills_dir):
        """Test POST /api/v1/skills."""
        unique_id = uuid4().hex[:8]
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": f"Test Skill {unique_id}",
                "file_path": f"/test/skill-{unique_id}/",
                "description": "A test skill",
                "tags": ["test", "api"],
                "version": "1.0.0",
                "icon": "zap",
                "icon_color": "#4A90E2",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "test" in data["tags"]
        # NOTE: version field removed - filesystem handles versioning
        assert data["icon"] == "zap"
        assert data["icon_color"] == "#4A90E2"

        # Verify SKILL.md was created
        skill_id = data["id"]
        skill_md = tmp_skills_dir / skill_id / "SKILL.md"
        assert skill_md.exists()
        content = skill_md.read_text()
        assert "name:" in content
        # NOTE: version field removed - filesystem handles versioning

    @pytest.mark.asyncio
    async def test_get_skill_success(self, client, skill):
        """Test GET /api/v1/skills/{id}."""
        response = await client.get(f"/api/v1/skills/{skill.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(skill.id)

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, client):
        """Test getting non-existent skill."""
        response = await client.get("/api/v1/skills/nonexistent-skill-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_skills(self, client, skill):
        """Test GET /api/v1/skills."""
        response = await client.get("/api/v1/skills")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_search_skills_by_tags(self, client, skill):
        """Test GET /api/v1/skills/search."""
        response = await client.get("/api/v1/skills/search?tags=python&match_all=false")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_update_skill_success(self, client, skill):
        """Test PATCH /api/v1/skills/{id}."""
        response = await client.patch(
            f"/api/v1/skills/{skill.id}",
            json={"name": f"Updated Skill {uuid4().hex[:8]}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated Skill" in data["name"]

    @pytest.mark.asyncio
    async def test_delete_skill_success(self, client, skill):
        """Test DELETE /api/v1/skills/{id}."""
        response = await client.delete(f"/api/v1/skills/{skill.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_create_skill_without_file_path(self, client):
        """Test creating skill with auto-generated file_path from name."""
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": f"Auto Path Skill {uuid4().hex[:8]}",
                "description": "Testing auto path generation",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # file_path should now contain actual filesystem path
        assert "auto-path-skill-" in data["file_path"]
        assert data["file_path"].rstrip("/").endswith(data["id"])

    @pytest.mark.asyncio
    async def test_create_skill_with_custom_id(self, client):
        """Test creating skill with custom ID for file_path generation."""
        custom_id = f"custom-skill-{uuid4().hex[:8]}"
        response = await client.post(
            "/api/v1/skills",
            json={
                "id": custom_id,
                "name": f"Skill With Custom ID {uuid4().hex[:8]}",
                "description": "Testing custom ID path generation",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # file_path should now contain actual filesystem path ending with custom_id
        assert data["file_path"].rstrip("/").endswith(custom_id)
        assert custom_id in data["file_path"]

    @pytest.mark.asyncio
    async def test_create_skill_with_frontend_fields(self, client):
        """Test creating skill with frontend-specific fields."""
        response = await client.post(
            "/api/v1/skills",
            json={
                "id": f"frontend-skill-{uuid4().hex[:8]}",
                "name": f"Frontend Skill {uuid4().hex[:8]}",
                "description": "Has frontend fields",
                "category": "testing",
                "license": "MIT",
                "version": "1.0.0",
                "content": "# Test Skill\n\nThis is test content.",
                "icon": "zap",
                "iconColor": "#4A90E2",
                "tags": ["test", "frontend"],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"].startswith("Frontend Skill")
        assert data["description"] == "Has frontend fields"
        assert data["tags"] == ["test", "frontend"]

    @pytest.mark.asyncio
    async def test_create_skill_with_explicit_file_path(self, client):
        """Test that explicit file_path is respected for skill_id extraction."""
        unique_id = uuid4().hex[:8]
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": f"Custom Path Skill {unique_id}",
                "file_path": f"/custom/skill-{unique_id}/path/",
                "description": "Testing custom file path",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # The skill_id is extracted from the last component of the path
        # and file_path will be the actual filesystem path
        assert data["id"] == "path"
        assert "path" in data["file_path"]

    @pytest.mark.asyncio
    async def test_update_skill_with_put(self, client, skill):
        """Test updating skill using PUT method (frontend compatibility)."""
        response = await client.put(
            f"/api/v1/skills/{skill.id}",
            json={"name": f"Updated via PUT {uuid4().hex[:8]}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Updated via PUT" in data["name"]

    @pytest.mark.asyncio
    async def test_load_skill_content(self, client, skill):
        """Test GET /api/v1/skills/{id}/content - load SKILL.md for AI context."""
        response = await client.get(f"/api/v1/skills/{skill.id}/content")

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "# Test Skill" in content
        assert "---" in content  # YAML frontmatter marker

    @pytest.mark.asyncio
    async def test_load_skill_content_not_found(self, client):
        """Test loading content for non-existent skill."""
        response = await client.get("/api/v1/skills/nonexistent/content")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_load_supporting_doc(self, client, skill, tmp_skills_dir):
        """Test GET /api/v1/skills/{id}/docs/{doc_path} - load supporting docs."""
        # Create a supporting document
        skill_dir = tmp_skills_dir / skill.id
        doc_file = skill_dir / "REFERENCE.md"
        doc_file.write_text("# Reference Documentation\n\nThis is a reference doc.")

        response = await client.get(f"/api/v1/skills/{skill.id}/docs/REFERENCE.md")

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Reference Documentation" in content

    @pytest.mark.asyncio
    async def test_load_nested_supporting_doc(self, client, skill, tmp_skills_dir):
        """Test loading nested supporting docs."""
        # Create nested directory structure
        skill_dir = tmp_skills_dir / skill.id
        nested_dir = skill_dir / "docs" / "api"
        nested_dir.mkdir(parents=True, exist_ok=True)
        doc_file = nested_dir / "endpoints.md"
        doc_file.write_text("# API Endpoints\n\nEndpoint documentation.")

        response = await client.get(
            f"/api/v1/skills/{skill.id}/docs/docs/api/endpoints.md"
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Endpoint documentation" in content

    @pytest.mark.asyncio
    async def test_load_supporting_doc_path_traversal_blocked(self, client, skill):
        """Test that path traversal attempts are blocked."""
        response = await client.get(
            f"/api/v1/skills/{skill.id}/docs/../../../etc/passwd"
        )

        # FastAPI normalizes the path before reaching our handler, resulting in 404
        # This is actually better security - blocked at the framework level
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_import_skill_from_local_path(self, client, tmp_path):
        """Test importing a skill from a local filesystem path."""
        # Create a temporary skill directory
        source_dir = tmp_path / "test-import-skill"
        source_dir.mkdir()

        # Create SKILL.md with proper frontmatter
        skill_md = source_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: Imported Test Skill
description: A skill imported from local path
tags: [test, import]
icon: star
iconColor: "#FF6B6B"
---

# Imported Test Skill

This is a test skill imported from a local path.
"""
        )

        # Create additional files
        examples_md = source_dir / "examples.md"
        examples_md.write_text("# Examples\n\nExample usage of the skill.")

        # Import the skill
        response = await client.post(
            "/api/v1/skills/import",
            json={
                "source": str(source_dir),
                "skill_id": f"imported-test-{uuid4().hex[:8]}",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "success"
        assert "skill" in data
        assert data["skill"]["name"] == "Imported Test Skill"
        assert data["skill"]["description"] == "A skill imported from local path"
        assert "test" in data["skill"]["tags"]
        assert "import" in data["skill"]["tags"]
        assert data["skill"]["icon"] == "star"
        assert data["skill"]["icon_color"] == "#FF6B6B"

    @pytest.mark.asyncio
    async def test_import_skill_missing_skill_md(self, client, tmp_path):
        """Test that importing without SKILL.md fails."""
        # Create a directory without SKILL.md
        source_dir = tmp_path / "invalid-skill"
        source_dir.mkdir()

        response = await client.post(
            "/api/v1/skills/import",
            json={"source": str(source_dir)},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "SKILL.md not found" in response.text

    @pytest.mark.asyncio
    async def test_import_skill_invalid_frontmatter(self, client, tmp_path):
        """Test that importing with invalid frontmatter fails."""
        source_dir = tmp_path / "bad-frontmatter-skill"
        source_dir.mkdir()

        # Create SKILL.md with invalid frontmatter (missing name)
        skill_md = source_dir / "SKILL.md"
        skill_md.write_text(
            """---
description: Missing name field
---

# Skill content
"""
        )

        response = await client.post(
            "/api/v1/skills/import",
            json={"source": str(source_dir)},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "missing required fields" in response.text.lower()
            or "name" in response.text.lower()
        )

    @pytest.mark.asyncio
    async def test_import_skill_nonexistent_path(self, client):
        """Test that importing from non-existent path fails."""
        response = await client.post(
            "/api/v1/skills/import",
            json={"source": "/nonexistent/path/to/skill"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "does not exist" in response.text.lower()
            or "not found" in response.text.lower()
        )
