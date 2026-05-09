"""
Transcript service.

Uses youtube-transcript-api directly, with optional proxy configuration for
cloud hosts such as Render where YouTube may block datacenter IPs.
"""

import asyncio
import os
import re
from typing import Dict

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig


def extract_video_id(url_or_id: str) -> str:
    """Accept a YouTube URL or raw 11-character video ID."""
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([0-9A-Za-z_-]{11})",
        r"^([0-9A-Za-z_-]{11})$",
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube URL or video ID")


def _build_proxy_config() -> GenericProxyConfig | None:
    proxy_url = os.getenv("YOUTUBE_PROXY_URL")
    http_proxy = os.getenv("YOUTUBE_HTTP_PROXY")
    https_proxy = os.getenv("YOUTUBE_HTTPS_PROXY")

    if proxy_url:
        return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
    if http_proxy or https_proxy:
        return GenericProxyConfig(http_url=http_proxy, https_url=https_proxy)
    return None


proxy_config = _build_proxy_config()
ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config) if proxy_config else YouTubeTranscriptApi()


async def fetch_transcript(video_url: str, language: str = "en") -> Dict:
    """
    Fetch a YouTube transcript.

    `video_url` may be a full YouTube URL or a raw video ID.
    """
    video_id = extract_video_id(video_url)
    languages = [language] if language == "en" else [language, "en"]

    try:
        transcript_data = await asyncio.to_thread(
            ytt_api.fetch,
            video_id,
            languages=languages,
        )
        segments = [_normalize_segment(item) for item in transcript_data]
        return _build_response(video_id, segments, language)
    except Exception as e:
        print("TRANSCRIPT FETCH ERROR:", str(e))
        raise ValueError(f"Failed to fetch transcript: {str(e)}")


def _normalize_segment(item) -> dict:
    if isinstance(item, dict):
        return {
            "text": item.get("text", ""),
            "start": float(item.get("start", 0)),
            "duration": float(item.get("duration", 0)),
        }

    return {
        "text": getattr(item, "text", ""),
        "start": float(getattr(item, "start", 0)),
        "duration": float(getattr(item, "duration", 0)),
    }


def _build_response(video_id: str, segments: list[dict], language: str) -> dict:
    full_text = " ".join(segment["text"] for segment in segments)
    duration = segments[-1]["start"] + segments[-1].get("duration", 0) if segments else 0

    formatted_segments = [
        {
            "text": segment["text"].strip(),
            "start": round(segment["start"], 2),
            "duration": round(segment.get("duration", 0), 2),
            "timestamp": _seconds_to_timestamp(segment["start"]),
        }
        for segment in segments
    ]

    return {
        "video_id": video_id,
        "language": language,
        "segments": formatted_segments,
        "transcript": full_text,
        "text": full_text,
        "duration_seconds": round(duration),
        "duration_human": _seconds_to_timestamp(duration),
        "word_count": len(full_text.split()),
        "is_generated": False,
    }


def _seconds_to_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"
