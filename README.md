# StudyAPI

> Turn any YouTube video into transcripts and summaries via a simple REST API.

---

## Endpoints

| Method | Endpoint | Description | Free | Pro |
|--------|----------|-------------|------|-----|
| POST | `/v1/transcript` | Raw transcript + optional timestamped segments | Yes | Yes |
| POST | `/v1/summary` | Video summary in concise, detailed, bullet, or ELI5 style | Yes | Yes |
| GET | `/` | Service metadata and available endpoints | Yes | Yes |
| GET | `/health` | Health check | Yes | Yes |

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

```

---

## Run Locally

```bash
git clone https://github.com/yourname/studyapi
cd studyapi
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

## Run with Docker

```bash
docker build -t studyapi .
docker run -p 8080:8080 --env-file .env studyapi
```

---

## Deploying on Render

1. Push the project to GitHub.
2. Create a new Web Service in Render.
3. Connect the repository.
4. Render will pick up `render.yaml`.
5. Add proxy variables if transcript fetching fails on cloud IPs.

### Recommended Environment Variables

- `YOUTUBE_PROXY_URL`
- or `YOUTUBE_HTTP_PROXY` and `YOUTUBE_HTTPS_PROXY`

### Why This Matters

YouTube often blocks transcript requests coming from hosting-provider IPs.
Using a proxy makes transcript fetching much more reliable on Render.

You do not need an OpenAI, Gemini, Groq, or other external LLM key. The summarizer is fully local.

---

## Pricing

| Plan | Price | Calls/month | Transcript | Summary |
|------|-------|-------------|------------|---------|
| Free | $0 | 100 | Yes | Yes |
| Pro | $19/mo | 5,000 | Yes | Yes |
| Enterprise | Custom | Unlimited | Yes | Yes |

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

## Deploy to Railway

```bash
railway login
railway init
railway up
railway domain
```

Set env vars from `.env.example` in the Railway dashboard.

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
  └── /v1/summary     → services/llm.py (local extractive summaries)
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
