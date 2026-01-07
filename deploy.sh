#!/bin/bash

# Production Deployment Script
# This script deploys the bot system to a production server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_success "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    log_success "Docker Compose is installed: $(docker-compose --version)"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found!"
        log_info "Please create .env file using: cp .env.template .env"
        exit 1
    fi
    log_success ".env file found"
    
    # Check if TELEGRAM_BOT_TOKEN is set
    source .env
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "YOUR_BOT_TOKEN_HERE" ]; then
        log_error "TELEGRAM_BOT_TOKEN not set in .env file!"
        exit 1
    fi
    log_success "TELEGRAM_BOT_TOKEN is configured"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p logs/api
    mkdir -p logs/bot
    mkdir -p logs/web
    mkdir -p data/mongodb
    mkdir -p data/redis
    
    log_success "Directories created"
}

# Set proper permissions
setup_permissions() {
    log_info "Setting up permissions..."
    
    chmod -R 755 logs/
    chmod -R 755 data/
    
    log_success "Permissions set"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    log_success "Docker images built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Services started"
}

# Wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to become healthy..."
    
    # Wait for MongoDB
    log_info "Waiting for MongoDB..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f docker-compose.prod.yml exec -T mongo mongosh --eval "db.adminCommand('ping')" &>/dev/null; then
            log_success "MongoDB is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "MongoDB failed to start"
        exit 1
    fi
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping &>/dev/null; then
            log_success "Redis is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Redis failed to start"
        exit 1
    fi
    
    # Wait for API
    log_info "Waiting for API..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/api/health &>/dev/null; then
            log_success "API is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "API failed to start"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check running containers
    log_info "Running containers:"
    docker-compose -f docker-compose.prod.yml ps
    
    # Check health endpoints
    log_info "Checking health endpoints..."
    
    API_HEALTH=$(curl -s http://localhost:8000/api/health)
    if [ -z "$API_HEALTH" ]; then
        log_error "API health check failed"
        exit 1
    fi
    log_success "API Health: $API_HEALTH"
    
    # Check logs
    log_info "Recent logs from API service:"
    docker-compose -f docker-compose.prod.yml logs --tail=20 centralized-api
    
    log_info "Recent logs from Bot service:"
    docker-compose -f docker-compose.prod.yml logs --tail=20 bot
}

# Display deployment summary
deployment_summary() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
    echo "=========================================="
    echo ""
    echo "Services running on:"
    echo "  API:   http://localhost:8000 (internal only)"
    echo "  Web:   http://localhost:8003 (internal only)"
    echo "  Bot:   Polling active"
    echo ""
    echo "Manage services with:"
    echo "  docker-compose -f docker-compose.prod.yml ps"
    echo "  docker-compose -f docker-compose.prod.yml logs -f"
    echo "  docker-compose -f docker-compose.prod.yml down"
    echo ""
    echo "Important files:"
    echo "  .env                           - Configuration (DO NOT COMMIT)"
    echo "  docker-compose.prod.yml        - Production config"
    echo "  logs/                          - Service logs"
    echo ""
    echo "Next steps:"
    echo "  1. Set up reverse proxy (Nginx/Apache)"
    echo "  2. Configure SSL/TLS certificate"
    echo "  3. Set up monitoring and alerts"
    echo "  4. Configure backups"
    echo "  5. Test /help command in Telegram"
    echo ""
    echo "=========================================="
}

# Main execution
main() {
    log_info "Starting production deployment..."
    echo ""
    
    check_prerequisites
    echo ""
    
    setup_directories
    echo ""
    
    setup_permissions
    echo ""
    
    build_images
    echo ""
    
    start_services
    echo ""
    
    wait_for_services
    echo ""
    
    verify_deployment
    echo ""
    
    deployment_summary
}

# Run main function
main "$@"
