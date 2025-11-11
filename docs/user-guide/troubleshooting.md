# Troubleshooting

Common issues and solutions.

## Connection Issues

### Tools Not Appearing in Claude
1. Check server is running: `lsof -i :8003`
2. Verify config has trailing slash: `/sse/`
3. Restart Claude Desktop completely
4. Check logs: `make tail-log`

### Port Already in Use
\`\`\`bash
lsof -i :8003
kill -9 <PID>
make dev
\`\`\`

## API Issues

### Tiingo API Errors
- Check API key in `.env`
- Verify not exceeding rate limit (500/day free)
- Check [status page](https://status.tiingo.com)

### OpenRouter Errors
- Verify API key
- Check account credits
- Try different model with `prefer_cheap=True`

## Database Issues

### Migration Errors
\`\`\`bash
make clean
rm -rf ~/.maverick_mcp/maverick_mcp.db
make dev  # Re-creates and seeds
\`\`\`

### S&P 500 Data Missing
\`\`\`bash
python scripts/seed_sp500.py
\`\`\`

## Performance Issues

### Slow Responses
1. Enable Redis caching
2. Use PostgreSQL instead of SQLite
3. Check internet connection
4. Verify API rate limits not exceeded

## Logging

View logs:
\`\`\`bash
make tail-log  # Real-time
tail -100 ~/.maverick_mcp/logs/maverick_mcp.log  # Last 100 lines
\`\`\`

[Need more help? →](../about/faq.md)
