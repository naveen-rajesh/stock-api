"""
LLM Service — uses Google Generative AI (Gemini) for all study features.
Swap model or provider here without touching routes.
"""

import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
SUMMARY_PROVIDER = os.getenv("SUMMARY_PROVIDER", "gemini").lower()

genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or os.getenv("GOOGLE_MODEL") or "gemini-2.5-flash"
model = genai.GenerativeModel(GEMINI_MODEL)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "for",
    "from", "had", "has", "have", "he", "her", "his", "i", "if", "in",
    "into", "is", "it", "its", "just", "like", "more", "not", "of", "on",
    "or", "our", "out", "so", "some", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "to", "up", "was",
    "we", "were", "what", "when", "which", "who", "will", "with", "you",
    "your",
}


def _extract_json(text: str) -> dict | list:
    """Extract and parse a JSON object/array from an LLM response."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()

    start_candidates = [idx for idx in (cleaned.find("{"), cleaned.find("[")) if idx != -1]
    if start_candidates:
        start = min(start_candidates)
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        if end > start:
            cleaned = cleaned[start:end + 1]

    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {exc.msg}") from exc


def _call(prompt: str, max_tokens: int = 1500) -> tuple[str, int]:
    """Call Gemini and return (text, token_count)."""
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )
    )
    text = response.text
    tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
    return text, tokens


async def generate_summary(transcript: str, style: str = "concise", language: str = "en") -> dict:
    """
    Summarize a video transcript.
    style: concise | detailed | bullet | eli5
    """
    if SUMMARY_PROVIDER in {"local", "offline", "extractive"} or not GEMINI_API_KEY:
        return _generate_local_summary(transcript, style=style)

    style_prompts = {
        "concise":  "Write a concise 3-5 sentence summary.",
        "detailed": "Write a detailed, structured summary with section headers.",
        "bullet":   "Write a bullet-point summary with key takeaways.",
        "eli5":     "Explain this like I'm 5 years old, using simple language and analogies.",
    }
    instruction = style_prompts.get(style, style_prompts["concise"])

    prompt = f"""You are an expert study assistant. Given this video transcript, {instruction}

Also extract:
- main_topics: list of 3-6 main topics covered
- key_terms: list of important terms/concepts (with 1-line definitions)
- timestamps_hint: any timestamps or chapter markers mentioned

Respond ONLY in this JSON format with no extra text or markdown:
{{
  "summary": "...",
  "main_topics": ["topic1", "topic2"],
  "key_terms": [{{"term": "...", "definition": "..."}}],
  "word_count": 0,
  "timestamps_hint": ["..."]
}}

