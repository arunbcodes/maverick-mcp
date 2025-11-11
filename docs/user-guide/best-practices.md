# Best Practices

Tips for optimal use of Maverick MCP.

## General Best Practices

### 1. Use Descriptive Commands
Be specific about what you want:

❌ "Get data"
✅ "Get historical stock data for AAPL from Jan 2024 to Dec 2024"

### 2. Combine Tools
Chain multiple operations:
\`\`\`
Fetch RELIANCE.NS Q1 2025 transcript, summarize it, 
analyze sentiment, and extract top concerns
\`\`\`

### 3. Cache Results
AI analyses are cached automatically. Don't force refresh unless needed.

## Conference Call Analysis

### 1. Fetch First, Analyze Later
\`\`\`
# Step 1: Fetch transcript
Fetch RELIANCE.NS Q1 2025

# Step 2: Analyze (uses cached transcript)
Summarize RELIANCE.NS Q1 2025
Analyze sentiment for RELIANCE.NS Q1 2025
\`\`\`

### 2. Use Appropriate Detail Levels
- **Concise**: Quick overview
- **Standard**: Balanced (default)
- **Detailed**: Comprehensive analysis

### 3. Compare Trends
Always compare across quarters for context.

## Cost Optimization

### 1. Use Caching
Results are cached by default. Reuse them!

### 2. Choose Right Detail Level
Concise mode costs ~50% less than detailed.

### 3. Batch Operations
Analyze multiple stocks in one request when possible.

## Performance

### 1. Enable Redis
Significantly faster with Redis caching.

### 2. Use PostgreSQL
Better for large datasets.

### 3. Parallel Requests
Server handles concurrent requests automatically.

[See more in Configuration →](../getting-started/configuration.md)
