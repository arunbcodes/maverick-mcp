# Research Tools

AI-powered research with multi-agent parallel execution.

## Features

### Comprehensive Research
Multi-agent parallel research system:
- **7-256x Speedup**: Parallel agent execution
- **400+ AI Models**: Smart model selection via OpenRouter
- **Cost Optimization**: 40-60% cost reduction
- **Early Termination**: Confidence-based stopping

### Company Research
Deep fundamental and competitive analysis:
- Financial performance analysis
- Competitive positioning
- Industry trends
- Management quality assessment
- Growth catalysts and risks

### Market Sentiment
Multi-source sentiment analysis:
- News aggregation from multiple sources
- Social media sentiment
- Analyst recommendations
- Insider trading activity
- Confidence scoring

## Usage Examples

### Comprehensive Research
```
Research AAPL comprehensively with financial analysis
```

Returns:
- Company overview and business model
- Financial health and metrics
- Competitive analysis
- Industry positioning
- Investment thesis
- Risk factors
- Analyst consensus

### Company-Specific Research
```
Research TCS.NS focusing on IT services sector
```

Focused analysis:
- Sector-specific metrics
- Competitor comparison
- Market share analysis
- Technology capabilities

### Sentiment Analysis
```
Analyze market sentiment for RELIANCE.NS
```

Multi-source sentiment:
- News sentiment (positive/negative/neutral)
- Volume of mentions
- Sentiment trend over time
- Key topics and themes
- Confidence score

## Multi-Agent Architecture

### Agent Types
- **Financial Analyst**: Numbers and metrics
- **Industry Expert**: Sector knowledge
- **Technical Analyst**: Charts and patterns
- **News Aggregator**: Current events
- **Sentiment Analyzer**: Market mood

### Parallel Execution
Agents work simultaneously:
1. Task distributed to all agents
2. Each agent researches in parallel
3. Results aggregated and synthesized
4. Consensus built from multiple viewpoints

### Performance
- **Sequential**: 5-10 minutes per company
- **Parallel**: 30-60 seconds per company
- **Speedup**: 7-256x depending on task
- **Quality**: Equal or better than sequential

## Model Selection

### Task-Based Selection
OpenRouter automatically selects optimal model:
- **Simple Tasks**: Fast, cheap models (Haiku, GPT-4o-mini)
- **Complex Analysis**: Powerful models (Opus, GPT-4)
- **Cost-Sensitive**: Balance quality and cost
- **Fallback**: Graceful degradation on errors

### Cost Optimization
- Cheap models for data gathering
- Expensive models only for synthesis
- Caching to avoid duplicate calls
- Early termination when confident

### Available Models
Access to 400+ models including:
- Claude (Opus, Sonnet, Haiku)
- GPT-4, GPT-4 Turbo, GPT-4o
- Gemini 2.0, 2.5 Pro
- DeepSeek R1
- Llama, Mixtral, and more

## Research Depth

### Quick Research (30-60 seconds)
- Basic company overview
- Current price and fundamentals
- Recent news headlines
- Quick sentiment check

### Standard Research (1-2 minutes)
- Comprehensive company analysis
- Financial metrics deep-dive
- Competitive positioning
- Industry trends
- Risk assessment

### Deep Research (2-5 minutes)
- All of standard research
- Historical performance analysis
- Management analysis
- Supply chain examination
- Regulatory landscape
- Long-term projections

## Confidence Scoring

All research includes confidence metrics:
- **Data Quality**: How reliable are sources
- **Consensus Level**: Agreement between agents
- **Recency**: How current is the information
- **Coverage**: Completeness of analysis

Example output:
```json
{
  "confidence": 0.85,
  "data_quality": "high",
  "consensus": "strong",
  "last_updated": "2025-01-10"
}
```

## Caching

Research results are cached:
- **Duration**: 24 hours for general research
- **Duration**: 1 hour for sentiment analysis
- **Invalidation**: Manual refresh available
- **Cost Savings**: Avoid duplicate AI calls

## API Reference

See [Research Tools](../user-guide/mcp-tools.md#research) for complete API documentation.

## Use Cases

### Investment Research
```
Research AAPL for long-term investment
```

### Sector Analysis
```
Compare research for AAPL, MSFT, GOOGL in tech sector
```

### Event-Driven
```
Research impact of earnings report on RELIANCE.NS
```

### Competitive Analysis
```
Compare INFY.NS vs TCS.NS vs WIPRO.NS
```

## Data Sources

### Financial Data
- Tiingo API (price, fundamentals)
- Company filings (10-K, 10-Q)
- Earnings transcripts
- Financial statements

### News & Sentiment
- Exa web search (optional)
- Major financial news outlets
- Company press releases
- Social media aggregation

### Analysis
- OpenRouter (AI synthesis)
- Multiple AI models
- Consensus building
- Fact verification
