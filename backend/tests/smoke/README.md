# Smoke Tests

## What are Smoke Tests?

**Smoke tests** are quick, critical tests that verify the application's basic functionality works. They answer: "Does it work at all?"

Named after hardware testing - if you turn on a device and see smoke, you know there's a serious problem!

## Characteristics

- ⚡ **Fast**: Run in seconds, not minutes
- 🎯 **Critical**: Test only the most important functionality
- 🔍 **Shallow**: Don't test edge cases or deep logic
- ✅ **Build Verification**: Catch major breaks immediately

## What We Test

### Application Health (`test_health.py`)
- ✅ Server starts without crashing
- ✅ Health endpoint responds
- ✅ API documentation is accessible
- ✅ Database connection works
- ✅ CORS is configured

### Critical Paths (`test_critical_paths.py`)
- ✅ Projects listing doesn't crash
- ✅ Agents listing doesn't crash
- ✅ Skills listing doesn't crash
- ✅ Sessions listing doesn't crash
- ✅ Error handling is graceful (no 500 errors)

## Running Smoke Tests

```bash
# Run only smoke tests (fastest)
pytest tests/smoke/ -v

# Run specific test file
pytest tests/smoke/test_health.py -v

# Run specific test class
pytest tests/smoke/test_health.py::TestApplicationHealth -v

# Run specific test
pytest tests/smoke/test_health.py::TestApplicationHealth::test_app_starts_without_crash -v

# Run with coverage
pytest tests/smoke/ --cov=app --cov-report=term

# Run smoke tests marked with @pytest.mark.smoke
pytest -m smoke -v
```

## Expected Behavior

These tests should:
- ✅ **Always pass** on main/develop branches
- ✅ **Run in CI** on every commit
- ✅ **Complete in <10 seconds**
- ❌ **Never be skipped** (they're critical!)

If smoke tests fail, the build is broken and should not be deployed.

## When to Add Smoke Tests

Add new smoke tests when:
- Adding a critical new feature
- Adding a new API endpoint
- Adding a new integration point
- Identifying a production bug that smoke tests should catch

## Test Philosophy

**Smoke Tests**: Does it work at all?
**Unit Tests**: Does each piece work correctly?
**Integration Tests**: Do pieces work together?
**E2E Tests**: Does the whole system work?

## Examples

### Good Smoke Test ✅
```python
def test_health_endpoint_responds(client):
    """Verify the health endpoint returns 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
```

### Bad Smoke Test ❌
```python
def test_complex_project_workflow(client):
    """Test creating, updating, and deleting projects with all edge cases."""
    # Too complex! This is an integration test
    # Smoke tests should be simple
```

## Smoke Tests vs Other Tests

| Type | Speed | Coverage | When to Run |
|------|-------|----------|-------------|
| **Smoke** | ⚡⚡⚡ Seconds | Critical paths only | Every commit |
| **Unit** | ⚡⚡ Fast | Individual functions | Every commit |
| **Integration** | ⚡ Slower | Feature workflows | Pre-merge |
| **E2E** | 🐌 Slowest | Full system | Pre-release |

## Maintenance

- Keep smoke tests **simple**
- Keep smoke tests **fast** (<10s total)
- Update when adding critical features
- Remove outdated tests promptly

---

**Remember**: If smoke tests fail, stop everything and fix them first!
