#!/bin/bash
# Run test coverage and generate reports

set -e

echo "🧪 Running tests with coverage..."
echo ""

# Run pytest with coverage
pytest

echo ""
echo "📊 Coverage Report Generated:"
echo "  - Terminal: Above"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo ""
echo "💡 To view HTML report:"
echo "  open htmlcov/index.html    # macOS"
echo "  xdg-open htmlcov/index.html # Linux"
echo "  start htmlcov/index.html   # Windows"
echo ""