TRANSCRIPT:
{transcript[:12000]}"""

    try:
        raw, tokens = _call(prompt, max_tokens=1500)
        result = _extract_json(raw)
    except Exception:
        return _generate_local_summary(transcript, style=style)

    result["word_count"] = len(result.get("summary", "").split())
    result["tokens_used"] = tokens
    result["provider"] = "gemini"
    return result


def _generate_local_summary(transcript: str, style: str = "concise") -> dict:
    sentences = _split_sentences(transcript)
    if not sentences:
        return {
            "summary": transcript.strip(),
            "main_topics": [],
            "key_terms": [],
            "word_count": len(transcript.split()),
            "timestamps_hint": [],
            "tokens_used": 0,
            "provider": "local",
        }

    frequencies = _word_frequencies(transcript)
    ranked = sorted(
        enumerate(sentences),
        key=lambda item: _sentence_score(item[1], frequencies),
        reverse=True,
    )

    count_by_style = {
        "concise": 4,
        "detailed": 8,
        "bullet": 6,
        "eli5": 4,
    }
    selected_indexes = sorted(idx for idx, _ in ranked[:count_by_style.get(style, 4)])
    selected = [sentences[idx] for idx in selected_indexes]

    if style == "bullet":
        summary = "\n".join(f"- {sentence}" for sentence in selected)
    elif style == "eli5":
        summary = " ".join(selected)
        summary = f"In simple terms: {summary}"
    elif style == "detailed":
        summary = "\n\n".join(selected)
    else:
        summary = " ".join(selected)

    terms = [word for word, _ in sorted(frequencies.items(), key=lambda item: item[1], reverse=True)[:8]]

    return {
        "summary": summary,
        "main_topics": terms[:6],
        "key_terms": [
            {"term": term, "definition": "Important recurring term from the transcript."}
            for term in terms[:5]
        ],
        "word_count": len(summary.split()),
        "timestamps_hint": _extract_timestamps(transcript),
        "tokens_used": 0,
        "provider": "local",
    }


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    unique_sentences = []
    seen = set()
    for sentence in sentences:
        cleaned = sentence.strip()
        normalized = re.sub(r"\s+", " ", cleaned.lower())
        if len(cleaned.split()) < 5 or normalized in seen:
            continue
        seen.add(normalized)
        unique_sentences.append(cleaned)
    return unique_sentences


def _word_frequencies(text: str) -> dict[str, int]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    frequencies: dict[str, int] = {}
    for word in words:
        if word in STOPWORDS:
            continue
        frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies


def _sentence_score(sentence: str, frequencies: dict[str, int]) -> float:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", sentence.lower())
    if not words:
        return 0
    return sum(frequencies.get(word, 0) for word in words) / len(words)


def _extract_timestamps(text: str) -> list[str]:
    return re.findall(r"\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b", text)[:10]


async def generate_quiz(transcript: str, num_questions: int = 5, difficulty: str = "medium", quiz_type: str = "mcq") -> dict:
    """
    Generate quiz questions from transcript.
    quiz_type: mcq | true_false | short_answer | mixed
    difficulty: easy | medium | hard
    """
    num_questions = min(num_questions, 20)  # cap at 20

    type_instruction = {
        "mcq":          "multiple choice questions (4 options each, one correct)",
        "true_false":   "true/false questions with explanation",
        "short_answer": "short answer questions (1-3 sentence answers)",
        "mixed":        "a mix of MCQ, true/false, and short answer questions",
    }.get(quiz_type, "multiple choice questions")

    prompt = f"""You are an expert educator. Generate {num_questions} {type_instruction} at {difficulty} difficulty based on this transcript.

Respond ONLY in this JSON format with no extra text or markdown:
{{
  "questions": [
    {{
      "id": 1,
      "type": "mcq",
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "...",
      "difficulty": "{difficulty}",
      "topic": "..."
    }}
  ],
  "total_questions": {num_questions},
  "estimated_time_minutes": 0
}}

For true_false omit options. For short_answer set correct_answer to the ideal answer.

TRANSCRIPT:
{transcript[:12000]}"""

    raw, tokens = _call(prompt, max_tokens=3000)
    result = _extract_json(raw)
    result["tokens_used"] = tokens
    result["estimated_time_minutes"] = max(1, len(result.get("questions", [])) * 2)
    return result


async def generate_flashcards(transcript: str, num_cards: int = 10) -> dict:
    """Generate Anki-style flashcards from transcript."""
    num_cards = min(num_cards, 30)

    prompt = f"""You are an expert educator. Create {num_cards} Anki-style flashcards from this transcript.
Focus on key concepts, definitions, formulas, and important facts.

Respond ONLY in this JSON format with no extra text or markdown:
{{
  "flashcards": [
    {{
      "id": 1,
      "front": "Question or term",
      "back": "Answer or definition",
      "tags": ["topic1", "topic2"],
      "difficulty": "easy|medium|hard"
    }}
  ],
  "total_cards": {num_cards}
}}

TRANSCRIPT:
{transcript[:12000]}"""

    raw, tokens = _call(prompt, max_tokens=2000)
    result = _extract_json(raw)
    result["tokens_used"] = tokens
    return result


async def generate_notes(transcript: str) -> dict:
    """Generate structured Cornell-style study notes."""
    prompt = f"""You are an expert note-taker. Convert this transcript into structured Cornell-style study notes.

Respond ONLY in this JSON format with no extra text or markdown:
{{
  "title": "...",
  "sections": [
    {{
      "heading": "...",
      "content": "...",
      "key_questions": ["Q1?", "Q2?"],
      "notes": ["bullet1", "bullet2"]
    }}
  ],
  "summary_paragraph": "...",
  "action_items": ["..."],
  "further_reading": ["suggested topic 1", "suggested topic 2"]
}}

TRANSCRIPT:
{transcript[:12000]}"""

    raw, tokens = _call(prompt, max_tokens=2000)
    result = _extract_json(raw)
    result["tokens_used"] = tokens
    return result
