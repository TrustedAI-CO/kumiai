# KumiAI Backend v2.0

**Status:** Design Phase Complete ✅
**Architecture:** Clean Architecture + DDD
**Stack:** FastAPI + PostgreSQL + SQLAlchemy
**Deployment:** Web App (Desktop app packaging later)

---

## 📋 Design Documents

All design documents are located in [`docs/`](./docs/):

| Document | Description | Status |
|----------|-------------|--------|
| [DESIGN.md](./DESIGN.md) | High-level architecture, design principles, layer organization | ✅ Complete |
| [DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md) | PostgreSQL schema, tables, indexes, constraints | ✅ Complete |
| [DOMAIN_MODEL.md](./docs/DOMAIN_MODEL.md) | Entities, value objects, business rules, state machines | ✅ Complete |
| [API_CONTRACTS.md](./docs/API_CONTRACTS.md) | API endpoints (v1 + v2), request/response formats | ✅ Complete |
| [MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md) | SQLite → PostgreSQL migration strategy | ✅ Complete |

---

## 🏗️ Architecture Overview

### Clean Architecture (4 Layers)

```
┌─────────────────────────────────────┐
│     API Layer (FastAPI)             │  ← HTTP, validation, OpenAPI
├─────────────────────────────────────┤
│     Application Layer (Services)    │  ← Use cases, orchestration
├─────────────────────────────────────┤
│     Domain Layer (Entities)         │  ← Business logic, rules
├─────────────────────────────────────┤
│     Infrastructure (Database, ...)  │  ← PostgreSQL, Claude SDK, files
└─────────────────────────────────────┘
```

**Dependency Rule:** Inner layers don't know about outer layers.

### Key Design Principles

- **SOLID Principles:** Single Responsibility, DI, Interface Segregation
- **Domain-Driven Design:** Rich entities, value objects, repositories
- **Test-Driven Development:** 80%+ test coverage target
- **Clean Code:** Meaningful names, small functions, no duplication

---

## 🗄️ Database Design

### PostgreSQL Schema (7 Tables)

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `projects` | Project metadata | id, name, path, pm_character_id |
| `characters` | Agent definitions | id, name, role, file_path |
| `sessions` | Active agent sessions | id, character_id, status, session_type |
| `messages` | Conversation history | id, session_id, role, content, sequence |
| `skills` | Reusable skill library | id, name, tags, file_path |
| `activity_logs` | Event tracking | id, session_id, event_type, event_data |
| `user_profiles` | User preferences | id, settings (singleton table) |

**Key Features:**
- UUID primary keys (distributed-friendly)
- PostgreSQL ENUMs (type safety)
- Proper indexes and foreign keys
- Soft deletes (deleted_at)
- Auto-updated timestamps

---

## 🎯 Domain Model

### Core Entities

**Session:**
- Represents active agent instance
- State machine: `initializing → idle → thinking → working → completed`
- Business methods: `start()`, `fail()`, `cancel()`, `resume()`

**Project:**
- Workspace containing files and sessions
- Can assign PM character + session
- Validation: PM references must be consistent

**Character:**
- Agent definition (personality in files)
- Metadata stored in database
- Full definition in `agent.md` file

**Message:**
- Conversation turn (user/assistant/system/tool_result)
- Ordered by sequence within session
- Tool results linked via `tool_use_id`

### Value Objects

- `SessionStatus` (ENUM with state machine)
- `SessionType` (pm, specialist, assistant)
- `MessageRole` (user, assistant, system, tool_result)

---

## 🌐 API Design

### Versioning Strategy

- **v1 endpoints:** Backwards compatible (existing frontend)
  - `/api/v1/agents/*` (sessions)
  - `/api/v1/projects/*`
  - `/api/v1/characters/*`

- **v2 endpoints:** Redesigned (better practices)
  - `/api/v2/sessions/*`
  - `/api/v2/projects/*`
  - `/api/v2/characters/*`
  - Wrapped responses with metadata
  - Pagination support

### Key Endpoints

```
POST   /api/v2/sessions              # Create session
GET    /api/v2/sessions/{id}         # Get session
POST   /api/v2/sessions/{id}/messages # Send message (streaming)
POST   /api/v2/sessions/{id}/cancel  # Cancel session
DELETE /api/v2/sessions/{id}         # Delete session

POST   /api/v2/projects              # Create project
GET    /api/v2/projects              # List projects
POST   /api/v2/projects/{id}/pm      # Assign PM
DELETE /api/v2/projects/{id}/pm      # Remove PM

GET    /api/v2/characters            # List characters
POST   /api/v2/characters            # Create character
```

---

