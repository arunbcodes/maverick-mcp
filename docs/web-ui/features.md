# Web UI Features

Detailed guide to all features available in the Maverick web dashboard.

## Dashboard

The dashboard provides a real-time overview of your financial status.

### Portfolio Summary Card

Displays key metrics at a glance:

- **Total Value**: Sum of all position values at current prices
- **Daily Change**: Dollar change from previous close
- **Daily Change %**: Percentage change
- **Color coding**: Green for positive, red for negative

### Performance Chart

Interactive chart showing portfolio value over time:

- **Time periods**: 1W, 1M, 3M, 6M, 1Y, ALL
- **Hover tooltips**: Exact values at any point
- **Benchmark comparison**: Optional S&P 500 overlay
- **Responsive**: Adapts to screen size

### Top Positions

Quick view of your best performers:

- Top 5 positions by daily gain
- Ticker, current price, change percentage
- Click to navigate to stock detail

### Live Price Updates

Real-time prices via SSE (Server-Sent Events):

- Automatic updates without page refresh
- Connection status indicator
- Graceful reconnection on disconnect

## Portfolio Management

Complete portfolio tracking and management.

### Position List

View all your holdings:

| Column | Description |
|--------|-------------|
| Ticker | Stock symbol (clickable) |
| Shares | Number of shares owned |
| Avg Cost | Average purchase price |
| Current Price | Live market price |
| Market Value | Shares × Current Price |
| Cost Basis | Shares × Avg Cost |
| P&L ($) | Market Value - Cost Basis |
| P&L (%) | Percentage gain/loss |

### Add Position

Modal form to add new holdings:

```
┌─────────────────────────────────────────┐
│  Add Position                        ✕  │
├─────────────────────────────────────────┤
│                                         │
│  Ticker *                               │
│  ┌─────────────────────────────────┐   │
│  │ AAPL                            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Shares *            Purchase Price *   │
│  ┌──────────────┐   ┌──────────────┐   │
│  │ 10           │   │ 150.00       │   │
│  └──────────────┘   └──────────────┘   │
│                                         │
│  Purchase Date      Notes (optional)    │
│  ┌──────────────┐   ┌──────────────┐   │
│  │ 2024-01-15   │   │ Long-term    │   │
│  └──────────────┘   └──────────────┘   │
│                                         │
│              [Cancel]  [Add Position]   │
└─────────────────────────────────────────┘
```

**Validation:**

- Ticker: Required, valid stock symbol
- Shares: Required, positive number
- Price: Required, positive number
- Date: Defaults to today

### Edit Position

Update existing holdings:

- All fields from Add Position
- Pre-filled with current values
- Option to add/remove shares

### Remove Position

Delete a position:

- Confirmation dialog
- Option to record sell price (coming soon)

### Portfolio Charts

**Allocation Pie Chart**

Visual breakdown by:

- Individual stock
- Sector
- Market cap

**Performance Line Chart**

Historical portfolio value:

- Daily, weekly, monthly views
- Benchmark comparison
- Hover for details

## Stock Screener

Discover stocks matching specific criteria.

### Screening Strategies

#### Maverick Bullish

Identifies high-momentum growth stocks:

- Strong upward price trend
- Above key moving averages
- High relative strength
- Increasing volume

#### Maverick Bearish

Identifies weak stocks:

- Declining price trend
- Below moving averages
- Weak relative strength
- Potential short candidates

#### Supply/Demand Breakouts

Stocks breaking out of consolidation:

- Price above all major MAs
- MA alignment (50 > 150 > 200)
- High momentum strength
- Institutional accumulation signals

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Min Price | Number | Minimum stock price |
| Max Price | Number | Maximum stock price |
| Min Volume | Number | Minimum daily volume |
| Sector | Select | Filter by sector |
| Momentum Score | Range | 0-100 momentum rating |

### Results Table

Sortable columns:

- **Rank**: Position in screening results
- **Ticker**: Stock symbol
- **Company**: Company name
- **Price**: Current price
- **Change**: Daily change %
- **Momentum**: Momentum score (0-100)
- **Volume**: Daily volume
- **Sector**: Industry sector

### Actions

- **Click row**: Navigate to stock detail
- **Add to Portfolio**: Quick add button
- **Export**: Download as CSV (coming soon)

