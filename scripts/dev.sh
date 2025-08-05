#!/bin/bash
# =============================================================================
# SYMPLLE DEVELOPMENT SCRIPTS
# scripts/dev.sh
# =============================================================================

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function para print colorido
print_status() {
    echo -e "${GREEN}[SYMPLLE]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# =============================================================================
# COMANDOS PRINCIPAIS
# =============================================================================

case "$1" in
    "setup")
        print_status "🚀 Setting up Symplle development environment..."
        
        # Verificar se Docker está rodando
        if ! docker info > /dev/null 2>&1; then
            print_error "Docker is not running. Please start Docker first."
            exit 1
        fi
        
        # Build containers
        print_info "Building containers..."
        docker-compose build
        
        # Start services
        print_info "Starting services..."
        docker-compose up -d postgres redis
        
        # Wait for database
        print_info "Waiting for database to be ready..."
        sleep 10
        
        # Run migrations
        print_info "Running database setup..."
        docker-compose exec postgres psql -U symplle -d symplle_dev -f /docker-entrypoint-initdb.d/init-db.sql
        
        # Start main application
        print_info "Starting Symplle API..."
        docker-compose up -d symplle-api
        
        print_status "✅ Symplle is ready! Access: http://localhost:5000"
        print_info "📊 PgAdmin: http://localhost:8080 (admin@symplle.com / symplle123)"
        print_info "🔴 Redis Commander: http://localhost:8081"
        ;;
        
    "start")
        print_status "🚀 Starting Symplle services..."
        docker-compose up -d
        print_status "✅ All services started!"
        ;;
        
    "stop")
        print_status "🛑 Stopping Symplle services..."
        docker-compose down
        print_status "✅ All services stopped!"
        ;;
        
    "restart")
        print_status "🔄 Restarting Symplle services..."
        docker-compose restart
        print_status "✅ All services restarted!"
        ;;
        
    "logs")
        if [ -z "$2" ]; then
            print_info "📋 Showing all logs..."
            docker-compose logs -f
        else
            print_info "📋 Showing logs for: $2"
            docker-compose logs -f "$2"
        fi
        ;;
        
    "shell")
        service=${2:-symplle-api}
        print_info "🐚 Opening shell in: $service"
        docker-compose exec "$service" /bin/bash
        ;;
        
    "db")
        case "$2" in
            "shell")
                print_info "🗄️ Opening database shell..."
                docker-compose exec postgres psql -U symplle -d symplle_dev
                ;;
            "reset")
                print_warning "⚠️ This will destroy all data! Are you sure? (y/N)"
                read -r response
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                    print_info "🗄️ Resetting database..."
                    docker-compose down
                    docker volume rm symplle-enterprise_postgres_data 2>/dev/null || true
                    docker-compose up -d postgres
                    sleep 10
                    docker-compose exec postgres psql -U symplle -d symplle_dev -f /docker-entrypoint-initdb.d/init-db.sql
                    print_status "✅ Database reset complete!"
                else
                    print_info "Database reset cancelled."
                fi
                ;;
            "backup")
                backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
                print_info "💾 Creating database backup: $backup_file"
                docker-compose exec postgres pg_dump -U symplle symplle_dev > "backups/$backup_file"
                print_status "✅ Backup created: backups/$backup_file"
                ;;
            *)
                print_error "Unknown database command. Use: shell, reset, backup"
                ;;
        esac
        ;;
        
    "test")
        print_info "🧪 Running tests..."
        docker-compose exec symplle-api python -m pytest src/tests/ -v
        ;;
        
    "clean")
        print_warning "🧹 This will remove all containers, volumes, and images. Continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            print_info "🧹 Cleaning up Docker resources..."
            docker-compose down -v --rmi all
            docker system prune -f
            print_status "✅ Cleanup complete!"
        else
            print_info "Cleanup cancelled."
        fi
        ;;
        
    "status")
        print_info "📊 Service Status:"
        docker-compose ps
        echo
        print_info "💾 Volume Usage:"
        docker volume ls | grep symplle
        echo
        print_info "🌐 Network Status:"
        docker network ls | grep symplle
        ;;
        
    "monitoring")
        print_status "📊 Starting monitoring services..."
        docker-compose --profile monitoring up -d
        print_info "🔴 Redis Commander: http://localhost:8081"
        print_info "📊 PgAdmin: http://localhost:8080"
        ;;
        
    "build")
        print_info "🔨 Building Symplle containers..."
        docker-compose build --no-cache
        print_status "✅ Build complete!"
        ;;
        
    "deploy")
        print_status "🚀 Preparing for deployment..."
        
        # Build production image
        print_info "Building production image..."
        docker build --target production -t symplle-enterprise:latest .
        
        # Run security scan
        print_info "Running security scan..."
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            -v $(pwd):/app aquasec/trivy image symplle-enterprise:latest
        
        print_status "✅ Ready for deployment!"
        ;;
        
    "help"|*)
        echo -e "${GREEN}Symplle Development Helper${NC}"
        echo
        echo "Usage: ./scripts/dev.sh [command]"
        echo
        echo "Commands:"
        echo "  setup      - Initial setup (first time only)"
        echo "  start      - Start all services"
        echo "  stop       - Stop all services"
        echo "  restart    - Restart all services"
        echo "  logs       - Show logs (optional: service name)"
        echo "  shell      - Open shell in container (optional: service name)"
        echo "  db         - Database operations (shell|reset|backup)"
        echo "  test       - Run tests"
        echo "  clean      - Clean all Docker resources"
        echo "  status     - Show service status"
        echo "  monitoring - Start monitoring services"
        echo "  build      - Build containers"
        echo "  deploy     - Prepare for deployment"
        echo "  help       - Show this help"
        echo
        echo "Examples:"
        echo "  ./scripts/dev.sh setup"
        echo "  ./scripts/dev.sh logs symplle-api"
        echo "  ./scripts/dev.sh shell postgres"
        echo "  ./scripts/dev.sh db shell"
        ;;
esac