# Quick Start Guide

**For:** KumiAI Backend v2.0 Implementation
**Timeline:** 10 weeks
**Last Updated:** 2026-01-20

---

## 📅 Sprint Overview

| Sprint | Weeks | Theme | Deliverables |
|--------|-------|-------|--------------|
| **0** | Pre-work | Setup | Dev environment ready |
| **1** | 1-2 | Foundation | PostgreSQL, Alembic, pytest, config |
| **2** | 3-4 | Domain | Entities, value objects, business logic |
| **3** | 3-4 | Infrastructure | Repositories, Claude SDK, filesystem |
| **4** | 5-6 | Services | Application services, DTOs, DI |
| **5** | 5-6 | API | FastAPI endpoints, SSE streaming |
| **6** | 7-8 | Migration | Data migration, testing, coverage |
| **7** | 9-10 | Integration | Frontend, docs, Docker |
| **8** | 9-10 | Deployment | Production go-live |

---

## 🎯 MVP Features (Must-Have)

### Core Functionality
- ✅ Create/manage projects
- ✅ Create/manage characters
- ✅ Launch sessions (PM, specialist, orchestrator)
- ✅ Execute queries with streaming
- ✅ Message persistence
- ✅ Session status management
- ✅ SQLite → PostgreSQL migration

### API Endpoints (v1 - Compatible)
```
POST   /api/v1/agents/spawn              # Create session
GET    /api/v1/agents/{id}               # Get session
POST   /api/v1/agents/{id}/query         # Execute query (SSE)
GET    /api/v1/agents/{id}/messages      # Get messages
DELETE /api/v1/agents/{id}               # Delete session

POST   /api/v1/projects                  # Create project
GET    /api/v1/projects                  # List projects
POST   /api/v1/projects/{id}/spawn_pm    # Assign PM
```

### Quality Gates
- 80%+ test coverage
- All tests passing
- No critical bugs
- Data migration validated

---

## 📊 Week-by-Week Breakdown

### Week 1-2: Foundation 🏗️

**Goal:** Set up project infrastructure

**Tasks:**
```bash
# Day 1-2: Setup
□ Create directory structure
□ Set up PostgreSQL + Docker
□ Configure Alembic
□ Create initial migration

# Day 3-4: Testing
□ Set up pytest + fixtures
□ Configure coverage
□ Write first tests

# Day 5-6: Core
□ Implement Settings (Pydantic)
□ Set up logging (structlog)
□ Create custom exceptions

# Day 7-10: Database
□ Define SQLAlchemy models
□ Create database schema
□ Test connectivity
```

**Deliverables:**
- ✅ Working dev environment
- ✅ PostgreSQL schema created
- ✅ Testing framework ready
- ✅ Core config + logging

---

### Week 3-4: Domain & Infrastructure 🧠

**Goal:** Build core business logic and data access

**Domain Tasks:**
```bash
# Day 1-2: Value Objects
□ SessionStatus + state machine
□ SessionType, MessageRole enums
□ Test all value objects

# Day 3-5: Entities
□ Session entity + business methods
□ Project, Character, Message entities
□ Test business rules

# Day 6-7: Repositories
□ Define repository interfaces
□ Document all methods
```

**Infrastructure Tasks:**
```bash
# Day 1-4: Repositories
□ Implement PostgreSQLSessionRepository
□ Implement PostgreSQLProjectRepository
□ Implement PostgreSQLCharacterRepository
□ Entity ↔ Model mapping

# Day 5-6: External Services
□ Claude SDK wrapper
□ Mock client for tests

# Day 7: Filesystem
□ FileManager class
□ Path validation
```

**Deliverables:**
- ✅ All domain entities (95%+ coverage)
- ✅ All repositories (90%+ coverage)
- ✅ Claude SDK wrapper
- ✅ Filesystem operations

---

### Week 5-6: Services & API 🌐

**Goal:** Implement business workflows and API

**Services Tasks:**
```bash
# Day 1: DTOs
□ Request/Response DTOs
□ Validation with Pydantic

# Day 2-4: Core Services
□ SessionService (create, query, stream)
□ ProjectService (CRUD, PM assignment)
□ CharacterService (CRUD)

# Day 5: DI Setup
□ Configure dependency-injector
□ Wire up all services
```

**API Tasks:**
```bash
# Day 1: Setup
□ Create FastAPI app
□ Add middleware (CORS, logging, errors)
□ Health endpoint

# Day 2-3: Session Endpoints
□ POST /agents/spawn
□ POST /agents/{id}/query (SSE)
□ GET /agents, /agents/{id}

# Day 4-5: Project Endpoints
□ POST /projects
□ POST /projects/{id}/spawn_pm
□ GET /projects
```

**Deliverables:**
- ✅ All services (90%+ coverage)
- ✅ All v1 API endpoints (85%+ coverage)
- ✅ SSE streaming working
- ✅ Dependency injection configured

---

### Week 7-8: Migration & Testing 🧪

**Goal:** Migrate data and comprehensive testing

