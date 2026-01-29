# KumiAI

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178c6.svg)](https://www.typescriptlang.org/)

Project-level multi-agent system powered by Claude. Build AI teams that collaborate on your projects with real-time coordination.


## What It Does

- **Multi-Agent Collaboration**: Create AI agents with specialized skills that work together on projects
- **AI Assistants**: Built-in assistants help you create and edit skills and agents interactively
- **Skill Management**: Create custom skills or import from [Anthropic's skill library](https://github.com/anthropics/skills)
- **Project Management**: Built-in PM agent coordinates team workflows and task delegation
- **Real-Time Streaming**: Watch agents think and collaborate in real-time via SSE
- **Persistent Sessions**: Sessions resume automatically with full context preservation
- **Kanban Workflow**: Visual project management with drag-and-drop task organization

## Quick Setup

### Prerequisites

- **Python 3.11+** (required for asyncio.timeout)
- Node.js 18+
- Claude API key (logged in via Claude Code)

### Installation

**Quick Setup:**

```bash
# 1. Backend Setup
cd backend

# Create virtual environment with Python 3.11+
python3.11 -m venv venv  # macOS/Linux
# Or: py -3.11 -m venv venv  # Windows

source venv/bin/activate  # macOS/Linux
# Or: venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY

# Start server (database auto-creates on first run)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 7892

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- **Backend:** `http://localhost:7892`
- **Frontend:** `http://localhost:1420`

### First Steps

1. **Manage Skills** → Skills page
   - **Import from GitHub**: Click Import → Paste URL (e.g., `https://github.com/anthropics/skills/tree/main/skills/internal-comms`)
   - **Create Your Own**: Click New Skill → Use the AI assistant (💬 button) for help writing SKILL.md
   - Browse Anthropic's skills: [github.com/anthropics/skills](https://github.com/anthropics/skills)
   - Explore community skills:
     - [VoltAgent/awesome-claude-skills](https://github.com/VoltAgent/awesome-claude-skills)
     - [BehiSecc/awesome-claude-skills](https://github.com/BehiSecc/awesome-claude-skills)
     - [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

2. **Create Agents** → Agents page
   - Click New Member → Assign skills → Define personality
   - Use the AI assistant (💬 button) to help write agent configurations

3. **Create Project** → Cmd/Ctrl+P → New Project → Select team & PM

4. **Launch Session** → Kanban → + button → Choose agents → Start

## Data Storage

All data stored in `~/.kumiai/` (created automatically on first run):
```
~/.kumiai/
├── agents/         # Agent definitions
├── skills/         # Skill library
└── projects/       # Project workspaces
```

Database: SQLite (`~/.kumiai/kumiai.db`) - auto-creates on first run, zero configuration

## Tech Stack

- **Backend**: FastAPI + SQLite + Claude Agent SDK
- **Frontend**: React 18 + TypeScript + Tailwind CSS v4
- **Real-time**: Server-Sent Events (SSE)
- **State**: Zustand
- **Database**: SQLite (zero-config, portable)

## Configuration (Optional)

```bash
# backend/.env
API_PORT=7892

# frontend/.env.local (for network access)
VITE_API_URL=http://YOUR_IP:7892
```

## API Docs

Visit `http://localhost:7892/docs` after starting the backend.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Questions or Issues?

- Open an issue: [GitHub Issues](https://github.com/dizzyvn/kumiai/issues)
- Email: thientquang@gmail.com

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/)
- Inspired by [Anthropic's Skills Library](https://github.com/anthropics/skills)
- Community skill collections:
  - [VoltAgent/awesome-claude-skills](https://github.com/VoltAgent/awesome-claude-skills)
  - [BehiSecc/awesome-claude-skills](https://github.com/BehiSecc/awesome-claude-skills)
  - [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)
