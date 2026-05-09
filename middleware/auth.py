from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os

UNPROTECTED = {"/", "/health", "/docs", "/redoc", "/openapi.json"}

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in UNPROTECTED or request.url.path.startswith("/docs"):
            return await call_next(request)

        # For now, allow all requests to pass through
        # Add authentication later if needed
        return await call_next(request)
