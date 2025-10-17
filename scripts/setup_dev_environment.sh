#!/bin/bash
# Development Environment Setup Script for MaverickMCP
# This script sets up everything needed to run tests and develop Phase 2

set -e  # Exit on error

echo "🚀 Setting up MaverickMCP Development Environment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "\n${BLUE}1. Checking Python version...${NC}"
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    echo -e "${RED}   ❌ Python 3.12+ required. Please upgrade Python.${NC}"
    exit 1
fi
echo -e "${GREEN}   ✅ Python version is compatible${NC}"

# Check if uv is installed
echo -e "\n${BLUE}2. Checking for uv package manager...${NC}"
if command -v uv &> /dev/null; then
    echo -e "${GREEN}   ✅ uv is installed${NC}"
    UV_AVAILABLE=true
else
    echo -e "${YELLOW}   ⚠️  uv not found${NC}"
    echo "   Would you like to install uv (recommended)? It's much faster than pip."
    echo "   Installation: curl -LsSf https://astral.sh/uv/install.sh | sh"
    UV_AVAILABLE=false
fi

# Setup virtual environment
echo -e "\n${BLUE}3. Setting up virtual environment...${NC}"

if [ "$UV_AVAILABLE" = true ]; then
    echo "   Using uv to create environment..."
    uv venv
    echo -e "${GREEN}   ✅ Virtual environment created with uv${NC}"
else
    if [ ! -d ".venv" ]; then
        echo "   Creating virtual environment with venv..."
        python -m venv .venv
        echo -e "${GREEN}   ✅ Virtual environment created${NC}"
    else
        echo -e "${GREEN}   ✅ Virtual environment already exists${NC}"
    fi
fi

# Activate virtual environment
echo -e "\n${BLUE}4. Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}   ✅ Virtual environment activated${NC}"

# Install dependencies
echo -e "\n${BLUE}5. Installing dependencies...${NC}"

if [ "$UV_AVAILABLE" = true ]; then
    echo "   Using uv sync (fast)..."
    uv sync
else
    echo "   Using pip (traditional)..."
    pip install --upgrade pip
    pip install -e ".[dev]"
fi

echo -e "${GREEN}   ✅ Dependencies installed${NC}"

# Check TA-Lib
echo -e "\n${BLUE}6. Checking TA-Lib installation...${NC}"
if python -c "import talib" 2>/dev/null; then
    echo -e "${GREEN}   ✅ TA-Lib is installed${NC}"
else
    echo -e "${YELLOW}   ⚠️  TA-Lib not found${NC}"
    echo "   TA-Lib is required for technical analysis."
    echo "   Installation:"
    echo "   - macOS: brew install ta-lib"
    echo "   - Linux: See https://ta-lib.github.io/ta-lib-python/"
    echo "   - Windows: Use conda or pre-built wheels"
fi

# Create .env if it doesn't exist
echo -e "\n${BLUE}7. Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}   ⚠️  Created .env from .env.example${NC}"
    echo "   Please add your API keys to .env"
else
    echo -e "${GREEN}   ✅ .env file already exists${NC}"
fi

# Check Redis
echo -e "\n${BLUE}8. Checking Redis (optional)...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}   ✅ Redis is installed and running${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Redis installed but not running${NC}"
        echo "   Start with: brew services start redis"
    fi
else
    echo -e "${YELLOW}   ⚠️  Redis not installed (optional)${NC}"
    echo "   Install with: brew install redis"
fi

# Summary
echo -e "\n${GREEN}=================================================="
echo "✅ Development Environment Setup Complete!"
echo "==================================================${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Activate environment: source .venv/bin/activate"
echo "2. Add API keys to .env file"
echo "3. Run migrations: make migrate"
echo "4. Run tests: pytest tests/test_multi_market.py -v"
echo "5. Start server: make dev"

echo -e "\n${BLUE}Quick Commands:${NC}"
echo "- Run Phase 1 tests: pytest tests/test_multi_market.py -v -m 'not integration'"
echo "- Run all tests: pytest tests/test_multi_market.py -v"
echo "- Check code: make lint"
echo "- Start development: make dev"

echo -e "\n${YELLOW}Note:${NC} If using traditional venv, always activate with:"
echo "      source .venv/bin/activate"

