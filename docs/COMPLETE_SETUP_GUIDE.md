# Complete Setup Guide for MaverickMCP

**Step-by-step guide to run MaverickMCP with full functionality.**

Choose your setup path:

- **🚀 Quick Start (Docker)** - Easiest, everything handled for you
- **💻 Local Development** - More control, faster iteration

---

## 🚀 **Option 1: Docker Setup (Easiest - Recommended for First Time)**

Docker automatically handles PostgreSQL, Redis, and all services.

### Prerequisites

1. **Install Docker Desktop**

   - macOS: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: `sudo apt-get install docker-compose`
   - Windows: [Download Docker Desktop](https://www.docker.com/products/docker-desktop)

2. **Verify Docker is running:**
   ```bash
   docker --version
   docker-compose --version
   ```

### Step-by-Step

**Step 1: Clone the repository**

```bash
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp
```

**Step 2: Create `.env` file**

```bash
# Create .env file
touch .env

# Add your API keys (see below for what's needed)
nano .env  # or use your favorite editor
```

**Minimum `.env` for Docker:**

```bash
# REQUIRED
TIINGO_API_KEY=your_tiingo_key_here

# OPTIONAL (but recommended for full functionality)
OPENROUTER_API_KEY=sk-or-v1-your_key_here
EXA_API_KEY=your_exa_key_here

# These are auto-configured by Docker
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/maverick_mcp
REDIS_HOST=redis
REDIS_PORT=6379
CACHE_ENABLED=true
```

**Step 3: Start everything with Docker**

```bash
# Build and start all services (PostgreSQL, Redis, MaverickMCP)
make docker-up

# Or manually:
docker-compose up --build -d
```

**This automatically starts:**

- ✅ PostgreSQL database (localhost:55432)
- ✅ Redis cache (localhost:56379)
- ✅ MaverickMCP server (localhost:8003)

**Step 4: Verify it's running**

```bash
# Check logs
make docker-logs

# Or manually:
docker-compose logs -f

# Check containers are running
docker ps
```

You should see 3 containers:

- `maverick-mcp-backend-1`
- `maverick-mcp-postgres-1`
- `maverick-mcp-redis-1`

**Step 5: Test the setup**

```bash
# The API should be accessible
curl http://localhost:8003/health

# Expected response: {"status": "ok"}
```

**Step 6: Connect to Claude Desktop**

Edit your Claude Desktop config:

```bash
# macOS
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
nano ~/.config/Claude/claude_desktop_config.json

# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json
```

Add MaverickMCP:

```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "maverick-mcp-backend-1",
        "python",
        "-m",
        "maverick_mcp.api.server"
      ]
    }
  }
}
```

**Step 7: Restart Claude Desktop**

Done! 🎉 You now have full functionality!

### Managing Docker Services

```bash
# Stop all services
make docker-down

# View logs
make docker-logs

# Restart services
docker-compose restart

# Check status
docker ps
```

---

## 💻 **Option 2: Local Development (More Control)**

Run services locally without Docker. You choose what to install.

### Prerequisites

1. **Python 3.12+**

   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **Install uv (Python package manager)**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.zshrc  # or ~/.bashrc
   ```

3. **Install TA-Lib (for technical analysis)**

   ```bash
   # macOS
   brew install ta-lib

   # Ubuntu/Debian
   sudo apt-get install ta-lib

   # Or from source (all platforms)
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install
   ```

### Step-by-Step

**Step 1: Clone and setup**

```bash
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# Install dependencies
uv sync
```

**Step 2: Choose your database option**

You have 2 choices:

#### **Option A: SQLite (Easiest - No setup needed)**

Default! Works out of the box, perfect for development.

```bash
# No configuration needed! Just don't set DATABASE_URL
# Creates maverick.db in your project directory
```

**Pros:**

- ✅ Zero setup
- ✅ No separate database server
- ✅ Perfect for development

**Cons:**

- ❌ Not suitable for production
- ❌ No concurrent writes
- ❌ Limited scalability

#### **Option B: PostgreSQL (Production-ready)**

Better performance and features.

**Install PostgreSQL:**

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get install postgresql-15
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify it's running
psql --version
```

**Create database:**

```bash
# Connect to PostgreSQL
psql postgres

# In psql:
CREATE DATABASE maverick_mcp;
CREATE USER maverick WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE maverick_mcp TO maverick;
\q
```

**Configure `.env`:**

```bash
DATABASE_URL=postgresql://maverick:your_password@localhost:5432/maverick_mcp
```

**Step 3: Choose your cache option**

Redis is **optional** but **recommended** for caching.

#### **Option A: Without Redis (Works fine)**

```bash
# In .env
CACHE_ENABLED=false

# Or just don't set it
```

**Pros:**

- ✅ No setup needed
- ✅ Works fine for light usage

**Cons:**

- ❌ No caching = more API calls = slower
- ❌ Hit rate limits faster

#### **Option B: With Redis (Recommended)**

**Install Redis:**

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis
sudo systemctl start redis
sudo systemctl enable redis

# Verify it's running
redis-cli ping
# Should respond: PONG
```

**Configure `.env`:**

```bash
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL_SECONDS=3600
```

**Managing Redis:**

```bash
# Start
make redis-start
# Or: brew services start redis (macOS)

# Stop
make redis-stop
# Or: brew services stop redis (macOS)

# Check status
redis-cli ping
```

**Step 4: Create `.env` file**

```bash
touch .env
nano .env
```

**Complete `.env` template:**

```bash
# ========================================
# REQUIRED - Won't work without this
# ========================================
TIINGO_API_KEY=your_tiingo_key_here

# ========================================
# STRONGLY RECOMMENDED - For AI features
# ========================================
OPENROUTER_API_KEY=sk-or-v1-your_key_here
EXA_API_KEY=your_exa_key_here

# ========================================
# DATABASE (Optional - defaults to SQLite)
# ========================================
# For SQLite (default): Don't set DATABASE_URL
# For PostgreSQL:
DATABASE_URL=postgresql://maverick:password@localhost:5432/maverick_mcp

# ========================================
# CACHE (Optional - recommended)
# ========================================
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL_SECONDS=3600

# ========================================
# OPTIONAL - Enhanced Features
# ========================================
OPENAI_API_KEY=sk-your_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
FRED_API_KEY=your_fred_key_here
TAVILY_API_KEY=your_tavily_key_here
EXCHANGE_RATE_API_KEY=your_exchange_rate_key_here

# ========================================
# SERVER (Optional)
# ========================================
API_HOST=0.0.0.0
API_PORT=8003
LOG_LEVEL=info
ENVIRONMENT=development
```

**Step 5: Run database migrations**

```bash
# Initialize/update database schema
make migrate

# Or manually:
./scripts/run-migrations.sh upgrade
```

**Step 6: Seed the database (optional)**

```bash
# Seed S&P 500 stocks
python scripts/seed_sp500.py

# Seed Indian stocks (Nifty 50 + Sensex)
python scripts/seed_indian_stocks.py
```

**Step 7: Start the server**

```bash
# Start development server
make dev

# Or manually:
uv run python -m maverick_mcp.api.server
```

**Step 8: Verify it's running**

```bash
# Test the API
curl http://localhost:8003/health

# Expected: {"status": "ok"}
```

**Step 9: Connect to Claude Desktop**

Edit Claude Desktop config:

```bash
# macOS
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add MaverickMCP:

```json
{
  "mcpServers": {
    "maverick-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/path/to/maverick-mcp",
        "run",
        "python",
        "-m",
        "maverick_mcp.api.server"
      ]
    }
  }
}
```

**Replace `/Users/YOUR_USERNAME/path/to/maverick-mcp` with your actual path!**

**Step 10: Restart Claude Desktop**

Done! 🎉

---

## 🎯 **What's Running? (Summary)**

### With Docker (`make docker-up`)

```
✅ PostgreSQL  → localhost:55432 (auto-started)
✅ Redis       → localhost:56379 (auto-started)
✅ MaverickMCP → localhost:8003 (auto-started)
```

**You don't need to manage anything!**

**Note for Rancher Desktop users**: Non-standard ports (55432, 56379) are used because Rancher Desktop's Lima VM reserves standard ports via SSH tunnel. Containers are configured to listen on these ports internally.

### With Local Setup (Minimal)

```
❌ PostgreSQL  → Optional (uses SQLite by default)
❌ Redis       → Optional (caching disabled)
✅ MaverickMCP → localhost:8003 (you start with `make dev`)
```

**Only MaverickMCP runs, no separate services needed!**

### With Local Setup (Full)

```
✅ PostgreSQL  → localhost:5432 (you start with `brew services start postgresql`)
✅ Redis       → localhost:6379 (you start with `make redis-start`)
✅ MaverickMCP → localhost:8003 (you start with `make dev`)
```

**You manage each service separately.**

---

## ✅ **Verification Checklist**

### 1. Check API is running

```bash
curl http://localhost:8003/health
# Expected: {"status": "ok"}
```

### 2. Check database connection

```bash
# If using PostgreSQL
psql -U maverick -d maverick_mcp -c "SELECT COUNT(*) FROM mcp_stocks;"

# If using SQLite
sqlite3 maverick.db "SELECT COUNT(*) FROM mcp_stocks;"
```

### 3. Check Redis (if using)

```bash
redis-cli ping
# Expected: PONG

# Check cache is working
redis-cli KEYS "*"
```

### 4. Test API functionality

```bash
# Get stock data
curl "http://localhost:8003/api/stock/AAPL?days=30"

# Test Indian market
curl "http://localhost:8003/api/stock/RELIANCE.NS?days=30"
```

### 5. Check Claude Desktop integration

Open Claude Desktop and try:

```
"What's the current price of Apple stock?"
"Analyze Tesla for investment"
"Show me bullish Indian stocks"
```

If it responds with stock data, **it's working!** 🎉

---

## 🔧 **Common Commands**

### Starting Services

```bash
# Docker (all-in-one)
make docker-up              # Start everything
make docker-down            # Stop everything
make docker-logs            # View logs

# Local development
make dev                    # Start MaverickMCP
make redis-start            # Start Redis (if installed)
brew services start postgresql@15  # Start PostgreSQL (macOS)
```

### Database Management

```bash
make migrate                # Run migrations
python scripts/seed_sp500.py       # Seed US stocks
python scripts/seed_indian_stocks.py  # Seed Indian stocks
```

### Testing

```bash
make test                   # Run unit tests
make test-all               # Run all tests
make test-cov               # Run with coverage report
```

### Development

```bash
make format                 # Format code
make lint                   # Run linter
make check                  # Run all checks
make clean                  # Clean up temp files
```

---

## 🐛 **Troubleshooting**

### Issue: "Connection refused" error

**Problem:** Can't connect to PostgreSQL or Redis

**Solution:**

```bash
# Check if services are running
brew services list          # macOS
sudo systemctl status postgresql redis  # Linux

# Start services
brew services start postgresql@15 redis  # macOS
sudo systemctl start postgresql redis   # Linux

# Or use Docker
make docker-up
```

### Issue: "API key not found"

**Problem:** API keys not loaded

**Solution:**

```bash
# Check .env exists
ls -la .env

# Check keys are set
cat .env | grep TIINGO_API_KEY

# Make sure no extra spaces
# Restart server
make dev
```

### Issue: "Database not initialized"

**Problem:** Database schema not created

**Solution:**

```bash
# Run migrations
make migrate

# Or manually
./scripts/run-migrations.sh upgrade
```

### Issue: "Import error: No module named 'talib'"

**Problem:** TA-Lib not installed

**Solution:**

```bash
# macOS
brew install ta-lib

# Ubuntu
sudo apt-get install ta-lib

# Then reinstall Python package
uv sync
```

### Issue: Docker containers won't start

**Problem:** Port conflicts or Docker issues

**Solution:**

```bash
# Check what's using ports
lsof -i :55432  # PostgreSQL (Docker)
lsof -i :56379  # Redis (Docker)
lsof -i :8003   # MaverickMCP

# Stop conflicting services
brew services stop postgresql redis

# Restart Docker
make docker-down
make docker-up
```

### Issue: Tests failing with "Docker not running"

**Problem:** Some tests need Docker for test database

**Solution:**

```bash
# Option 1: Start Docker Desktop
open -a Docker  # macOS

# Option 2: Run only unit tests (no Docker needed)
pytest tests/test_validators.py -v
pytest tests/test_datetime_utils.py -v
```

---

## 📊 **Performance Tips**

### For Best Performance:

1. **Use PostgreSQL instead of SQLite**

   - Much faster for large datasets
   - Supports concurrent queries

2. **Enable Redis caching**

   - Reduces API calls by 80%+
   - Faster response times
   - Prevents hitting rate limits

3. **Use Docker for production**
   - Pre-configured for optimal performance
   - Auto-scaling ready
   - Easy deployment

### Cache Hit Rates:

```bash
# Check Redis cache effectiveness
redis-cli INFO stats | grep keyspace_hits
redis-cli INFO stats | grep keyspace_misses

# Calculate hit rate
# hit_rate = hits / (hits + misses) * 100%
```

---

## 🎯 **Recommended Setup by Use Case**

### For Quick Testing (5 minutes)

```bash
# Just SQLite, no Redis, basic API keys
TIINGO_API_KEY=xxx
make dev
```

### For Development (10 minutes)

```bash
# SQLite + Redis, full API keys
TIINGO_API_KEY=xxx
OPENROUTER_API_KEY=xxx
CACHE_ENABLED=true
make redis-start
make dev
```

### For Production (Docker - 2 minutes)

```bash
# Everything configured automatically
make docker-up
```

### For Full Local Development (30 minutes)

```bash
# PostgreSQL + Redis + All services
# Complete control, best for debugging
brew install postgresql@15 redis ta-lib
# ... configure everything ...
make dev
```

---

## 📚 **Next Steps**

After setup is complete:

1. **Read the API Keys Guide**

   - See `docs/API_KEYS_GUIDE.md`
   - Understand what each key enables

2. **Try the Examples**

   ```bash
   python examples/indian_market_analysis.py
   python examples/llm_speed_demo.py
   ```

3. **Test Stock Screening**

   ```bash
   python scripts/run_stock_screening.py
   ```

4. **Read Documentation**

   - `docs/INDIAN_MARKET.md` - Indian market features
   - `docs/TESTING.md` - Testing guide
   - `CLAUDE.md` - Claude Desktop integration

5. **Contribute!**
   - Check `CONTRIBUTING.md`
   - Look for issues labeled "good first issue"

---

## 🎊 **That's It!**

You now have MaverickMCP running with full functionality! 🚀

**Quick Reference:**

| Need                 | Solution                    |
| -------------------- | --------------------------- |
| **Easiest**          | `make docker-up` (2 min)    |
| **Fastest**          | SQLite + no Redis (5 min)   |
| **Best Performance** | PostgreSQL + Redis (30 min) |
| **Production**       | Docker (2 min)              |

**Questions?** Open an issue on GitHub! 💬
