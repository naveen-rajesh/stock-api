# Stock Market API

Real-time stock prices, historical data, and market indices using **yfinance** (completely free, no API keys needed).

## Features

✅ **Real-time stock prices** with change %, volume, market cap, P/E ratio  
✅ **Historical OHLCV data** for any date range  
✅ **Detailed fundamentals** (P/E, EPS, debt-to-equity, dividend yield, etc.)  
✅ **Major indices tracking** (Nifty50, Sensex, S&P500, NASDAQ, DAX, FTSE)  
✅ **Top gainers/losers** for the day  
✅ **Stock search** by name or symbol  
✅ **Pre-loaded Indian stocks** (TCS, Reliance, Infosys, HDFC, etc.)  
✅ **No authentication required** • **No rate limits** • **Free forever**

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger UI.

---

## API Endpoints

### Stock Data

#### `GET /stock/{symbol}`
Get current price and basic info.

**Example:**
```bash
curl http://localhost:8000/stock/TCS.NS
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "TCS.NS",
    "name": "Tata Consultancy Services Limited",
    "current_price": 2394.4,
    "change": -7.0,
    "change_percent": -0.29,
    "volume": 3791556,
    "market_cap": 8663148265472,
    "pe_ratio": 17.61,
    "52_week_high": 3630.5,
    "52_week_low": 2346.2,
    "dividend_yield": 5.18,
    "beta": 0.289
  }
}
```

---

#### `GET /stock/{symbol}/history?days=30`
Get OHLCV historical data.

**Parameters:**
- `days` (int, 1-365): Number of historical days. Default: 30.

**Example:**
```bash
curl "http://localhost:8000/stock/RELIANCE/history?days=7"
```

**Response:**
```json
{
  "success": true,
  "symbol": "RELIANCE",
  "days": 7,
  "count": 5,
  "data": [
    {
      "date": "2026-05-04",
      "open": 1433.4,
      "high": 1467.4,
      "low": 1433.4,
      "close": 1463.1,
      "volume": 24035700
    }
  ]
}
```

---

#### `GET /stock/{symbol}/info`
Get detailed fundamentals (P/E, market cap, EPS, sector, industry, debt ratios, etc.).

**Example:**
```bash
curl http://localhost:8000/stock/INFY/info
```

---

### Market Data

#### `GET /market/indices`
Get all major indices.

**Example:**
```bash
curl http://localhost:8000/market/indices
```

**Returns data for:** Nifty50, Sensex, S&P500, NASDAQ, DAX, FTSE

---

#### `GET /market/indices/{index}`
Get specific index.

**Example:**
```bash
curl http://localhost:8000/market/indices/NIFTY50
```

---

#### `GET /market/movers?market=india&limit=10`
Get top gainers and losers for the day.

**Parameters:**
- `market` (string): `india` or `us`. Default: `india`.
- `limit` (int, 1-50): Number of top movers. Default: 10.

**Example:**
```bash
curl "http://localhost:8000/market/movers?market=india&limit=5"
```

**Response:**
```json
{
  "success": true,
  "market": "india",
  "data": {
    "gainers": [
      {
        "symbol": "ASIANPAINT.NS",
        "name": "Asian Paints Limited",
        "price": 2599.9,
        "change_percent": 2.74,
        "change": 69.3
      }
    ],
    "losers": [
      {
        "symbol": "HDFCBANK.NS",
        "name": "HDFC Bank Limited",
        "price": 780.85,
        "change_percent": -1.91,
        "change": -15.2
      }
    ]
  }
}
```

---

#### `GET /market/search?q=reliance`
Search stocks by name or symbol.

**Example:**
```bash
curl "http://localhost:8000/market/search?q=infosys"
```

**Response:**
```json
{
  "success": true,
  "query": "infosys",
  "count": 1,
  "data": [
    {
      "name": "INFY",
      "symbol": "INFY.NS",
      "exchange": "NSE"
    }
  ]
}
```

---

## Supported Stocks

### **Global Markets Supported** 🌍

You can fetch data for **ANY stock from any global market** using yfinance. Here are the major exchanges:

| Market | Format | Example |
|--------|--------|---------|
| **India (NSE)** | `SYMBOL.NS` or just `SYMBOL` | `TCS.NS`, `INFY`, `RELIANCE` |
| **USA (NASDAQ/NYSE)** | `SYMBOL` | `AAPL`, `GOOGL`, `MSFT`, `TSLA` |
| **Germany (Xetra)** | `SYMBOL.DE` | `BMW.DE`, `SAP.DE` |
| **Netherlands (Euronext)** | `SYMBOL.AS` | `ASML.AS`, `PHIA.AS` |
| **UK (LSE)** | `SYMBOL.L` | `SHEL.L`, `BP.L` |
| **Canada (TSX)** | `SYMBOL.TO` | `RY.TO`, `TD.TO` |
| **Japan (Tokyo)** | `SYMBOL.T` | `7203.T`, `6758.T` |
| **Hong Kong** | `SYMBOL.HK` | `0700.HK`, `0388.HK` |
| **Brazil (B3)** | `SYMBOL.SA` | `VALE3.SA` |
| **Australia (ASX)** | `SYMBOL.AX` | `BHP.AX` |