## Stock Detail Page

Comprehensive view of any stock.

### Header Section

- **Ticker & Name**: e.g., "AAPL - Apple Inc."
- **Current Price**: Live price
- **Change**: Dollar and percentage
- **Add to Portfolio**: Quick action button

### Price Chart

Interactive chart with:

- **Timeframes**: 1W, 1M, 3M, 1Y, ALL
- **Chart types**: Line, Candlestick (coming soon)
- **Volume overlay**: Optional volume bars
- **Drawing tools**: Coming soon

### Technical Indicators

#### RSI (Relative Strength Index)

- Current RSI value (0-100)
- Overbought/oversold zones
- Visual gauge

#### MACD

- MACD line and signal line
- Histogram
- Crossover signals

#### Moving Averages

- SMA 20, 50, 150, 200
- Current price vs MAs
- MA alignment status

#### Support & Resistance

- Key support levels
- Key resistance levels
- Distance to levels

### Company Information

- **Sector**: Industry classification
- **Market Cap**: Total market value
- **P/E Ratio**: Price to earnings
- **52-Week Range**: High/Low prices
- **Description**: Company summary

## Settings

Account and application settings.

### API Keys Management

Create and manage API keys for programmatic access:

#### Create Key

```
┌─────────────────────────────────────────┐
│  Create API Key                      ✕  │
├─────────────────────────────────────────┤
│                                         │
│  Key Name *                             │
│  ┌─────────────────────────────────┐   │
│  │ My Trading Bot                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Expiration                             │
│  ○ 30 days                             │
│  ● 90 days                             │
│  ○ 1 year                              │
│  ○ Never                               │
│                                         │
│              [Cancel]  [Create Key]     │
└─────────────────────────────────────────┘
```

#### Key List

| Column | Description |
|--------|-------------|
| Name | Key identifier |
| Prefix | First 8 characters |
| Created | Creation date |
| Expires | Expiration date |
| Last Used | Most recent usage |
| Actions | Copy, Revoke |

#### Copy Key

New keys are shown once:

```
┌─────────────────────────────────────────┐
│  API Key Created                     ✕  │
├─────────────────────────────────────────┤
│                                         │
│  ⚠️  Copy this key now - it won't be   │
│      shown again!                       │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ mav_sk_abc123xyz789...         📋│   │
│  └─────────────────────────────────┘   │
│                                         │
│                            [Done]       │
└─────────────────────────────────────────┘
```

### Change Password

Secure password update:

- Current password (required)
- New password with strength indicator
- Confirm new password
- Validation feedback

### Theme (Coming Soon)

- Light mode
- Dark mode
- System preference

### Notifications (Coming Soon)

- Price alerts
- Portfolio updates
- Screening results

## Authentication Pages

### Login

```
┌─────────────────────────────────────────┐
│                                         │
│           🚀 MAVERICK                   │
│     Financial Analysis Platform         │
│                                         │
│  Email                                  │
│  ┌─────────────────────────────────┐   │
│  │ user@example.com                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Password                               │
│  ┌─────────────────────────────────┐   │
│  │ ••••••••••••                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [        Sign In        ]             │
│                                         │
│  Don't have an account? Sign up         │
│                                         │
└─────────────────────────────────────────┘
```

### Register

- Email (must be unique)
- Password (with requirements)
- Confirm password
- Name (optional)
- Terms acceptance

## Responsive Design

The UI adapts to all screen sizes:

| Breakpoint | Layout |
|------------|--------|
| Mobile (<640px) | Single column, collapsed nav |
| Tablet (640-1024px) | Two columns, sidebar |
| Desktop (>1024px) | Full layout, expanded sidebar |

### Mobile Considerations

- Touch-friendly tap targets
- Swipe gestures for charts
- Bottom navigation
- Collapsible sections

## Accessibility

- **Keyboard navigation**: All interactive elements
- **Screen reader support**: ARIA labels
- **Color contrast**: WCAG AA compliant
- **Focus indicators**: Visible focus states
- **Reduced motion**: Respects user preferences

## Next Steps

- [Configuration](configuration.md) - Environment setup
- [Development](development.md) - Contributing to the UI

