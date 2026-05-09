from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from dotenv import load_dotenv

load_dotenv()

from routes import stock, market
from middleware.auth import APIKeyMiddleware
from middleware.ratelimit import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Stock Market API started")
    yield
    print("🛑 Stock Market API shutting down")

app = FastAPI(
    title="Stock Market API",
    description="Real-time stock prices, historical data, and market indices. Free, no API keys needed.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)

app.include_router(stock.router, tags=["Stock"])
app.include_router(market.router, tags=["Market"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Stock Market API",
        "version": "2.0.0",
        "status": "operational",
        "description": "Real-time stock data powered by yfinance (free, no API keys)",
        "docs": "/docs",
        "endpoints": {
            "stock": {
                "GET /stock/{symbol}": "Current price and basic info",
                "GET /stock/{symbol}/history": "OHLCV historical data",
                "GET /stock/{symbol}/info": "Detailed fundamentals (P/E, market cap, EPS)"
            },
            "market": {
                "GET /market/indices": "All major indices",
                "GET /market/indices/{index}": "Specific index data",
                "GET /market/movers": "Top gainers/losers",
                "GET /market/search": "Search stocks by name"
            }
        }
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "timestamp": time.time()}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "message": str(exc)})
