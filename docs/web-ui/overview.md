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

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | TailwindCSS + shadcn/ui |
| Data Fetching | React Query (TanStack Query) |
| Forms | React Hook Form + Zod |
| Charts | Recharts |
| Icons | Lucide React |
| Fonts | Geist (Sans & Mono) |

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

## Quick Start

### Docker (Recommended)

```bash
# Start full stack
make docker-full-up

# Open dashboard
open http://localhost:3000
```

### Local Development

```bash
# Start backend first
make docker-backend

# Run web locally
cd apps/web
npm install
npm run dev

# Open dashboard
open http://localhost:3000
```

## Navigation

| Route | Page |
|-------|------|
| `/` | Landing / Login redirect |
| `/login` | Login page |
| `/register` | Registration page |
| `/forgot-password` | Password recovery |
| `/reset-password` | Password reset |
| `/dashboard` | Main dashboard |
| `/portfolio` | Portfolio management |
| `/watchlist` | Stock watchlists |
| `/screener` | Stock screener |
| `/risk` | Risk analytics dashboard |
| `/stocks/[ticker]` | Stock detail page |
| `/settings` | Account settings |

## Demo Account

For testing, use the demo account:

| Field | Value |
|-------|-------|
| Email | `demo@maverick.example` |
| Password | `demo123456` |

## Next Steps

- [Features Guide](features.md) - Detailed feature documentation
- [Configuration](configuration.md) - Environment setup
- [Development](development.md) - Component structure, contributing
