"""
Centralized Symbol Mapping for Indian Stocks.

Provides mappings between stock symbols and company names
to eliminate duplication across news scrapers and other components.
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class IndianStockSymbolMapper:
    """
    Centralized mapper for Indian stock symbols to company names.
    
    Provides a single source of truth for symbol-to-company-name mappings
    across all scrapers and components.
    """
    
    # Centralized symbol-to-company mapping
    _SYMBOL_TO_COMPANY: Dict[str, str] = {
        # Major NSE/BSE stocks
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "INFY": "Infosys",
        "HDFCBANK": "HDFC Bank",
        "ITC": "ITC",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel",
        "ICICIBANK": "ICICI Bank",
        "HINDUNILVR": "Hindustan Unilever",
        "LT": "Larsen & Toubro",
        "WIPRO": "Wipro",
        "AXISBANK": "Axis Bank",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "MARUTI": "Maruti Suzuki",
        "TATASTEEL": "Tata Steel",
        "SUNPHARMA": "Sun Pharmaceutical",
        "TITAN": "Titan Company",
        "ULTRACEMCO": "UltraTech Cement",
        "NESTLEIND": "Nestle India",
        "BAJFINANCE": "Bajaj Finance",
        "BAJAJFINSV": "Bajaj Finserv",
        "TECHM": "Tech Mahindra",
        "POWERGRID": "Power Grid Corporation",
        "NTPC": "NTPC",
        "M&M": "Mahindra & Mahindra",
        "ONGC": "Oil and Natural Gas Corporation",
        "TATAMOTORS": "Tata Motors",
        "JSWSTEEL": "JSW Steel",
        "INDUSINDBK": "IndusInd Bank",
        "ADANIENT": "Adani Enterprises",
        "ADANIPORTS": "Adani Ports",
        "COALINDIA": "Coal India",
        "HINDALCO": "Hindalco Industries",
        "GRASIM": "Grasim Industries",
        "DIVISLAB": "Divi's Laboratories",
        "DRREDDY": "Dr. Reddy's Laboratories",
        "CIPLA": "Cipla",
        "APOLLOHOSP": "Apollo Hospitals",
        "EICHERMOT": "Eicher Motors",
        "BRITANNIA": "Britannia Industries",
        "BPCL": "Bharat Petroleum",
        "HEROMOTOCO": "Hero MotoCorp",
        "TATACONSUM": "Tata Consumer Products",
        "SBILIFE": "SBI Life Insurance",
        "BAJAJ-AUTO": "Bajaj Auto",
        "HDFCLIFE": "HDFC Life Insurance",
        "IOC": "Indian Oil Corporation",
        "UPL": "UPL Limited",
        "HCLTECH": "HCL Technologies",
        "ASIANPAINT": "Asian Paints",
    }
    
    # Reverse mapping (company name to symbol) - lazily computed
    _COMPANY_TO_SYMBOL: Optional[Dict[str, str]] = None
    
    @classmethod
    def get_company_name(cls, symbol: str) -> Optional[str]:
        """
        Get company name for a given symbol.
        
        Args:
            symbol: Stock symbol (without suffix, e.g., "RELIANCE")
            
        Returns:
            Company name or None if not found
            
        Example:
            >>> IndianStockSymbolMapper.get_company_name("RELIANCE")
            'Reliance Industries'
        """
        return cls._SYMBOL_TO_COMPANY.get(symbol.upper())
    
    @classmethod
    def get_symbol(cls, company_name: str) -> Optional[str]:
        """
        Get symbol for a given company name.
        
        Args:
            company_name: Company name
            
        Returns:
            Stock symbol or None if not found
            
        Example:
            >>> IndianStockSymbolMapper.get_symbol("Reliance Industries")
            'RELIANCE'
        """
        # Lazy initialization of reverse mapping
        if cls._COMPANY_TO_SYMBOL is None:
            cls._COMPANY_TO_SYMBOL = {
                v.lower(): k for k, v in cls._SYMBOL_TO_COMPANY.items()
            }
        
        return cls._COMPANY_TO_SYMBOL.get(company_name.lower())
    
    @classmethod
    def register_mapping(cls, symbol: str, company_name: str) -> None:
        """
        Register a new symbol-to-company mapping.
        
        Args:
            symbol: Stock symbol
            company_name: Company name
            
        Example:
            >>> IndianStockSymbolMapper.register_mapping("NEWCO", "New Company Ltd")
        """
        symbol_upper = symbol.upper()
        
        if symbol_upper in cls._SYMBOL_TO_COMPANY:
            logger.warning(
                f"Overwriting existing mapping for {symbol_upper}: "
                f"{cls._SYMBOL_TO_COMPANY[symbol_upper]} -> {company_name}"
            )
        
        cls._SYMBOL_TO_COMPANY[symbol_upper] = company_name
        
        # Invalidate reverse mapping cache
        cls._COMPANY_TO_SYMBOL = None
        
        logger.info(f"Registered mapping: {symbol_upper} -> {company_name}")
    
    @classmethod
    def has_symbol(cls, symbol: str) -> bool:
        """
        Check if a symbol is registered.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if symbol is registered
        """
        return symbol.upper() in cls._SYMBOL_TO_COMPANY
    
    @classmethod
    def get_all_symbols(cls) -> list[str]:
        """
        Get all registered symbols.
        
        Returns:
            List of registered stock symbols
        """
        return list(cls._SYMBOL_TO_COMPANY.keys())
    
    @classmethod
    def get_all_companies(cls) -> list[str]:
        """
        Get all registered company names.
        
        Returns:
            List of registered company names
        """
        return list(cls._SYMBOL_TO_COMPANY.values())


__all__ = ["IndianStockSymbolMapper"]

