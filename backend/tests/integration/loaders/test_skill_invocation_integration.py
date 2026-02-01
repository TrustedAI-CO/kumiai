#!/usr/bin/env python3
"""
Test if the Skill tool actually works with custom skills in .claude/skills/

This creates a real Claude SDK session with:
1. Skill symlinks in .claude/skills/
2. "Skill" in allowed_tools
3. Tries to invoke the qa-tester skill
"""

import asyncio
import sys
from pathlib import Path
import shutil

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)
from app.infrastructure.filesystem.skill_repository import FileBasedSkillRepository
from app.application.loaders.skill_loader import SkillLoader


async def test_skill_invocation():
    """Test if Skill tool works with our custom skills."""

    print("=" * 80)
    print("TESTING SKILL TOOL WITH CUSTOM SKILLS")
    print("=" * 80)

    # 1. Setup test directory with .claude/skills/
    test_dir = Path("/tmp/test_skill_invocation")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()

    print(f"\n1. Setting up test directory: {test_dir}")

    # 2. Load skills and create symlinks
    skills_base = Path.home() / ".kumiai" / "skills"
    repo = FileBasedSkillRepository(base_path=skills_base)
    loader = SkillLoader(skill_repository=repo)

    skills = await repo.get_all()
    print(f"\n2. Available skills: {[s.id for s in skills]}")

    if not skills:
        print("   ❌ No skills found!")
        return False

    # Create symlinks for all skills
    skill_ids = [s.id for s in skills]
    skill_descriptions = await loader.load_skills_for_session(skill_ids, test_dir)

    claude_skills = test_dir / ".claude" / "skills"
    print(f"\n3. Created symlinks in: {claude_skills}")
    for item in claude_skills.iterdir():
        print(f"   - {item.name} -> {item.resolve()}")

    # 3. Create system prompt with skill descriptions
    system_prompt = f"""You are a helpful assistant with access to skills.

Available skills in .claude/skills/:
{chr(10).join(skill_descriptions)}

To use a skill, you can reference the skill documentation.
"""

    print(f"\n4. System prompt length: {len(system_prompt)} chars")

    # 4. Create Claude SDK options
    options = ClaudeAgentOptions(
        cwd=str(test_dir),
        system_prompt=system_prompt,
        allowed_tools=["Read", "Skill"],  # Include Skill tool
        model="sonnet",
        max_turns=3,
    )

    print("\n5. ClaudeAgentOptions:")
    print(f"   cwd: {options.cwd}")
    print(f"   allowed_tools: {options.allowed_tools}")
    print(f"   model: {options.model}")

    # 5. Test skill invocation
    print("\n6. Testing skill invocation...")
    print("   Asking: 'Use the qa-tester skill to create a test plan'")

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(
                "Use the qa-tester skill to create a test plan for a login feature"
            )

            print("\n7. Claude's response:")
            print("-" * 80)

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"[Text] {block.text}")
                        elif isinstance(block, ToolUseBlock):
                            print(f"[Tool] {block.name}")
                            print(f"  Input: {block.input}")

            print("-" * 80)

        print("\n✅ Test completed")
        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print("\n8. Cleaned up test directory")


if __name__ == "__main__":
    success = asyncio.run(test_skill_invocation())
    sys.exit(0 if success else 1)
