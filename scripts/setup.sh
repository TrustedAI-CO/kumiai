#!/bin/bash
set -e

echo "🚀 KumiAI Setup Script"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
    echo -e "${RED}❌ Error: Please run this script from the KumiAI project root${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose"
    exit 1
fi

# Use 'docker compose' or 'docker-compose' based on availability
DOCKER_COMPOSE="docker compose"
if ! docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
fi

echo "📦 Step 1: Starting PostgreSQL database..."
cd backend
$DOCKER_COMPOSE up -d

echo -e "${GREEN}✓${NC} Database container started"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec kumiai_postgres pg_isready -U kumiai &> /dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Error: PostgreSQL failed to start${NC}"
        echo "Check logs with: docker logs kumiai_postgres"
        exit 1
    fi
    sleep 1
done
echo ""

# Check Python version
echo "🐍 Step 2: Checking Python version..."
PYTHON_CMD=""
for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 11 ]; then
            PYTHON_CMD=$cmd
            echo -e "${GREEN}✓${NC} Found $cmd (version $VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Error: Python 3.11+ is required${NC}"
    exit 1
fi
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Step 3: Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo "📦 Step 3: Virtual environment already exists"
fi
echo ""

# Activate virtual environment and install dependencies
echo "📦 Step 4: Installing Python dependencies..."
source venv/bin/activate || . venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Setup .env file
echo "⚙️  Step 5: Configuring environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️${NC}  Created .env from .env.example"
    echo -e "${YELLOW}⚠️${NC}  Please edit backend/.env and set your ANTHROPIC_API_KEY"
    NEED_API_KEY=true
else
    echo -e "${GREEN}✓${NC} .env file already exists"

    # Check if API key is set
    if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env || grep -q "ANTHROPIC_API_KEY=$" .env; then
        echo -e "${YELLOW}⚠️${NC}  ANTHROPIC_API_KEY is not configured in .env"
        NEED_API_KEY=true
    fi
fi
echo ""

# Run database migrations
echo "🗄️  Step 6: Running database migrations..."
alembic upgrade head
echo -e "${GREEN}✓${NC} Database schema initialized"
echo ""

# Create ~/.kumiai directories
echo "📁 Step 7: Creating data directories..."
mkdir -p ~/.kumiai/agents
mkdir -p ~/.kumiai/skills
mkdir -p ~/.kumiai/projects
echo -e "${GREEN}✓${NC} Data directories created at ~/.kumiai/"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start the backend:"
echo "   cd backend && source venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 7892"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend && npm install && npm run dev"
echo ""

if [ "$NEED_API_KEY" = true ]; then
    echo -e "${YELLOW}⚠️  IMPORTANT: Set your ANTHROPIC_API_KEY in backend/.env before starting${NC}"
    echo ""
fi

echo "📚 Documentation: https://github.com/yourusername/kumiai"
echo "🔍 API Docs: http://localhost:7892/api/docs (after starting backend)"
