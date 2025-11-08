# Installation

Complete installation guide for Maverick MCP.

## System Requirements

- Python 3.12 or higher
- 4GB RAM minimum (8GB recommended)
- 1GB free disk space
- Internet connection for API access

## Installation Methods

### Method 1: Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# Install dependencies
uv sync
```

### Method 2: Using pip

```bash
# Clone repository
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Next Steps

[Configure your environment →](configuration.md)
