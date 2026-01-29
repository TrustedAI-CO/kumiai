# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- MIT License
- Community contribution guidelines

## [0.1.0] - 2026-01-26

### Added
- Multi-agent collaboration system powered by Claude
- Built-in AI assistants for creating and editing skills and agents
- Skill management with GitHub import support
- Project management with built-in PM agent
- Real-time streaming via Server-Sent Events (SSE)
- Persistent sessions with context preservation
- Kanban workflow for visual project management
- File attachment functionality with inline preview
- Inter-session communication (contact_session tool)
- Welcome messages for PM, Agent, and Skill assistant sessions
- Bootstrap system for initializing templates on first run
- Session error recovery and automatic cleanup
- File upload and management
- SQLite database with zero-configuration setup
- Skills import/export functionality

### Changed
- Migrated from PostgreSQL to SQLite for portability
- Reduced status badge size in session card
- Moved attachment icon to top toolbar in chat input
- Consolidated empty states with shadcn components
- Applied shadcn/ui default styling across components
- Improved PM label display in chat messages
- Enhanced onboarding modal with better UX and branding

### Fixed
- Prevent overwriting existing PROJECT.md on project creation
- Handle undefined content in Write tool widget
- Prevent app hangs when messaging dead/hung sessions
- Add timeout protection to database operations
- Prevent multiple SSE connections causing message duplication
- Enable scrolling in sidebar chat sessions
- Remove unique constraint on messages(session_id, sequence)
- Handle ghost sessions with critical status
- Prevent PROJECT.md regeneration on PM session resume
- Add automatic recovery for terminated Claude SDK subprocesses
- Fix SQLite connection pool configuration (NullPool)
- Add connection semaphore to limit concurrent SQLite connections

### Security
- Proper .gitignore configuration for sensitive files
- Environment-based configuration with .env.example
- No API keys or secrets in repository

## [0.0.1] - 2026-01-09

### Added
- Initial project setup
- Basic FastAPI backend structure
- React frontend with TypeScript
- Claude SDK integration
- Database models and migrations
- API routes for sessions, projects, agents, skills
- File management system
- MCP server support

---

## Version History

- **0.1.0** - First public release candidate (unreleased)
- **0.0.1** - Internal development version

## Links

- [Repository](https://github.com/dizzyvn/kumiai)
- [Issue Tracker](https://github.com/dizzyvn/kumiai/issues)
- [Documentation](https://github.com/dizzyvn/kumiai#readme)

---

**Note**: This changelog will be maintained going forward for all releases.
