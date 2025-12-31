#!/usr/bin/env bash
# ============================================================================
# Security Audit Script for MaverickMCP
# ============================================================================
# Runs comprehensive security checks before pushing code
# Tools: safety (dependency vulnerabilities), bandit (static analysis)
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECURITY_AUDIT_SKIP=${SECURITY_AUDIT_SKIP:-false}
BANDIT_CONFIG=".bandit"
MIN_SEVERITY="medium"

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_tool_installed() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed"
        echo "Install with: pip install $1"
        return 1
    fi
    return 0
}

# ============================================================================
# Main Script
# ============================================================================

print_header "MaverickMCP Security Audit"

# Check if security audit should be skipped
if [ "$SECURITY_AUDIT_SKIP" = "true" ]; then
    print_warning "Security audit skipped (SECURITY_AUDIT_SKIP=true)"
    exit 0
fi

# Track overall status
AUDIT_FAILED=false

# ============================================================================
# 1. Dependency Vulnerability Scanning (safety)
# ============================================================================

print_header "1. Dependency Vulnerability Scanning (safety)"

if check_tool_installed safety; then
    echo "Scanning dependencies for known security vulnerabilities..."
    
    if safety check --json > /tmp/safety_report.json 2>&1; then
        print_success "No known vulnerabilities found in dependencies"
    else
        # Check if it's a real error or just warnings
        if grep -q "vulnerabilities found" /tmp/safety_report.json 2>/dev/null; then
            print_error "Security vulnerabilities found in dependencies!"
            echo ""
            safety check --output=text || true
            echo ""
            print_warning "Review the vulnerabilities above and update dependencies"
            print_warning "To skip this check: export SECURITY_AUDIT_SKIP=true"
            AUDIT_FAILED=true
        else
            print_success "Dependency scan completed (check output for warnings)"
        fi
    fi
else
    print_warning "safety not installed, skipping dependency scan"
    echo "Install with: pip install safety"
fi

# ============================================================================
# 2. Static Security Analysis (bandit)
# ============================================================================

print_header "2. Static Security Analysis (bandit)"

if check_tool_installed bandit; then
    echo "Running static security analysis on Python code..."
    
    # Create bandit config if it doesn't exist
    if [ ! -f ".bandit" ]; then
        print_warning "Creating default .bandit configuration..."
        cat > .bandit << 'BANDITEOF'
[bandit]
# Bandit configuration for MaverickMCP
# https://bandit.readthedocs.io/en/latest/config.html

# Directories to exclude
exclude_dirs = [
    '/tests/',
    '/test_*',
    '/.venv/',
    '/venv/',
    '/build/',
    '/dist/',
    '/__pycache__/'
]

# Test files to skip
skips = ['B101', 'B601']

# Severity level threshold (low, medium, high)
# Only report issues at or above this level
level = 'medium'

# Confidence level threshold (low, medium, high)
confidence = 'medium'
BANDITEOF
        print_success "Created .bandit configuration"
    fi
    
    # Run bandit with configuration
    if bandit -r packages/ -c .bandit -f screen; then
        print_success "No security issues found (medium+ severity)"
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 1 ]; then
            print_error "Security issues found by bandit!"
            echo ""
            print_warning "Review the issues above and fix before pushing"
            print_warning "To see detailed report: bandit -r packages/ -c .bandit -f html -o bandit_report.html"
            print_warning "To skip this check: export SECURITY_AUDIT_SKIP=true"
            AUDIT_FAILED=true
        else
            print_warning "Bandit completed with warnings (review output above)"
        fi
    fi
else
    print_warning "bandit not installed, skipping static analysis"
    echo "Install with: pip install bandit"
fi

# ============================================================================
# 3. Additional Checks (optional but recommended)
# ============================================================================

print_header "3. Additional Security Checks"

# Check for exposed secrets in code
print_warning "Checking for potential exposed secrets..."
if git diff --cached | grep -iE "(password|api[_-]?key|secret|token|bearer)" | grep -v ".env.example" | grep -q "^+"; then
    print_error "Potential secrets found in staged changes!"
    echo ""
    git diff --cached | grep -iE "(password|api[_-]?key|secret|token|bearer)" | grep -v ".env.example" | grep "^+"
    echo ""
    print_warning "Review the lines above and ensure no secrets are committed"
    print_warning "Use environment variables for all secrets"
    AUDIT_FAILED=true
else
    print_success "No obvious secrets detected in staged changes"
fi

# Check for .env file being committed
if git diff --cached --name-only | grep -q "^\.env$"; then
    print_error ".env file is staged for commit!"
    echo ""
    print_warning "The .env file contains secrets and should NEVER be committed"
    print_warning "Run: git restore --staged .env"
    AUDIT_FAILED=true
else
    print_success ".env file not in staged changes"
fi

# ============================================================================
# Summary and Exit
# ============================================================================

print_header "Security Audit Summary"

if [ "$AUDIT_FAILED" = true ]; then
    print_error "Security audit failed! Fix issues before pushing."
    echo ""
    echo "To skip this audit temporarily (not recommended):"
    echo "  export SECURITY_AUDIT_SKIP=true"
    echo ""
    echo "To run audit manually:"
    echo "  make security-audit"
    echo "  ./scripts/security_audit.sh"
    echo ""
    exit 1
else
    print_success "All security checks passed!"
    echo ""
    exit 0
fi
