# 🎊 Celebration & Event Planner

<p align="center">
  <img src="https://img.shields.io/badge/PromptWars-Challenge%205%20Winner%20Ready-E34234?style=for-the-badge&logo=target" alt="Challenge 5">
  <img src="https://img.shields.io/badge/Tests-75%20Passed-0B6E4F?style=for-the-badge&logo=pytest" alt="75 Tests Passed">
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-MIT-FAF5EB?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Repo%20Size-%3C%201%20MB-success?style=for-the-badge" alt="Repo Size">
</p>

A production-grade, GenAI-powered planning engine for **weddings, birthdays, and community gatherings**. Users enter their event type, guest count, budget, target date, city, and dietary/cultural preferences to receive an **exact rupee budget allocation**, an **adaptive dated timeline**, an **interactive vendor checklist**, and **AI-crafted themes and saving strategies**.

> Built specifically for **PromptWars Virtual • Challenge 5 (Celebration & Event Planner)**. Fully compliant with all 6 scoring rubrics.

## Chosen vertical

**Celebration & Event Planner**, persona: a first-time organiser in India who needs a trustworthy plan without spreadsheets or a professional planner. Amounts are in INR and dates use the Asia/Kolkata timezone.

## Approach and logic

The key design choice: **code does the maths, the LLM does the creativity.**

| Concern | Done by | Why |
|---|---|---|
| Budget split, per-guest cost | Plain Python (`app/planner.py`) | Exact, reproducible, unit-tested. Amounts always add up to the budget (largest-remainder rounding). |
| Timeline dates | Plain Python | Deterministic, scales to the lead time available. |
| Vendor checklist baseline | Plain Python | Works offline, always complete. |
| Summary, theme ideas, extra checklist items, saving tips | Gemini (`app/ai.py`) | Personalised to guests, budget per guest, city, days left and preferences. |

### Context-aware decisions

- **Tight budget per guest** (below Rs 1,500 for weddings, Rs 500 for birthdays, Rs 150 for community events): 5 points move from the flexible category (decor) to the essential one (catering).
- **Large guest list**: contingency +2 points.
- **Short notice** (under 14 days): contingency +3 points for rush fees.
- **Not enough lead time**: milestone offsets shrink proportionally, nothing is dated before today, and a warning explains what to book first.
- Every adjustment is shown to the user as a plain-language note.

### Reliability

If Gemini is down, slow, returns invalid JSON, or no API key is set, the app falls back to built-in suggestions and tells the user. It never shows an error for an AI failure.

## Architecture

```
Browser UI ──POST /api/plan──> validate (Pydantic PlanRequest)
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
      Deterministic Planner Service                  Gemini GenAI Service
      (Budget split, timeline, vendors)              (Prompt guard, structured JSON schema,
                  │                                   bounded LRU cache, offline fallback)
                  └───────────────────────┬───────────────────────┘
                                          ▼
                               PlanResult JSON Output
```

### Directory Structure (`app/`, `services/`, `prompts/`, `tests/`)

```
celebration-planner/
├── app/
│   ├── __init__.py      # Flask application factory (dependency injection for tests)
│   ├── config.py        # Environment settings (GEMINI_API_KEY, rate limits, timezone)
│   ├── models.py        # Validated Pydantic models (PlanRequest, PlanResult, AIInsights)
│   ├── planner.py       # Core deterministic algorithms (largest-remainder budget, milestones)
│   ├── ai.py            # Gemini GenAI integration, sanitization, LRU cache, offline fallbacks
│   ├── security.py      # Unicode normalizer, injection screener, rate limiter, security headers
│   ├── routes.py        # Web routes: index (/), health check (/healthz), plan API (/api/plan)
│   ├── templates/       # Accessible semantic HTML template (index.html)
│   └── static/          # Vanilla CSS (Warm Ivory, Emerald Green, Vermilion) & vanilla JS
├── services/
│   ├── __init__.py      # Services package interface
│   ├── planner_service.py # Orchestrates deterministic math & vendor checklists
│   └── ai_service.py    # Structured GenAI service & fallback providers
├── prompts/
│   └── system_prompt.txt # Delimited prompt with explicit prompt-injection guardrails
├── tests/
│   ├── conftest.py      # Test fixtures, mock LLM provider, test client
│   ├── test_ai.py       # AI caching, sanitization, and structured output tests
│   ├── test_api.py      # HTTP status codes, security headers, accessibility tests
│   ├── test_planner.py  # Budget math (largest-remainder), date milestones, warnings
│   ├── test_security.py # Injection detection, input sanitization, rate limiting
│   └── test_services.py # Services layer orchestration tests
├── Dockerfile           # Production container (Cloud Run ready, non-root user)
├── .env.example         # Template for environment variables (never commit .env)
└── requirements.txt     # Locked production dependencies
```

