from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from routes import transcript, summary
from middleware.auth import APIKeyMiddleware
from middleware.ratelimit import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 StudyAPI started")
    yield
    print("🛑 StudyAPI shutting down")

app = FastAPI(
    title="StudyAPI",
    description="Turn any YouTube video into transcripts and summaries instantly.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)

app.include_router(transcript.router, prefix="/v1", tags=["Transcript"])
app.include_router(summary.router,    prefix="/v1", tags=["Summary"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "StudyAPI",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": ["/v1/transcript", "/v1/summary"]
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "timestamp": time.time()}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "message": str(exc)})