### Pre-loaded Indian Stocks

For convenience, these Indian stocks are pre-loaded (no exchange suffix needed):

---

## Supported Indices

| Name | Symbol |
|------|--------|
| Nifty 50 | NIFTY50 |
| BSE Sensex | SENSEX |
| S&P 500 | SP500 |
| NASDAQ | NASDAQ |
| DAX | DAX |
| FTSE 100 | FTSE |

---

## Example Usage

### Python

```python
import requests

# Get current price - India
response = requests.get("http://localhost:8000/stock/TCS.NS")
print(response.json())

# Get current price - USA
response = requests.get("http://localhost:8000/stock/AAPL")
print(response.json())

# Get current price - Germany
response = requests.get("http://localhost:8000/stock/BMW.DE")
print(response.json())

# Get 30-day history
response = requests.get("http://localhost:8000/stock/AAPL/history?days=30")
print(response.json())

# Get top gainers in Indian market
response = requests.get("http://localhost:8000/market/movers?market=india&limit=10")
print(response.json())

# Get top gainers in US market
response = requests.get("http://localhost:8000/market/movers?market=us&limit=10")
print(response.json())

# Search stocks
response = requests.get("http://localhost:8000/market/search?q=infosys")
print(response.json())
```

### JavaScript/Node.js

```javascript
// Get Apple stock
fetch('http://localhost:8000/stock/AAPL')
  .then(res => res.json())
  .then(data => console.log(data))

// Get BMW stock (Germany)
fetch('http://localhost:8000/stock/BMW.DE')
  .then(res => res.json())
  .then(data => console.log(data))

// Get Nifty50 index
fetch('http://localhost:8000/market/indices/NIFTY50')
  .then(res => res.json())
  .then(data => console.log(data))

// Get NASDAQ index
fetch('http://localhost:8000/market/indices/NASDAQ')
  .then(res => res.json())
  .then(data => console.log(data))
```

### Curl Examples

```bash
# Apple (USA)
curl http://localhost:8000/stock/AAPL

# Infosys (India)
curl http://localhost:8000/stock/INFY

# BMW (Germany)
curl http://localhost:8000/stock/BMW.DE

# ASML (Netherlands)
curl http://localhost:8000/stock/ASML.AS

# Tesla with 30-day history
curl "http://localhost:8000/stock/TSLA/history?days=30"

# Top gainers in US market
curl "http://localhost:8000/market/movers?market=us&limit=5"
```

---

## Data Source

This API uses **yfinance** which fetches data from Yahoo Finance in real-time.

- **No API keys required**
- **No rate limiting**
- **Completely free**
- **Global stock coverage**

---

## Documentation

- **Swagger UI**: Visit `/docs` after starting the server
- **ReDoc**: Visit `/redoc` after starting the server

---

## Deployment

The API is ready to deploy on any platform that supports Python/FastAPI:
- **Fly.io** (recommended for this region)
- **Render.com**
- **Heroku**
- **AWS, GCP, Azure**
- **Docker** (included: Dockerfile)

No environment variables needed—this API works out of the box!

---

## Error Handling

All errors return a standard JSON response:

```json
{
  "detail": "Stock symbol not found"
}
```

---

## License

MIT - Free to use and modify.

---

## Support

For issues or feature requests, create an issue in the repository.
}
```

Errors:
```json
{
  "error": "rate_limit_exceeded",
  "message": "You've hit the free plan limit of 10 req/min.",
  "retry_after_seconds": 43,
  "upgrade": "https://studyapi.dev/pricing"
}
```

---

## Deploy to Railway

```bash
railway login
railway init
railway up
railway domain
```

Set env vars from `.env.example` in the Railway dashboard.

---

## Architecture

```
Client
  │
  ▼
FastAPI App (main.py)
  ├── APIKeyMiddleware   → validates key, attaches plan to request.state
  ├── RateLimitMiddleware → per-key per-minute throttle (swap for Redis)
  │
  ├── /v1/transcript  → services/youtube.py (youtube-transcript-api)
  └── /v1/summary     → services/llm.py (local extractive summaries)
```

---

## Monetization Checklist

- [ ] Deploy to Railway / Fly.io / Render
- [ ] Add real DB (SQLite → Postgres)
- [ ] Add Stripe webhook for key provisioning
- [ ] List on RapidAPI
- [ ] Build a simple landing page (studyapi.dev)
- [ ] Post on IndieHackers, Product Hunt, Twitter/X
- [ ] Reach out to EdTech SaaS founders on LinkedIn
