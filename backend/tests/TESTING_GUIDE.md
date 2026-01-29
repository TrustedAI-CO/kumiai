# KumiAI Testing Guide

## Quick Start

```bash
# Run all tests
pytest

# Run only smoke tests (fast!)
pytest tests/smoke/ -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run and open coverage report
pytest --cov=app --cov-report=html && open htmlcov/index.html
```

## Test Structure

```
tests/
├── smoke/              # ⚡ Quick tests for critical functionality
│   ├── test_health.py
│   └── test_critical_paths.py
├── unit/               # 🧪 Fast tests for individual functions
├── integration/        # 🔗 Tests for component interactions
└── e2e/               # 🌐 Full end-to-end workflows
```

## Test Types Explained

### 1. Smoke Tests ⚡
**Purpose**: "Does it work at all?"
**Speed**: <10 seconds
**Coverage**: Critical paths only

```bash
pytest tests/smoke/ -v
```

**When to run**: Every commit, in CI/CD

**Example**:
```python
def test_app_starts(client):
    response = client.get("/api/health")
    assert response.status_code == 200
```

### 2. Unit Tests 🧪
**Purpose**: Test individual functions/methods
**Speed**: Fast (<1 second each)
**Coverage**: Individual components

```bash
pytest tests/unit/ -v
```

**When to run**: Before committing

**Example**:
```python
def test_create_project_validates_name():
    with pytest.raises(ValidationError):
        create_project(name="")
```

### 3. Integration Tests 🔗
**Purpose**: Test component interactions
**Speed**: Slower (database, API calls)
**Coverage**: Feature workflows

```bash
pytest tests/integration/ -v
```

**When to run**: Before merging PR

**Example**:
```python
async def test_create_project_creates_database_record(db_session):
    project = await create_project(db_session, name="Test")
    result = await db_session.get(Project, project.id)
    assert result.name == "Test"
```

### 4. E2E Tests 🌐
**Purpose**: Test full user workflows
**Speed**: Slowest (minutes)
**Coverage**: Complete system

```bash
pytest tests/e2e/ -v
```

**When to run**: Before release

**Example**:
```python
async def test_full_project_workflow(client):
    # Create project -> Add agent -> Start session -> Complete task
    ...
```

## Running Tests

### By Category
```bash
# Smoke tests only
pytest -m smoke

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Everything except slow tests
pytest -m "not slow"
```

### By Path
```bash
# Specific directory
pytest tests/smoke/

# Specific file
pytest tests/smoke/test_health.py

# Specific class
pytest tests/smoke/test_health.py::TestApplicationHealth

# Specific test
pytest tests/smoke/test_health.py::TestApplicationHealth::test_app_starts
```

### With Options
```bash
# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## Coverage

```bash
# Generate coverage report
pytest --cov=app

# HTML report (opens in browser)
pytest --cov=app --cov-report=html && open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# Coverage for specific module
pytest tests/smoke/ --cov=app.api --cov-report=term
```

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange: Set up test data
    user = User(name="Test User")

    # Act: Perform the action
    result = user.get_display_name()

    # Assert: Verify the result
    assert result == "Test User"
```

### Good Test Names

```python
# ✅ Good: Describes what is being tested
def test_create_project_with_valid_name_succeeds():
    ...

def test_create_project_with_empty_name_raises_validation_error():
    ...

# ❌ Bad: Vague or unclear
def test_project():
    ...

def test_it_works():
    ...
```

### Using Fixtures

```python
@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return Project(id="123", name="Test Project")

def test_project_name(sample_project):
    assert sample_project.name == "Test Project"
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test", "TEST"),
    ("hello", "HELLO"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

## Best Practices

### DO ✅

- Write tests before or alongside code (TDD)
- Use descriptive test names
- Test one thing per test
- Use fixtures for common setup
- Mock external dependencies
- Clean up after tests

### DON'T ❌

- Test implementation details
- Write tests that depend on each other
- Hardcode paths or URLs
- Skip tests (fix or remove them)
- Ignore failing tests
- Test third-party libraries

## Continuous Integration

Tests run automatically in CI on:
- Every push to main/develop
- Every pull request
- Before releases

See `.github/workflows/ci.yml` for configuration.

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Overall | 80% | TBD |
| Services | 90% | TBD |
| Domain | 95% | TBD |
| API | 85% | TBD |

## Troubleshooting

### Tests fail locally but pass in CI
- Check environment variables
- Check Python/package versions
- Clear pytest cache: `pytest --cache-clear`

### Tests are slow
- Run only smoke tests: `pytest -m smoke`
- Use parallel execution: `pytest -n auto`
- Check for database cleanup issues

### Import errors
- Ensure you're in the backend directory
- Install test dependencies: `pip install -r requirements-dev.txt`
- Check PYTHONPATH

### Database errors
- Check database connection
- Ensure test database is created
- Check migrations are applied

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Remember**: Tests are code too - keep them clean, readable, and maintainable!
