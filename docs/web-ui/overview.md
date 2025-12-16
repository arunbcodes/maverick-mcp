# Web UI Overview

Maverick includes a modern web dashboard built with Next.js 14, providing a beautiful interface for financial analysis.

## Features

### 🏠 Dashboard

Real-time portfolio overview with:

- **Portfolio summary**: Total value, daily P&L, percentage change
- **Top positions**: Your best and worst performing stocks
- **Performance chart**: Historical portfolio performance
- **Market overview**: Index prices and sentiment

### 📊 Portfolio Management

Complete portfolio tracking:

- **Position list**: All holdings with live prices
- **Add positions**: Buy stocks with price, date, and notes
- **Edit positions**: Update shares, cost basis, notes
- **Remove positions**: Close out positions
- **Performance metrics**: Unrealized P&L, allocation breakdown

### 🔍 Stock Screener

Discover investment opportunities:

- **Maverick Bullish**: High momentum growth stocks
- **Maverick Bearish**: Weak stocks for hedging
- **Supply/Demand**: Breakout patterns
- **Filters**: Price, volume, sector, momentum score
- **Sorting**: By any metric

### 📈 Stock Detail

Deep dive into any stock:

- **Price chart**: Interactive with multiple timeframes
- **Technical indicators**: RSI, MACD, moving averages
- **Support/Resistance**: Key price levels
- **Quick actions**: Add to portfolio, set alerts

### 👁️ Watchlist

Track stocks you're interested in:

- **Multiple watchlists**: Organize by strategy or sector
- **Real-time prices**: Live price updates via SSE
- **Quick actions**: Add to portfolio, set alerts
- **Notes**: Add personal notes per stock

### 🛡️ Risk Analytics

Monitor portfolio risk:

- **Risk scores**: Per-position and portfolio-wide
- **Concentration analysis**: Sector and position sizing
- **Volatility metrics**: Historical volatility tracking
- **Risk alerts**: Warnings for high-risk positions

### ⚙️ Settings

Account management:

- **API Keys**: Create, view, revoke
- **Change Password**: Secure password updates
- **Preferences**: Theme, notifications (coming soon)

## Technology Stack

| Layer         | Technology                   |
| ------------- | ---------------------------- |
| Framework     | Next.js 14 (App Router)      |
| Styling       | TailwindCSS + shadcn/ui      |
| Data Fetching | React Query (TanStack Query) |
| Forms         | React Hook Form + Zod        |
| Charts        | Recharts                     |
| Icons         | Lucide React                 |
| Fonts         | Geist (Sans & Mono)          |

## Screenshots

### Dashboard

The main dashboard provides an at-a-glance view of your portfolio:

```
┌─────────────────────────────────────────────────────────────┐
│  MAVERICK                            👤 Profile  ⚙️ Settings │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Portfolio Value          Today's Change                    │
│  $125,432.50             +$1,234.56 (+0.99%)               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │          📈 Performance Chart (90 days)             │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Top Positions                    Recent Activity          │
│  ├─ AAPL  +12.5%                 • Added MSFT              │
│  ├─ NVDA  +8.2%                  • Sold TSLA              │
│  └─ MSFT  +5.1%                  • Dividend: AAPL          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Stock Screener

Filter and find stocks matching your criteria:

```
┌─────────────────────────────────────────────────────────────┐
│  Stock Screener                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Strategy: [Maverick Bullish ▼]                            │
│                                                             │
│  Filters:                                                   │
│  Min Price: $10    Max Price: $500    Sector: [All ▼]      │
│                                                             │
│  ┌─────────┬────────┬─────────┬──────────┬─────────────┐   │
│  │ Ticker  │ Price  │ Change  │ Momentum │ Sector      │   │
│  ├─────────┼────────┼─────────┼──────────┼─────────────┤   │
│  │ NVDA    │ $875   │ +3.2%   │ 95       │ Technology  │   │
│  │ META    │ $485   │ +2.1%   │ 88       │ Technology  │   │
│  │ AMZN    │ $178   │ +1.5%   │ 82       │ Consumer    │   │
│  └─────────┴────────┴─────────┴──────────┴─────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Testing Locally - Step by Step

