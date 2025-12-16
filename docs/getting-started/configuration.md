# Configuration

Configure Maverick MCP with your API keys and settings.

## Environment Variables

All configuration is done through environment variables stored in a `.env` file.

### Required Configuration

```ini
# Required - Stock Data Provider
TIINGO_API_KEY=your-tiingo-key-here
```

Get a free Tiingo API key at [tiingo.com](https://tiingo.com) - includes 500 requests/day.

### Recommended Configuration

```ini
# AI Features (Highly Recommended)
OPENROUTER_API_KEY=your-openrouter-key-here

# For RAG Q&A (Required for conference call queries)
OPENAI_API_KEY=your-openai-key-here
```

### Optional Configuration

```ini
# Enhanced Data
FRED_API_KEY=your-fred-key-here
EXA_API_KEY=your-exa-key-here

# Database (SQLite by default)
DATABASE_URL=postgresql://localhost/maverick_mcp

# Redis Caching
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Configuration File

Create `.env` in the project root:

```bash
cp .env.example .env
nano .env  # Edit with your keys
```

## API Key Details

### Tiingo (Required)
- **Purpose**: Stock market data (prices, fundamentals)
- **Free Tier**: 500 requests/day
- **Sign Up**: [tiingo.com](https://tiingo.com)
- **Cost**: Free tier sufficient for personal use

### OpenRouter (Recommended)
- **Purpose**: AI analysis, natural language search, stock explanations
- **Pricing**: Pay-as-you-go, access to 400+ models
- **Sign Up**: [openrouter.ai](https://openrouter.ai)
- **Cost**: ~$0.01-0.05 per analysis
- **Without it**: App falls back to rule-based parsing (functional but less accurate)

### OpenAI (Optional - RAG Only)
- **Purpose**: Embeddings for RAG Q&A
- **Required For**: Conference call Q&A feature
- **Sign Up**: [platform.openai.com](https://platform.openai.com)
- **Cost**: ~$0.0001 per transcript

### FRED (Optional)
- **Purpose**: Economic indicators
- **Free**: Unlimited
- **Sign Up**: [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)

### Exa (Optional)
- **Purpose**: Web search for research
- **Sign Up**: [exa.ai](https://exa.ai)

## Database Configuration

### SQLite (Default)
No configuration needed. Database created automatically at:
```
~/.maverick_mcp/maverick_mcp.db
```

### PostgreSQL (Optional)
For better performance with large datasets:

```bash
# Install PostgreSQL
brew install postgresql

# Create database
createdb maverick_mcp

# Add to .env
DATABASE_URL=postgresql://localhost/maverick_mcp

# Run migrations
make migrate
```

## Caching Configuration

### In-Memory (Default)
Works out of the box, no setup required.

### Redis (Recommended)
For better performance:

```bash
# Install Redis
brew install redis

# Start Redis
brew services start redis

# Add to .env
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Docker Configuration

When running with Docker, configure environment variables in `docker/.env`:

```bash
# Copy template
cp docker/env.example docker/.env

# Edit with your keys
nano docker/.env
```

**Required for Docker:**
```ini
TIINGO_API_KEY=your-tiingo-key

# For AI features (natural language search, explanations)
OPENROUTER_API_KEY=your-openrouter-key
```

## Security

### Protect API Keys

```bash
# Set proper permissions
chmod 600 .env
chmod 600 docker/.env
```

### Pre-commit Hooks

The repository includes gitleaks pre-commit hooks to prevent accidental secret commits:

```bash
# Install pre-commit
pip install pre-commit

# Install gitleaks
brew install gitleaks  # macOS

# Activate hooks
pre-commit install

# Verify no secrets
pre-commit run --all-files
```

### Gitignore

The `.gitignore` protects these files:
```
.env
.env.*
docker/.env
docker/.env.*
*.pem
*.key
```

### Never Commit

Never commit API keys to version control!

## Verification

Test your configuration:

```bash
# Start server
make dev

# Check logs for any errors
make tail-log
```

## Next Steps

- [Quick Start Guide](quick-start.md)
- [Claude Desktop Setup](claude-desktop-setup.md)
- [Cursor IDE Setup](cursor-setup.md)
