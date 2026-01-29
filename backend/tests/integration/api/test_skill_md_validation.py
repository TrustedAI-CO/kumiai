"""Integration tests for SKILL.md YAML frontmatter validation."""

import pytest
from fastapi import status


class TestSkillMdValidation:
    """Test SKILL.md validation through API endpoints."""

    @pytest.mark.asyncio
    async def test_update_skill_md_with_valid_frontmatter(self, client, skill):
        """Test updating SKILL.md with valid frontmatter succeeds."""
        valid_content = """---
name: Updated Skill
description: Updated description
tags: [python, testing]
icon: terminal
iconColor: "#00FF00"
---

# Updated Skill

This is the updated content.
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": valid_content,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == valid_content

    @pytest.mark.asyncio
    async def test_update_skill_md_without_frontmatter_fails(self, client, skill):
        """Test updating SKILL.md without frontmatter fails."""
        invalid_content = """# Skill Without Frontmatter

This has no YAML frontmatter.
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": invalid_content,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "must start with YAML frontmatter" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_update_skill_md_with_invalid_yaml_fails(self, client, skill):
        """Test updating SKILL.md with invalid YAML syntax fails."""
        invalid_content = """---
name: Test
invalid: yaml: syntax: here
---
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": invalid_content,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid YAML syntax" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_update_skill_md_missing_name_fails(self, client, skill):
        """Test updating SKILL.md without required 'name' field fails."""
        invalid_content = """---
description: A skill without name
tags: [test]
---
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": invalid_content,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "missing required fields: name" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_update_skill_md_empty_name_fails(self, client, skill):
        """Test updating SKILL.md with empty name field fails."""
        invalid_content = """---
name: ""
description: Test
---
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": invalid_content,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "'name' field cannot be empty" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_update_skill_md_invalid_tags_type_fails(self, client, skill):
        """Test updating SKILL.md with non-list tags fails."""
        invalid_content = """---
name: Test Skill
tags: "not a list"
---
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": invalid_content,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "'tags' field must be a list" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_update_other_md_files_no_validation(self, client, skill):
        """Test updating other .md files doesn't require frontmatter."""
        # Create a regular markdown file without frontmatter
        content = """# Regular Markdown File

This is just a regular markdown file, not SKILL.md.
No frontmatter required.
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "README.md",
                "content": content,
            },
        )

        # Should succeed - validation only applies to SKILL.md
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_update_skill_md_case_insensitive(self, client, skill):
        """Test SKILL.md validation is case-insensitive for filename."""
        invalid_content = """# No frontmatter"""

        # Test with lowercase
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "skill.md",
                "content": invalid_content,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test with mixed case
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "Skill.MD",
                "content": invalid_content,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_update_skill_md_minimal_valid_frontmatter(self, client, skill):
        """Test SKILL.md with only required 'name' field succeeds."""
        minimal_content = """---
name: Minimal Skill
---

# Minimal content
"""
        response = await client.put(
            f"/api/v1/skills/{skill.id}/files/content",
            json={
                "file_path": "SKILL.md",
                "content": minimal_content,
            },
        )

        assert response.status_code == status.HTTP_200_OK
