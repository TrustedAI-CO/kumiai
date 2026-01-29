# Pre-commit Hooks Setup Guide

Pre-commit hooks automatically format and lint your code before each commit, preventing common issues from reaching CI.

---

## Quick Setup

```bash
# From project root
source backend/venv/bin/activate
pre-commit install
```

That's it! Hooks will run automatically on `git commit`.

---

## What Pre-commit Does

### Automatic Fixes ✅

1. **Black** - Formats all Python code
2. **Ruff** - Fixes auto-fixable linting issues
3. **Trailing whitespace** - Removes extra spaces
4. **End of file** - Ensures files end with newline
5. **Mixed line endings** - Normalizes to LF

### Checks (Will block commit if fails) ❌

1. **YAML/JSON validation** - Ensures valid syntax
2. **Large files** - Blocks files > 1MB
3. **Merge conflicts** - Detects conflict markers
4. **Private keys** - Prevents committing secrets
5. **Ruff errors** - Reports unfixable issues

---

## Usage

### Normal Workflow

```bash
# Make changes to code
vim backend/app/main.py

# Stage changes
git add backend/app/main.py

# Commit (hooks run automatically)
git commit -m "feat: add new feature"

# Pre-commit will:
# 1. Format with black
# 2. Fix linting with ruff
# 3. Run all checks
# 4. If changes made, you'll need to git add again
```

### Manual Runs

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files backend/app/main.py

# Run only black
pre-commit run black --all-files

# Run only ruff
pre-commit run ruff --all-files
```

### Skip Hooks (Emergency Only)

```bash
# Skip all hooks (not recommended!)
git commit --no-verify -m "emergency fix"

# Better: Fix the issues instead
pre-commit run --all-files
git add .
git commit -m "fix: proper commit with checks"
```

---

## Configuration

See `.pre-commit-config.yaml` in project root.

### Enabled Hooks

**General Checks:**
- trailing-whitespace
- end-of-file-fixer
- check-yaml (with unsafe mode for GitHub Actions)
- check-added-large-files (max 1MB)
- check-json
- check-toml
- check-merge-conflict
- detect-private-key
- mixed-line-ending

**Python:**
- black (formatting)
- ruff (linting + fixes)
- ruff-format (additional formatting)

**Optional (commented out):**
- mypy (type checking) - can be slow
- prettier (frontend formatting)

### Customization

Edit `.pre-commit-config.yaml` to:
- Enable/disable hooks
- Adjust file patterns
- Add new hooks
- Change tool versions

---

## Troubleshooting

### Hooks Fail on Every Commit

**Problem**: Pre-commit makes changes, you commit, it makes more changes.

**Solution**:
```bash
# Run until no more changes
pre-commit run --all-files
git add .
git commit -m "style: apply pre-commit fixes"
```

### Hooks Are Too Slow

**Solution 1**: Run only on changed files (default behavior)
```bash
# This is automatic, no action needed
git commit -m "message"
```

**Solution 2**: Disable slow hooks like mypy
```yaml
# In .pre-commit-config.yaml, comment out mypy
# - repo: https://github.com/pre-commit/mirrors-mypy
#   ...
```

### Need to Skip Hooks Once

```bash
# Emergency only - skips all checks
git commit --no-verify -m "hotfix: critical bug"

# Better: Fix specific issues
pre-commit run --files path/to/file.py
git add path/to/file.py
git commit -m "fix: proper commit"
```

### Hook Installation Failed

```bash
# Reinstall hooks
pre-commit clean
pre-commit install

# Update to latest versions
pre-commit autoupdate

# Install all environments
pre-commit install-hooks
```

---

## First-Time Setup: Fixing All Files

When setting up pre-commit on existing project:

```bash
# 1. Install hooks
pre-commit install

# 2. Run on all files (will fix many issues)
pre-commit run --all-files

# 3. Stage auto-fixed files
git add -u

# 4. Review remaining errors
git diff

# 5. Fix remaining issues manually
# Edit files to fix unfixable ruff errors

# 6. Commit
git commit -m "style: apply pre-commit formatting to entire codebase"
```

---

## Integration with CI

Pre-commit hooks run the same checks as CI, so:

✅ **If pre-commit passes locally → CI will pass**
❌ **If you skip pre-commit → CI will likely fail**

### CI Configuration

`.github/workflows/ci.yml` runs similar checks:
- `black --check` (formatting)
- `ruff check` (linting)
- `pytest` (tests)

Pre-commit ensures these pass before code reaches CI.

---

## Benefits

1. **Faster Feedback** - Catch issues before pushing
2. **Cleaner Commits** - No "fix linting" commits
3. **Less CI Failures** - Issues caught locally
4. **Consistent Style** - Automatic formatting
5. **Learn Best Practices** - See what gets fixed

---

## Common Errors and Fixes

### Error: `black would reformat file.py`

**Meaning**: File needs formatting

**Fix**: Automatic - black reformats it for you
```bash
# Just stage the changes and commit again
git add file.py
git commit -m "same message"
```

### Error: `F401 imported but unused`

**Meaning**: Import not used in file

**Fix**: Remove the import or use it
```python
# Before
from typing import Dict, List  # List unused

# After
from typing import Dict
```

### Error: `F841 Local variable assigned but never used`

**Meaning**: Variable created but not used

**Fix**: Remove it or use it
```python
# Before
result = expensive_calculation()  # Never used
return True

# After
return True  # Remove unused variable
```

### Error: `E722 Do not use bare except`

**Meaning**: `except:` without exception type

**Fix**: Specify exception type
```python
# Before
try:
    risky_operation()
except:
    pass

# After
try:
    risky_operation()
except Exception as e:
    logger.error(f"Error: {e}")
```

---

## Best Practices

1. **Always install pre-commit** when setting up project
2. **Run on all files** after pulling latest changes
3. **Don't skip hooks** unless absolutely necessary
4. **Fix issues** instead of suppressing warnings
5. **Update hooks** periodically: `pre-commit autoupdate`

---

## Advanced Usage

### Run Specific Hook

```bash
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run trailing-whitespace --all-files
```

### Update Hook Versions

```bash
# Update all hooks to latest versions
pre-commit autoupdate

# Shows what will be updated
pre-commit autoupdate --freeze
```

### Add Custom Hooks

Edit `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: custom-check
        name: Custom Check
        entry: ./scripts/custom-check.sh
        language: script
        files: \.py$
```

---

## Uninstalling

```bash
# Remove hooks
pre-commit uninstall

# Clean cached environments
pre-commit clean

# Remove config (optional)
rm .pre-commit-config.yaml
```

---

## Resources

- **Official Docs**: https://pre-commit.com/
- **Hook List**: https://pre-commit.com/hooks.html
- **Black**: https://black.readthedocs.io/
- **Ruff**: https://docs.astral.sh/ruff/

---

**Questions?** See `CONTRIBUTING.md` or open an issue.