**Migration Tasks:**
```bash
# Day 1-2: Scripts
□ export_sqlite.py
□ transform_data.py
□ import_postgresql.py

# Day 3: Testing
□ Test on copy of production DB
□ Fix data issues

# Day 4: Validation
□ validate_migration.py
□ Check row counts, FK integrity
```

**Testing Tasks:**
```bash
# Day 5-6: E2E Tests
□ Project workflow (create → PM → query)
□ Session lifecycle
□ Error scenarios

# Day 7-8: Coverage
□ Run coverage report
□ Write missing tests
□ Achieve 80%+ coverage

# Day 9-10: Bug Fixing
□ Fix all bugs found
□ Add regression tests
```

**Deliverables:**
- ✅ Migration scripts working
- ✅ Data migrated successfully
- ✅ 80%+ test coverage
- ✅ All bugs fixed

---

### Week 9-10: Integration & Deployment 🚀

**Goal:** Frontend integration and production deployment

**Integration Tasks:**
```bash
# Day 1: Documentation
□ OpenAPI docs (Swagger UI)
□ API examples

# Day 2: Docker
□ docker-compose.yml
□ Test local deployment

# Day 3-5: Frontend
□ Update frontend to v1 API
□ Test all workflows
□ Fix integration issues

# Day 6-7: Deployment Prep
□ Production config
□ Database backup
□ Deployment checklist
```

**Deployment Tasks:**
```bash
# Day 8: Migration
□ Stop v1.0 app
□ Run migration scripts
□ Validate data
□ Start v2.0 app

# Day 9-10: Monitoring
□ Monitor logs
□ Check errors
□ Fix critical issues
□ Celebrate! 🎉
```

**Deliverables:**
- ✅ OpenAPI docs complete
- ✅ Frontend integrated
- ✅ Production deployment successful
- ✅ All features working

---

## 🛠️ Daily Workflow

### Morning (9 AM - 12 PM)
1. Review yesterday's progress
2. Check tests (all should pass)
3. Pick next task from sprint
4. Write tests first (TDD)
5. Implement feature

### Afternoon (1 PM - 5 PM)
1. Continue implementation
2. Run tests frequently
3. Commit code (small, frequent commits)
4. Update documentation
5. Review coverage

### End of Day
1. Run full test suite
2. Check coverage report
3. Commit all work
4. Update todo list
5. Plan tomorrow

---

## ✅ Definition of Done

A task is "done" when:
- [ ] Code implemented
- [ ] Tests written and passing
- [ ] Coverage meets target (80%+)
- [ ] Code reviewed (if team)
- [ ] Documentation updated
- [ ] Committed to git
- [ ] No linting errors

---

## 🚦 Quality Checks

### Before Each Commit
```bash
# Run tests
pytest

# Check coverage
pytest --cov=app --cov-report=html

# Lint code
ruff check .
black --check .

# Type check
mypy app/
```

### End of Each Sprint
```bash
# Full test suite
pytest -v

# Coverage report
pytest --cov=app --cov-report=term-missing

# Check all endpoints work
python scripts/smoke_test.py
```

---

## 📈 Progress Tracking

### Burndown Chart (Weekly)

| Week | Tasks Planned | Tasks Completed | Remaining |
|------|--------------|-----------------|-----------|
| 1    | 15           | -               | -         |
| 2    | 15           | -               | -         |
| 3    | 20           | -               | -         |
| 4    | 20           | -               | -         |
| 5    | 18           | -               | -         |
| 6    | 18           | -               | -         |
| 7    | 12           | -               | -         |
| 8    | 12           | -               | -         |
| 9    | 10           | -               | -         |
| 10   | 10           | -               | -         |

**Total:** ~150 tasks

---

## 🎓 Learning Resources

### FastAPI
- [Official Docs](https://fastapi.tiangolo.com/)
- [Full Stack FastAPI Template](https://github.com/tiangolo/full-stack-fastapi-template)

### SQLAlchemy
- [Async ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

### Testing
- [pytest Documentation](https://docs.pytest.org/)
- [Test-Driven Development](https://testdriven.io/)

### Clean Architecture
- [Clean Architecture in Python](https://www.thedigitalcatonline.com/blog/2016/11/14/clean-architectures-in-python-a-step-by-step-example/)

---

## 🆘 Troubleshooting

### Common Issues

**Tests failing?**
```bash
# Clear pytest cache
pytest --cache-clear

# Run specific test
pytest tests/unit/test_entities.py -v

# Debug with pdb
pytest --pdb
```

**Database issues?**
```bash
# Reset database
alembic downgrade base
alembic upgrade head

# Check connection
psql -U kumiai -d kumiai_db -c "SELECT 1"
```

**Import errors?**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## 📞 Getting Help

1. **Check documentation:** All design docs in `docs/`
2. **Review implementation plan:** `IMPLEMENTATION_PLAN.md`
3. **Search issues:** Check if someone else had the same problem
4. **Ask for help:** Don't spend > 2 hours stuck

---

**Ready to start? Begin with Sprint 0!** 🚀

```bash
# Clone repository
cd ~/workspace/personal/kumiai

# Review design documents
ls backend/docs/

# Start Sprint 0
# See IMPLEMENTATION_PLAN.md for details
```
