from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict

# In-memory store (swap for Redis in prod)
# { api_key: { "count": int, "window_start": float } }
_rate_store: dict = defaultdict(lambda: {"count": 0, "window_start": time.time()})

# Requests per minute per plan
PLAN_LIMITS = {
    "free":       10,
    "pro":        60,
    "enterprise": 300,
}

UNPROTECTED = {"/", "/health", "/docs", "/redoc", "/openapi.json"}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNPROTECTED:
            return await call_next(request)

        api_key = (
            request.headers.get("x-api-key") or
            request.query_params.get("api_key")
        )
        if not api_key:
            return await call_next(request)

        plan = getattr(request.state, "plan", "free")
        rpm  = PLAN_LIMITS.get(plan, 10)

        store = _rate_store[api_key]
        now   = time.time()

        # Reset window every 60 seconds
        if now - store["window_start"] > 60:
            store["count"] = 0
            store["window_start"] = now

        if store["count"] >= rpm:
            retry_after = int(60 - (now - store["window_start"]))
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(store["window_start"] + 60))
                },
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"You've hit the {plan} plan limit of {rpm} req/min.",
                    "retry_after_seconds": retry_after,
                    "upgrade": "https://studyapi.dev/pricing"
                }
            )

        store["count"] += 1
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"]     = str(rpm)
        response.headers["X-RateLimit-Remaining"] = str(rpm - store["count"])
        return response
