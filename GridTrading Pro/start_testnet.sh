#!/bin/bash

# GridTrading Pro Testnet Startup Script
# Pre-configured for BTC/USDT Futures Trading with 50x Leverage

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_testnet() {
    echo -e "${PURPLE}[TESTNET]${NC} $1"
}

# Display testnet warning
echo "=================================================================="
echo -e "${PURPLE}         GridTrading Pro v2.0.0 - TESTNET MODE${NC}"
echo "=================================================================="
echo -e "${YELLOW}⚠️  WARNING: This is configured for HIGH LEVERAGE trading!${NC}"
echo -e "${YELLOW}⚠️  Trading Pair: BTC/USDT Futures${NC}"
echo -e "${YELLOW}⚠️  Leverage: 50x${NC}"
echo -e "${YELLOW}⚠️  Environment: Binance Testnet${NC}"
echo "=================================================================="
echo

# Confirmation prompt
read -p "Do you want to continue with testnet trading? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Testnet startup cancelled"
    exit 0
fi

# Check if Python is available
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    print_error "Python is not installed or not in PATH"
    exit 1
fi

print_success "Python detected: $($PYTHON_CMD --version)"

# Check and create virtual environment
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

# Install dependencies
print_status "Installing/updating dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies ready"

# Setup testnet environment
print_testnet "Setting up testnet environment..."

# Sync testnet environment file to .env
print_status "Synchronizing environment variables..."
if [ -f ".env.testnet" ]; then
    # Always copy .env.testnet to .env to ensure latest settings
    cp .env.testnet .env
    print_success "✅ Synced .env.testnet → .env"

    # Show key configuration parameters
    echo
    print_testnet "📊 Current Environment Settings:"

    if grep -q "INITIAL_BASE_PRICE=" .env; then
        BASE_PRICE=$(grep "INITIAL_BASE_PRICE=" .env | cut -d'=' -f2)
        print_testnet "   Base Price: $BASE_PRICE USDT"
    fi

    if grep -q "INITIAL_PRINCIPAL=" .env; then
        PRINCIPAL=$(grep "INITIAL_PRINCIPAL=" .env | cut -d'=' -f2)
        print_testnet "   Principal: $PRINCIPAL USDT"
    fi

    if grep -q "ENVIRONMENT=" .env; then
        ENV_TYPE=$(grep "ENVIRONMENT=" .env | cut -d'=' -f2)
        print_testnet "   Environment: $ENV_TYPE"
    fi

    # Verify API keys are set (without showing them)
    if grep -q "BINANCE_API_KEY=" .env && [ -n "$(grep "BINANCE_API_KEY=" .env | cut -d'=' -f2)" ]; then
        print_testnet "   API Key: ✅ Set"
    else
        print_warning "   API Key: ⚠️  Not set or empty"
    fi

    if grep -q "BINANCE_API_SECRET=" .env && [ -n "$(grep "BINANCE_API_SECRET=" .env | cut -d'=' -f2)" ]; then
        print_testnet "   API Secret: ✅ Set"
    else
        print_warning "   API Secret: ⚠️  Not set or empty"
    fi

    echo
    print_success "Environment variables synchronized and verified"
else
    print_error "❌ .env.testnet file not found!"
    print_error "Please create .env.testnet file with your testnet configuration"
    exit 1
fi

# Check if testnet config exists
if [ ! -f "config.testnet.yaml" ]; then
    print_error "Testnet configuration file not found!"
    exit 1
fi

# Create necessary directories
mkdir -p data/backups logs
print_success "Directories created"

# Display configuration summary
echo
print_testnet "=== TESTNET CONFIGURATION SUMMARY ==="
print_testnet "Trading Mode: USDT-M Futures"
print_testnet "Symbol: BTC/USDT"
print_testnet "Leverage: 50x"
print_testnet "Grid Size: 0.5% (dynamic)"
print_testnet "Max Drawdown: -10%"
print_testnet "Daily Loss Limit: -5%"
print_testnet "Web Dashboard: http://localhost:58181"
echo

# Final confirmation
print_warning "⚠️  FINAL WARNING: 50x leverage is extremely risky!"
print_warning "⚠️  Only use testnet funds for testing!"
read -p "Are you sure you want to start? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Testnet startup cancelled"
    exit 0
fi

# Start the application with testnet config
print_testnet "Starting GridTrading Pro in testnet mode..."
echo
$PYTHON_CMD main.py --config config.testnet.yaml --testnet

# Cleanup message
echo
print_testnet "GridTrading Pro testnet session ended"
print_status "Remember to review logs and performance before live trading!"
