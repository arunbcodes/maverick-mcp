# API Keys Guide for MaverickMCP

Complete guide to all API keys needed to fully utilize MaverickMCP features.

---

## 🔑 **Required API Keys**

### 1. **TIINGO_API_KEY** (Required)

**What it does:** Provides stock price data, historical data, and market information

**Cost:** FREE (500 requests/day on free tier)

**How to get:**
1. Go to [tiingo.com](https://tiingo.com)
2. Sign up for a free account
3. Navigate to your dashboard
4. Copy your API token

**Add to .env:**
```bash
TIINGO_API_KEY=your_tiingo_api_key_here
```

**Features enabled:**
- ✅ Historical stock data (US, Indian markets)
- ✅ Real-time stock quotes
- ✅ Technical indicators
- ✅ Stock screening

---

## 🚀 **Strongly Recommended API Keys**

### 2. **OPENROUTER_API_KEY** (Strongly Recommended)

**What it does:** Access to 400+ AI models with intelligent cost optimization

**Cost:** Pay-as-you-go (40-60% cheaper than direct API access)

**Why recommended:**
- Access to multiple LLMs (GPT-4, Claude, Llama, etc.)
- Automatic model selection for cost optimization
- Fallback routing if one model is down
- Much cheaper than using OpenAI/Anthropic directly

**How to get:**
1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Add credits to your account
4. Generate an API key

**Add to .env:**
```bash
OPENROUTER_API_KEY=sk-or-v1-your_key_here
```

**Features enabled:**
- ✅ AI-powered stock analysis
- ✅ Deep research capabilities
- ✅ Market insights
- ✅ Natural language queries

### 3. **EXA_API_KEY** (Recommended for Research)

**What it does:** Web search capabilities for comprehensive financial research

**Cost:** Free tier available, paid plans for heavy usage

**How to get:**
1. Go to [exa.ai](https://exa.ai)
2. Sign up for an account
3. Generate an API key

**Add to .env:**
```bash
EXA_API_KEY=your_exa_api_key_here
```

**Features enabled:**
- ✅ Web search for financial news
- ✅ Company research
- ✅ Market trends analysis
- ✅ Deep research agent

---

## 📊 **Optional API Keys (Nice-to-Have)**

### 4. **OPENAI_API_KEY** (Fallback)

**What it does:** Direct access to OpenAI models (GPT-4, GPT-3.5)

**Cost:** Pay-as-you-go (more expensive than OpenRouter)

**When to use:**
- If you prefer direct OpenAI access
- Already have OpenAI credits
- Don't want to use OpenRouter

**How to get:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up and add payment method
3. Generate an API key

**Add to .env:**
```bash
OPENAI_API_KEY=sk-your_openai_key_here
```

### 5. **ANTHROPIC_API_KEY** (Fallback)

**What it does:** Direct access to Claude models

**Cost:** Pay-as-you-go

**When to use:**
- If you prefer direct Anthropic access
- Already have Anthropic credits
- Don't want to use OpenRouter

**How to get:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up and add payment method
3. Generate an API key

**Add to .env:**
```bash
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
```

### 6. **FRED_API_KEY** (Economic Data)

**What it does:** Federal Reserve economic data (US economic indicators)

**Cost:** FREE

**How to get:**
1. Go to [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
2. Sign up for a free account
3. Request an API key

**Add to .env:**
```bash
FRED_API_KEY=your_fred_api_key_here
```

**Features enabled:**
- ✅ GDP data
- ✅ Inflation rates
- ✅ Interest rates
- ✅ Employment data

### 7. **TAVILY_API_KEY** (Alternative Search)

**What it does:** Alternative web search provider

**Cost:** Free tier available

**When to use:**
- As alternative to Exa
- For additional search coverage

**How to get:**
1. Go to [tavily.com](https://tavily.com)
2. Sign up for an account
3. Generate an API key

**Add to .env:**
```bash
TAVILY_API_KEY=your_tavily_api_key_here
```

---

## 💱 **Currency & Exchange Rate Keys**

### 8. **EXCHANGE_RATE_API_KEY** (Optional, for INR/USD conversion)

**What it does:** Real-time currency exchange rates

**Cost:** FREE tier available (1,500 requests/month)

**Fallback:** Yahoo Finance (works without API key but less accurate)

**How to get:**
1. Go to [exchangerate-api.com](https://www.exchangerate-api.com/)
2. Sign up for a free account
3. Get your API key

**Add to .env:**
```bash
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here
```

**Features enabled:**
- ✅ Real-time INR/USD conversion
- ✅ Accurate cross-market comparisons
- ✅ Historical exchange rates

**Note:** Works fine without this key using Yahoo Finance fallback!

---

## 🇮🇳 **Indian Market Keys (Future Enhancements)**

These are NOT currently implemented but documented for future use:

### 9. **RBI_API_KEY** (Not Required Yet)

**What it would do:** Real-time RBI economic data

**Status:** Currently uses approximate data and World Bank API

**Future implementation:** See `docs/INDIAN_MARKET.md` - Future Enhancements

### 10. **MONEYCONTROL_API_KEY** (Not Required Yet)

**What it would do:** Direct MoneyControl API access

**Status:** Currently uses RSS feeds and web scraping (no API key needed)

### 11. **ECONOMIC_TIMES_API_KEY** (Not Required Yet)

**What it would do:** Direct Economic Times API access

**Status:** Currently uses RSS feeds and web scraping (no API key needed)

---

## 🔧 **Configuration**

### Create .env File

```bash
# Copy example (if available)
cp .env.example .env

# Or create new .env file
touch .env
```

### Complete .env Template

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
# OPTIONAL - LLM Fallbacks
# ========================================
OPENAI_API_KEY=sk-your_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# ========================================
# OPTIONAL - Enhanced Data
# ========================================
FRED_API_KEY=your_fred_key_here
TAVILY_API_KEY=your_tavily_key_here
EXCHANGE_RATE_API_KEY=your_exchange_rate_key_here

# ========================================
# PERFORMANCE - Caching
# ========================================
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379

# ========================================
# DATABASE (Optional, defaults to SQLite)
# ========================================
DATABASE_URL=postgresql://user:pass@localhost/maverick_mcp
```

---

## 📊 **Feature Matrix**

| Feature | Required Keys | Optional Keys |
|---------|---------------|---------------|
| **Basic Stock Data** | TIINGO_API_KEY | - |
| **AI Analysis** | TIINGO_API_KEY | OPENROUTER_API_KEY |
| **Deep Research** | TIINGO_API_KEY, OPENROUTER_API_KEY | EXA_API_KEY |
| **US Economic Data** | TIINGO_API_KEY | FRED_API_KEY |
| **Indian Market Data** | TIINGO_API_KEY | - |
| **Currency Conversion** | TIINGO_API_KEY | EXCHANGE_RATE_API_KEY |
| **News Sentiment** | TIINGO_API_KEY | - |
| **Technical Analysis** | TIINGO_API_KEY | - |
| **Stock Screening** | TIINGO_API_KEY | - |

---

## 💰 **Cost Breakdown**

### Free Tier (Basic Usage)

**Total Cost: $0/month**

- ✅ TIINGO_API_KEY (free)
- ✅ FRED_API_KEY (free)
- ✅ EXCHANGE_RATE_API_KEY (free tier: 1,500 req/month)

**What you get:**
- Stock data (500 req/day)
- Basic technical analysis
- US economic data
- Indian market data
- News sentiment

### Recommended (Full Features)

**Total Cost: ~$5-20/month** (depending on usage)

- ✅ Everything in Free Tier
- ✅ OPENROUTER_API_KEY ($5-10/month typical)
- ✅ EXA_API_KEY ($0-10/month depending on usage)

**What you get:**
- AI-powered analysis
- Deep research capabilities
- Web search
- Natural language queries
- All Claude Desktop features

---

## ✅ **Getting Started Checklist**

### Minimum Setup (Free)

```bash
1. ✅ Sign up for Tiingo (free)
2. ✅ Get TIINGO_API_KEY
3. ✅ Add to .env
4. ✅ Run: make dev
```

**You can now:**
- Get stock data for US & Indian markets
- Run technical analysis
- Screen stocks
- View news sentiment

### Recommended Setup (~$10/month)

```bash
1. ✅ Complete Minimum Setup above
2. ✅ Sign up for OpenRouter
3. ✅ Add $10 credits
4. ✅ Get OPENROUTER_API_KEY
5. ✅ Add to .env
6. ✅ Sign up for Exa (free tier)
7. ✅ Get EXA_API_KEY
8. ✅ Add to .env
9. ✅ Restart: make dev
```

**You can now:**
- Ask Claude about any stock
- Get AI-powered insights
- Deep research on companies
- Market trend analysis
- **Full features! 🎉**

---

## 🔒 **Security Best Practices**

### DO:
- ✅ Keep API keys in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment-specific keys (dev/prod)
- ✅ Rotate keys periodically
- ✅ Monitor API usage
- ✅ Set spending limits where possible

### DON'T:
- ❌ Commit API keys to git
- ❌ Share keys publicly
- ❌ Use production keys for testing
- ❌ Store keys in code files
- ❌ Share your `.env` file

---

## 🛠️ **Troubleshooting**

### "API key not found" Error

```bash
# Check .env file exists
ls -la .env

# Check key is set
cat .env | grep TIINGO_API_KEY

# Restart server
make dev
```

### "Invalid API key" Error

```bash
# Verify key is correct (no extra spaces)
# Check key status on provider website
# Try regenerating the key
```

### "Rate limit exceeded" Error

```bash
# Wait for rate limit to reset
# Upgrade to paid tier
# Use caching to reduce API calls
```

---

## 📚 **Resources**

- **Tiingo:** [tiingo.com/documentation](https://tiingo.com/documentation)
- **OpenRouter:** [openrouter.ai/docs](https://openrouter.ai/docs)
- **Exa:** [docs.exa.ai](https://docs.exa.ai)
- **FRED:** [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api)
- **Exchange Rate API:** [exchangerate-api.com/docs](https://www.exchangerate-api.com/docs)

---

## 🎯 **Summary**

### For Basic Usage (FREE):
```
TIINGO_API_KEY=required
```

### For Full Features (~$10/month):
```
TIINGO_API_KEY=required
OPENROUTER_API_KEY=highly_recommended
EXA_API_KEY=recommended
```

### Everything Else:
```
Optional - add as needed
```

---

**That's it! Start with just TIINGO_API_KEY and add others as you need more features.** 🚀

