"""Unit tests for SkillService YAML frontmatter validation."""

from unittest.mock import AsyncMock

import pytest

from app.application.services.skill_service import SkillService
from app.core.exceptions import ValidationError


@pytest.fixture
def skill_service():
    """Create SkillService with mocked dependencies."""
    return SkillService(
        skill_repo=AsyncMock(),
        file_service=AsyncMock(),
    )


class TestSkillMdValidation:
    """Test SKILL.md YAML frontmatter validation."""

    def test_valid_skill_md_with_all_fields(self, skill_service):
        """Test validation passes with valid frontmatter including all fields."""
        content = """---
name: Test Skill
description: A test skill for validation
tags: [python, testing]
icon: zap
iconColor: "#4A90E2"
---

# Test Skill

This is the skill content.
"""
        # Should not raise
        skill_service._validate_skill_md_frontmatter(content)

    def test_valid_skill_md_minimal_required_fields(self, skill_service):
        """Test validation passes with only required fields."""
        content = """---
name: Test Skill
---

# Minimal Skill
"""
        # Should not raise
        skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_no_frontmatter(self, skill_service):
        """Test validation fails when frontmatter is missing."""
        content = """# Test Skill

No frontmatter here.
"""
        with pytest.raises(ValidationError, match="must start with YAML frontmatter"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_incomplete_frontmatter_markers(self, skill_service):
        """Test validation fails with incomplete frontmatter markers."""
        content = """---
name: Test Skill

# Missing closing ---
"""
        with pytest.raises(ValidationError, match="Invalid YAML frontmatter format"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_yaml_syntax(self, skill_service):
        """Test validation fails with invalid YAML syntax."""
        content = """---
name: Test Skill
invalid: yaml: syntax: here
---
"""
        with pytest.raises(ValidationError, match="Invalid YAML syntax"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_frontmatter_not_dict(self, skill_service):
        """Test validation fails when frontmatter is not a dictionary."""
        content = """---
- list item 1
- list item 2
---
"""
        with pytest.raises(ValidationError, match="must be a YAML object"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_missing_name_field(self, skill_service):
        """Test validation fails when required 'name' field is missing."""
        content = """---
description: A skill without name
tags: [test]
---
"""
        with pytest.raises(ValidationError, match="missing required fields: name"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_empty_name_field(self, skill_service):
        """Test validation fails when 'name' field is empty."""
        content = """---
name: ""
description: A skill with empty name
---
"""
        with pytest.raises(ValidationError, match="'name' field cannot be empty"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_whitespace_only_name(self, skill_service):
        """Test validation fails when 'name' field is whitespace only."""
        content = """---
name: "   "
description: A skill with whitespace name
---
"""
        with pytest.raises(ValidationError, match="'name' field cannot be empty"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_tags_not_list(self, skill_service):
        """Test validation fails when 'tags' field is not a list."""
        content = """---
name: Test Skill
tags: "not a list"
---
"""
        with pytest.raises(ValidationError, match="'tags' field must be a list"):
            skill_service._validate_skill_md_frontmatter(content)

    def test_invalid_description_not_string(self, skill_service):
        """Test validation fails when 'description' field is not a string."""
        content = """---
name: Test Skill
description: 12345
---
"""
        with pytest.raises(
            ValidationError, match="'description' field must be a string"
        ):
            skill_service._validate_skill_md_frontmatter(content)

    def test_valid_with_null_description(self, skill_service):
        """Test validation passes when description is null/None."""
        content = """---
name: Test Skill
description: null
---
"""
        # Should not raise
        skill_service._validate_skill_md_frontmatter(content)

    def test_valid_with_empty_tags_list(self, skill_service):
        """Test validation passes with empty tags list."""
        content = """---
name: Test Skill
tags: []
---
"""
        # Should not raise
        skill_service._validate_skill_md_frontmatter(content)

    def test_valid_multiline_description(self, skill_service):
        """Test validation passes with multiline description."""
        content = """---
name: Test Skill
description: |
  This is a multiline
  description for the skill.
  It spans multiple lines.
tags: [test]
---
"""
        # Should not raise
        skill_service._validate_skill_md_frontmatter(content)
