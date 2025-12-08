"""
Export Service.

Handles data export in multiple formats (CSV, PDF, Excel).
"""

import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================
# Enums and Types
# ============================================


class ExportFormat(Enum):
    """Available export formats."""
    
    CSV = "csv"
    JSON = "json"
    # PDF and Excel require additional libraries
    # PDF = "pdf"
    # EXCEL = "xlsx"


class ExportType(Enum):
    """Types of data that can be exported."""
    
    PORTFOLIO = "portfolio"
    PORTFOLIO_HISTORY = "portfolio_history"
    WATCHLIST = "watchlist"
    SCREENING_RESULTS = "screening_results"
    STOCK_ANALYSIS = "stock_analysis"
    TAX_REPORT = "tax_report"
    TRADE_JOURNAL = "trade_journal"


@dataclass
class ExportConfig:
    """Configuration for an export."""
    
    export_type: ExportType
    format: ExportFormat
    include_headers: bool = True
    date_format: str = "%Y-%m-%d"
    decimal_places: int = 2
    
    # Type-specific options
    options: dict | None = None


@dataclass
class ExportResult:
    """Result of an export operation."""
    
    content: bytes
    filename: str
    content_type: str
    row_count: int
    generated_at: datetime


# ============================================
# Export Service
# ============================================


