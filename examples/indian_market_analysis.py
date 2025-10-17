"""
Indian Market Analysis Example

Comprehensive example demonstrating all Indian market features:
- Stock screening strategies
- Economic indicators
- News sentiment analysis
- Market comparison
- Currency conversion
- Technical analysis

Usage:
    python examples/indian_market_analysis.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from maverick_mcp.providers.indian_market_data import IndianMarketDataProvider
from maverick_mcp.application.screening.indian_market import (
    get_maverick_bullish_india,
    get_maverick_bearish_india,
    get_nifty50_momentum,
    get_nifty_sector_rotation,
    get_value_picks_india,
    format_indian_currency,
)
from maverick_mcp.providers.rbi_data import RBIDataProvider
from maverick_mcp.providers.indian_news import IndianNewsProvider
from maverick_mcp.analysis.market_comparison import MarketComparisonAnalyzer
from maverick_mcp.utils.currency_converter import CurrencyConverter


def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def example_1_market_status():
    """Example 1: Check Indian market status"""
    print_header("Example 1: Indian Market Status")
    
    provider = IndianMarketDataProvider()
    status = provider.get_market_status()
    
    print(f"Market Status: {status['status']}")
    print(f"Exchange: NSE")
    print(f"Trading Hours: 9:15 AM - 3:30 PM IST")
    
    if status['status'] == 'open':
        print("✅ Market is currently OPEN for trading")
    else:
        print("❌ Market is currently CLOSED")


def example_2_stock_screening():
    """Example 2: Stock screening strategies"""
    print_header("Example 2: Stock Screening Strategies")
    
    # Bullish recommendations
    print("\n📈 Maverick Bullish India (Top 5):")
    bullish = get_maverick_bullish_india(limit=5)
    for i, stock in enumerate(bullish[:5], 1):
        print(f"  {i}. {stock['symbol']}: {format_indian_currency(stock['price'])}")
        print(f"     RSI: {stock.get('rsi', 'N/A')}, Volume: {stock.get('volume', 'N/A'):,}")
    
    # Bearish recommendations
    print("\n📉 Maverick Bearish India (Top 3):")
    bearish = get_maverick_bearish_india(limit=3)
    for i, stock in enumerate(bearish[:3], 1):
        print(f"  {i}. {stock['symbol']}: {format_indian_currency(stock['price'])}")
    
    # Nifty 50 Momentum
    print("\n🚀 Nifty 50 Momentum (Top 5):")
    momentum = get_nifty50_momentum(limit=5)
    for i, stock in enumerate(momentum[:5], 1):
        print(f"  {i}. {stock['symbol']}: {format_indian_currency(stock['price'])}")


def example_3_sector_rotation():
    """Example 3: Sector rotation analysis"""
    print_header("Example 3: Nifty Sector Rotation Analysis")
    
    try:
        sector_data = get_nifty_sector_rotation(lookback_days=90, top_n=3)
        
        print("\n🔥 Top Performing Sectors (90-day lookback):")
        for i, sector in enumerate(sector_data.get('top_sectors', [])[:3], 1):
            print(f"\n  {i}. {sector['name']}")
            print(f"     Average Return: {sector['avg_return']:.2f}%")
            print(f"     Stock Count: {sector['stock_count']}")
            print(f"     Top Stocks:")
            for stock in sector.get('top_stocks', [])[:3]:
                print(f"       - {stock['symbol']}: {stock['return']:.2f}%")
    except Exception as e:
        print(f"⚠️  Sector rotation analysis requires stock data: {e}")
        print("   Tip: Seed the database first with Indian stocks")


def example_4_economic_indicators():
    """Example 4: RBI economic indicators"""
    print_header("Example 4: Indian Economic Indicators")
    
    provider = RBIDataProvider()
    
    # Policy rates
    print("\n🏦 RBI Policy Rates:")
    rates = provider.get_policy_rates()
    print(f"  Repo Rate: {rates.get('repo_rate', 'N/A')}%")
    print(f"  Reverse Repo Rate: {rates.get('reverse_repo_rate', 'N/A')}%")
    print(f"  CRR: {rates.get('crr', 'N/A')}%")
    print(f"  SLR: {rates.get('slr', 'N/A')}%")
    
    # GDP Growth
    print("\n📊 GDP Growth:")
    gdp = provider.get_gdp_growth()
    if 'current' in gdp:
        print(f"  Current: {gdp['current']:.2f}%")
        print(f"  Previous: {gdp['previous']:.2f}%")
        print(f"  Year: {gdp['year']}")
    else:
        print(f"  Status: {gdp.get('status', 'Data unavailable')}")
    
    # Forex Reserves
    print("\n💰 Foreign Exchange Reserves:")
    forex = provider.get_forex_reserves()
    if 'total_reserves_usd' in forex:
        print(f"  Total: ${forex['total_reserves_usd']:.2f} billion")
    
    # Economic Calendar
    print("\n📅 Upcoming Economic Events:")
    calendar = provider.get_economic_calendar(days_ahead=30)
    for event in calendar[:3]:
        print(f"  {event['date'][:10]}: {event['event']}")


def example_5_news_sentiment():
    """Example 5: News and sentiment analysis"""
    print_header("Example 5: News & Sentiment Analysis")
    
    provider = IndianNewsProvider()
    
    # Market news
    print("\n📰 Latest Market News:")
    market_news = provider.get_market_news(limit=3)
    for i, article in enumerate(market_news, 1):
        print(f"\n  {i}. {article['title']}")
        print(f"     Source: {article['source']} | Sentiment: {article.get('sentiment', 'N/A')}")
    
    # Stock-specific sentiment
    symbol = "TCS.NS"
    print(f"\n💭 Sentiment Analysis for {symbol}:")
    sentiment = provider.analyze_sentiment(symbol, period="7d")
    print(f"  Overall Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
    print(f"  Sentiment Score: {sentiment.get('sentiment_score', 0):.2f}")
    print(f"  Articles Analyzed: {sentiment.get('article_count', 0)}")
    
    if 'sentiment_distribution' in sentiment:
        dist = sentiment['sentiment_distribution']
        print(f"  Distribution: {dist['positive']} positive, {dist['negative']} negative, {dist['neutral']} neutral")
    
    # Trending topics
    print("\n🔥 Trending Topics:")
    topics = provider.get_trending_topics(limit=5)
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")


def example_6_market_comparison():
    """Example 6: US vs Indian market comparison"""
    print_header("Example 6: Market Comparison (US vs India)")
    
    analyzer = MarketComparisonAnalyzer()
    
    # Index comparison
    print("\n🌍 S&P 500 vs Nifty 50 (1-year):")
    try:
        comparison = analyzer.compare_indices(period="1y")
        
        if comparison.get('status') == 'success':
            print(f"\n  S&P 500:")
            print(f"    Return: {comparison['sp500']['return_pct']:.2f}%")
            print(f"    Volatility: {comparison['sp500']['volatility_pct']:.2f}%")
            print(f"    Current Level: {comparison['sp500']['current_level']:,.2f}")
            
            print(f"\n  Nifty 50:")
            print(f"    Return: {comparison['nifty50']['return_pct']:.2f}%")
            print(f"    Volatility: {comparison['nifty50']['volatility_pct']:.2f}%")
            print(f"    Current Level: {comparison['nifty50']['current_level']:,.2f}")
            
            print(f"\n  Correlation: {comparison['correlation']:.3f}")
            print(f"  Better Performer: {comparison['comparison']['better_performer']}")
        else:
            print(f"  ⚠️  {comparison.get('error', 'Unable to fetch data')}")
    except Exception as e:
        print(f"  ⚠️  Market comparison requires network access: {e}")
    
    # Stock comparison
    print("\n🏢 Microsoft vs TCS:")
    try:
        stock_comp = analyzer.compare_stocks("MSFT", "TCS.NS", period="1y", currency="USD")
        
        if stock_comp.get('status') == 'success':
            print(f"\n  Microsoft:")
            print(f"    Return: {stock_comp['us_stock']['return_pct']:.2f}%")
            print(f"    Current Price: ${stock_comp['us_stock']['current_price']:.2f}")
            
            print(f"\n  TCS:")
            print(f"    Return: {stock_comp['indian_stock']['return_pct']:.2f}%")
            print(f"    Current Price: ${stock_comp['indian_stock']['current_price']:.2f}")
            
            print(f"\n  Correlation: {stock_comp['correlation']:.3f}")
        else:
            print(f"  ⚠️  {stock_comp.get('error', 'Unable to fetch data')}")
    except Exception as e:
        print(f"  ⚠️  Stock comparison requires network access: {e}")


def example_7_currency_conversion():
    """Example 7: Currency conversion"""
    print_header("Example 7: Currency Conversion")
    
    converter = CurrencyConverter()
    
    # Get exchange rate
    rate = converter.get_exchange_rate("USD", "INR")
    print(f"\n💱 Current Exchange Rate:")
    print(f"  1 USD = ₹{rate:.2f} INR")
    
    # INR to USD conversions
    print(f"\n₹ → $ Conversions:")
    inr_amounts = [1000, 10000, 100000, 1000000]
    for inr in inr_amounts:
        usd = converter.convert(inr, "INR", "USD")
        print(f"  {format_indian_currency(inr)} = ${usd:,.2f}")
    
    # USD to INR conversions
    print(f"\n$ → ₹ Conversions:")
    usd_amounts = [100, 1000, 10000]
    for usd in usd_amounts:
        inr = converter.convert(usd, "USD", "INR")
        print(f"  ${usd:,} = {format_indian_currency(inr)}")


def example_8_technical_analysis():
    """Example 8: Technical analysis on Indian stock"""
    print_header("Example 8: Technical Analysis - Reliance Industries")
    
    try:
        provider = IndianMarketDataProvider()
        
        # Get data for Reliance
        symbol = "RELIANCE.NS"
        print(f"\n📊 Analyzing {symbol}...")
        
        data = provider.get_stock_data(symbol, period="3m")
        
        if not data.empty:
            current_price = data['close'].iloc[-1]
            high_52w = data['high'].max()
            low_52w = data['low'].min()
            avg_volume = data['volume'].mean()
            
            print(f"\n  Current Price: {format_indian_currency(current_price)}")
            print(f"  52-Week High: {format_indian_currency(high_52w)}")
            print(f"  52-Week Low: {format_indian_currency(low_52w)}")
            print(f"  Avg Volume: {avg_volume:,.0f}")
            
            # Calculate simple metrics
            price_from_high = ((current_price - high_52w) / high_52w) * 100
            price_from_low = ((current_price - low_52w) / low_52w) * 100
            
            print(f"\n  From 52W High: {price_from_high:.2f}%")
            print(f"  From 52W Low: {price_from_low:.2f}%")
            
            # Price position
            position = ((current_price - low_52w) / (high_52w - low_52w)) * 100
            print(f"  Position in Range: {position:.1f}%")
        else:
            print("  ⚠️  No data available")
            
    except Exception as e:
        print(f"  ⚠️  Technical analysis requires network access: {e}")


def example_9_portfolio_scenario():
    """Example 9: Multi-market portfolio scenario"""
    print_header("Example 9: Multi-Market Portfolio Analysis")
    
    converter = CurrencyConverter()
    
    # Define portfolio
    print("\n💼 Portfolio Composition:")
    print("\n  US Stocks:")
    us_portfolio = {
        "AAPL": {"shares": 50, "price": 175.00},
        "MSFT": {"shares": 30, "price": 380.00},
        "GOOGL": {"shares": 20, "price": 140.00}
    }
    
    us_total = 0
    for symbol, data in us_portfolio.items():
        value = data['shares'] * data['price']
        us_total += value
        print(f"    {symbol}: {data['shares']} shares @ ${data['price']:.2f} = ${value:,.2f}")
    
    print(f"\n  Total US Portfolio: ${us_total:,.2f}")
    
    print("\n  Indian Stocks:")
    indian_portfolio = {
        "RELIANCE.NS": {"shares": 100, "price": 2500.00},
        "TCS.NS": {"shares": 50, "price": 3600.00},
        "INFY.NS": {"shares": 200, "price": 1500.00}
    }
    
    indian_total_inr = 0
    for symbol, data in indian_portfolio.items():
        value = data['shares'] * data['price']
        indian_total_inr += value
        print(f"    {symbol}: {data['shares']} shares @ ₹{data['price']:.2f} = {format_indian_currency(value)}")
    
    print(f"\n  Total Indian Portfolio: {format_indian_currency(indian_total_inr)}")
    
    # Convert to common currency
    indian_total_usd = converter.convert(indian_total_inr, "INR", "USD")
    total_portfolio = us_total + indian_total_usd
    
    print(f"\n💰 Total Portfolio Value:")
    print(f"  US Portion: ${us_total:,.2f} ({(us_total/total_portfolio)*100:.1f}%)")
    print(f"  Indian Portion: ${indian_total_usd:,.2f} ({(indian_total_usd/total_portfolio)*100:.1f}%)")
    print(f"  TOTAL: ${total_portfolio:,.2f}")


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "INDIAN MARKET ANALYSIS - COMPLETE EXAMPLES" + " " * 20 + "║")
    print("╚" + "═" * 78 + "╝")
    
    examples = [
        ("Market Status", example_1_market_status),
        ("Stock Screening", example_2_stock_screening),
        ("Sector Rotation", example_3_sector_rotation),
        ("Economic Indicators", example_4_economic_indicators),
        ("News & Sentiment", example_5_news_sentiment),
        ("Market Comparison", example_6_market_comparison),
        ("Currency Conversion", example_7_currency_conversion),
        ("Technical Analysis", example_8_technical_analysis),
        ("Portfolio Analysis", example_9_portfolio_scenario),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print_header(f"Example {i}: {name}")
            print(f"\n⚠️  Error running example: {e}")
            print("   This may be due to missing data or network issues.")
    
    # Summary
    print("\n")
    print("=" * 80)
    print("  ✅ All examples completed!")
    print("=" * 80)
    print("\nNotes:")
    print("  • Some examples require network access to fetch real-time data")
    print("  • Run 'python scripts/seed_indian_stocks.py' to populate database")
    print("  • Configure API keys in .env for enhanced features")
    print("\nFor more information:")
    print("  • Documentation: docs/INDIAN_MARKET.md")
    print("  • API Reference: docs/PHASE4_IMPLEMENTATION.md")
    print()


if __name__ == "__main__":
    main()

