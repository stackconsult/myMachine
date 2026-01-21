#!/bin/bash
# CEP Machine Local Setup (No Docker Required)

set -e

echo "🚀 Setting up CEP Machine locally (no Docker)..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup backend environment
echo "🔧 Setting up backend environment..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env - please edit with your API keys"
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Setup frontend environment
echo "🎨 Setting up frontend environment..."
if [ ! -f "frontend/.env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
    echo "✅ Created frontend/.env.local"
fi

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

# Setup local Redis alternative (using file-based cache)
echo "💾 Setting up local cache..."
mkdir -p data/cache

# Initialize database
echo "🗄️ Initializing database..."
python -c "
import asyncio
import sys
sys.path.append('.')
try:
    from cep_machine.core.database import Database
    asyncio.run(Database().initialize())
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️  Database initialization warning: {e}')
    print('   The application will create the database on first run')
"

echo ""
echo "✅ Local setup complete!"
echo ""
echo "To start the application:"
echo "  ./start-local.sh"
echo ""
echo "Or start manually:"
echo "  source venv/bin/activate"
echo "  cd backend && python main.py &"
echo "  cd frontend && npm run dev"
echo ""
echo "Services will be available at:"
echo "  🎨 Frontend: http://localhost:3000"
echo "  🔧 Backend:  http://localhost:8000"
echo "  💾 Cache:    File-based (./data/cache)"
