"""Stock data routes - no /v1 prefix"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from services.stockdata import StockDataService

router = APIRouter(prefix="/stock", tags=["Stock"])

@router.get("/{symbol}")
async def get_stock(symbol: str):
    """Get current price and basic info for a stock"""
    data = StockDataService.get_stock_price(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    return {"success": True, "data": data}

@router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of history")
):
    """Get OHLCV historical data for a stock"""
    data = StockDataService.get_stock_history(symbol, days)
    if not data:
        raise HTTPException(status_code=404, detail=f"Could not fetch history for {symbol}")
    return {
        "success": True,
        "symbol": symbol,
        "days": days,
        "count": len(data),
        "data": data
    }

@router.get("/{symbol}/info")
async def get_stock_info(symbol: str):
    """Get detailed stock information (P/E, market cap, EPS, etc.)"""
    data = StockDataService.get_stock_info(symbol)
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    return {"success": True, "data": data}