class ExportService:
    """
    Service for exporting data in multiple formats.
    
    Features:
    - CSV export for all data types
    - JSON export for programmatic access
    - Portfolio export with positions and P&L
    - Watchlist export
    - Screening results export
    - Tax report generation (cost basis, gains)
    """
    
    # Content types
    CONTENT_TYPES = {
        ExportFormat.CSV: "text/csv",
        ExportFormat.JSON: "application/json",
    }
    
    def __init__(self):
        pass
    
    # ================================
    # Main Export Method
    # ================================
    
    async def export(
        self,
        export_type: ExportType,
        data: list[dict] | dict,
        format: ExportFormat = ExportFormat.CSV,
        config: ExportConfig | None = None,
    ) -> ExportResult:
        """
        Export data in the specified format.
        
        Args:
            export_type: Type of data being exported
            data: The data to export
            format: Output format
            config: Export configuration options
        
        Returns:
            ExportResult with content bytes and metadata
        """
        if config is None:
            config = ExportConfig(export_type=export_type, format=format)
        
        # Normalize data to list
        if isinstance(data, dict):
            data = [data]
        
        # Generate export based on format
        if format == ExportFormat.CSV:
            content = self._export_csv(data, config)
        elif format == ExportFormat.JSON:
            content = self._export_json(data, config)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Generate filename
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        extension = format.value
        filename = f"{export_type.value}_{timestamp}.{extension}"
        
        return ExportResult(
            content=content,
            filename=filename,
            content_type=self.CONTENT_TYPES[format],
            row_count=len(data),
            generated_at=datetime.now(UTC),
        )
    
    # ================================
    # Portfolio Export
    # ================================
    
    async def export_portfolio(
        self,
        positions: list[dict],
        format: ExportFormat = ExportFormat.CSV,
        include_summary: bool = True,
    ) -> ExportResult:
        """
        Export portfolio positions.
        
        Columns: Ticker, Shares, Cost Basis, Current Price, Market Value,
                 Unrealized P&L, P&L %, Sector
        """
        # Transform positions to export format
        export_data = []
        
        for pos in positions:
            export_data.append({
                "Ticker": pos.get("ticker", ""),
                "Shares": self._format_number(pos.get("shares", 0), 4),
                "Cost Basis": self._format_currency(pos.get("cost_basis", 0)),
                "Avg Cost": self._format_currency(pos.get("avg_cost", 0)),
                "Current Price": self._format_currency(pos.get("current_price", 0)),
                "Market Value": self._format_currency(pos.get("market_value", 0)),
                "Unrealized P&L": self._format_currency(pos.get("unrealized_pl", 0)),
                "P&L %": self._format_percent(pos.get("unrealized_pl_pct", 0)),
                "Sector": pos.get("sector", ""),
            })
        
        # Add summary row if requested
        if include_summary and export_data:
            total_cost = sum(p.get("cost_basis", 0) or 0 for p in positions)
            total_value = sum(p.get("market_value", 0) or 0 for p in positions)
            total_pl = total_value - total_cost
            total_pl_pct = (total_pl / total_cost * 100) if total_cost else 0
            
            export_data.append({
                "Ticker": "TOTAL",
                "Shares": "",
                "Cost Basis": self._format_currency(total_cost),
                "Avg Cost": "",
                "Current Price": "",
                "Market Value": self._format_currency(total_value),
                "Unrealized P&L": self._format_currency(total_pl),
                "P&L %": self._format_percent(total_pl_pct),
                "Sector": "",
            })
        
        config = ExportConfig(
            export_type=ExportType.PORTFOLIO,
            format=format,
        )
        
        return await self.export(ExportType.PORTFOLIO, export_data, format, config)
    
    # ================================
    # Watchlist Export
    # ================================
    
    async def export_watchlist(
        self,
        watchlist_name: str,
        items: list[dict],
        format: ExportFormat = ExportFormat.CSV,
    ) -> ExportResult:
        """
        Export watchlist items.
        
        Columns: Ticker, Added Date, Notes, Target Price, Stop Price,
                 Current Price, Price Change %
        """
        export_data = []
        
        for item in items:
            export_data.append({
                "Ticker": item.get("ticker", ""),
                "Added Date": self._format_date(item.get("added_at")),
                "Notes": item.get("notes", ""),
                "Target Price": self._format_currency(item.get("target_price")),
                "Stop Price": self._format_currency(item.get("stop_price")),
                "Current Price": self._format_currency(item.get("current_price")),
                "Price Change %": self._format_percent(item.get("price_change_pct")),
            })
        
        config = ExportConfig(
            export_type=ExportType.WATCHLIST,
            format=format,
            options={"watchlist_name": watchlist_name},
        )
        
        result = await self.export(ExportType.WATCHLIST, export_data, format, config)
        result.filename = f"watchlist_{watchlist_name.lower().replace(' ', '_')}_{datetime.now(UTC).strftime('%Y%m%d')}.{format.value}"
        
        return result
    
    # ================================
    # Screening Results Export
    # ================================
    
    async def export_screening_results(
        self,
        screener_name: str,
        results: list[dict],
        format: ExportFormat = ExportFormat.CSV,
    ) -> ExportResult:
        """
        Export screening results.
        
        Dynamic columns based on available data.
        """
        if not results:
            export_data = [{"Message": "No results"}]
        else:
            # Get all unique keys from results
            all_keys = set()
            for result in results:
                all_keys.update(result.keys())
            
            # Order keys: ticker first, then alphabetical
            ordered_keys = ["ticker"] if "ticker" in all_keys else []
            ordered_keys.extend(sorted(k for k in all_keys if k != "ticker"))
            
            export_data = []
            for result in results:
                row = {}
                for key in ordered_keys:
                    value = result.get(key)
                    # Format based on type
                    if isinstance(value, float):
                        row[key] = self._format_number(value, 2)
                    else:
                        row[key] = value if value is not None else ""
                export_data.append(row)
        
        config = ExportConfig(
            export_type=ExportType.SCREENING_RESULTS,
            format=format,
            options={"screener_name": screener_name},
        )
        
        result = await self.export(ExportType.SCREENING_RESULTS, export_data, format, config)
        safe_name = screener_name.lower().replace(" ", "_")[:30]
        result.filename = f"screen_{safe_name}_{datetime.now(UTC).strftime('%Y%m%d')}.{format.value}"
        
        return result
    
    # ================================
    # Tax Report Export
    # ================================
    
    async def export_tax_report(
        self,
        year: int,
        transactions: list[dict],
        format: ExportFormat = ExportFormat.CSV,
    ) -> ExportResult:
        """
        Export tax report with realized gains/losses.
        
        Columns: Date Acquired, Date Sold, Ticker, Shares, Cost Basis,
                 Proceeds, Gain/Loss, Term (Short/Long)
        """
        export_data = []
        
        total_short_term = 0
        total_long_term = 0
        
        for tx in transactions:
            gain_loss = tx.get("proceeds", 0) - tx.get("cost_basis", 0)
            is_long_term = tx.get("is_long_term", False)
            
            if is_long_term:
                total_long_term += gain_loss
            else:
                total_short_term += gain_loss
            
            export_data.append({
                "Date Acquired": self._format_date(tx.get("acquired_date")),
                "Date Sold": self._format_date(tx.get("sold_date")),
                "Ticker": tx.get("ticker", ""),
                "Shares": self._format_number(tx.get("shares", 0), 4),
                "Cost Basis": self._format_currency(tx.get("cost_basis", 0)),
                "Proceeds": self._format_currency(tx.get("proceeds", 0)),
                "Gain/Loss": self._format_currency(gain_loss),
                "Term": "Long-term" if is_long_term else "Short-term",
            })
        
        # Add summary
        export_data.append({})  # Empty row
        export_data.append({
            "Date Acquired": "SUMMARY",
            "Date Sold": "",
            "Ticker": "",
            "Shares": "",
            "Cost Basis": "",
            "Proceeds": "",
            "Gain/Loss": "",
            "Term": "",
        })
        export_data.append({
            "Date Acquired": "Short-term Gains/Losses:",
            "Date Sold": "",
            "Ticker": "",
            "Shares": "",
            "Cost Basis": "",
            "Proceeds": "",
            "Gain/Loss": self._format_currency(total_short_term),
            "Term": "",
        })
        export_data.append({
            "Date Acquired": "Long-term Gains/Losses:",
            "Date Sold": "",
            "Ticker": "",
            "Shares": "",
            "Cost Basis": "",
            "Proceeds": "",
            "Gain/Loss": self._format_currency(total_long_term),
            "Term": "",
        })
        export_data.append({
            "Date Acquired": "Total Gains/Losses:",
            "Date Sold": "",
            "Ticker": "",
            "Shares": "",
            "Cost Basis": "",
            "Proceeds": "",
            "Gain/Loss": self._format_currency(total_short_term + total_long_term),
            "Term": "",
        })
        
        config = ExportConfig(
            export_type=ExportType.TAX_REPORT,
            format=format,
            options={"year": year},
        )
        
        result = await self.export(ExportType.TAX_REPORT, export_data, format, config)
        result.filename = f"tax_report_{year}.{format.value}"
        
        return result
    
    # ================================
    # Trade Journal Export
    # ================================
    
    async def export_trade_journal(
        self,
        trades: list[dict],
        format: ExportFormat = ExportFormat.CSV,
    ) -> ExportResult:
        """
        Export trade journal with decision tracking.
        
        Columns: Date, Ticker, Action, Shares, Price, Thesis, Outcome, Notes
        """
        export_data = []
        
        for trade in trades:
            export_data.append({
                "Date": self._format_date(trade.get("date")),
                "Ticker": trade.get("ticker", ""),
                "Action": trade.get("action", ""),  # BUY/SELL
                "Shares": self._format_number(trade.get("shares", 0), 4),
                "Price": self._format_currency(trade.get("price", 0)),
                "Total Value": self._format_currency(trade.get("total_value", 0)),
                "Thesis": trade.get("thesis", ""),
                "Outcome": trade.get("outcome", ""),
                "Notes": trade.get("notes", ""),
            })
        
        config = ExportConfig(
            export_type=ExportType.TRADE_JOURNAL,
            format=format,
        )
        
        return await self.export(ExportType.TRADE_JOURNAL, export_data, format, config)
    
    # ================================
    # Stock Analysis Export
    # ================================
    
    async def export_stock_analysis(
        self,
        ticker: str,
        analysis: dict,
        format: ExportFormat = ExportFormat.JSON,
    ) -> ExportResult:
        """
        Export comprehensive stock analysis.
        
        Best exported as JSON due to nested structure.
        """
        export_data = {
            "ticker": ticker,
            "generated_at": datetime.now(UTC).isoformat(),
            "analysis": analysis,
        }
        
        config = ExportConfig(
            export_type=ExportType.STOCK_ANALYSIS,
            format=format,
        )
        
        result = await self.export(ExportType.STOCK_ANALYSIS, [export_data], format, config)
        result.filename = f"{ticker}_analysis_{datetime.now(UTC).strftime('%Y%m%d')}.{format.value}"
        
        return result
    
    # ================================
    # Format Exporters
    # ================================
    
    def _export_csv(self, data: list[dict], config: ExportConfig) -> bytes:
        """Export data as CSV."""
        if not data:
            return b""
        
        output = io.StringIO()
        
        # Get headers from first row
        headers = list(data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=headers)
        
        if config.include_headers:
            writer.writeheader()
        
        writer.writerows(data)
        
        return output.getvalue().encode("utf-8")
    
    def _export_json(self, data: list[dict], config: ExportConfig) -> bytes:
        """Export data as JSON."""
        return json.dumps(data, indent=2, default=str).encode("utf-8")
    
    # ================================
    # Formatters
    # ================================
    
    def _format_number(self, value: float | None, decimals: int = 2) -> str:
        """Format a number with specified decimal places."""
        if value is None:
            return ""
        return f"{value:.{decimals}f}"
    
    def _format_currency(self, value: float | None) -> str:
        """Format a value as currency."""
        if value is None:
            return ""
        return f"${value:,.2f}"
    
    def _format_percent(self, value: float | None) -> str:
        """Format a value as percentage."""
        if value is None:
            return ""
        return f"{value:.2f}%"
    
    def _format_date(self, value: str | datetime | None) -> str:
        """Format a date."""
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        return value.strftime("%Y-%m-%d")


# ============================================
# Factory Function
# ============================================


def get_export_service() -> ExportService:
    """Get ExportService instance."""
    return ExportService()

