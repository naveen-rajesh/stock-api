"""
LLM Service — fully local, zero external API calls.
- Summaries: TF-IDF style extractive algorithm
- Quizzes: sentence-based question generation
- Flashcards: term extraction from transcript
- Notes: Cornell-style section splitting
"""

import re
import random
from collections import Counter

STOPWORDS = {
    "a","an","and","are","as","at","be","been","being","but","by","can","could",
    "did","do","does","doing","done","for","from","get","got","had","has","have",
    "he","her","him","his","how","i","if","in","into","is","it","its","just",
    "like","may","me","more","my","not","now","of","off","on","or","our","out",
    "own","said","she","so","some","than","that","the","their","them","then",
    "there","these","they","this","those","through","to","too","up","us","was",
    "we","were","what","when","which","who","will","with","would","you","your",
}

def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    seen, out = set(), []
    for s in sentences:
        s = s.strip()
        norm = re.sub(r"\s+", " ", s.lower())
        if len(s.split()) >= 5 and norm not in seen:
            seen.add(norm)
            out.append(s)
    return out

def _word_freq(text: str) -> dict[str, int]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    return dict(Counter(w for w in words if w not in STOPWORDS))

def _sentence_score(sentence: str, freq: dict[str, int]) -> float:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", sentence.lower())
    if not words:
        return 0.0
    return sum(freq.get(w, 0) for w in words) / len(words)

def _top_sentences(sentences: list[str], freq: dict[str, int], n: int) -> list[str]:
    if not sentences:
        return []
    ranked = sorted(range(len(sentences)), key=lambda i: _sentence_score(sentences[i], freq), reverse=True)
    selected = sorted(ranked[:n])
    return [sentences[i] for i in selected]

def _extract_timestamps(text: str) -> list[str]:
    return re.findall(r"\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b", text)[:10]

def _extract_key_terms(freq: dict[str, int], n: int = 8) -> list[str]:
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:n]]


async def generate_summary(transcript: str, style: str = "concise", language: str = "en") -> dict:
    sentences = _split_sentences(transcript)
    freq = _word_freq(transcript)
    terms = _extract_key_terms(freq)
    count = {"concise": 4, "detailed": 10, "bullet": 6, "eli5": 4}.get(style, 4)
    picked = _top_sentences(sentences, freq, count) if sentences else []

    if style == "bullet":
        summary = "\n".join(f"• {s}" for s in picked)
    elif style == "eli5":
        summary = "In simple words: " + " ".join(picked)
    elif style == "detailed":
        summary = "\n\n".join(picked)
    else:
        summary = " ".join(picked)

    return {
        "summary": summary or transcript[:500],
        "main_topics": terms[:6],
        "key_terms": [{"term": t, "definition": "Key concept from the video."} for t in terms[:5]],
        "word_count": len(summary.split()),
        "timestamps_hint": _extract_timestamps(transcript),
        "provider": "local",
        "tokens_used": 0,
    }




async def generate_notes(transcript: str) -> dict:
    sentences = _split_sentences(transcript)
    freq = _word_freq(transcript)
    terms = _extract_key_terms(freq, 10)
    chunk_size = max(1, len(sentences) // 3)
    chunks = [sentences[i:i+chunk_size] for i in range(0, len(sentences), chunk_size)][:3]

    sections = []
    for j, chunk in enumerate(chunks, start=1):
        best = _top_sentences(chunk, freq, 1)
        heading = (best[0][:60] + "...") if best and len(best[0]) > 60 else (best[0] if best else f"Section {j}")
        sections.append({
            "heading": heading,
            "content": " ".join(chunk),
            "key_questions": [
                "What is the main idea of this section?",
                f"How does this relate to {terms[j % len(terms)] if terms else 'the topic'}?",
            ],
            "notes": _top_sentences(chunk, freq, 3),
        })

    return {
        "title": "Study Notes",
        "sections": sections,
        "summary_paragraph": " ".join(_top_sentences(sentences, freq, 3)),
        "action_items": [f"Review: '{t}'" for t in terms[:3]],
        "further_reading": [f"Search: {t}" for t in terms[3:6]],
        "provider": "local", "tokens_used": 0,
    }
