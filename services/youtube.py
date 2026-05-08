"""
Transcript Service
Primary: RapidAPI youtube138 (works on cloud servers)
Fallback: youtube-transcript-api (works locally)
"""

import re
import os
import httpx
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "8bc5ce880cmsh84404c9d75b1223p1205b3jsnf9e7285c3c55")


def extract_video_id(url_or_id: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$"
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


async def fetch_transcript(video_id: str, language: str = "en") -> dict:
    # Try RapidAPI first (works on cloud), fall back to direct
    if RAPIDAPI_KEY:
        try:
            return await _fetch_via_rapidapi(video_id, language)
        except Exception:
            pass

    # Fallback: direct fetch (works locally)
    try:
        segments = _fetch_direct(video_id, language)
        return _build_response(video_id, segments, language)
    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise ValueError(f"No transcript found for video {video_id}.")
    except Exception as e:
        raise ValueError(f"Failed to fetch transcript: {str(e)}")


async def _fetch_via_rapidapi(video_id: str, language: str) -> dict:
    url = "https://youtube-transcript3.p.rapidapi.com/api/transcript"
    headers = {
        "x-rapidapi-host": "youtube-transcript3.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, headers=headers, params={"videoId": video_id, "lang": language})
        resp.raise_for_status()
        data = resp.json()

    # Response: { transcript: [ {text, start, duration} ] }
    raw = data.get("transcript") or data.get("segments") or []
    if not raw:
        raise ValueError("Empty transcript from RapidAPI")

    segments = [
        {
            "text": item.get("text", ""),
            "start": float(item.get("start", 0)),
            "duration": float(item.get("duration", 0)),
        }
        for item in raw
    ]
    return _build_response(video_id, segments, language)


def _fetch_direct(video_id: str, language: str) -> list[dict]:
    languages = [language] if language == "en" else [language, "en"]
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    else:
        api = YouTubeTranscriptApi()
        raw = api.fetch(video_id, languages=languages)
    return [
        {
            "text": s.get("text", "") if isinstance(s, dict) else getattr(s, "text", ""),
            "start": s.get("start", 0) if isinstance(s, dict) else getattr(s, "start", 0),
            "duration": s.get("duration", 0) if isinstance(s, dict) else getattr(s, "duration", 0),
        }
        for s in raw
    ]


def _build_response(video_id: str, segments: list[dict], language: str) -> dict:
    full_text = " ".join(s["text"] for s in segments)
    duration = segments[-1]["start"] + segments[-1].get("duration", 0) if segments else 0
    formatted = [
        {
            "start": round(s["start"], 2),
            "duration": round(s.get("duration", 0), 2),
            "text": s["text"].strip(),
            "timestamp": _seconds_to_timestamp(s["start"]),
        }
        for s in segments
    ]
    return {
        "video_id": video_id,
        "text": full_text,
        "segments": formatted,
        "duration_seconds": round(duration),
        "duration_human": _seconds_to_timestamp(duration),
        "language": language,
        "word_count": len(full_text.split()),
        "is_generated": False,
    }


def _seconds_to_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"