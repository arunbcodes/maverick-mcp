# Security Audit Automation

MaverickMCP includes automated security auditing to help maintain code security and prevent common vulnerabilities.

## Overview

The security audit system includes:

- **Dependency vulnerability scanning** with `safety`
- **Static security analysis** with `bandit`
- **Secret detection** to prevent accidental commits
- **Automated pre-push hooks** to run checks before pushing code

## Quick Start

### 1. Install Security Tools

```bash
make security-install
```

This installs:

- `safety`: Scans dependencies for known security vulnerabilities
- `bandit`: Static analysis tool for Python code security issues

### 2. Set Up Git Hooks (Recommended)

```bash
make setup-hooks
```

This installs a pre-push hook that automatically runs security audits before pushing code to the remote repository.

### 3. Run Security Audit Manually

```bash
make security-audit
```

Or directly:

```bash
./scripts/security_audit.sh
```

## What Gets Checked

### 1. Dependency Vulnerabilities (safety)

Scans all project dependencies against a database of known security vulnerabilities:

```bash
safety check
```

**What it catches:**

- Known CVEs in dependencies
- Deprecated packages with security issues
- Vulnerable package versions

**Example output:**

```
✓ No known vulnerabilities found in dependencies
```

### 2. Static Security Analysis (bandit)

Analyzes Python code for common security issues:

```bash
bandit -r maverick_mcp/ -c .bandit
```

**What it catches:**

- Hardcoded passwords, API keys, tokens
- SQL injection vulnerabilities
- Use of insecure functions (eval, exec, pickle)
- Weak cryptography
- Command injection risks
- Path traversal vulnerabilities

**Example issues:**

- `B105`: Hardcoded password in code
- `B201`: Flask app with debug=True
- `B608`: SQL injection via string formatting

### 3. Secret Detection

Scans staged git changes for potential secrets:

**What it catches:**

- API keys, passwords, tokens in code
- `.env` file accidentally staged
- Bearer tokens, authentication credentials

**Patterns detected:**

- `password`, `api_key`, `secret`, `token`
- `bearer`, `auth`, `credential`
- And more...

## Configuration

### Bandit Configuration

Edit `.bandit` to customize security checks:

```ini
[bandit]
# Directories to exclude
exclude_dirs = ['/tests/', '/.venv/']

# Tests to skip
skips = ['B101', 'B601']

# Severity level (low, medium, high)
level = 'medium'

# Confidence level (low, medium, high)
confidence = 'medium'
```

### Skip Security Audit

**Not recommended**, but you can skip security checks:

```bash
# Skip for single push (bypass pre-push hook)
git push --no-verify

# Skip for terminal session
export SECURITY_AUDIT_SKIP=true
git push
```

## Pre-Push Hook

The pre-push hook automatically runs security audits before pushing code.

### How It Works

1. You run `git push`
2. Hook executes `./scripts/security_audit.sh`
3. If audit **passes** → push proceeds
4. If audit **fails** → push is aborted with error details

### Install/Reinstall Hook

```bash
./scripts/setup_git_hooks.sh
```

### Remove Hook

```bash
rm .git/hooks/pre-push
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Security Audit
  run: |
    pip install safety bandit
    ./scripts/security_audit.sh
```

```yaml
# GitLab CI example
security_audit:
  script:
    - pip install safety bandit
    - ./scripts/security_audit.sh
```

## Common Issues

### Issue: safety check fails due to outdated database

**Solution:**

```bash
safety check --db
```

### Issue: bandit reports false positives

**Solution:** Add skip codes to `.bandit`:

```ini
skips = ['B101', 'B601', 'B404']
```

### Issue: Secret detected in staged changes

**Solution:**

1. Remove the secret from code
2. Use environment variables instead
3. Update `.env` file (not committed)
4. Unstage if accidentally staged: `git restore --staged .env`

### Issue: Want to skip audit temporarily

**Solution:**

```bash
# Skip this push only
git push --no-verify

# Skip for session
export SECURITY_AUDIT_SKIP=true
```

## Best Practices

### DO

✅ Run security audit before every push
✅ Keep security tools up to date
✅ Fix security issues immediately
✅ Use environment variables for secrets
✅ Review audit output carefully
✅ Add security audit to CI/CD

### DON'T

❌ Commit `.env` file
❌ Hardcode API keys in code
❌ Skip security audits routinely
❌ Ignore security warnings
❌ Use `--no-verify` by default

## Security Tools Documentation

- **safety**: https://github.com/pyupio/safety
- **bandit**: https://bandit.readthedocs.io/
- **Security Best Practices**: See `SECURITY.md`

## Troubleshooting

### Permission denied: ./scripts/security_audit.sh

**Fix:**

```bash
chmod +x scripts/security_audit.sh
chmod +x scripts/setup_git_hooks.sh
```

### Hook not running

**Fix:**

```bash
# Reinstall hooks
./scripts/setup_git_hooks.sh

# Verify hook exists
ls -la .git/hooks/pre-push
```

### Security tools not found

**Fix:**

```bash
# Install tools
make security-install

# Or manually
pip install safety bandit
```

## Reporting Security Issues

Found a security vulnerability? See `SECURITY.md` for reporting instructions.

**DO NOT** open public GitHub issues for security vulnerabilities.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [MaverickMCP Security Policy](../SECURITY.md)
