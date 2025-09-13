#!/bin/bash
# BotArmy Deployment Script Wrapper
# 
# Usage:
#   ./deploy.sh dev              # Deploy to development
#   ./deploy.sh staging          # Deploy to staging
#   ./deploy.sh prod             # Deploy to production
#   ./deploy.sh health-check     # Run health check only
#   ./deploy.sh migrate          # Run migrations only

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if required packages are installed
    if ! python3 -c "import requests, structlog" 2>/dev/null; then
        print_warning "Installing required Python packages..."
        pip3 install requests structlog
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [ENVIRONMENT|COMMAND]"
    echo ""
    echo "Environments:"
    echo "  dev                Deploy to development environment"
    echo "  staging           Deploy to staging environment"
    echo "  prod              Deploy to production environment"
    echo ""
    echo "Commands:"
    echo "  health-check      Run health check only"
    echo "  migrate           Run database migrations only"
    echo "  help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev            # Deploy to development"
    echo "  $0 health-check   # Check application health"
    echo "  $0 migrate        # Run migrations only"
}

# Main deployment logic
main() {
    local command="$1"
    
    case "$command" in
        "dev"|"staging"|"prod")
            print_status "Starting deployment to $command environment..."
            check_python
            python3 deploy.py --environment "$command"
            print_success "Deployment to $command completed successfully!"
            ;;
        "health-check")
            print_status "Running health check..."
            check_python
            python3 deploy.py --health-check
            print_success "Health check completed!"
            ;;
        "migrate")
            print_status "Running database migrations..."
            check_python
            python3 deploy.py --migrate-only
            print_success "Database migrations completed!"
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        "")
            print_error "No environment or command specified"
            show_usage
            exit 1
            ;;
        *)
            print_error "Unknown environment or command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Check if script is being run from correct directory
if [[ ! -f "deploy.py" ]]; then
    print_error "deploy.py not found. Please run this script from the project root directory."
    exit 1
fi

# Run main function with all arguments
main "$@"