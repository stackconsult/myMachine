# CEP Machine Docker Management

.PHONY: help setup dev prod stop clean logs health

# Default target
help:
	@echo "CEP Machine Docker Commands:"
	@echo ""
	@echo "  setup    - Initial Docker setup"
	@echo "  dev      - Start development environment"
	@echo "  prod     - Start production environment"
	@echo "  stop     - Stop all services"
	@echo "  clean    - Remove all containers and images"
	@echo "  logs     - Show logs for all services"
	@echo "  health   - Check health of all services"
	@echo ""

# Initial setup
setup:
	@echo "🐳 Setting up CEP Machine Docker environment..."
	./docker-setup.sh

# Development mode
dev:
	@echo "🏃 Starting development environment..."
	docker-compose -f docker-compose.dev.yml up --build

# Production mode
prod:
	@echo "🏭 Starting production environment..."
	docker-compose -f docker-compose.full.yml up --build -d

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	docker-compose -f docker-compose.yml down
	docker-compose -f docker-compose.dev.yml down || true
	docker-compose -f docker-compose.full.yml down || true

# Clean everything
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose -f docker-compose.yml down -v --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans || true
	docker-compose -f docker-compose.full.yml down -v --remove-orphans || true
	docker system prune -f

# Show logs
logs:
	docker-compose -f docker-compose.dev.yml logs -f

# Health check
health:
	@echo "🏥 Checking service health..."
	@echo "DragonflyDB:"
	@docker exec cep-dragonfly-dev redis-cli ping 2>/dev/null || echo "❌ Down"
	@echo "Backend:"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo "Frontend:"
	@curl -f http://localhost:3000 2>/dev/null && echo "✅ Healthy" || echo "❌ Down"

# Quick restart
restart: stop dev

# Build only
build:
	@echo "🔨 Building Docker images..."
	docker-compose -f docker-compose.dev.yml build

# Shell access
shell-backend:
	docker-compose -f docker-compose.dev.yml exec backend-dev /bin/bash

shell-frontend:
	docker-compose -f docker-compose.dev.yml exec frontend-dev /bin/sh

shell-dragonfly:
	docker exec cep-dragonfly-dev /bin/sh
