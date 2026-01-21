#!/bin/bash
# CEP Machine Setup Verification Script

set -e

echo "🔍 Verifying CEP Machine setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# Check Docker availability
echo ""
echo "🐳 Docker Environment Check:"
if command -v docker &> /dev/null; then
    print_status 0 "Docker is installed"
    docker --version
else
    print_status 1 "Docker is not installed"
    print_info "Install Docker Desktop or Colima:"
    print_info "  Docker Desktop: https://docs.docker.com/get-docker/"
    print_info "  Colima: brew install colima && colima start"
fi

if command -v docker-compose &> /dev/null; then
    print_status 0 "Docker Compose is installed"
    docker-compose --version
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    print_status 0 "Docker Compose (plugin) is installed"
    docker compose version
else
    print_status 1 "Docker Compose is not installed"
fi

# Check Python environment
echo ""
echo "🐍 Python Environment Check:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status 0 "Python is installed: $PYTHON_VERSION"
    
    # Check if version is 3.10+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        print_status 0 "Python version is 3.10+"
    else
        print_status 1 "Python version must be 3.10 or higher"
    fi
else
    print_status 1 "Python 3 is not installed"
fi

# Check Node.js environment
echo ""
echo "📦 Node.js Environment Check:"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status 0 "Node.js is installed: $NODE_VERSION"
    
    # Check if version is 18+
    if node -e "process.exit(process.version.slice(1).split('.')[0] >= 18 ? 0 : 1)" 2>/dev/null; then
        print_status 0 "Node.js version is 18+"
    else
        print_status 1 "Node.js version must be 18 or higher"
    fi
else
    print_status 1 "Node.js is not installed"
fi

if command -v npm &> /dev/null; then
    print_status 0 "npm is installed"
    npm --version
else
    print_status 1 "npm is not installed"
fi

# Check project structure
echo ""
echo "📁 Project Structure Check:"
if [ -d "backend" ]; then
    print_status 0 "Backend directory exists"
else
    print_status 1 "Backend directory missing"
fi

if [ -d "frontend" ]; then
    print_status 0 "Frontend directory exists"
else
    print_status 1 "Frontend directory missing"
fi

if [ -d "cep_machine" ]; then
    print_status 0 "CEP Machine core directory exists"
else
    print_status 1 "CEP Machine core directory missing"
fi

if [ -f "docker-compose.yml" ]; then
    print_status 0 "Docker Compose file exists"
else
    print_status 1 "Docker Compose file missing"
fi

if [ -f "Makefile" ]; then
    print_status 0 "Makefile exists"
else
    print_status 1 "Makefile missing"
fi

# Check environment files
echo ""
echo "🔧 Environment Configuration Check:"
if [ -f "backend/.env" ]; then
    print_status 0 "Backend .env file exists"
    
    # Check for required API keys
    if grep -q "ANTHROPIC_API_KEY=" backend/.env && ! grep -q "ANTHROPIC_API_KEY=$" backend/.env; then
        print_status 0 "ANTHROPIC_API_KEY is configured"
    else
        print_warning "ANTHROPIC_API_KEY needs to be set in backend/.env"
    fi
else
    print_warning "Backend .env file missing (copy from .env.example)"
fi

if [ -f "frontend/.env.local" ]; then
    print_status 0 "Frontend .env.local file exists"
else
    print_warning "Frontend .env.local file missing"
fi

# Check Docker files
echo ""
echo "🐳 Docker Configuration Check:"
if [ -f "backend/Dockerfile" ]; then
    print_status 0 "Backend Dockerfile exists"
else
    print_status 1 "Backend Dockerfile missing"
fi

if [ -f "frontend/Dockerfile" ]; then
    print_status 0 "Frontend Dockerfile exists"
else
    print_status 1 "Frontend Dockerfile missing"
fi

if [ -f "docker-compose.dev.yml" ]; then
    print_status 0 "Development Docker Compose exists"
else
    print_status 1 "Development Docker Compose missing"
fi

if [ -f "docker-compose.full.yml" ]; then
    print_status 0 "Production Docker Compose exists"
else
    print_status 1 "Production Docker Compose missing"
fi

# Check if Docker is running (if available)
if command -v docker &> /dev/null; then
    echo ""
    echo "🏥 Docker Service Health Check:"
    if docker info &> /dev/null; then
        print_status 0 "Docker daemon is running"
        
        # Check if DragonflyDB container exists
        if docker ps -a --format "table {{.Names}}" | grep -q "cep-dragonfly"; then
            if docker ps --format "table {{.Names}}" | grep -q "cep-dragonfly"; then
                print_status 0 "DragonflyDB container is running"
            else
                print_warning "DragonflyDB container exists but is not running"
            fi
        else
            print_warning "DragonflyDB container not found (run 'make setup')"
        fi
    else
        print_status 1 "Docker daemon is not running"
        print_info "Start Docker Desktop or run 'colima start'"
    fi
fi

# Summary
echo ""
echo "📋 Setup Summary:"
echo "   For Docker setup: make setup"
echo "   For development: make dev"
echo "   For production: make prod"
echo "   For help: make help"
echo ""
echo "📚 Documentation:"
echo "   DOCKER.md - Complete Docker guide"
echo "   README.md - Project overview"
echo "   docs/ - Detailed documentation"
echo ""

if [ -f "backend/.env" ] && [ -f "frontend/.env.local" ] && command -v docker &> /dev/null; then
    echo -e "${GREEN}🎉 Ready to start! Run 'make dev' to begin development.${NC}"
else
    echo -e "${YELLOW}⚠️  Setup incomplete. Please address the issues above.${NC}"
fi
