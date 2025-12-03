#!/usr/bin/env bash
# Generate TypeScript API client from OpenAPI spec
# Usage: ./scripts/generate-api-client.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
OPENAPI_URL="${OPENAPI_URL:-http://localhost:8000/api/openapi.json}"
OUTPUT_DIR="$PROJECT_ROOT/packages-js/api-client/src/generated"

echo "=== Maverick API Client Generator ==="
echo "OpenAPI URL: $OPENAPI_URL"
echo "Output dir: $OUTPUT_DIR"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Check if API server is running
if ! curl -s "$OPENAPI_URL" > /dev/null 2>&1; then
    echo "Error: API server not running at $OPENAPI_URL"
    echo "Start the API with: docker-compose -f docker-compose.api.yml up"
    exit 1
fi

# Generate client using openapi-generator-cli
# Requires: npm install -g @openapitools/openapi-generator-cli
if command -v openapi-generator-cli &> /dev/null; then
    openapi-generator-cli generate \
        -i "$OPENAPI_URL" \
        -g typescript-fetch \
        -o "$OUTPUT_DIR" \
        --additional-properties=supportsES6=true,typescriptThreePlus=true,withInterfaces=true
    
    echo "✅ API client generated at $OUTPUT_DIR"
else
    echo "Warning: openapi-generator-cli not installed"
    echo "Install with: npm install -g @openapitools/openapi-generator-cli"
    echo ""
    echo "Alternative: Download OpenAPI spec manually:"
    echo "  curl $OPENAPI_URL > openapi.json"
fi

