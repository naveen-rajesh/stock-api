# StudyAPI 📚

> Turn any YouTube video into summaries, quizzes, flashcards, and study notes — via a simple REST API.

---

## Endpoints

| Method | Endpoint | Description | Free | Pro |
|--------|----------|-------------|------|-----|
| POST | `/v1/transcript` | Raw transcript + timestamps | ✅ | ✅ |
| POST | `/v1/summary` | AI summary (4 styles) | ✅ | ✅ |
| POST | `/v1/quiz` | Quiz questions (MCQ/T-F/SA) | 5 q | 20 q |
| POST | `/v1/flashcards` | Anki-style flashcards | 10 | 30 |
| POST | `/v1/notes` | Cornell study notes | ❌ | ✅ |
| GET  | `/v1/usage` | Quota & usage stats | ✅ | ✅ |

---

## Quick Start

```bash
# 1. Get transcript
curl -X POST https://api.studyapi.dev/v1/transcript \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtube.com/watch?v=VIDEO_ID"}'

# 2. Summarize (bullet style)
curl -X POST https://api.studyapi.dev/v1/summary \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtube.com/watch?v=VIDEO_ID", "style": "bullet"}'

# 3. Generate 10 MCQ questions
curl -X POST https://api.studyapi.dev/v1/quiz \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtube.com/watch?v=VIDEO_ID", "num_questions": 10, "difficulty": "medium"}'

# 4. Flashcards
curl -X POST https://api.studyapi.dev/v1/flashcards \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://youtube.com/watch?v=VIDEO_ID", "num_cards": 15}'
```

---

## Run Locally

```bash
git clone https://github.com/yourname/studyapi
cd studyapi
cp .env.example .env        # add your ANTHROPIC_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

## Run with Docker

```bash
docker build -t studyapi .
docker run -p 8000:8000 --env-file .env studyapi
```

---

## Pricing

| Plan | Price | Calls/month | Quiz | Flashcards | Notes |
|------|-------|-------------|------|------------|-------|
| Free | $0 | 100 | 5 q | 10 cards | ❌ |
| Pro | $19/mo | 5,000 | 20 q | 30 cards | ✅ |
| Enterprise | Custom | Unlimited | ✅ | ✅ | ✅ |

---

## Response Format

All endpoints return:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "latency_ms": 1240,
    "plan": "pro",
    "calls_remaining": 3841
  }
}
```

Errors:
```json
{
  "error": "rate_limit_exceeded",
  "message": "You've hit the free plan limit of 10 req/min.",
  "retry_after_seconds": 43,
  "upgrade": "https://studyapi.dev/pricing"
}
```

---

## Deploy to Railway (1-click)

```bash
railway login
railway init
railway up
railway domain
```

Set env var `ANTHROPIC_API_KEY` in Railway dashboard. Done.

---

## Architecture

```
Client
  │
  ▼
FastAPI App (main.py)
  ├── APIKeyMiddleware   → validates key, attaches plan to request.state
  ├── RateLimitMiddleware → per-key per-minute throttle (swap for Redis)
  │
  ├── /v1/transcript  → services/youtube.py (youtube-transcript-api)
  ├── /v1/summary     → services/llm.py (Claude claude-sonnet-4-20250514)
  ├── /v1/quiz        → services/llm.py
  ├── /v1/flashcards  → services/llm.py
  ├── /v1/notes       → services/llm.py (Pro only)
  └── /v1/usage       → models/db.py
```

---

## Monetization Checklist

- [ ] Deploy to Railway / Fly.io / Render
- [ ] Add real DB (SQLite → Postgres)
- [ ] Add Stripe webhook for key provisioning
- [ ] List on RapidAPI
- [ ] Build a simple landing page (studyapi.dev)
- [ ] Post on IndieHackers, Product Hunt, Twitter/X
- [ ] Reach out to EdTech SaaS founders on LinkedIn
