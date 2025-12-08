"""
Data Export API Endpoints.

Provides endpoints for exporting data in various formats.
"""

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import Field

from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_schemas.auth import AuthenticatedUser
from maverick_services import (
    ExportService,
    ExportFormat,
    get_export_service,
)
from maverick_api.dependencies import get_current_user, get_request_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])


# ============================================
# Request Models
# ============================================


class ExportPortfolioRequest(MaverickBaseModel):
    """Request to export portfolio."""
    
    positions: list[dict] = Field(description="Portfolio positions to export")
    include_summary: bool = Field(default=True)


class ExportWatchlistRequest(MaverickBaseModel):
    """Request to export watchlist."""
    
    watchlist_name: str
    items: list[dict] = Field(description="Watchlist items to export")


class ExportScreeningRequest(MaverickBaseModel):
    """Request to export screening results."""
    
    screener_name: str
    results: list[dict] = Field(description="Screening results to export")


class ExportTaxReportRequest(MaverickBaseModel):
    """Request to export tax report."""
    
    year: int
    transactions: list[dict] = Field(description="Realized transactions")


class ExportTradeJournalRequest(MaverickBaseModel):
    """Request to export trade journal."""
    
    trades: list[dict] = Field(description="Trade entries")


class ExportAnalysisRequest(MaverickBaseModel):
    """Request to export stock analysis."""
    
    ticker: str
    analysis: dict = Field(description="Analysis data")


# ============================================
# Dependencies
# ============================================


def get_export_service_dep() -> ExportService:
    """Get export service instance."""
    return get_export_service()


# ============================================
# Export Endpoints
# ============================================


@router.post("/portfolio")
async def export_portfolio(
    data: ExportPortfolioRequest,
    format: str = Query(default="csv", description="Export format (csv, json)"),
    user: AuthenticatedUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service_dep),
):
    """
    Export portfolio positions.
    
    Returns a downloadable file with portfolio data.
    """
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    result = await export_service.export_portfolio(
        positions=data.positions,
        format=export_format,
        include_summary=data.include_summary,
    )
    
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={result.filename}",
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/watchlist")
async def export_watchlist(
    data: ExportWatchlistRequest,
    format: str = Query(default="csv"),
    user: AuthenticatedUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service_dep),
):
    """Export watchlist items."""
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    result = await export_service.export_watchlist(
        watchlist_name=data.watchlist_name,
        items=data.items,
        format=export_format,
    )
    
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={result.filename}",
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/screening-results")
async def export_screening_results(
    data: ExportScreeningRequest,
    format: str = Query(default="csv"),
    user: AuthenticatedUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service_dep),
):
    """Export screening results."""
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    result = await export_service.export_screening_results(
        screener_name=data.screener_name,
        results=data.results,
        format=export_format,
    )
    
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={result.filename}",
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/tax-report")
async def export_tax_report(
    data: ExportTaxReportRequest,
    format: str = Query(default="csv"),
    user: AuthenticatedUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service_dep),
):
    """
    Export tax report with realized gains/losses.
    
    Includes summary of short-term and long-term capital gains.
    """
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    result = await export_service.export_tax_report(
        year=data.year,
        transactions=data.transactions,
        format=export_format,
    )
    
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={result.filename}",
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/trade-journal")
async def export_trade_journal(
    data: ExportTradeJournalRequest,
    format: str = Query(default="csv"),
    user: AuthenticatedUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service_dep),
):
    """Export trade journal with decision tracking."""
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    result = await export_service.export_trade_journal(
        trades=data.trades,
        format=export_format,
    )
    
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={result.filename}",
            "X-Row-Count": str(result.row_count),
        },
    )


@router.post("/stock-analysis")
async def export_stock_analysis(
    data: ExportAnalysisRequest,
    format: str = Query(default="json"),
    user: AuthenticatedUser = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service_dep),
):
    """
    Export comprehensive stock analysis.
    
    Best exported as JSON due to nested structure.
    """
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
    
    result = await export_service.export_stock_analysis(
        ticker=data.ticker,
        analysis=data.analysis,
        format=export_format,
    )
    
    return Response(
        content=result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={result.filename}",
            "X-Row-Count": str(result.row_count),
        },
    )


# ============================================
# Format Info
# ============================================


@router.get("/formats")
async def get_export_formats(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get available export formats."""
    return APIResponse(
        data={
            "formats": [
                {"value": "csv", "label": "CSV (Spreadsheet)", "extension": ".csv"},
                {"value": "json", "label": "JSON (Data)", "extension": ".json"},
            ],
            "export_types": [
                {"value": "portfolio", "label": "Portfolio", "formats": ["csv", "json"]},
                {"value": "watchlist", "label": "Watchlist", "formats": ["csv", "json"]},
                {"value": "screening_results", "label": "Screening Results", "formats": ["csv", "json"]},
                {"value": "tax_report", "label": "Tax Report", "formats": ["csv"]},
                {"value": "trade_journal", "label": "Trade Journal", "formats": ["csv", "json"]},
                {"value": "stock_analysis", "label": "Stock Analysis", "formats": ["json"]},
            ],
        },
        meta=ResponseMeta(request_id=request_id, timestamp=datetime.now(UTC)),
    )

