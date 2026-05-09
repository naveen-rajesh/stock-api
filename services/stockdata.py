"""Stock data service using yfinance - free, no API keys needed"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

class StockDataService:
    """Fetch stock data from Yahoo Finance"""
    
    # Popular indices to track
    INDICES = {
        "NIFTY50": "^NSEI",
        "SENSEX": "^BSESN",
        "SP500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DAX": "^GDAXI",
        "FTSE": "^FTSE"
    }
    
    # Indian stocks (NSE)
    INDIAN_STOCKS = {
        "TCS": "TCS.NS",
        "RELIANCE": "RELIANCE.NS",
        "INFY": "INFY.NS",
        "WIPRO": "WIPRO.NS",
        "BAJAJFINSV": "BAJAJFINSV.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "KOTAK": "KOTAK.NS",
        "LT": "LT.NS",
        "ASIANPAINT": "ASIANPAINT.NS"
    }
    
    @staticmethod
    def get_stock_price(symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price and basic info"""
        try:
            ticker = yf.Ticker(_normalize_symbol(symbol))
            data = ticker.info
            
            if not data:
                return None
            
            return {
                "symbol": symbol,
                "name": data.get("longName", ""),
                "current_price": data.get("currentPrice"),
                "change": data.get("regularMarketChange"),
                "change_percent": data.get("regularMarketChangePercent"),
                "volume": data.get("volume"),
                "market_cap": data.get("marketCap"),
                "pe_ratio": data.get("trailingPE"),
                "52_week_high": data.get("fiftyTwoWeekHigh"),
                "52_week_low": data.get("fiftyTwoWeekLow"),
                "avg_volume": data.get("averageVolume"),
                "dividend_yield": data.get("dividendYield"),
                "beta": data.get("beta"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    @staticmethod
    def get_stock_history(symbol: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get OHLCV data for specified days"""
        try:
            ticker = yf.Ticker(_normalize_symbol(symbol))
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return None
            
            result = []
            for index, row in df.iterrows():
                result.append({
                    "date": index.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
            
            return result
        except Exception as e:
            return None
    
    @staticmethod
    def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed stock information (fundamentals)"""
        try:
            ticker = yf.Ticker(_normalize_symbol(symbol))
            data = ticker.info
            
            if not data:
                return None
            
            return {
                "symbol": symbol,
                "name": data.get("longName", ""),
                "sector": data.get("sector", ""),
                "industry": data.get("industry", ""),
                "employees": data.get("fullTimeEmployees"),
                "website": data.get("website"),
                "market_cap": data.get("marketCap"),
                "pe_ratio": data.get("trailingPE"),
                "forward_pe": data.get("forwardPE"),
                "peg_ratio": data.get("pegRatio"),
                "price_to_book": data.get("priceToBook"),
                "eps": data.get("trailingEps"),
                "revenue": data.get("totalRevenue"),
                "net_income": data.get("netIncomeToCommon"),
                "debt_to_equity": data.get("debtToEquity"),
                "current_ratio": data.get("currentRatio"),
                "roe": data.get("returnOnEquity"),
                "dividend_yield": data.get("dividendYield"),
                "52_week_high": data.get("fiftyTwoWeekHigh"),
                "52_week_low": data.get("fiftyTwoWeekLow"),
                "200_day_average": data.get("twoHundredDayAverage"),
                "50_day_average": data.get("fiftyDayAverage")
            }
        except Exception as e:
            return None
    
    @staticmethod
    def get_index_data(index_name: str) -> Optional[Dict[str, Any]]:
        """Get current index data"""
        try:
            symbol = StockDataService.INDICES.get(index_name.upper())
            if not symbol:
                return None
            
            ticker = yf.Ticker(symbol)
            data = ticker.info
            
            if not data:
                return None
            
            return {
                "index": index_name,
                "symbol": symbol,
                "current_price": data.get("currentPrice"),
                "change": data.get("regularMarketChange"),
                "change_percent": data.get("regularMarketChangePercent"),
                "52_week_high": data.get("fiftyTwoWeekHigh"),
                "52_week_low": data.get("fiftyTwoWeekLow"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    @staticmethod
    def get_all_indices() -> Dict[str, Dict[str, Any]]:
        """Get data for all major indices"""
        result = {}
        for index_name in StockDataService.INDICES.keys():
            data = StockDataService.get_index_data(index_name)
            if data:
                result[index_name] = data
        return result
    
    @staticmethod
    def search_stocks(query: str) -> List[Dict[str, str]]:
        """Search for stocks by name (returns available Indian stocks matching query)"""
        query_lower = query.lower()
        results = []
        
        # Search in Indian stocks
        for name, symbol in StockDataService.INDIAN_STOCKS.items():
            if query_lower in name.lower():
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "exchange": "NSE"
                })
        
        return results
    
    @staticmethod
    def get_top_gainers_losers(market: str = "india", limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get top gainers and losers for the day"""
        try:
            result = {"gainers": [], "losers": []}
            
            if market.lower() == "india":
                stocks_to_check = list(StockDataService.INDIAN_STOCKS.values())
            else:
                # For US market, use popular tickers
                stocks_to_check = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT"]
            
            stock_data = []
            for stock in stocks_to_check:
                ticker = yf.Ticker(stock)
                info = ticker.info
                
                if info and "regularMarketChangePercent" in info:
                    stock_data.append({
                        "symbol": stock,
                        "name": info.get("longName", stock),
                        "price": info.get("currentPrice", 0),
                        "change_percent": info.get("regularMarketChangePercent", 0),
                        "change": info.get("regularMarketChange", 0)
                    })
            
            # Sort by change percent
            stock_data.sort(key=lambda x: x["change_percent"], reverse=True)
            
            result["gainers"] = stock_data[:limit]
            result["losers"] = stock_data[-limit:][::-1]
            
            return result
        except Exception as e:
            return {"gainers": [], "losers": []}


def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol to yfinance format"""
    symbol = symbol.upper().strip()
    
    # Check if it's an Indian stock
    if symbol in StockDataService.INDIAN_STOCKS:
        return StockDataService.INDIAN_STOCKS[symbol]
    
    # If it doesn't have an exchange code, return as-is
    # yfinance will handle US stocks, crypto, etc.
    if not ("." in symbol):
        return symbol
    
    return symbol
