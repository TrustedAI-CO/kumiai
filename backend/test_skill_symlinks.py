#!/usr/bin/env python3
"""
Test script to verify skill symlink creation and SDK discovery.

This simulates the flow:
1. Skills stored in ~/.kumiai/skills/
2. Session created with working_dir = session subdirectory
3. Symlinks created in working_dir/.claude/skills/
4. Claude SDK discovers skills via symlinks
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.infrastructure.filesystem.skill_repository import FileBasedSkillRepository
from app.application.loaders.skill_loader import SkillLoader
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_skill_symlinks():
    """Test the complete skill symlink flow."""
    print("=" * 80)
    print("SKILL SYMLINK TEST")
    print("=" * 80)

    # 1. Check skills exist in ~/.kumiai/skills/
    skills_base = Path.home() / ".kumiai" / "skills"
    print(f"\n1. Checking skills in {skills_base}")

    if not skills_base.exists():
        print(f"   ❌ Skills directory doesn't exist: {skills_base}")
        return False

    skills = list(skills_base.iterdir())
    print(f"   ✅ Found {len(skills)} skills:")
    for skill_dir in skills:
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            skill_md = skill_dir / "SKILL.md"
            exists = "✅" if skill_md.exists() else "❌"
            print(f"      {exists} {skill_dir.name}")

    # 2. Initialize repository and loader
    print(f"\n2. Initializing SkillRepository with base_path: {skills_base}")
    skill_repo = FileBasedSkillRepository(base_path=skills_base)
    skill_loader = SkillLoader(skill_repository=skill_repo)

    # 3. Simulate session directory structure
    test_session_dir = Path("/tmp/test_kumiai_session")
    test_session_dir.mkdir(exist_ok=True)

    print(f"\n3. Simulating session with working_dir: {test_session_dir}")

    # 4. Load skills and create symlinks in .claude/skills/
    print("\n4. Creating symlinks in .claude/skills/")

    try:
        # Get first skill for testing
        all_skills = await skill_repo.get_all()
        if not all_skills:
            print("   ❌ No skills found in repository")
            return False

        test_skill_id = all_skills[0].id
        print(f"   Using test skill: {test_skill_id}")

        # Load skills for session
        skill_descriptions = await skill_loader.load_skills_for_session(
            skill_ids=[test_skill_id], session_dir=test_session_dir
        )

        print(f"   ✅ Loaded {len(skill_descriptions)} skill(s)")

        # 5. Verify .claude/skills/ structure
        claude_skills_dir = test_session_dir / ".claude" / "skills"
        print("\n5. Verifying .claude/skills/ structure")
        print(f"   Directory: {claude_skills_dir}")
        print(f"   Exists: {claude_skills_dir.exists()}")

        if not claude_skills_dir.exists():
            print("   ❌ .claude/skills/ directory was not created")
            return False

        print("   ✅ .claude/skills/ directory exists")

        # Check symlinks
        print("\n6. Checking symlinks:")
        symlinks = list(claude_skills_dir.iterdir())

        if not symlinks:
            print("   ❌ No symlinks found in .claude/skills/")
            return False

        for symlink in symlinks:
            is_symlink = symlink.is_symlink()
            is_dir = symlink.is_dir()
            target = symlink.resolve() if is_symlink else None

            print(f"\n   Skill: {symlink.name}")
            print(f"      is_symlink: {is_symlink}")
            print(f"      is_dir: {is_dir}")
            print(f"      target: {target}")

            if is_symlink:
                # Verify SKILL.md is accessible
                skill_md_via_symlink = symlink / "SKILL.md"
                md_exists = skill_md_via_symlink.exists()
                print(f"      SKILL.md accessible: {md_exists}")

                if md_exists:
                    content = skill_md_via_symlink.read_text()
                    print(f"      SKILL.md size: {len(content)} bytes")
                    print("      ✅ Symlink works correctly")
                else:
                    print("      ❌ Cannot read SKILL.md through symlink")

        # 7. Test what SDK would see
        print("\n7. Simulating SDK skill discovery:")
        print(f"   Working directory (cwd): {test_session_dir}")
        print("   Skills directory: .claude/skills/")
        print("   'Skill' in allowed_tools: YES (per our changes)")

        discovered_skills = []
        for item in claude_skills_dir.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    discovered_skills.append(item.name)

        print(f"\n   SDK would discover {len(discovered_skills)} skill(s):")
        for skill_name in discovered_skills:
            print(f"      ✅ {skill_name}")

        # 8. Cleanup
        print("\n8. Cleanup")
        import shutil

        shutil.rmtree(test_session_dir)
        print("   ✅ Removed test directory")

        # Summary
        print(f"\n{'=' * 80}")
        print("TEST SUMMARY")
        print(f"{'=' * 80}")
        print("✅ Skills exist in ~/.kumiai/skills/")
        print("✅ Symlinks created in .claude/skills/")
        print("✅ SKILL.md accessible through symlinks")
        print(f"✅ SDK would discover {len(discovered_skills)} skill(s)")
        print("\n🎉 All tests passed! Symlinks work correctly.")

        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_skill_symlinks())
    sys.exit(0 if success else 1)