### Prerequisites

- **Docker Desktop** or **Rancher Desktop** installed and running
- Git

### Option 1: Full Docker Stack (Easiest - Recommended)

Everything runs in Docker containers. Best for first-time testing.

```bash
# 1. Clone the repo (skip if already done)
git clone https://github.com/arunbcodes/maverick-mcp.git
cd maverick-mcp

# 2. Copy environment template
cp docker/env.example docker/.env

# 3. (Optional) Add API keys for AI features
nano docker/.env
# Add: TIINGO_API_KEY=your-key
# Add: OPENROUTER_API_KEY=your-key (for AI search)

# 4. Start all services
make docker-full-up

# 5. Wait for services to be healthy (about 30-60 seconds)
docker ps  # All containers should show "healthy"

# 6. Open the UI
open http://localhost:3000
```

**Login with demo account:**
- Email: `demo@maverick.example`
- Password: `demo123456`

**Stop everything:**
```bash
make docker-full-down
```

### Option 2: Docker Backend + Local Web (For Web Development)

Backend in Docker, web runs locally with hot-reload. Best for UI development.

```bash
# 1. Start backend services (API + Database + Redis)
make docker-backend

# 2. In a new terminal, run web locally
cd apps/web
npm install
npm run dev

# 3. Open the UI
open http://localhost:3000
```

**Why use this?**
- Faster hot-reload when editing UI code
- No need to rebuild Docker image for frontend changes

### Option 3: Everything Local (Advanced)

For full-stack development. Requires Node.js 20+, Python 3.12+, PostgreSQL, Redis.

```bash
# 1. Start only database services in Docker
docker compose -f docker/docker-compose.yml up -d postgres redis

# 2. Start API locally (Terminal 1)
cd packages/api
pip install -e .
uvicorn maverick_api.main:app --reload --port 8000

# 3. Start Web locally (Terminal 2)
cd apps/web
npm install
npm run dev

# 4. Open the UI
open http://localhost:3000
```

### Quick Reference

| Setup | Command | UI URL | Use Case |
|-------|---------|--------|----------|
| Full Docker | `make docker-full-up` | http://localhost:3000 | Testing, demos |
| Docker + Local Web | `make docker-backend` + `npm run dev` | http://localhost:3000 | UI development |
| All Local | Manual setup | http://localhost:3000 | Full-stack dev |

### Services & Ports

| Service | Port | URL |
|---------|------|-----|
| Web UI | 3000 | http://localhost:3000 |
| REST API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| MCP Server | 8003 | http://localhost:8003 |
| PostgreSQL | 5432 | - |
| Redis | 6379 | - |

### Troubleshooting

**Container won't start?**
```bash
# Check logs
docker compose -f docker/docker-compose.yml logs api
docker compose -f docker/docker-compose.yml logs web
```

**Port already in use?**
```bash
# Find what's using the port
lsof -i :3000
lsof -i :8000

# Kill it or use different port
```

**Clean restart:**
```bash
make docker-clean  # Removes all containers and volumes
make docker-full-up
```

## Navigation

| Route              | Page                     |
| ------------------ | ------------------------ |
| `/`                | Landing / Login redirect |
| `/login`           | Login page               |
| `/register`        | Registration page        |
| `/forgot-password` | Password recovery        |
| `/reset-password`  | Password reset           |
| `/dashboard`       | Main dashboard           |
| `/portfolio`       | Portfolio management     |
| `/watchlist`       | Stock watchlists         |
| `/screener`        | Stock screener           |
| `/risk`            | Risk analytics dashboard |
| `/stocks/[ticker]` | Stock detail page        |
| `/settings`        | Account settings         |

## Demo Account

For testing, use the demo account:

| Field    | Value                   |
| -------- | ----------------------- |
| Email    | `demo@maverick.example` |
| Password | `demo123456`            |

## Next Steps

- [Features Guide](features.md) - Detailed feature documentation
- [Configuration](configuration.md) - Environment setup
- [Development](development.md) - Component structure, contributing
