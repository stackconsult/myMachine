# CEP Machine Docker Setup

Complete containerized development and deployment setup for the CEP Machine.

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (macOS Sonoma+) OR Colima (for older macOS)
- Docker Compose
- 4GB+ RAM

### Initial Setup

```bash
# Run the setup script
make setup

# Or manually
./docker-setup.sh
```

### Development Mode

```bash
# Start all services in development mode
make dev

# Or with docker-compose
docker-compose -f docker-compose.dev.yml up
```

### Production Mode

```bash
# Start all services in production mode
make prod

# Or with docker-compose
docker-compose -f docker-compose.full.yml up -d
```

## 📁 Docker Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base DragonflyDB service |
| `docker-compose.dev.yml` | Development environment |
| `docker-compose.full.yml` | Production environment with nginx |
| `backend/Dockerfile` | Production backend image |
| `backend/Dockerfile.dev` | Development backend with hot reload |
| `frontend/Dockerfile` | Production frontend image |
| `frontend/Dockerfile.dev` | Development frontend with hot reload |
| `nginx/nginx.conf` | Reverse proxy configuration |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │  DragonflyDB    │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│    (Redis)      │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Nginx       │
                    │  (Reverse Proxy)│
                    │   Port: 80/443  │
                    └─────────────────┘
```

## 🛠️ Management Commands

### Using Make (Recommended)

```bash
make help          # Show all commands
make setup         # Initial setup
make dev           # Development mode
make prod          # Production mode
make stop          # Stop all services
make clean         # Clean up everything
make logs          # View logs
make health        # Check service health
make restart       # Quick restart
make build         # Build images only
```

### Shell Access

```bash
make shell-backend    # Access backend container
make shell-frontend   # Access frontend container
make shell-dragonfly  # Access DragonflyDB container
```

### Manual Docker Commands

```bash
# Build images
docker-compose -f docker-compose.dev.yml build

# Start services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Clean up
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f
```

## 🔧 Environment Configuration

### Backend Environment (`backend/.env`)

```bash
# Required
ANTHROPIC_API_KEY=your-anthropic-api-key
REDIS_URL=redis://dragonfly:6379

# Optional
OPENAI_API_KEY=your-openai-api-key
COPILOTKIT_API_KEY=your-copilotkit-api-key
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
```

### Frontend Environment (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 Service Health

### Health Checks

All services include built-in health checks:

- **DragonflyDB**: Redis ping every 10 seconds
- **Backend**: HTTP health endpoint every 30 seconds
- **Frontend**: HTTP check every 30 seconds

### Monitoring

```bash
# Check all services
make health

# Individual service checks
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
docker exec cep-dragonfly redis-cli ping  # DragonflyDB
```

## 🚀 Deployment Options

### Development Mode
- Hot reload enabled
- Volume mounts for live code changes
- Debug logging enabled
- All ports exposed to host

### Production Mode
- Optimized builds
- Nginx reverse proxy
- SSL support (configure certificates)
- Health checks and restarts
- Resource limits

### Production with SSL

1. Add SSL certificates to `nginx/ssl/`
2. Update `nginx/nginx.conf` for SSL configuration
3. Run with production profile:

```bash
docker-compose -f docker-compose.full.yml --profile production up -d
```

## 🔍 Troubleshooting

### Common Issues

**Docker not available on macOS Monterey:**
```bash
# Install Colima instead of Docker Desktop
brew install colima
colima start

# Verify installation
docker --version
docker-compose --version
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000
lsof -i :6379

# Change ports in docker-compose files if needed
```

**Permission issues:**
```bash
# Fix Docker permissions
sudo chown -R $USER:$USER .
chmod +x docker-setup.sh
```

**Container won't start:**
```bash
# View detailed logs
docker-compose -f docker-compose.dev.yml logs service-name

# Rebuild containers
docker-compose -f docker-compose.dev.yml build --no-cache
```

### Reset Everything

```bash
# Complete reset
make clean
docker system prune -a
make setup
```

## 📈 Performance

### Resource Allocation

- **DragonflyDB**: 2GB RAM (production), 1GB RAM (development)
- **Backend**: Minimal base + application requirements
- **Frontend**: Build-time resources only

### Optimization Tips

1. Use `.dockerignore` files to exclude unnecessary files
2. Multi-stage builds for smaller production images
3. Volume mounts for development, not production
4. Health checks to ensure service availability

## 🔗 Integration

### IDE Integration

Most IDEs (VS Code, IntelliJ) can connect directly to containers:

- **VS Code**: Use Docker extension + Remote-Containers
- **IntelliJ**: Use Docker plugin
- **Cursor**: Native Docker integration

### Database Access

```bash
# Connect to DragonflyDB
docker exec -it cep-dragonfly redis-cli

# Or use local Redis CLI
redis-cli -h localhost -p 6379
```

### API Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Test through nginx (production)
curl http://localhost/api/health
```

---

*For more details, see the main [README.md](README.md) and [docs/](docs/) directory.*
