# Features Overview

Maverick MCP provides comprehensive stock analysis and conference call analysis tools designed for use with Claude Desktop and other MCP-compatible clients.

## Core Capabilities

### 📊 Stock Analysis
- **Multi-Market Support**: US (NASDAQ/NYSE), Indian NSE, Indian BSE
- **Real-time & Historical Data**: Price quotes, volume, fundamentals
- **Technical Indicators**: 15+ indicators including RSI, MACD, Bollinger Bands
- **Pre-seeded Database**: 520+ S&P 500 stocks ready to analyze

### 📞 Conference Call Analysis
- **Transcript Fetching**: Automatic retrieval from IR websites and NSE
- **AI Summarization**: Structured summaries with key metrics and insights
- **Sentiment Analysis**: Multi-dimensional sentiment scoring
- **RAG Q&A**: Ask questions over transcripts with source citations
- **Trend Analysis**: Compare sentiment across quarters

### 🔍 Stock Screening
- **Maverick Strategies**: Bullish/Bearish momentum patterns
- **Breakout Detection**: Supply/demand breakout candidates
- **Indian Market Screening**: 7 specialized strategies for NSE/BSE
- **Pre-calculated Results**: Instant screening from database

### 📈 Portfolio Analysis
- **Modern Portfolio Theory**: Optimization and efficient frontier
- **Risk Metrics**: Sharpe ratio, volatility, correlation matrices
- **Performance Tracking**: Returns, drawdowns, alpha/beta

### 🧪 Backtesting
- **VectorBT Engine**: High-performance vectorized backtesting
- **15+ Strategies**: Including ML-powered adaptive algorithms
- **Walk-Forward Optimization**: Out-of-sample testing
- **Monte Carlo Simulation**: Robustness testing

### 🔬 Research Tools
- **AI-Powered Research**: Multi-agent parallel research (7-256x faster)
- **Market Sentiment**: Multi-source sentiment analysis
- **Company Research**: Deep fundamental and competitive analysis
- **Smart Model Selection**: 400+ AI models via OpenRouter

## Key Features

### Multi-Market Support
Analyze stocks from:
- **US Markets**: NASDAQ, NYSE
- **Indian NSE**: `.NS` suffix (e.g., RELIANCE.NS)
- **Indian BSE**: `.BO` suffix (e.g., TCS.BO)

Market-specific features:
- Trading calendars (NYSE, NSE)
- Currency handling (USD, INR)
- Circuit breakers (7% US, 10% India)
- Settlement cycles (T+2 US, T+1 India)

### Production-Grade Caching
Multi-tier caching for optimal performance:
- **L1 Cache**: Redis/In-memory (1-5ms)
- **L2 Cache**: Database (10-50ms)
- **L3 Source**: External APIs (seconds to minutes)

Benefits:
- 100-1000x speedup for cached data
- Significant cost savings on AI operations
- Automatic TTL management

### AI Integration
Intelligent AI model selection:
- **OpenRouter**: Access to 400+ models
- **Cost Optimization**: 40-60% cost reduction
- **Task-Specific Models**: Automatic selection based on complexity
- **Fallback Support**: Graceful degradation

### Data Sources
- **Tiingo API**: Stock market data (500 requests/day free)
- **OpenRouter**: AI analysis and summarization
- **OpenAI**: Embeddings for RAG Q&A
- **FRED**: Economic indicators (optional)
- **Exa**: Web search for research (optional)

## Architecture

### Design Principles
- **SOLID Principles**: Single Responsibility, Open/Closed, etc.
- **Modular Design**: Easy to extract components
- **Provider Pattern**: Swappable data providers
- **Cache-First**: Minimize API calls and costs
- **Error Resilient**: Graceful fallback and recovery

### Database
- **Default**: SQLite (zero setup required)
- **Optional**: PostgreSQL for better performance
- **Pre-seeded**: S&P 500 stocks and screening data
- **Migrations**: Alembic-based schema management

### Performance
- **Connection Pooling**: Efficient database connections
- **Parallel Processing**: Multi-threaded operations
- **Vector Search**: Fast similarity search for RAG
- **Batch Operations**: Bulk data processing

## Use Cases

### For Individual Investors
- Screen stocks based on technical patterns
- Analyze earnings call transcripts
- Compare sentiment across quarters
- Build and optimize portfolios
- Backtest trading strategies

### For Traders
- Real-time technical analysis
- Breakout candidate detection
- Multi-timeframe analysis
- Risk management tools
- Performance tracking

### For Researchers
- Historical data analysis
- Strategy development and testing
- Sentiment analysis at scale
- Market trend identification
- Comparative analysis

### For Developers
- MCP server reference implementation
- SOLID architecture patterns
- Multi-market data handling
- AI integration best practices
- Production-grade caching

## Getting Started

1. **Installation**: [Installation Guide](../getting-started/installation.md)
2. **Configuration**: [API Keys Setup](../getting-started/configuration.md)
3. **Quick Start**: [Quick Start Guide](../getting-started/quick-start.md)
4. **Claude Desktop**: [Integration Guide](../getting-started/claude-desktop-setup.md)

## Feature Pages

Explore detailed documentation for each feature:

- [Stock Analysis](stock-analysis.md) - Real-time quotes and historical data
- [Technical Analysis](technical-analysis.md) - Indicators and charting
- [Stock Screening](stock-screening.md) - Pattern-based screening
- [Portfolio Analysis](portfolio-analysis.md) - MPT and optimization
- [Conference Call Analysis](conference-call-analysis.md) - Transcript analysis
- [Research Tools](research-tools.md) - AI-powered research
- [Backtesting](backtesting.md) - Strategy testing and optimization
