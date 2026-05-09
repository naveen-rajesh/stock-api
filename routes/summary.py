from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from services.youtube import fetch_transcript, extract_video_id
from services.llm import generate_summary
from models.db import increment_usage
import time

router = APIRouter()


class SummaryRequest(BaseModel):
    video_url: str  = Field(..., example="https://youtube.com/watch?v=dQw4w9WgXcQ")
    style:     str  = Field("concise", description="concise | detailed | bullet | eli5")
    language:  str  = Field("en")
    transcript: str | None = Field(
        None,
        description="Optional transcript text. Leave empty to fetch from video_url.",
        example=None,
    )


@router.post("/summary", summary="Summarize a YouTube video")
async def summarize(body: SummaryRequest, request: Request):
    """
    Generate an AI summary of a YouTube video.

    **Styles:**
    - `concise` — 3-5 sentence overview
    - `detailed` — section-by-section breakdown
    - `bullet` — key takeaways as bullet points
    - `eli5` — explain like I'm 5

    Also returns: main topics, key terms with definitions, timestamps.
    """
    t0 = time.time()

    provided_transcript = _usable_transcript(body.transcript)

    # Use provided transcript or fetch from YouTube.
    # Swagger's default placeholder is "string"; treat it as empty input.
    if provided_transcript:
        transcript_text = provided_transcript
        video_id = "custom"
    else:
        try:
            video_id = extract_video_id(body.video_url)
            data = await fetch_transcript(body.video_url, language=body.language)
            transcript_text = data["text"]
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    if len(transcript_text.strip()) < 100:
        raise HTTPException(status_code=422, detail="Transcript too short to summarize.")

    result = await generate_summary(transcript_text, style=body.style, language=body.language)

    latency = int((time.time() - t0) * 1000)
    await increment_usage(
        api_key=getattr(request.state, "api_key", "anon"),
        endpoint="summary",
        video_id=video_id,
        tokens=result.pop("tokens_used", 0),
        latency_ms=latency
    )

    return {
        "success": True,
        "data": result,
        "meta": {
            "style": body.style,
            "video_id": video_id,
            "latency_ms": latency,
            "plan": getattr(request.state, "plan", "free"),
        }
    }


def _usable_transcript(transcript: str | None) -> str | None:
    if transcript is None:
        return None

    cleaned = transcript.strip()
    if not cleaned or cleaned.lower() == "string":
        return None

    return cleaned
