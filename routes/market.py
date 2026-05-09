"""Market data routes - indices, movers, search"""

from fastapi import APIRouter, Query, HTTPException
from services.stockdata import StockDataService

router = APIRouter(prefix="/market", tags=["Market"])

@router.get("/indices")
async def get_all_indices():
    """Get all major indices (Nifty50, Sensex, S&P500, NASDAQ, etc.)"""
    data = StockDataService.get_all_indices()
    if not data:
        raise HTTPException(status_code=500, detail="Could not fetch index data")
    return {
        "success": True,
        "count": len(data),
        "data": data
    }

@router.get("/indices/{index}")
async def get_index(index: str):
    """Get specific index data"""
    data = StockDataService.get_index_data(index)
    if not data:
        raise HTTPException(status_code=404, detail=f"Index {index} not found")
    return {"success": True, "data": data}

@router.get("/movers")
async def get_movers(
    market: str = Query("india", description="Market: india or us"),
    limit: int = Query(10, ge=1, le=50, description="Number of top movers to return")
):
    """Get top gainers and losers for the day"""
    data = StockDataService.get_top_gainers_losers(market, limit)
    return {
        "success": True,
        "market": market,
        "data": data
    }

@router.get("/search")
async def search_stocks(q: str = Query(..., description="Stock name or symbol to search")):
    """Search stocks by name or symbol"""
    if len(q) < 1:
        raise HTTPException(status_code=400, detail="Query must be at least 1 character")
    
    data = StockDataService.search_stocks(q)
    if not data:
        raise HTTPException(status_code=404, detail=f"No stocks found matching '{q}'")
    
    return {
        "success": True,
        "query": q,
        "count": len(data),
        "data": data
    }
