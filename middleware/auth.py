from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from models.db import get_api_key_record
import os

UNPROTECTED = {"/", "/health", "/docs", "/redoc", "/openapi.json"}
RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET")

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNPROTECTED or request.url.path.startswith("/docs"):
            return await call_next(request)

        if RAPIDAPI_PROXY_SECRET:
            proxy_secret = (
                request.headers.get("x-rapidapi-proxy-secret") or
                request.headers.get("x-mashape-proxy-secret")
            )
            if proxy_secret != RAPIDAPI_PROXY_SECRET:
                return JSONResponse(status_code=403, content={
                    "error": "rapidapi_proxy_required",
                    "message": "Requests must come through the RapidAPI proxy."
                })

        api_key = (
            request.headers.get("x-api-key") or
            request.query_params.get("api_key")
        )

        # If no API key provided, use defaults for testing
        if not api_key:
            request.state.api_key    = "test_key"
            request.state.user_id    = request.headers.get("x-rapidapi-user", "test_user")
            request.state.plan       = request.headers.get("x-rapidapi-subscription", "free").lower()
            request.state.calls_used = 0
            request.state.calls_limit = 100
            return await call_next(request)

        record = await get_api_key_record(api_key)
        if not record:
            return JSONResponse(status_code=401, content={
                "error": "invalid_api_key",
                "message": "API key not found or revoked."
            })

        if record["status"] != "active":
            return JSONResponse(status_code=403, content={
                "error": "key_suspended",
                "message": "Your API key has been suspended. Contact support."
            })

        # Attach key metadata to request state for downstream use
        request.state.api_key    = api_key
        request.state.user_id    = record["user_id"]
        request.state.plan       = record["plan"]          # free | pro | enterprise
        request.state.calls_used = record["calls_used"]
        request.state.calls_limit = record["calls_limit"]

        return await call_next(request)
