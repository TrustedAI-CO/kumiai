#!/bin/bash

# KumiAI Backend Setup Script

set -e

echo "🚀 Setting up KumiAI Backend v2.0..."

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not found"
    exit 1
fi

echo "✓ Python 3.11 found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install app in editable mode
echo "📦 Installing app in editable mode..."
pip install -e .

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ .env created - Please update with your settings"
else
    echo "✓ .env already exists"
fi

# Start Docker Compose (PostgreSQL)
echo "🐘 Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run Alembic migrations (once we create them)
# echo "📊 Running database migrations..."
# alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Update .env with your API keys"
echo "  3. Run database migrations: alembic upgrade head"
echo "  4. Start backend: uvicorn app.main:app --reload --port 7892"
echo ""
echo "Optional:"
echo "  - View database: docker-compose --profile tools up -d pgadmin"
echo "  - Access PgAdmin: http://localhost:5050 (admin@kumiai.local / admin)"
echo ""
