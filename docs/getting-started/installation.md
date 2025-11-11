# Installation

Complete installation guide for Maverick MCP.

## System Requirements

### Minimum Requirements
- **Python**: 3.12 or higher
- **RAM**: 4GB minimum
- **Disk Space**: 1GB free
- **Internet**: For API access

### Recommended
- **RAM**: 8GB+
- **Redis**: For caching
- **PostgreSQL**: For better database performance

## Installation Methods

### Method 1: Using uv (Recommended - Fastest)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager.

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone repository
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# 3. Install dependencies (very fast!)
uv sync

# 4. Done! Dependencies installed
```

### Method 2: Using pip (Traditional)

```bash
# 1. Clone repository
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -e .

# 5. Done!
```

## Post-Installation Setup

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

Add your keys:
```ini
TIINGO_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here  # For AI features
OPENAI_API_KEY=your-key-here      # For RAG Q&A
```

### 2. Verify Installation

```bash
# Test server starts
make dev

# Should see:
# INFO: Server started on http://localhost:8003
# INFO: 40+ tools registered
```

### 3. Check Database

Database is created automatically with S&P 500 data:

```bash
# Check database location
ls ~/.maverick_mcp/maverick_mcp.db

# Verify S&P 500 data seeded
# Should see logs about 520+ stocks loaded
```

## Optional Components

### Redis (Recommended)

For better caching performance:

=== "macOS"
    ```bash
    brew install redis
    brew services start redis
    ```

=== "Ubuntu/Debian"
    ```bash
    sudo apt update
    sudo apt install redis-server
    sudo systemctl start redis
    ```

=== "Windows"
    Download from [redis.io/download](https://redis.io/download)

### PostgreSQL (Optional)

For larger datasets:

=== "macOS"
    ```bash
    brew install postgresql
    brew services start postgresql
    createdb maverick_mcp
    ```

=== "Ubuntu/Debian"
    ```bash
    sudo apt install postgresql
    sudo systemctl start postgresql
    sudo -u postgres createdb maverick_mcp
    ```

=== "Windows"
    Download from [postgresql.org/download](https://www.postgresql.org/download/)

## Troubleshooting

### Python Version

```bash
python --version  # Should be 3.12+
```

If older:

=== "macOS"
    ```bash
    brew install python@3.12
    ```

=== "Ubuntu"
    ```bash
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.12
    ```

### Permission Errors

```bash
# macOS/Linux
chmod +x scripts/*.sh

# Fix .env permissions
chmod 600 .env
```

### Missing Dependencies

```bash
# Reinstall
pip install --force-reinstall -e .

# Or with uv
uv sync --reinstall
```

### Port 8003 in Use

```bash
# Find process
lsof -i :8003

# Kill it
kill -9 <PID>
```

## Verify Everything Works

Run these commands to verify installation:

```bash
# 1. Check Python version
python --version

# 2. Activate environment (if using pip)
source .venv/bin/activate

# 3. Start server
make dev

# 4. In another terminal, check it's running
lsof -i :8003

# 5. View logs
make tail-log
```

## Next Steps

Installation complete! Now:

1. [Configure your API keys](configuration.md)
2. [Start using with Quick Start guide](quick-start.md)
3. [Connect to Claude Desktop](claude-desktop-setup.md)
4. [Or use with Cursor IDE](cursor-setup.md)

## Uninstallation

To remove Maverick MCP:

```bash
# Stop server
make stop

# Remove virtual environment
rm -rf .venv

# Remove database (optional)
rm -rf ~/.maverick_mcp

# Remove repository
cd ..
rm -rf maverick-mcp
```

## Updating

To update to the latest version:

```bash
cd maverick-mcp
git pull origin main

# Reinstall dependencies
uv sync  # or pip install -e .

# Restart server
make stop
make dev
```
