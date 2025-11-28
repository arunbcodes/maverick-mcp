"""
Indian Stock Symbol Mapping.

Maps stock symbols to company names for Indian markets (NSE/BSE).
"""

import logging
from typing import ClassVar

logger = logging.getLogger(__name__)


class IndianStockSymbolMapper:
    """
    Utility class for mapping Indian stock symbols to company names.

    Provides mappings for major NSE and BSE stocks.
    """

    # Mapping of symbol base names to company names
    SYMBOL_TO_COMPANY: ClassVar[dict[str, str]] = {
        # Nifty 50 constituents
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank",
        "INFY": "Infosys",
        "ICICIBANK": "ICICI Bank",
        "HINDUNILVR": "Hindustan Unilever",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "ITC": "ITC Limited",
        "LT": "Larsen & Toubro",
        "AXISBANK": "Axis Bank",
        "ASIANPAINT": "Asian Paints",
        "MARUTI": "Maruti Suzuki",
        "WIPRO": "Wipro",
        "HCLTECH": "HCL Technologies",
        "BAJFINANCE": "Bajaj Finance",
        "ONGC": "Oil and Natural Gas Corporation",
        "NTPC": "NTPC Limited",
        "POWERGRID": "Power Grid Corporation",
        "TITAN": "Titan Company",
        "SUNPHARMA": "Sun Pharmaceutical",
        "ULTRACEMCO": "UltraTech Cement",
        "TECHM": "Tech Mahindra",
        "NESTLEIND": "Nestle India",
        "M&M": "Mahindra & Mahindra",
        "TATASTEEL": "Tata Steel",
        "TATAMOTORS": "Tata Motors",
        "DRREDDY": "Dr. Reddy's Laboratories",
        "CIPLA": "Cipla",
        "BAJAJFINSV": "Bajaj Finserv",
        "ADANIENT": "Adani Enterprises",
        "ADANIPORTS": "Adani Ports",
        "DIVISLAB": "Divi's Laboratories",
        "GRASIM": "Grasim Industries",
        "EICHERMOT": "Eicher Motors",
        "BRITANNIA": "Britannia Industries",
        "JSWSTEEL": "JSW Steel",
        "HINDALCO": "Hindalco Industries",
        "COALINDIA": "Coal India",
        "BPCL": "Bharat Petroleum",
        "INDUSINDBK": "IndusInd Bank",
        "SBILIFE": "SBI Life Insurance",
        "HEROMOTOCO": "Hero MotoCorp",
        "APOLLOHOSP": "Apollo Hospitals",
        "TATACONSUM": "Tata Consumer Products",
        "UPL": "UPL Limited",
        "LTIM": "LTIMindtree",
        "HDFCLIFE": "HDFC Life Insurance",
        # Additional popular stocks
        "BAJAJ-AUTO": "Bajaj Auto",
        "VEDL": "Vedanta",
        "PIDILITIND": "Pidilite Industries",
        "DABUR": "Dabur India",
        "GODREJCP": "Godrej Consumer Products",
        "SIEMENS": "Siemens India",
        "HAVELLS": "Havells India",
        "PAGEIND": "Page Industries",
        "COLPAL": "Colgate-Palmolive",
        "MARICO": "Marico",
        "TRENT": "Trent Limited",
        "ZOMATO": "Zomato",
        "PAYTM": "Paytm (One97)",
        "NYKAA": "Nykaa (FSN E-Commerce)",
        "POLICYBZR": "PB Fintech",
        "DMART": "Avenue Supermarts",
        "IRCTC": "Indian Railway Catering",
        "HAL": "Hindustan Aeronautics",
        "RVNL": "Rail Vikas Nigam",
    }

    @classmethod
    def get_company_name(cls, symbol: str) -> str | None:
        """
        Get company name for a given symbol.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "RELIANCE.NS", "RELIANCE.BO")

        Returns:
            Company name or None if not found
        """
        # Remove exchange suffix
        base_symbol = symbol.upper().replace(".NS", "").replace(".BO", "")

        return cls.SYMBOL_TO_COMPANY.get(base_symbol)

    @classmethod
    def get_symbol_for_company(cls, company_name: str) -> str | None:
        """
        Get symbol for a given company name.

        Args:
            company_name: Company name to search for

        Returns:
            Stock symbol or None if not found
        """
        company_lower = company_name.lower()

        for symbol, name in cls.SYMBOL_TO_COMPANY.items():
            if name.lower() in company_lower or company_lower in name.lower():
                return symbol

        return None

    @classmethod
    def search_companies(cls, query: str) -> list[dict[str, str]]:
        """
        Search for companies matching a query.

        Args:
            query: Search query

        Returns:
            List of matching companies with symbol and name
        """
        query_lower = query.lower()
        results = []

        for symbol, name in cls.SYMBOL_TO_COMPANY.items():
            if query_lower in symbol.lower() or query_lower in name.lower():
                results.append({"symbol": symbol, "name": name})

        return results


__all__ = ["IndianStockSymbolMapper"]