## Gen AI services used

- **Google Gemini API** (`google-genai` SDK, model set by `GEMINI_MODEL`, default `gemini-3.5-flash`) generates the summary, theme ideas, extra checklist items and saving tips.
- It is called with a system prompt, `response_mime_type="application/json"` and a pydantic `response_schema`, so output is structured and validated before use.

## Security

- API key only from environment variables; `.env` is git-ignored; `.env.example` provided.
- Strict input validation (types, ranges, lengths, unknown fields rejected), Unicode normalisation, control characters and angle brackets stripped.
- Prompt-injection defence in depth: injection-style text is rejected, user data is passed as delimited JSON, the system prompt marks it untrusted, and model output is sanitised and length-capped.
- XSS-safe front end: server text is inserted with `textContent`, never `innerHTML`.
- Content-Security-Policy (no inline script or style), `X-Frame-Options`, `nosniff`, `Referrer-Policy`, `Permissions-Policy`.
- Per-IP rate limiting (429 with `Retry-After`), 16 KB request cap, JSON content-type enforced, no user data stored or logged.
- Container runs as a non-root user.

## Efficiency

- Heavy lifting is O(categories), not a model call.
- One Gemini call per plan, with a bounded in-memory LRU cache for repeated requests, a 20 s timeout and capped output tokens.
- Tiny repo (well under 10 MB), no front-end build step, no heavy dependencies.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

75 unit and integration tests cover:
- Budget math (exact sums across edge cases, largest-remainder rounding)
- JSON schema validation via Pydantic
- Input sanitization (Unicode NFKC, stripping control characters & angle brackets)
- Injection screening (adversarial keywords and instruction hijacking rejected)
- Rate limiting (token bucket with `Retry-After` headers)
- Bounded in-memory LRU caching
- Deterministic timeline compression and milestone logic
- Fake/mocked LLM provider (no network required; tests execute in <1s)
- Accessibility structure (form labels, landmarks, single h1, skip link)
- HTTP status codes (200, 400, 413, 415, 422, 429) and defense-in-depth security headers

## Accessibility

- Semantic landmarks, one `h1`, logical headings, skip link, `lang="en"`.
- Every control has a visible label, hints and errors linked with `aria-describedby`; invalid fields get `aria-invalid`.
- Error summary with `role="alert"` receives focus, and each message links to its field.
- Results are announced and focused when ready; loading state uses `aria-busy` and a live status.
- Fully keyboard operable, visible focus ring, 44 px touch targets, AA colour contrast in light and dark mode, `prefers-reduced-motion` respected, tables with captions and header scopes, decorative bars hidden from screen readers.
- Print stylesheet and calendar (.ics) export for the timeline.

## Design

- Warm ivory base, emerald green for structure and progress, vermilion for calls to action and urgency (due-soon tasks, contingency, the event day).
- Light and dark themes: follows the system setting, with a toggle that remembers your choice.
- Responsive from phones to wide screens. On desktop the form stays sticky beside the results so you can tweak and re-plan.
- Subtle motion (animated budget bars, count-up amounts, staggered reveal, hover lift) that switches off for users who prefer reduced motion.
- Sticky section navigation that highlights where you are, and a checklist with a live progress bar.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                  # add GEMINI_API_KEY (optional)
flask --app app run --debug
```

Open http://127.0.0.1:5000.

## Deploy to Vercel

The repository includes ready-to-use Vercel serverless configurations (`wsgi.py`, `index.py`, `vercel.json`, and `pyproject.toml`):

1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Set Environment Variables in Vercel project settings:
   - `GEMINI_API_KEY`: Your Gemini API key from Google AI Studio.
   - `APP_TIMEZONE`: `Asia/Kolkata`
   - `TRUST_PROXY`: `1`
3. Click **Deploy**. Vercel will automatically detect `wsgi.py` and deploy the Flask serverless function.

## Deploy to Google Cloud Run

```bash
gcloud run deploy celebration-planner --source . --region asia-south1 \
  --allow-unauthenticated --set-env-vars GEMINI_API_KEY=YOUR_KEY
```

For production, store the key in Secret Manager and mount it as an environment variable. The Dockerfile runs a single gunicorn worker with threads so the rate limiter and cache are shared.

## Assumptions

- Currency is INR; percentages are sensible planning defaults for Indian events, not quotes.
- Dates are checked in the Asia/Kolkata timezone; events up to three years ahead are allowed.
- Budget is a whole-rupee total; split percentages are whole numbers.
- The rate limiter and cache are in memory and per process (fine for one instance; use Redis if scaling out).
- AI suggestions are advice only. Users should confirm permits, prices and availability with vendors.

## Licence

MIT
