"""
Mock database layer.
In production: swap with SQLite (sqlite-aio) or Postgres (asyncpg).
Schema:

  api_keys table:
    key TEXT PRIMARY KEY,
    user_id TEXT,
    plan TEXT,          -- free | pro | enterprise
    status TEXT,        -- active | suspended | expired
    calls_used INT,
    calls_limit INT,
    created_at TIMESTAMP

  usage_logs table:
    id SERIAL,
    api_key TEXT,
    endpoint TEXT,
    video_id TEXT,
    tokens_used INT,
    latency_ms INT,
    timestamp TIMESTAMP
"""

# ----- Mock in-memory data (replace with real DB calls) -----

_KEYS = {
    "sk_free_demo123": {
        "user_id": "user_001",
        "plan": "free",
        "status": "active",
        "calls_used": 47,
        "calls_limit": 100,       # 100 calls/month free
    },
    "sk_pro_demo456": {
        "user_id": "user_002",
        "plan": "pro",
        "status": "active",
        "calls_used": 1203,
        "calls_limit": 5000,      # 5000 calls/month pro
    },
    "sk_ent_demo789": {
        "user_id": "user_003",
        "plan": "enterprise",
        "status": "active",
        "calls_used": 28000,
        "calls_limit": 999999,
    },
}

_USAGE_LOG = []

async def get_api_key_record(api_key: str) -> dict | None:
    return _KEYS.get(api_key)

async def increment_usage(api_key: str, endpoint: str, video_id: str = "", tokens: int = 0, latency_ms: int = 0):
    if api_key in _KEYS:
        _KEYS[api_key]["calls_used"] += 1
    _USAGE_LOG.append({
        "api_key": api_key,
        "endpoint": endpoint,
        "video_id": video_id,
        "tokens_used": tokens,
        "latency_ms": latency_ms,
    })

async def get_usage_stats(api_key: str) -> dict:
    record = _KEYS.get(api_key, {})
    logs   = [l for l in _USAGE_LOG if l["api_key"] == api_key]
    endpoint_counts = {}
    for l in logs:
        endpoint_counts[l["endpoint"]] = endpoint_counts.get(l["endpoint"], 0) + 1
    return {
        "plan":         record.get("plan", "free"),
        "calls_used":   record.get("calls_used", 0),
        "calls_limit":  record.get("calls_limit", 100),
        "calls_remaining": record.get("calls_limit", 100) - record.get("calls_used", 0),
        "endpoint_breakdown": endpoint_counts,
        "total_tokens_used": sum(l["tokens_used"] for l in logs),
    }
