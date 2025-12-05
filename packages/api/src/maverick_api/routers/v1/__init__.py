"""
Version 1 API routes.

All endpoints are prefixed with /api/v1
"""

from fastapi import APIRouter

from maverick_api.routers.v1 import auth, users, stocks, technical, portfolio, screening, sse

router = APIRouter()

# Include all v1 routers
router.include_router(auth.router, tags=["Authentication"])
router.include_router(users.router, tags=["Users"])
router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
router.include_router(technical.router, prefix="/technical", tags=["Technical Analysis"])
router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
router.include_router(screening.router, prefix="/screening", tags=["Screening"])
router.include_router(sse.router, prefix="/sse", tags=["Real-time"])

__all__ = ["router"]

