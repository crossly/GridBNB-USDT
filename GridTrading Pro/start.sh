#!/bin/bash

# GridTrading Pro Startup Script
# This script helps you start GridTrading Pro with proper environment setup

set -e

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python installation
check_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Check virtual environment
check_venv() {
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating..."
        $PYTHON_CMD -m venv .venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
        print_success "Virtual environment activated (Windows)"
    else
        print_error "Failed to activate virtual environment"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Check configuration
check_config() {
    if [ ! -f "config.yaml" ]; then
        print_warning "config.yaml not found. Please copy and configure it:"
        print_status "cp config.yaml.example config.yaml"
        print_status "Edit config.yaml with your settings"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Please copy and configure it:"
        print_status "cp .env.example .env"
        print_status "Edit .env with your API credentials"
        exit 1
    fi
    
    print_success "Configuration files found"
}

# Create necessary directories
create_directories() {
    mkdir -p data/backups
    mkdir -p logs
    print_success "Directories created"
}

# Main startup function
start_gridtrading() {
    print_status "Starting GridTrading Pro..."
    
    # Parse command line arguments
    ARGS=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --testnet)
                ARGS="$ARGS --testnet"
                print_status "Testnet mode enabled"
                shift
                ;;
            --config)
                ARGS="$ARGS --config $2"
                print_status "Using config file: $2"
                shift 2
                ;;
            --dry-run)
                ARGS="$ARGS --dry-run"
                print_status "Dry run mode enabled"
                shift
                ;;
            *)
                print_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    # Start the application
    $PYTHON_CMD main.py $ARGS
}

# Main script
main() {
    echo "=================================================="
    echo "         GridTrading Pro v2.0.0 Startup"
    echo "=================================================="
    echo
    
    # Check system requirements
    print_status "Checking system requirements..."
    check_python
    
    # Setup environment
    print_status "Setting up environment..."
    check_venv
    install_dependencies
    
    # Check configuration
    print_status "Checking configuration..."
    check_config
    
    # Create directories
    print_status "Creating directories..."
    create_directories
    
    echo
    print_success "Setup complete! Starting GridTrading Pro..."
    echo
    
    # Start the application
    start_gridtrading "$@"
}

# Handle script interruption
trap 'print_warning "Startup interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