## 📦 Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── api/                       # API layer
│   │   ├── v1/                    # v1 endpoints (compatible)
│   │   ├── v2/                    # v2 endpoints (redesigned)
│   │   └── middleware/            # Error handling, logging
│   ├── application/               # Application layer
│   │   ├── services/              # Use case services
│   │   └── dtos/                  # Data transfer objects
│   ├── domain/                    # Domain layer
│   │   ├── entities/              # Business entities
│   │   ├── value_objects/         # Immutable value objects
│   │   └── repositories/          # Repository interfaces
│   ├── infrastructure/            # Infrastructure layer
│   │   ├── database/              # PostgreSQL (models, repos)
│   │   ├── claude/                # Claude SDK wrapper
│   │   └── filesystem/            # File operations
│   └── core/                      # Cross-cutting concerns
│       ├── config.py              # Settings
│       ├── exceptions.py          # Custom exceptions
│       ├── logging.py             # Structured logging
│       └── dependencies.py        # DI container
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
├── alembic/                       # Database migrations
├── docs/                          # Design documentation
├── requirements.txt               # Production dependencies
└── requirements-dev.txt           # Development dependencies
```

---

## 🔄 Migration Strategy

### SQLite (v1.0) → PostgreSQL (v2.0)

**Approach:** Offline migration (acceptable for single-user app)

**Steps:**
1. Export SQLite data to JSON
2. Transform data (add UUIDs, convert types)
3. Import to PostgreSQL
4. Validate data integrity
5. Switch application to v2.0
6. Backup SQLite for rollback

**Timeline:** ~1 week (including testing and buffer)

See [MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md) for detailed scripts.

---

## 🧪 Testing Strategy

### Test Pyramid

```
       /\
      /e2e\      ← 10% (critical workflows)
     /──────\
    / integr \   ← 20% (API + database)
   /──────────\
  /    unit    \ ← 70% (services, entities)
 /──────────────\
```

**Coverage Goals:**
- Overall: 80%+
- Services: 90%+
- Domain entities: 95%+
- API endpoints: 85%+

**Frameworks:**
- pytest + pytest-asyncio
- pytest-cov (coverage)
- httpx (API testing)
- faker (test data generation)

---

## 🚀 Deployment Strategy

### Phase 1: Web App

1. **Backend:** FastAPI on port 7892
2. **Frontend:** React/Vue (separate repo)
3. **Database:** PostgreSQL (local or Docker)
4. **Development:** `uvicorn app.main:app --reload`
5. **Production:** Uvicorn + Nginx reverse proxy

### Phase 2: Desktop App (Future)

**Option A: Electron**
- Bundle web frontend
- ~150MB installer
- Cross-platform

**Option B: Tauri**
- Lightweight (~10MB)
- Uses system webview
- Rust-based

**Option C: PySide6**
- Pure Python
- Qt WebEngine
- Good for Python-heavy apps

---

## 📚 Tech Stack

### Core
- **Python 3.11+** (async features)
- **FastAPI 0.115.5** (web framework)
- **PostgreSQL 16+** (database)
- **SQLAlchemy 2.0** (async ORM)
- **Alembic 1.14** (migrations)

### Key Libraries
- **Pydantic 2.10** (validation, settings)
- **asyncpg** (PostgreSQL driver)
- **anthropic** (Claude SDK)
- **structlog** (structured logging)
- **dependency-injector** (DI container)

### Development
- **pytest** (testing)
- **black** (formatting)
- **ruff** (linting)
- **mypy** (type checking)

---

## 🎯 Next Steps

### Design Phase ✅
- [x] High-level architecture
- [x] Database schema
- [x] Domain model
- [x] API contracts
- [x] Migration strategy

### Implementation Phase (Next)

**Week 1-2: Foundation**
- [ ] Set up project structure
- [ ] Configure PostgreSQL + Docker Compose
- [ ] Set up Alembic migrations
- [ ] Set up pytest + test fixtures
- [ ] Implement core configuration

**Week 3-4: Domain & Infrastructure**
- [ ] Implement domain entities
- [ ] Implement value objects
- [ ] Implement PostgreSQL repositories
- [ ] Write unit tests (80%+ coverage)

**Week 5-6: Application & API**
- [ ] Implement application services
- [ ] Set up dependency injection
- [ ] Implement v1 API endpoints (compatible)
- [ ] Implement v2 API endpoints (redesigned)
- [ ] Write integration tests

**Week 7-8: Migration & Testing**
- [ ] Implement migration scripts
- [ ] Test migration on copy
- [ ] Run full test suite
- [ ] Perform migration
- [ ] Validate data integrity

**Week 9: Frontend Integration**
- [ ] Update frontend to use v2 API
- [ ] Test end-to-end workflows
- [ ] Fix any integration issues

**Week 10: Deployment**
- [ ] Deploy to production
- [ ] Monitor for issues
- [ ] Keep v1 as rollback

---

## 📖 Development Guidelines

### Code Style
- Follow [Clean Code principles](../.claude/CLAUDE.md)
- Use type hints everywhere
- Write docstrings for public APIs
- Keep functions small (<20 lines)

### Commit Messages
- Follow [Conventional Commits](../.claude/CLAUDE.md#clean-commits-rule)
- Format: `type(scope): description`
- Examples:
  - `feat(api): add session cancellation endpoint`
  - `fix(db): prevent race condition in message persistence`
  - `docs: update API contracts with new endpoints`

### Testing
- Write tests first (TDD)
- Test behavior, not implementation
- Use meaningful test names
- Aim for 80%+ coverage

---

## 🤝 Contributing

1. Read design documents in `docs/`
2. Follow clean code guidelines
3. Write tests for new features
4. Update documentation
5. Create pull request

---

## 📝 License

This project is licensed under the MIT License. See [LICENSE](../LICENSE) file for details.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/dizzyvn/kumiai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dizzyvn/kumiai/discussions)
- **Security**: See [SECURITY.md](../SECURITY.md) for reporting vulnerabilities
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines

---

**Last Updated:** 2026-01-20
**Status:** Ready for implementation ✅
