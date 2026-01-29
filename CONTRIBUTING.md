# Contributing to KumiAI

Thank you for your interest in contributing to KumiAI!

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Claude API key

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/kumiai.git
   cd kumiai
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Install dev dependencies

   # Configure environment
   cp .env.example .env
   # Edit .env and set your ANTHROPIC_API_KEY
   ```

3. **Install Pre-commit Hooks** (Recommended)
   ```bash
   # From project root
   source backend/venv/bin/activate  # If not already activated
   pre-commit install

   # This will automatically format and lint code before each commit
   # Run manually on all files:
   pre-commit run --all-files
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

5. **Run the application**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 7892

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

   - Backend: http://localhost:7892
   - Frontend: http://localhost:1420
   - API Docs: http://localhost:7892/docs

## Development Guidelines

### Code Style

We follow **Clean Code principles** (see `.claude/CLAUDE.md`):

- Use meaningful, pronounceable, and searchable names
- Keep functions small (prefer <20 lines)
- One function, one responsibility
- Minimal nesting (1-2 indent levels)
- No redundant code
- Write self-documenting code (minimal comments)

**Python:**
- Use type hints everywhere
- Follow PEP 8 style guide
- Use `black` for formatting (automated via pre-commit)
- Use `ruff` for linting (automated via pre-commit)
- Use `mypy` for type checking

**TypeScript/React:**
- Use TypeScript strict mode
- Functional components with hooks
- Feature-based organization (see `frontend/ARCHITECTURE.md`)
- Use Tailwind CSS for styling
- Follow React best practices

### Pre-commit Hooks (Recommended)

We use pre-commit hooks to automatically format and lint code before each commit:

**What it does:**
- ✅ Automatically formats Python code with Black
- ✅ Fixes linting issues with Ruff
- ✅ Removes trailing whitespace
- ✅ Fixes end-of-file markers
- ✅ Checks for merge conflicts
- ✅ Detects private keys
- ✅ Validates YAML/JSON syntax

**Setup:**
```bash
# Install hooks (one-time setup)
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files backend/app/main.py

# Skip hooks for a commit (not recommended)
git commit --no-verify -m "message"
```

**Configuration:** See `.pre-commit-config.yaml`

### Commit Messages

We use **Conventional Commits** format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**
```bash
feat(api): add session cancellation endpoint
fix(db): prevent race condition in message persistence
docs: update API contracts with new endpoints
refactor(frontend): consolidate empty states with shadcn components
```

Use `!` or `BREAKING CHANGE:` footer for breaking changes:
```bash
feat(api)!: change session response format

BREAKING CHANGE: Session API now returns wrapped responses with metadata
```

### Testing

**Backend:**
```bash
cd backend
pytest                    # Run all tests
pytest tests/unit         # Run unit tests only
pytest --cov=app          # Run with coverage
```

**Frontend:**
```bash
cd frontend
npm run typecheck         # TypeScript type checking
npm run build             # Test production build
```

**Testing Requirements:**
- Write tests for new features
- Maintain or improve code coverage
- Test edge cases and error handling
- Use meaningful test names that describe behavior

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**
   - Follow code style guidelines
   - Write meaningful commit messages
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Backend
   cd backend
   black app/           # Format code
   ruff check app/      # Lint code
   mypy app/            # Type check
   pytest               # Run tests

   # Frontend
   cd frontend
   npm run typecheck    # Type check
   npm run build        # Test build
   ```

4. **Push your branch**
   ```bash
   git push origin feat/your-feature-name
   ```

5. **Open a Pull Request**
   - Use a clear, descriptive title
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers
   - Respond to feedback promptly

### PR Review Criteria

Your PR will be reviewed for:
- Code quality and style
- Test coverage
- Documentation updates
- Breaking changes (clearly marked)
- Performance impact
- Security implications

## Project Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── api/              # API layer (FastAPI routes)
│   ├── application/      # Application layer (services, use cases)
│   ├── core/             # Core config, exceptions, logging
│   └── infrastructure/   # Database, Claude SDK, filesystem
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
└── alembic/              # Database migrations
```

### Frontend (`frontend/src/`)

```
src/
├── components/
│   ├── features/         # Feature-specific components
│   ├── layout/           # Layout components
│   ├── modals/           # Modal dialogs
│   └── ui/               # Shared UI primitives
├── hooks/                # Custom React hooks
│   ├── api/              # Data fetching hooks
│   ├── queries/          # React Query hooks
│   ├── state/            # State management hooks
│   └── utils/            # Utility hooks
├── lib/                  # Libraries and utilities
├── stores/               # Zustand state stores
├── types/                # TypeScript types
└── pages/                # Page-level components
```

See `frontend/ARCHITECTURE.md` for detailed frontend architecture.

## Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python/Node version)
   - Screenshots or error messages

## Requesting Features

1. Check existing feature requests
2. Use the feature request template
3. Explain:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered
   - Why this benefits KumiAI users

## Documentation

Help improve our documentation:
- Fix typos or unclear instructions
- Add examples or use cases
- Improve API documentation
- Translate documentation (future)

## Questions?

- Open a [GitHub Discussion](https://github.com/dizzyvn/kumiai/discussions)
- Check the [README](README.md) and documentation
- Review existing issues and PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing!
