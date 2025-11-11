# Frequently Asked Questions

## General

### What is Maverick MCP?
A personal stock analysis MCP server with AI-powered conference call analysis.

### Is it free?
Yes, the software is MIT licensed and free. You only pay for API services you use (Tiingo, OpenRouter, etc.).

### What markets are supported?
- US (NASDAQ/NYSE)
- Indian NSE (.NS suffix)
- Indian BSE (.BO suffix)

## Setup

### What API keys do I need?
**Required**: Tiingo (free tier available)
**Recommended**: OpenRouter (for AI features)
**Optional**: OpenAI (for RAG Q&A)

### How do I connect to Claude Desktop?
See [Claude Desktop Setup](../getting-started/claude-desktop-setup.md)

### Does it work with Cursor?
Yes! See [Cursor IDE Setup](../getting-started/cursor-setup.md)

## Features

### Can I analyze Indian stocks?
Yes! Full support for NSE and BSE stocks.

### How many stocks are pre-loaded?
520+ S&P 500 stocks with screening data.

### Can I add more companies?
Yes, use the seeding script to add any company.

## Conference Calls

### Where do transcripts come from?
1. Company IR websites (primary)
2. NSE exchange filings (fallback)

### How much does AI analysis cost?
- Summarization: ~$0.01-0.05 per transcript
- Sentiment: ~$0.005-0.01 per transcript
- RAG embeddings: ~$0.0001 per transcript

### Are results cached?
Yes, all AI analyses are cached in database.

## Technical

### What Python version?
Python 3.12 or higher required.

### Can I use PostgreSQL?
Yes, it's optional but recommended for large datasets.

### Is Redis required?
No, but recommended for better performance.

[Need more help? Report an issue →](https://github.com/arunbcodes/maverick-mcp/issues)
