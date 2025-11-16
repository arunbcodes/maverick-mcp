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
    echo "Database is empty - Running stock market seeding"
    echo "=================================================="
    echo ""
    echo "This will seed:"
    echo "  • S&P 500 stocks (~520 US stocks)"
    echo "  • Nifty 50 stocks (~50 Indian stocks)"
    echo ""
    echo "Estimated time: 3-12 minutes"
    echo ""

    # Run S&P 500 seed script
    echo "1/2: Seeding S&P 500 stocks..."
    if python /app/scripts/seed_sp500.py; then
        echo "✅ S&P 500 seeding completed!"
    else
        echo "⚠️  S&P 500 seeding failed (continuing anyway)"
    fi

    echo ""
    
    # Run Indian stocks seed script
    echo "2/2: Seeding Indian stocks..."
    if python /app/scripts/seed_indian_stocks.py; then
        echo "✅ Indian stocks seeding completed!"
    else
        echo "⚠️  Indian stocks seeding failed (continuing anyway)"
    fi

    echo ""
    echo "=================================================="
    echo "✅ Database seeding completed!"
    echo "=================================================="
    echo ""
    return 0
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
