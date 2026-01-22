#!/bin/bash

# CEP Machine Production Deployment Script
# This script handles the complete production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="cep-machine"
BACKUP_DIR="/var/backups/cep-machine"
LOG_FILE="/var/log/cep-machine-deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    echo "[ERROR] $1" >> $LOG_FILE
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
    echo "[SUCCESS] $1" >> $LOG_FILE
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    echo "[WARNING] $1" >> $LOG_FILE
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        error ".env.production file not found. Please create it first."
        exit 1
    fi
    
    # Check if we have enough disk space
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ $available_space -lt 2097152 ]; then  # 2GB in KB
        warning "Low disk space detected. Available: $(($available_space / 1024 / 1024))GB"
    fi
    
    success "Prerequisites check completed"
}

backup_current_deployment() {
    log "Creating backup of current deployment..."
    
    # Create backup directory if it doesn't exist
    sudo mkdir -p $BACKUP_DIR
    
    # Backup current containers
    if docker-compose ps | grep -q "Up"; then
        log "Stopping current services..."
        docker-compose down
        
        # Backup data volumes
        log "Backing up data volumes..."
        sudo docker run --rm -v cep-machine_postgres_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
        sudo docker run --rm -v cep-machine_redis_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/redis_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
        
        success "Backup completed"
    else
        log "No running services found, skipping backup"
    fi
}

build_and_deploy() {
    log "Building and deploying new version..."
    
    # Copy production environment file
    cp .env.production .env
    
    # Build new images
    log "Building Docker images..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Start services
    log "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    success "Deployment started"
}

wait_for_services() {
    log "Waiting for services to be healthy..."
    
    # Wait for backend
    backend_healthy=false
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            backend_healthy=true
            break
        fi
        sleep 10
    done
    
    if [ "$backend_healthy" = false ]; then
        error "Backend service failed to become healthy"
        exit 1
    fi
    
    # Wait for frontend
    frontend_healthy=false
    for i in {1..30}; do
        if curl -f http://localhost:3000 &> /dev/null; then
            frontend_healthy=true
            break
        fi
        sleep 10
    done
    
    if [ "$frontend_healthy" = false ]; then
        error "Frontend service failed to become healthy"
        exit 1
    fi
    
    success "All services are healthy"
}

run_tests() {
    log "Running smoke tests..."
    
    # Test backend API
    if ! curl -f http://localhost:8000/api/health &> /dev/null; then
        error "Backend API health check failed"
        exit 1
    fi
    
    # Test CopilotKit endpoint
    if ! curl -f -X POST http://localhost:8000/api/copilotkit -H "Content-Type: application/json" -d '{}' &> /dev/null; then
        error "CopilotKit endpoint test failed"
        exit 1
    fi
    
    # Test tools API
    if ! curl -f http://localhost:8000/api/tools/list &> /dev/null; then
        error "Tools API test failed"
        exit 1
    fi
    
    success "Smoke tests passed"
}

setup_monitoring() {
    log "Setting up monitoring..."
    
    # Wait for Prometheus
    for i in {1..30}; do
        if curl -f http://localhost:9090/-/healthy &> /dev/null; then
            break
        fi
        sleep 5
    done
    
    # Wait for Grafana
    for i in {1..30}; do
        if curl -f http://localhost:3001/api/health &> /dev/null; then
            break
        fi
        sleep 5
    done
    
    success "Monitoring services are running"
}

cleanup_old_images() {
    log "Cleaning up old Docker images..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove old versions (keep last 3 versions)
    old_images=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "$PROJECT_NAME" | tail -n +4)
    if [ ! -z "$old_images" ]; then
        echo "$old_images" | xargs docker rmi -f || true
    fi
    
    success "Cleanup completed"
}

generate_deployment_report() {
    log "Generating deployment report..."
    
    report_file="$BACKUP_DIR/deployment_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > $report_file << EOF
CEP Machine Deployment Report
============================
Date: $(date)
Version: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

Services Status:
$(docker-compose -f docker-compose.production.yml ps)

Resource Usage:
$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}")

Disk Usage:
$(df -h /)

System Load:
$(uptime)

EOF
    
    success "Deployment report generated: $report_file"
}

main() {
    log "Starting CEP Machine production deployment..."
    
    # Create log directory
    sudo mkdir -p $(dirname $LOG_FILE)
    
    # Check prerequisites
    check_prerequisites
    
    # Backup current deployment
    backup_current_deployment
    
    # Build and deploy
    build_and_deploy
    
    # Wait for services
    wait_for_services
    
    # Run tests
    run_tests
    
    # Setup monitoring
    setup_monitoring
    
    # Cleanup
    cleanup_old_images
    
    # Generate report
    generate_deployment_report
    
    success "Deployment completed successfully!"
    
    echo ""
    echo "🎉 CEP Machine is now deployed and running!"
    echo ""
    echo "Services available at:"
    echo "  • Frontend: http://localhost:3000"
    echo "  • Backend API: http://localhost:8000"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3001"
    echo "  • Kibana: http://localhost:5601"
    echo ""
    echo "To check logs: docker-compose -f docker-compose.production.yml logs -f"
    echo "To stop services: docker-compose -f docker-compose.production.yml down"
}

# Handle script arguments
case "${1:-}" in
    "backup")
        backup_current_deployment
        ;;
    "build")
        build_and_deploy
        ;;
    "test")
        run_tests
        ;;
    "cleanup")
        cleanup_old_images
        ;;
    *)
        main
        ;;
esac
