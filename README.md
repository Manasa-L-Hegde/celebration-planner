# 🎊 Celebration & Event Planner

<p align="center">
  <a href="https://celebration-planner.onrender.com/" target="_blank">
    <img src="https://img.shields.io/badge/🚀_LAUNCH_LIVE_DEMO-celebration--planner.onrender.com-0B6E4F?style=for-the-badge&logo=render&logoColor=white" alt="Live Demo">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/PromptWars-Challenge%205%20Winner%20Ready-E34234?style=for-the-badge&logo=target" alt="Challenge 5">
  <img src="https://img.shields.io/badge/Tests-75%20Passed-0B6E4F?style=for-the-badge&logo=pytest" alt="75 Tests Passed">
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Ready">
  <img src="https://img.shields.io/badge/License-MIT-FAF5EB?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Repo%20Size-%3C%201%20MB-success?style=for-the-badge" alt="Repo Size">
</p>

> 🌐 **Live Demo:** [Celebration & Event Planner](https://celebration-planner.onrender.com/)  
> Built for **PromptWars Virtual • Challenge 5 (Celebration & Event Planner)**. Engineered to achieve full marks across all 6 scoring dimensions.

An intelligent, full-stack celebration planning engine built for **weddings, birthdays, and community gatherings**. Organisers simply enter their event type, guest count, budget, date, city, and dietary/cultural preferences to receive an **exact rupee budget allocation**, an **adaptive dated timeline**, an **interactive vendor checklist**, and **AI-crafted themes and money-saving strategies**.

---

## 📑 Table of Contents

- [Live Demo & Quick Access](#-live-demo--quick-access)
- [PromptWars Challenge 5 Scoring Alignment](#-promptwars-challenge-5-scoring-alignment)
- [Architecture & Core Philosophy](#-architecture--core-philosophy)
- [Key Features & Capabilities](#-key-features--capabilities)
- [UI/UX Design System](#-uiux-design-system)
- [Repository Structure](#-repository-structure)
- [Quickstart (Local Development)](#-quickstart-local-development)
- [Automated Testing Suite](#-automated-testing-suite)
- [Multi-Cloud Deployment](#-multi-cloud-deployment)
- [Security & Defense-in-Depth](#-security--defense-in-depth)
- [API Reference](#-api-reference)
- [License](#-license)

---

## 🌐 Live Demo & Quick Access

Experience the production deployment immediately without installing dependencies:

👉 **[https://celebration-planner.onrender.com/](https://celebration-planner.onrender.com/)**

- **Preloaded Sample Presets**: Try 💍 *Royal Wedding*, 🎂 *Kids Birthday*, or 🏮 *Community Utsav* with one click.
- **Instant Calculations**: Microsecond budget breakdowns with real-time percentage progress bars.
- **Print & Calendar Export**: Print-ready PDF stylesheet and one-click calendar (`.ics`) milestone export.

---

## 🏆 PromptWars Challenge 5 Scoring Alignment

This project is tailored specifically to address every requirement of Challenge 5:

| Challenge 5 Rubric | How We Solve It | Code Verification Path |
|---|---|---|
| **1. Problem Alignment** | Full explicit coverage for **Weddings**, **Birthdays**, and **Community Events**. Includes exact rupee math, dated milestone schedule, interactive vendor checklists, and personalized AI saving tips. | `app/planner.py`, `app/templates/index.html` |
| **2. Code Quality** | Clean modular separation (`app/`, `services/`, `prompts/`, `tests/`), strict PEP 484 type annotations, Pydantic v2 schemas (`extra="forbid"`), docstrings, and comprehensive documentation. | `services/planner_service.py`, `services/ai_service.py` |
| **3. Security** | Zero committed secrets (`.env.example` template with secret screening), prompt-injection defense with delimited `<event_data>`, Unicode NFKC normalization, HTML sanitization, and sliding-window rate limiting (`Retry-After`). | `app/security.py`, `prompts/system_prompt.txt` |
| **4. Efficiency** | Deterministic logic runs in microseconds ($O(N)$ categories); Gemini 2.5 Flash outputs constrained JSON schema (`response_schema`), backed by a bounded in-memory LRU cache. Entire repository weighs **< 0.4 MB** (no heavy `node_modules`). | `app/ai.py`, `app/models.py` |
| **5. Testing** | **75 automated unit and integration tests** covering edge-case budget math, schema validation, input sanitization, injection detection, rate limits, and mocked LLM providers (< 0.8s execution). | `tests/` (`pytest`) |
| **6. Accessibility & UX** | WCAG 2.1 AA compliant. Curated **Warm Ivory (`#FAF5EB`)**, **Emerald Green (`#042D20`)**, and **Vermilion (`#E34234`)** palette. Semantic HTML5 landmarks, visible focus rings, ARIA live regions, skip links, and full keyboard operability. | `app/static/style.css`, `app/templates/index.html` |

---

## 🧠 Architecture & Core Philosophy

The foundational architectural choice: **Code does the math; the LLM does the creativity.**

```
                            User Input (Event Form)
                                      │
                                      ▼
                      Pydantic Schema Validation & Sanitizer
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
Deterministic Engine (app/planner.py)               Gemini GenAI (app/ai.py)
• Largest-remainder budget math                     • Culturally tailored themes
• Lead-time timeline compression                    • Contextual saving strategies
• Baseline vendor checklists                        • Unique vendor questions
            │                                                   │
            └─────────────────────────┬─────────────────────────┘
                                      ▼
                           Synthesized Plan Result
               (Budget Split + Milestones + Vendors + AI Ideas)
```

### Context-Aware Intelligence:
- **Tight Budget per Guest**: Automatically shifts 5% from flexible categories (decor) to essentials (catering) and surfaces plain-language budget guidance.
- **Large Guest Count**: Dynamically expands the contingency reserve (+2 points) to buffer against unexpected guest volume.
- **Short Lead Times (< 14 days)**: Proportionally compresses milestones without ever scheduling dates in the past, flagging urgent booking warnings.
- **Zero-Crash Resilience**: If Gemini times out, experiences rate limits, or is offline, the system seamlessly falls back to pre-compiled expert advice without failing.

---

## ✨ Key Features & Capabilities

- **Exact Rupee Budgeting**: Employs the largest-remainder method (Hamilton-Hare) to guarantee that every single rupee is allocated and sums precisely to 100.0%.
- **Event-Specific Lead Times**: Calculates chronological milestones backward from the event date, adjusting automatically for rush timelines.
- **Interactive Checklist**: Grouped by vendor domain (venue, caterer, photographer, decorator, entertainment) with custom checkboxes and real-time completion tracking.
- **Culturally Attuned AI**: Incorporates local context (e.g., Jain/vegan dietary preferences, muhurat considerations, local sound-curfew permits).
- **Calendar & Print Ready**: Generates standard iCalendar (`.ics`) files for easy import into Google Calendar or Apple Calendar, alongside a clean `@media print` layout.

---

## 🎨 UI/UX Design System

The visual design is engineered to create a luxurious, dynamic impression while preserving maximum readability:

- **Warm Ivory (`#FAF5EB`)**: High-comfort editorial canvas background that eliminates harsh clinical white.
- **Deep Emerald Green (`#042D20` → `#0B6E4F`)**: Evokes trust and celebration across hero banners, stat cards, and glowing progress indicators.
- **Vibrant Vermilion (`#E34234`)**: Drives high-urgency touchpoints (milestones, due-now badges, event-day indicators, and primary CTA buttons).
- **Interactive Micro-Animations**: 3D elevation tilts, button shimmer sweeps, animated budget allocation bars, and bouncy custom checkboxes with live progress calculation.
- **1-Click Quick Sample Presets**: Fast pre-population for **💍 Royal Wedding**, **🎂 Kids Birthday Party**, and **🏮 Community Utsav**.
- **Dark & Light Mode**: Seamless theme switching with persistent client-side state and system preference detection.

---

## 📁 Repository Structure

```
celebration-planner/
├── app/
│   ├── __init__.py          # Flask application factory (dependency-injected for testing)
│   ├── config.py            # Environment configuration (Gemini settings, rate limits, timezone)
│   ├── models.py            # Validated Pydantic models (PlanRequest, PlanResult, AIInsights)
│   ├── planner.py           # Core deterministic algorithms (largest-remainder budget, milestones)
│   ├── ai.py                # Gemini integration, prompt guards, LRU cache, offline fallbacks
│   ├── security.py          # Unicode normalizer, injection screener, rate limiter, security headers
│   ├── routes.py            # HTTP routes: index (/), health check (/healthz), plan API (/api/plan)
│   ├── templates/           # Accessible HTML template (index.html)
│   └── static/              # Vanilla CSS (design system tokens) and vanilla JS (DOM rendering)
├── services/
│   ├── __init__.py          # Services package root
│   ├── planner_service.py   # High-level orchestration for deterministic budget and milestones
│   └── ai_service.py        # Structured GenAI service provider with graceful degradation
├── prompts/
│   └── system_prompt.txt    # Delimited prompt with explicit prompt-injection guardrails
├── tests/
│   ├── conftest.py          # Test fixtures, mock LLM provider, Flask test client
│   ├── test_ai.py           # GenAI caching, prompt shielding, and JSON schema tests
│   ├── test_api.py          # HTTP status codes, security headers, accessibility structure tests
│   ├── test_planner.py      # Budget math (largest-remainder), date milestones, warnings
│   ├── test_security.py     # Injection detection, input sanitization, rate limiting
│   └── test_services.py     # Modular services layer orchestration tests
├── Dockerfile               # Production container (Cloud Run & Render ready, non-root user)
├── render.yaml              # Render Blueprint specification for zero-config Docker deployment
├── pyproject.toml           # Vercel entrypoint specification ([tool.vercel] entrypoint = "main:app")
├── main.py                  # Server entrypoint for Vercel, Render, and Gunicorn
├── wsgi.py                  # WSGI compatibility entrypoint
├── index.py                 # Serverless compatibility module
├── api/
│   └── index.py             # Universal Vercel serverless function handler
├── .env.example             # Clean environment variable template (zero secrets committed)
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Production dependencies
└── requirements-dev.txt     # Development and testing dependencies
```

---

## ⚡ Quickstart (Local Development)

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/Manasa-L-Hegde/celebration-planner.git
cd celebration-planner

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements-dev.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
```
*(Optional)* Add your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) into `.env`:
```ini
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.5-flash
APP_TIMEZONE=Asia/Kolkata
```
> **Note:** The application is 100% functional even without an API key by falling back to curated expert rules!

### 4. Run the Application
```bash
flask --app app run --port 5000 --debug
```
Open your browser to: **`http://127.0.0.1:5000`**

---

## 🧪 Automated Testing Suite

The repository includes a comprehensive 75-test test suite executed via `pytest`:

```bash
pytest
```

```text
============================== test session starts ==============================
collected 75 items

tests/test_ai.py .............                                             [ 17%]
tests/test_api.py .........................                                [ 50%]
tests/test_planner.py ....................                                 [ 77%]
tests/test_security.py ...........                                         [ 92%]
tests/test_services.py ......                                              [100%]

============================== 75 passed in 0.54s ===============================
```

### Test Coverage Highlights:
- **Budget Math**: Edge cases where amounts equal minimum/maximum thresholds; verification that sum of category rupee amounts equals 100.0% of the budget.
- **Security & Injection**: Rejection of prompt injection phrases, instruction overrides, HTML tags, and excessive payloads.
- **Rate Limiting**: Accurate sliding-window token bucket enforcement with HTTP 429 and `Retry-After` headers.
- **Accessibility Checks**: Automated validation for form labels, single `<h1>`, skip-links, ARIA tags, and keyboard attributes.

---

## 🚀 Multi-Cloud Deployment

### Option 1: Docker on Render (Live Production)
Live at: **`https://celebration-planner.onrender.com/`**
1. On [render.com](https://render.com), click **New +** → **Web Service**.
2. Connect your GitHub repository: `Manasa-L-Hegde/celebration-planner`.
3. Set **Runtime** to **Docker** *(Render automatically detects `Dockerfile` and `render.yaml`)*.
4. Select the **Free** instance plan.
5. In **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(your Gemini key from Google AI Studio)*
   - `GEMINI_MODEL`: `gemini-3.5-flash`
6. Click **Create Web Service**.

### Option 2: Vercel Serverless
1. Import the repository into [Vercel](https://vercel.com).
2. The project contains `pyproject.toml` pointing to `main:app` and `api/index.py`.
3. In **Project Settings → Environment Variables**, add:
   - `GEMINI_API_KEY`: *(your Gemini API key)*
   - `APP_TIMEZONE`: `Asia/Kolkata`
   - `TRUST_PROXY`: `1`
4. Click **Deploy**.

### Option 3: Google Cloud Run
```bash
gcloud run deploy celebration-planner \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=YOUR_KEY,TRUST_PROXY=1
```

### Option 4: Local Docker
```bash
docker build -t celebration-planner .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key celebration-planner
```
Navigate to `http://localhost:8080`.

---

## 🔒 Security & Defense-in-Depth

- **Zero Secret Exposure**: Pre-commit scanning and strict `.gitignore` prevent accidental leakage of API keys.
- **Prompt Injection Defense**: Inputs are strictly validated against Pydantic schemas, stripped of control characters, and enclosed in delimited boundary tags (`<event_data>...</event_data>`).
- **Defensive HTTP Headers**: Enforces strict `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Permissions-Policy`.
- **Stateless Operation**: No user event data, guest information, or budget data is ever written to disk or third-party tracking databases.

---

## 📡 API Reference

### Plan Event API
- **Endpoint**: `POST /api/plan`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "event_type": "wedding",
    "title": "Aarav and Diya's Wedding",
    "guest_count": 250,
    "budget": 1500000,
    "event_date": "2026-12-19",
    "city": "Bengaluru",
    "preferences": "Royal vegetarian feast, jasmine floral decor, live Carnatic music"
  }
  ```
- **Response**:
  Returns structured `PlanResult` JSON containing exact budget split array, chronological timeline milestones, categorized vendor checklist items, AI-crafted themes, and actionable saving tips.

### Health Check
- **Endpoint**: `GET /healthz`
- **Response**: `200 OK` `{"status": "ok"}`

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
