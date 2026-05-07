from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel, Field
from services.youtube import fetch_transcript, extract_video_id
from models.db import increment_usage
import time

router = APIRouter()


class TranscriptRequest(BaseModel):
    video_url: str = Field(..., description="YouTube URL or video ID", example="https://youtube.com/watch?v=dQw4w9WgXcQ")
    language:  str = Field("en", description="Language code for transcript")
    include_segments: bool = Field(True, description="Include timestamped segments in response")


@router.post("/transcript", summary="Fetch video transcript with timestamps")
async def get_transcript(body: TranscriptRequest, request: Request):
    """
    Fetch the full transcript of a YouTube video with timestamps.

    **Free plan**: 100 calls/month
    **Pro plan**: 5,000 calls/month
    """
    t0 = time.time()
    try:
        video_id = extract_video_id(body.video_url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        data = await fetch_transcript(video_id, language=body.language)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not body.include_segments:
        data.pop("segments", None)

    latency = int((time.time() - t0) * 1000)
    await increment_usage(
        api_key=getattr(request.state, "api_key", "anon"),
        endpoint="transcript",
        video_id=video_id,
        latency_ms=latency
    )

    return {
        "success": True,
        "data": data,
        "meta": {
            "latency_ms": latency,
            "plan": getattr(request.state, "plan", "free"),
            "calls_remaining": getattr(request.state, "calls_limit", 100) - getattr(request.state, "calls_used", 0) - 1
        }
    }
