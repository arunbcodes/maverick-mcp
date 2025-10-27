#!/usr/bin/env bash
# ============================================================================
# Git Hooks Setup Script
# ============================================================================
# Installs git hooks for MaverickMCP
# Run this after cloning the repository: ./scripts/setup_git_hooks.sh
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Setting up Git Hooks for MaverickMCP${NC}"
echo -e "${BLUE}============================================================================${NC}\n"

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# ============================================================================
# Pre-Push Hook - Security Audit
# ============================================================================

cat > .git/hooks/pre-push << 'PREPUSH'
#!/usr/bin/env bash
# ============================================================================
# Git Pre-Push Hook - Security Audit
# ============================================================================
# Runs security checks before pushing code to remote repository
# To skip: git push --no-verify (not recommended)
# ============================================================================

echo ""
echo "🔒 Running security audit before push..."
echo ""

# Run security audit script
if [ -f "scripts/security_audit.sh" ]; then
    ./scripts/security_audit.sh
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo ""
        echo "❌ Push aborted due to security audit failure"
        echo ""
        echo "Options:"
        echo "  1. Fix the security issues and try again"
        echo "  2. Skip audit (not recommended): git push --no-verify"
        echo "  3. Skip audit for this session: export SECURITY_AUDIT_SKIP=true"
        echo ""
        exit 1
    fi
else
    echo "⚠️  Warning: security_audit.sh not found, skipping security checks"
fi

echo ""
echo "✓ Security audit passed, proceeding with push..."
echo ""

exit 0
PREPUSH

chmod +x .git/hooks/pre-push

echo -e "${GREEN}✓ Pre-push hook installed${NC}"
echo ""
echo "The following hook has been set up:"
echo "  - pre-push: Runs security audit (safety, bandit, secret detection)"
echo ""
echo "To skip hook during push (not recommended):"
echo "  git push --no-verify"
echo ""
echo -e "${GREEN}Git hooks setup complete!${NC}"
echo ""

