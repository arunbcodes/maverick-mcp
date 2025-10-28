#!/usr/bin/env bash
# ============================================================================
# Run Service Tests in Docker (Rancher Desktop Compatible)
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Running Service Tests in Docker${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker is not running or not accessible${NC}"
    echo ""
    echo "For Rancher Desktop users, make sure:"
    echo "  1. Rancher Desktop is running"
    echo "  2. Docker CLI is linked (check: docker ps)"
    echo ""
    exit 1
fi

# Check if backend container is running
if ! docker ps --format '{{.Names}}' | grep -q "maverick-mcp-backend"; then
    echo -e "${YELLOW}⚠️  MaverickMCP backend container is not running${NC}"
    echo ""
    echo "Start it with: docker-compose up -d"
    echo ""
    exit 1
fi

CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep "maverick-mcp-backend" | head -1)

echo -e "${GREEN}✓ Found container: $CONTAINER_NAME${NC}\n"

# Run the tests
echo -e "${BLUE}Running MarketCalendarService tests...${NC}\n"

docker exec "$CONTAINER_NAME" pytest \
    tests/services/test_market_calendar_service.py \
    -v \
    --tb=short \
    --no-cov

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed (exit code: $EXIT_CODE)${NC}"
fi

echo ""
echo "To run with coverage:"
echo "  docker exec $CONTAINER_NAME pytest tests/services/ --cov=maverick_mcp.services --cov-report=term"
echo ""

exit $EXIT_CODE

