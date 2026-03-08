"""Tests for doc_guard_hook."""

import pytest

from app.infrastructure.claude.execution.hooks import (
    doc_guard_hook,
    _is_doc_file,
)


def _pre_tool_input(file_path: str, content: str = "", new_string: str = "") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_input": {
            "file_path": file_path,
            "content": content,
            "new_string": new_string,
        },
    }


def _post_tool_input(file_path: str, content: str = "") -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_input": {"file_path": file_path, "content": content},
        "tool_response": "File created successfully.",
    }


# ---------------------------------------------------------------------------
# _is_doc_file
# ---------------------------------------------------------------------------


class TestIsDocFile:
    # Should trigger warning (non-standard doc)
    def test_arbitrary_md_triggers(self):
        assert _is_doc_file("notes.md") is True

    def test_random_txt_triggers(self):
        assert _is_doc_file("output.txt") is True

    def test_nested_arbitrary_md_triggers(self):
        assert _is_doc_file("some/path/report.md") is True

    # Allowed stems — never trigger
    def test_readme_allowed(self):
        assert _is_doc_file("README.md") is False

    def test_claude_md_allowed(self):
        assert _is_doc_file("CLAUDE.md") is False

    def test_agents_md_allowed(self):
        assert _is_doc_file("AGENTS.md") is False

    def test_contributing_allowed(self):
        assert _is_doc_file("CONTRIBUTING.md") is False

    def test_changelog_allowed(self):
        assert _is_doc_file("CHANGELOG.md") is False

    def test_memory_md_allowed(self):
        assert _is_doc_file("MEMORY.md") is False

    def test_worklog_md_allowed(self):
        assert _is_doc_file("WORKLOG.md") is False

    # Allowed directories — never trigger
    def test_docs_dir_allowed(self):
        assert _is_doc_file("docs/guide.md") is False

    def test_skills_dir_allowed(self):
        assert _is_doc_file("skills/my-skill.md") is False

    def test_memory_dir_allowed(self):
        assert _is_doc_file("memory/session.md") is False

    def test_claude_commands_dir_allowed(self):
        assert _is_doc_file(".claude/commands/deploy.md") is False

    def test_claude_plans_dir_allowed(self):
        assert _is_doc_file(".claude/plans/feature.md") is False

    # Allowed patterns
    def test_plan_md_allowed(self):
        assert _is_doc_file("feature.plan.md") is False

    # Non-doc extensions — never trigger
    def test_python_file(self):
        assert _is_doc_file("app/main.py") is False

    def test_typescript_file(self):
        assert _is_doc_file("src/index.ts") is False

    def test_json_file(self):
        assert _is_doc_file("config.json") is False

    def test_mdx_not_checked(self):
        assert _is_doc_file("blog/post.mdx") is False

    def test_rst_not_checked(self):
        assert _is_doc_file("docs/api.rst") is False


# ---------------------------------------------------------------------------
# doc_guard_hook
# ---------------------------------------------------------------------------


class TestDocGuardHook:
    @pytest.mark.asyncio
    async def test_warns_arbitrary_md(self):
        result = await doc_guard_hook(_post_tool_input("notes.md"), "", None)
        output = result["hookSpecificOutput"]
        assert output["hookEventName"] == "PostToolUse"
        assert (
            "[Hook] WARNING: Non-standard documentation file detected"
            in output["additionalContext"]
        )
        assert "notes.md" in output["additionalContext"]
        assert "docs/" in output["additionalContext"]

    @pytest.mark.asyncio
    async def test_silent_for_readme(self):
        result = await doc_guard_hook(_post_tool_input("README.md"), "", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_silent_for_claude_md(self):
        result = await doc_guard_hook(_post_tool_input("CLAUDE.md"), "", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_silent_for_docs_dir(self):
        result = await doc_guard_hook(_post_tool_input("docs/guide.md"), "", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_silent_for_python_file(self):
        result = await doc_guard_hook(_post_tool_input("app/service.py"), "", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_silent_for_typescript_file(self):
        result = await doc_guard_hook(_post_tool_input("src/component.tsx"), "", None)
        assert result == {}

    @pytest.mark.asyncio
    async def test_ignores_pre_tool_use_event(self):
        result = await doc_guard_hook(_pre_tool_input("notes.md"), "", None)
        assert result == {}
