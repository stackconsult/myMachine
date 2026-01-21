#!/bin/bash
# CEP Machine Docker Setup Script

set -e

echo "🐳 Setting up CEP Machine with Docker..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   On macOS: Install Docker Desktop or use Colima"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p nginx/ssl
mkdir -p data

# Setup environment files
echo "📝 Setting up environment files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from example"
    echo "   Please edit backend/.env with your API keys"
fi

# Build and start services
echo "🔨 Building Docker images..."
docker-compose -f docker-compose.yml build

echo "🚀 Starting DragonflyDB..."
docker-compose -f docker-compose.yml up -d dragonfly

# Wait for DragonflyDB to be ready
echo "⏳ Waiting for DragonflyDB to be ready..."
sleep 10

# Check DragonflyDB connection
if docker exec cep-dragonfly redis-cli ping > /dev/null 2>&1; then
    echo "✅ DragonflyDB is ready"
else
    echo "❌ DragonflyDB not responding"
    exit 1
fi

echo ""
echo "✅ Docker setup complete!"
echo ""
echo "Available commands:"
echo "  🏃 Development:  docker-compose -f docker-compose.dev.yml up"
echo "  🏭 Production:   docker-compose -f docker-compose.full.yml up"
echo "  🛑 Stop all:     docker-compose -f docker-compose.yml down"
echo ""
echo "Services will be available at:"
echo "  🎨 Frontend:     http://localhost:3000"
echo "  🔧 Backend:      http://localhost:8000"
echo "  🐲 DragonflyDB: localhost:6379"
echo ""
echo "To start development mode:"
echo "  docker-compose -f docker-compose.dev.yml up"
