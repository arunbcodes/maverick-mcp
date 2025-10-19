"""
Market Strategy Pattern Implementation

Encapsulates market-specific behavior for different stock exchanges.
Makes it trivial to add new markets (e.g., crypto) by implementing IMarketStrategy.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable, Optional

from maverick_mcp.config.markets import Market, MarketConfig, MARKET_CONFIGS

logger = logging.getLogger(__name__)


@runtime_checkable
class IMarketStrategy(Protocol):
    """
    Interface for market-specific behavior strategies.
    
    Implement this protocol to add support for a new market (e.g., crypto).
    """
    
    @property
    def market(self) -> Market:
        """Get the market this strategy handles."""
        ...
    
    @property
    def config(self) -> MarketConfig:
        """Get the market configuration."""
        ...
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is valid for this market.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            True if valid for this market
        """
        ...
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize a symbol to the canonical format for this market.
        
        Args:
            symbol: Stock ticker symbol (may have or lack suffix)
            
        Returns:
            Normalized symbol (e.g., 'RELIANCE.NS', 'AAPL')
        """
        ...
    
    def strip_suffix(self, symbol: str) -> str:
        """
        Remove market-specific suffix from symbol.
        
        Args:
            symbol: Full symbol with suffix
            
        Returns:
            Base symbol without suffix
        """
        ...
    
    def get_data_source(self) -> str:
        """
        Get the preferred data source for this market.
        
        Returns:
            Data source identifier (e.g., 'yfinance', 'binance')
        """
        ...
    
    def validate_symbol_format(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Validate symbol format and return error message if invalid.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        ...


class BaseMarketStrategy(ABC):
    """
    Abstract base class for market strategies.
    
    Provides common functionality and enforces the IMarketStrategy interface.
    """
    
    def __init__(self, market: Market):
        """
        Initialize the market strategy.
        
        Args:
            market: Market enum value
        """
        self._market = market
        self._config = MARKET_CONFIGS[market]
        logger.debug(f"Initialized {self.__class__.__name__} for {market.value}")
    
    @property
    def market(self) -> Market:
        """Get the market this strategy handles."""
        return self._market
    
    @property
    def config(self) -> MarketConfig:
        """Get the market configuration."""
        return self._config
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol to canonical format.
        
        Default implementation adds the market suffix if missing.
        """
        clean_symbol = symbol.split(".")[0].upper()
        return f"{clean_symbol}{self.config.symbol_suffix}"
    
    def strip_suffix(self, symbol: str) -> str:
        """Remove market-specific suffix."""
        return self.config.strip_suffix(symbol)
    
    def get_data_source(self) -> str:
        """Get preferred data source (default: yfinance)."""
        return "yfinance"
    
    @abstractmethod
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid for this market."""
        pass
    
    @abstractmethod
    def validate_symbol_format(self, symbol: str) -> tuple[bool, Optional[str]]:
        """Validate symbol format."""
        pass


class USMarketStrategy(BaseMarketStrategy):
    """
    Strategy for US stock market (NYSE, NASDAQ, AMEX).
    
    Symbol format: 1-5 uppercase letters (e.g., AAPL, GOOGL)
    """
    
    # Common US stock symbols for validation
    KNOWN_SYMBOLS = {
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM",
        "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC", "VZ",
        "ADBE", "CRM", "NFLX", "INTC", "CSCO", "PFE", "T", "KO", "PEP",
        "ABT", "MRK", "COST", "AVGO", "ACN", "TMO", "NKE", "DHR", "LLY",
        "NEE", "MDT", "ORCL", "TXN", "UNP", "PM", "BMY", "HON", "QCOM",
        "UPS", "RTX", "LIN", "LOW", "IBM", "AMGN", "SBUX", "CAT", "GE",
        # ETFs
        "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "EFA", "EEM", "AGG",
        "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
    }
    
    def __init__(self):
        super().__init__(Market.US)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if symbol is valid for US market.
        
        Valid if:
        - 1-5 uppercase letters
        - Matches known symbol pattern
        """
        clean_symbol = self.strip_suffix(symbol).upper()
        
        # Check if it's a known symbol (fast path)
        if clean_symbol in self.KNOWN_SYMBOLS:
            return True
        
        # Validate format: 1-5 uppercase letters
        return bool(re.match(r"^[A-Z]{1,5}$", clean_symbol))
    
    def validate_symbol_format(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Validate US stock symbol format.
        
        Returns:
            (True, None) if valid
            (False, error_message) if invalid
        """
        clean_symbol = self.strip_suffix(symbol).upper()
        
        if not clean_symbol:
            return False, "Symbol cannot be empty"
        
        if len(clean_symbol) > 5:
            return False, "US stock symbols must be 1-5 characters"
        
        if not re.match(r"^[A-Z]+$", clean_symbol):
            return False, "US stock symbols must contain only uppercase letters"
        
        return True, None


class IndianNSEMarketStrategy(BaseMarketStrategy):
    """
    Strategy for Indian NSE (National Stock Exchange).
    
    Symbol format: SYMBOL.NS (e.g., RELIANCE.NS, TCS.NS)
    """
    
    # Major NSE stocks (Nifty 50)
    KNOWN_SYMBOLS = {
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
        "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK", "LT",
        "HCLTECH", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA",
        "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "BAJAJFINSV",
        "TECHM", "POWERGRID", "NTPC", "M&M", "ONGC", "TATAMOTORS",
        "JSWSTEEL", "INDUSINDBK", "ADANIENT", "ADANIPORTS", "TATASTEEL",
        "COALINDIA", "HINDALCO", "GRASIM", "DIVISLAB", "DRREDDY",
        "CIPLA", "APOLLOHOSP", "EICHERMOT", "BRITANNIA", "BPCL",
        "HEROMOTOCO", "TATACONSUM", "SBILIFE", "BAJAJ-AUTO", "HDFCLIFE",
    }
    
    def __init__(self):
        super().__init__(Market.INDIA_NSE)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if symbol is valid for NSE.
        
        Valid if:
        - Has .NS suffix or is known NSE symbol
        - Base symbol is uppercase letters/numbers/hyphens
        """
        if symbol.upper().endswith(".NS"):
            base_symbol = self.strip_suffix(symbol).upper()
        else:
            base_symbol = symbol.upper()
        
        # Check known symbols (fast path)
        if base_symbol in self.KNOWN_SYMBOLS:
            return True
        
        # Validate format: uppercase letters, numbers, hyphens, ampersands
        return bool(re.match(r"^[A-Z0-9&-]+$", base_symbol))
    
    def validate_symbol_format(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Validate NSE symbol format.
        
        Returns:
            (True, None) if valid
            (False, error_message) if invalid
        """
        base_symbol = self.strip_suffix(symbol).upper()
        
        if not base_symbol:
            return False, "Symbol cannot be empty"
        
        if len(base_symbol) > 20:
            return False, "NSE symbols must be 20 characters or less"
        
        if not re.match(r"^[A-Z0-9&-]+$", base_symbol):
            return False, "NSE symbols must contain only uppercase letters, numbers, hyphens, and ampersands"
        
        return True, None


class IndianBSEMarketStrategy(BaseMarketStrategy):
    """
    Strategy for Indian BSE (Bombay Stock Exchange).
    
    Symbol format: SYMBOL.BO (e.g., RELIANCE.BO, TCS.BO)
    """
    
    # Major BSE stocks (Sensex 30)
    KNOWN_SYMBOLS = {
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
        "ITC", "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK", "LT",
        "HCLTECH", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA",
        "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "TECHM", "POWERGRID",
        "NTPC", "M&M", "ONGC", "TATAMOTORS", "JSWSTEEL", "INDUSINDBK",
        "TATASTEEL",
    }
    
    def __init__(self):
        super().__init__(Market.INDIA_BSE)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Check if symbol is valid for BSE.
        
        Valid if:
        - Has .BO suffix or is known BSE symbol
        - Base symbol is uppercase letters/numbers/hyphens
        """
        if symbol.upper().endswith(".BO"):
            base_symbol = self.strip_suffix(symbol).upper()
        else:
            base_symbol = symbol.upper()
        
        # Check known symbols (fast path)
        if base_symbol in self.KNOWN_SYMBOLS:
            return True
        
        # Validate format: uppercase letters, numbers, hyphens, ampersands
        return bool(re.match(r"^[A-Z0-9&-]+$", base_symbol))
    
    def validate_symbol_format(self, symbol: str) -> tuple[bool, Optional[str]]:
        """
        Validate BSE symbol format.
        
        Returns:
            (True, None) if valid
            (False, error_message) if invalid
        """
        base_symbol = self.strip_suffix(symbol).upper()
        
        if not base_symbol:
            return False, "Symbol cannot be empty"
        
        if len(base_symbol) > 20:
            return False, "BSE symbols must be 20 characters or less"
        
        if not re.match(r"^[A-Z0-9&-]+$", base_symbol):
            return False, "BSE symbols must contain only uppercase letters, numbers, hyphens, and ampersands"
        
        return True, None


class MarketStrategyFactory:
    """
    Factory for creating and caching market strategies.
    
    Usage:
        factory = MarketStrategyFactory()
        strategy = factory.get_strategy("AAPL")  # Returns USMarketStrategy
        strategy = factory.get_strategy("RELIANCE.NS")  # Returns IndianNSEMarketStrategy
    """
    
    _strategies: dict[Market, IMarketStrategy] = {}
    
    @classmethod
    def get_strategy(cls, symbol: str) -> IMarketStrategy:
        """
        Get the appropriate market strategy for a symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Market strategy instance
            
        Example:
            >>> factory = MarketStrategyFactory()
            >>> strategy = factory.get_strategy("AAPL")
            >>> strategy.market
            Market.US
            >>> strategy = factory.get_strategy("RELIANCE.NS")
            >>> strategy.market
            Market.INDIA_NSE
        """
        from maverick_mcp.config.markets import get_market_from_symbol
        
        market = get_market_from_symbol(symbol)
        
        # Return cached strategy if available
        if market in cls._strategies:
            return cls._strategies[market]
        
        # Create new strategy
        if market == Market.US:
            strategy = USMarketStrategy()
        elif market == Market.INDIA_NSE:
            strategy = IndianNSEMarketStrategy()
        elif market == Market.INDIA_BSE:
            strategy = IndianBSEMarketStrategy()
        else:
            raise ValueError(f"No strategy available for market: {market}")
        
        # Cache and return
        cls._strategies[market] = strategy
        logger.info(f"Created and cached {strategy.__class__.__name__} for {market.value}")
        return strategy
    
    @classmethod
    def get_strategy_by_market(cls, market: Market) -> IMarketStrategy:
        """
        Get strategy by market enum.
        
        Args:
            market: Market enum value
            
        Returns:
            Market strategy instance
        """
        # Return cached strategy if available
        if market in cls._strategies:
            return cls._strategies[market]
        
        # Create new strategy
        if market == Market.US:
            strategy = USMarketStrategy()
        elif market == Market.INDIA_NSE:
            strategy = IndianNSEMarketStrategy()
        elif market == Market.INDIA_BSE:
            strategy = IndianBSEMarketStrategy()
        else:
            raise ValueError(f"No strategy available for market: {market}")
        
        # Cache and return
        cls._strategies[market] = strategy
        return strategy
    
    @classmethod
    def clear_cache(cls):
        """Clear the strategy cache."""
        cls._strategies.clear()
        logger.debug("Cleared market strategy cache")


__all__ = [
    "IMarketStrategy",
    "BaseMarketStrategy",
    "USMarketStrategy",
    "IndianNSEMarketStrategy",
    "IndianBSEMarketStrategy",
    "MarketStrategyFactory",
]

