"""
Transcript Service
Fetches YouTube transcripts using youtube-transcript-api (free, no quota).
Falls back to RapidAPI youtube138 if needed.
"""

import re
import os
import httpx
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled


def extract_video_id(url_or_id: str) -> str:
    """Accept full URL or raw video ID."""
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
    """
    Fetch transcript for a YouTube video.
    Returns: { text, segments, duration_seconds, language, word_count }
    """
    try:
        segments = _fetch_transcript_segments(video_id, language)

        full_text = " ".join(s["text"] for s in segments)
        duration  = segments[-1]["start"] + segments[-1].get("duration", 0) if segments else 0

        # Format segments with timestamps
        formatted_segments = [
            {
                "start":    round(s["start"], 2),
                "duration": round(s.get("duration", 0), 2),
                "text":     s["text"].strip(),
                "timestamp": _seconds_to_timestamp(s["start"])
            }
            for s in segments
        ]

        return {
            "video_id":        video_id,
            "text":            full_text,
            "segments":        formatted_segments,
            "duration_seconds": round(duration),
            "duration_human":  _seconds_to_timestamp(duration),
            "language":        language,
            "word_count":      len(full_text.split()),
            "is_generated":    False,
        }

    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise ValueError(f"No transcript found for video {video_id} in language '{language}'.")
    except Exception as e:
        raise ValueError(f"Failed to fetch transcript: {str(e)}")


def _fetch_transcript_segments(video_id: str, language: str) -> list[dict]:
    """
    Support both youtube-transcript-api 0.x and 1.x response shapes.
    0.x exposed get_transcript as a class method returning dicts.
    1.x exposes fetch on an instance returning snippet objects.
    """
    languages = [language]
    if language != "en":
        languages.append("en")

    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        raw_segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    else:
        api = YouTubeTranscriptApi()
        raw_segments = api.fetch(video_id, languages=languages)

    return [_normalize_segment(segment) for segment in raw_segments]


def _normalize_segment(segment) -> dict:
    if isinstance(segment, dict):
        return {
            "text": segment.get("text", ""),
            "start": segment.get("start", 0),
            "duration": segment.get("duration", 0),
        }

    return {
        "text": getattr(segment, "text", ""),
        "start": getattr(segment, "start", 0),
        "duration": getattr(segment, "duration", 0),
    }


def _seconds_to_timestamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"
