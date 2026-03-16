#!/bin/bash
# OOCAA Docker Startup Script
# This script simplifies common Docker operations for OOCAA

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Visit https://docs.docker.com/get-docker/"
        exit 1
    fi
    if ! command -v docker compose &> /dev/null; then
        echo "Error: Docker Compose is not installed."
        exit 1
    fi
    print_success "Docker and Docker Compose are installed"
}

# Setup environment
setup_env() {
    print_header "Setting up environment variables"
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success ".env file created from .env.example"
            print_warning "Please edit .env with your configuration (especially DB_PASSWORD)"
            return
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Build and start containers
start_containers() {
    print_header "Building and starting Docker containers"
    
    docker compose up -d
    print_success "Containers started"
    
    echo ""
    print_header "Waiting for database to be ready..."
    sleep 5
    
    # Run migrations
    echo "Running database migrations..."
    docker compose exec web python manage.py migrate
    print_success "Database migrations completed"
}

# Create superuser
create_superuser() {
    print_header "Creating admin user"
    
    echo "Run the following command to create a superuser:"
    echo "  docker compose exec web python manage.py createsuperuser"
    echo ""
    echo "Or run:"
    echo "  bash script/create_admin.sh"
}

# Show status and next steps
show_status() {
    print_header "Application Status"
    
    docker compose ps
    
    print_header "Next Steps"
    echo "1. Open your browser: http://localhost:8000"
    echo "2. Create an admin user:"
    echo "   docker compose exec web python manage.py createsuperuser"
    echo "3. Login and start exploring!"
    echo ""
    echo "Useful commands:"
    echo "  - View logs:     docker compose logs -f"
    echo "  - Stop:          docker compose stop"
    echo "  - Start again:   docker compose start"
    echo "  - Full cleanup:  docker compose down -v"
    echo ""
    print_success "OOCAA is ready to use!"
}

# Menu for different operations
show_menu() {
    print_header "OOCAA Docker Control"
    echo "1. Start containers (build if needed)"
    echo "2. Stop containers"
    echo "3. View logs"
    echo "4. Create superuser"
    echo "5. Run migration"
    echo "6. Access web shell"
    echo "7. Access database shell"
    echo "8. Clean everything (WARNING: deletes data)"
    echo "9. Exit"
    echo ""
    read -p "Choose an option (1-9): " choice
    
    case $choice in
        1)
            docker compose up -d
            print_success "Containers started. Access at http://localhost:8000"
            ;;
        2)
            docker compose stop
            print_success "Containers stopped"
            ;;
        3)
            docker compose logs -f
            ;;
        4)
            docker compose exec web python manage.py createsuperuser
            ;;
        5)
            docker compose exec web python manage.py migrate
            print_success "Migrations completed"
            ;;
        6)
            docker compose exec web python manage.py shell
            ;;
        7)
            docker compose exec db psql -U postgres oocaa_db
            ;;
        8)
            read -p "Are you sure? This will delete all data. (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                docker compose down -v
                print_success "Cleaned up"
            else
                print_warning "Cancelled"
            fi
            ;;
        9)
            exit 0
            ;;
        *)
            print_warning "Invalid option"
            ;;
    esac
}

# Main execution
if [ $# -eq 0 ]; then
    # Interactive mode
    check_docker
    setup_env
    start_containers
    create_superuser
    show_status
    
    echo ""
    read -p "Launch interactive control menu? (y/n): " launch_menu
    if [ "$launch_menu" = "y" ]; then
        while true; do
            show_menu
            echo ""
        done
    fi
else
    # Command mode
    case $1 in
        start)
            check_docker
            docker compose up -d
            print_success "OOCAA started at http://localhost:8000"
            ;;
        stop)
            docker compose stop
            print_success "OOCAA stopped"
            ;;
        logs)
            docker compose logs -f
            ;;
        restart)
            docker compose restart
            print_success "OOCAA restarted"
            ;;
        clean)
            docker compose down -v
            print_success "OOCAA cleaned up"
            ;;
        *)
            echo "Usage: $0 {start|stop|logs|restart|clean}"
            ;;
    esac
fi
