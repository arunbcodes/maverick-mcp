#!/bin/bash
set -e

echo "=================================================="
echo "Maverick MCP - Docker Entrypoint"
echo "=================================================="

# Function to check if database is seeded
check_database_seeded() {
    echo "Checking if database is seeded..." >&2

    # Try to count stocks in database
    stock_count=$(python -c "
from maverick_mcp.data.models import engine, Stock
from sqlalchemy.orm import Session
try:
    with Session(engine) as session:
        count = session.query(Stock).count()
        print(count)
except Exception:
    print('0')
" 2>/dev/null || echo "0")

    echo "Found $stock_count stocks in database" >&2
    echo "$stock_count"
}

# Function to seed database
seed_database() {
    echo ""
    echo "=================================================="
    echo "Database is empty - Running S&P 500 seeding"
    echo "=================================================="
    echo ""
    echo "This will:"
    echo "  - Fetch S&P 500 company list from Wikipedia"
    echo "  - Enrich with data from yfinance API"
    echo "  - Create ~520 stock records"
    echo "  - Generate screening recommendations"
    echo ""
    echo "Estimated time: 2-10 minutes"
    echo ""

    # Run the seed script
    if python /app/scripts/seed_sp500.py; then
        echo ""
        echo "=================================================="
        echo "✅ Database seeding completed successfully!"
        echo "=================================================="
        echo ""
        return 0
    else
        echo ""
        echo "=================================================="
        echo "⚠️  Database seeding failed"
        echo "=================================================="
        echo ""
        echo "The server will start anyway, but screening tools"
        echo "may return empty results."
        echo ""
        echo "You can manually seed later with:"
        echo "  docker exec <container> python /app/scripts/seed_sp500.py"
        echo ""
        return 1
    fi
}

# Main entrypoint logic
main() {
    # Wait a bit for database to be ready
    echo "Waiting for database to be ready..."
    sleep 2

    # Check if database needs seeding
    stock_count=$(check_database_seeded)

    if [ "$stock_count" -lt 10 ]; then
        echo ""
        echo "Database has fewer than 10 stocks - seeding required"
        seed_database
    else
        echo ""
        echo "=================================================="
        echo "✅ Database already seeded ($stock_count stocks)"
        echo "=================================================="
        echo ""
    fi

    # Start the MCP server with passed arguments
    echo "Starting Maverick MCP server..."
    echo "Command: $@"
    echo ""
    exec "$@"
}

# Run main function
main "$@"
