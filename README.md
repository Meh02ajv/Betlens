# BetLens

A sports statistics and probability analytics web app for football and NBA.

> **Disclaimer:** BetLens is an analytics and decision-support tool. It never accepts bets, never holds user money, and never promises profit. All probabilities are statistical estimates — no outcome is guaranteed.

---

## Table of Contents

1. [What BetLens Does](#what-betlens-does)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Quick Start (Docker)](#quick-start-docker)
5. [Manual Setup](#manual-setup)
6. [Environment Variables](#environment-variables)
7. [Mock Data & Development](#mock-data--development)
8. [Running Tests](#running-tests)
9. [Key Pages & Features](#key-pages--features)
10. [API Overview](#api-overview)
11. [Probability Engine](#probability-engine)
12. [AI Assistant](#ai-assistant)
13. [Deployment](#deployment)
14. [Build Roadmap](#build-roadmap)

---

## What BetLens Does

BetLens helps football and basketball fans understand the real statistical chances of sporting events:

- **Dashboard** — personalized view of your favorite teams' upcoming matches and probabilities
- **Competition pages** — standings, fixtures, stats, and season-simulation outlook
- **Team pages** — form, squad, injuries, head-to-head, and predictions
- **Match pages** — probability panel (1X2, over/under, BTTS, correct score), lineups, live events, odds comparison
- **Player pages** — season stats, per-90 numbers, next-match probabilities (scorer, assist, cards)
- **Value finder** — surfaces matches where the model probability exceeds bookmaker implied probability
- **Accumulator analyzer** — combined probability, expected value, and risk label for multi-selection slips
- **Bet tracker** — personal journal of bets with P&L, ROI, and hit-rate charts
- **AI Assistant** — natural-language chat grounded entirely in platform data (no hallucinated numbers)

### Competitions covered at launch

| Competition | Sport | Code |
|---|---|---|
| Premier League | Football | PL |
| La Liga | Football | LL |
| Serie A | Football | SA |
| Bundesliga | Football | BL |
| Ligue 1 | Football | L1 |
| UEFA Champions League | Football | UCL |
| UEFA Europa League | Football | UEL |
| UEFA Conference League | Football | UECL |
| NBA | Basketball | NBA |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript strict |
| Styling | Tailwind CSS, shadcn/ui (Radix primitives) |
| Data fetching | TanStack Query |
| Forms | React Hook Form + Zod |
| Charts | Recharts, Apache ECharts |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Background jobs | Celery + Redis broker + Celery Beat |
| Database | PostgreSQL 16 |
| Cache / queue | Redis 7 |
| ML | pandas, NumPy, SciPy, statsmodels, scikit-learn, LightGBM |
| AI assistant | Anthropic Claude API (tool use + streaming) |
| Auth | fastapi-users (email/password + Google OAuth) |
| Payments | Stripe Checkout + Customer Portal |
| Email | Resend |
| Push | Web Push (VAPID) |
| Realtime | Server-Sent Events (SSE) |
| Testing | Pytest, Vitest, React Testing Library, Playwright |
| DevOps | Docker, Docker Compose, GitHub Actions |

---

## Project Structure

```
betlens/
├── apps/
│   ├── web/                    # Next.js 15 frontend (PWA)
│   │   └── src/
│   │       ├── app/            # App Router pages
│   │       ├── components/     # ui/, match/, team/, charts/, chat/, layout/
│   │       ├── lib/            # API client, utils, auth, formatters
│   │       ├── hooks/          # Custom React hooks
│   │       ├── styles/         # Global CSS, design tokens
│   │       └── types/          # Shared TypeScript types
│   └── api/                    # FastAPI backend (modular monolith)
│       └── app/
│           ├── core/           # Config, security, logging, deps
│           ├── db/             # Models, session, Alembic migrations
│           ├── modules/        # auth, users, sports_data, predictions,
│           │                   # odds_value, assistant, notifications,
│           │                   # billing, admin
│           ├── providers/      # football_provider, nba_provider, odds_provider, mock/
│           ├── ml/             # features, models, training, calibration, backtest
│           └── workers/        # Celery app + scheduled tasks
├── packages/
│   └── shared-types/           # Generated OpenAPI TypeScript client
├── infra/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   └── .github/workflows/ci.yml
├── docs/                       # Specification, ADRs
├── .env.example
├── Makefile
└── README.md
```

---

## Quick Start (Docker)

**Prerequisites:** Docker Desktop (or Docker Engine + Compose plugin)

```bash
# 1. Clone the repo
git clone https://github.com/your-org/betlens.git
cd betlens

# 2. Copy environment file and fill in any keys you have
#    (everything works with mock providers — no paid API keys needed)
cp .env.example .env

# 3. Start all services
docker compose -f infra/docker-compose.yml up --build

# 4. In a second terminal, run migrations and seed demo data
docker compose -f infra/docker-compose.yml exec api python -m app.db.seed

# 5. Open the app
open http://localhost:3000
```

Services started by Docker Compose:

| Service | Port | Description |
|---|---|---|
| web | 3000 | Next.js frontend |
| api | 8000 | FastAPI backend |
| worker | — | Celery worker |
| beat | — | Celery Beat scheduler |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Redis 7 |

API docs (Swagger UI): http://localhost:8000/docs  
API docs (ReDoc): http://localhost:8000/redoc

---

## Manual Setup

### Backend

```bash
cd apps/api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp ../../.env.example ../../.env

# Run database migrations
alembic upgrade head

# Seed demo data
python -m app.db.seed

# Start the API server
uvicorn app.main:app --reload --port 8000

# In a separate terminal: start the Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# In a separate terminal: start Celery Beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Start the dev server
npm run dev
# → http://localhost:3000
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values you need. All providers default to `mock` so the app is fully functional without any paid API keys.

```env
# Core
APP_ENV=development
DATABASE_URL=postgresql+psycopg://betlens:betlens@localhost:5432/betlens
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-to-a-long-random-string
FRONTEND_URL=http://localhost:3000

# Auth (Google OAuth — optional for dev)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
JWT_ACCESS_TTL_MIN=15
JWT_REFRESH_TTL_DAYS=30

# Data providers (mock works out of the box)
FOOTBALL_PROVIDER=mock        # mock | api_football | sportmonks
FOOTBALL_API_KEY=
NBA_PROVIDER=mock             # mock | balldontlie | sportradar
NBA_API_KEY=
ODDS_PROVIDER=mock            # mock | the_odds_api
ODDS_API_KEY=

# AI assistant (optional — assistant returns mock answers without this)
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5
ASSISTANT_FREE_DAILY_LIMIT=10
ASSISTANT_PRO_DAILY_LIMIT=200

# Billing (optional for dev)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=

# Email (optional for dev — emails are logged to console)
RESEND_API_KEY=

# Web Push (optional)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=

# Monitoring (optional)
SENTRY_DSN=
```

---

## Mock Data & Development

When `FOOTBALL_PROVIDER=mock`, `NBA_PROVIDER=mock`, and `ODDS_PROVIDER=mock` (the defaults), the app uses realistic seeded data so every feature works without paid API keys:

- 6 football competitions with standings, fixtures, and results
- NBA regular season with 30 teams
- Pre-computed probabilities for all upcoming matches
- Bookmaker odds for value comparison
- Player stats and injury reports
- A demo user account: **demo@betlens.com / demo123456**

Run the seed script to populate the database:

```bash
# Docker
docker compose -f infra/docker-compose.yml exec api python -m app.db.seed

# Local
cd apps/api && python -m app.db.seed
```

---

## Running Tests

### Backend

```bash
cd apps/api

# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific module
pytest tests/test_predictions.py -v
```

### Frontend

```bash
cd apps/web

# Unit tests (Vitest)
npm run test

# Component tests with coverage
npm run test:coverage

# End-to-end tests (Playwright) — requires the app to be running
npm run test:e2e
```

### All at once (via Makefile)

```bash
make test
```

---

## Key Pages & Features

| URL | Access | Description |
|---|---|---|
| `/` | Public | Landing page — value proposition, feature preview, pricing |
| `/login` `/signup` | Public | Authentication |
| `/onboarding` | Auth (first time) | Competition + team selection wizard |
| `/dashboard` | Auth | Personalized home with your teams and today's matches |
| `/competitions` | Public | All covered competitions |
| `/competitions/[slug]` | Public | Standings, fixtures, stats, season outlook |
| `/teams/[id]` | Public | Team hub — overview, squad, stats, predictions |
| `/matches/[id]` | Public | Match center — probabilities, lineups, live, odds |
| `/players/[id]` | Public | Player profile and next-match probabilities |
| `/value` | Pro | Value finder with filters |
| `/slip` | Auth | Accumulator analyzer |
| `/tracker` | Auth | Bet journal and statistics |
| `/assistant` | Auth | Full-page AI chat |
| `/notifications` | Auth | Notification center |
| `/settings` | Auth | Profile, preferences, plan, privacy |
| `/model` | Public | Model performance and methodology |
| `/admin` | Admin | User management, job logs, model versions |

### Free vs Pro

| Feature | Free | Pro |
|---|---|---|
| Standings, fixtures, results | ✅ | ✅ |
| Headline match probability | ✅ | ✅ |
| All markets + player probabilities | 3 matches/day | ✅ Full |
| Value finder | Preview | ✅ Full |
| Accumulator analyzer | 3 selections | ✅ Unlimited |
| Bet tracker | ✅ | ✅ + advanced stats |
| Assistant messages/day | 10 | 200 |
| Notifications | In-app + email digest | ✅ + push + custom triggers |

---

## API Overview

All endpoints are versioned under `/api/v1`. Interactive docs at `/docs`.

### Authentication
```
POST /api/v1/auth/signup
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
POST /api/v1/auth/verify-email
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
```

### Sports Data
```
GET /api/v1/competitions
GET /api/v1/competitions/{slug}
GET /api/v1/competitions/{slug}/standings
GET /api/v1/competitions/{slug}/fixtures
GET /api/v1/competitions/{slug}/stats
GET /api/v1/competitions/{slug}/outlook
GET /api/v1/teams/{id}
GET /api/v1/matches/{id}
GET /api/v1/matches/{id}/predictions
GET /api/v1/matches/{id}/live          ← SSE stream
GET /api/v1/players/{id}
GET /api/v1/search?q=
```

### User Features
```
GET  /api/v1/me/dashboard
GET  /api/v1/me/favorites
PUT  /api/v1/me/favorites
POST /api/v1/slips/analyze
GET  /api/v1/bets
POST /api/v1/bets
GET  /api/v1/value
POST /api/v1/chat/sessions
POST /api/v1/chat/sessions/{id}/messages   ← SSE stream
```

### Prediction Response Format

```json
{
  "match_id": "uuid",
  "model_version": "football-dc-2026.10.1",
  "generated_at": "2026-10-12T08:00:00Z",
  "confidence": "medium",
  "markets": {
    "1x2": { "home": 0.52, "draw": 0.25, "away": 0.23 },
    "totals": [{ "line": 2.5, "over": 0.58, "under": 0.42 }],
    "btts": { "yes": 0.54, "no": 0.46 },
    "correct_score": [{ "score": "2-1", "p": 0.11 }],
    "cards": { "any_red": 0.07, "expected_yellows": 3.9 }
  },
  "expected_goals": { "home": 1.72, "away": 1.05 },
  "factors": [
    { "label": "Home attack strength", "direction": "up", "impact": 0.06 }
  ],
  "players": [
    { "player_id": "uuid", "anytime_scorer": 0.41, "decisive": 0.55, "carded": 0.12 }
  ]
}
```

---

## Probability Engine

### Football — Dixon-Coles Poisson Model

1. Each team has an **attack strength** and **defence strength** estimated from historical results with exponential time decay (recent matches weigh more).
2. Expected goals: `λ_home = league_avg_home × attack_home × defence_away × home_adv`
3. A scoreline matrix (up to 10×10) is built with the Dixon-Coles low-score correction.
4. Summing cells gives 1X2, over/under, BTTS, and correct-score probabilities.
5. Adjustments for confirmed lineups, injuries, rest days, and travel.
6. A **LightGBM** second stage blends Poisson output with Elo difference, rolling xG, form, and odds-implied probability.
7. Final probabilities are **calibrated** with isotonic regression.

### NBA — Elo / Net Rating Model

- Margin-adjusted Elo with recency weighting, home-court advantage, rest days, back-to-back flag, and injury impact.
- Win probability from a logistic function of the adjusted rating difference.
- Player props: projected minutes × per-minute rates, adjusted for opponent defense and pace.

### Season Simulations

Monte Carlo: 10,000 simulations of remaining fixtures → title, top-4, European qualification, and relegation probabilities.

### Confidence Labels

| Label | Meaning |
|---|---|
| High | Enough data, lineup confirmed, model agrees with market |
| Medium | Reasonable data, some uncertainty (e.g. unconfirmed lineup) |
| Low | Sparse data, major unknowns — shown with a warning |

---

## AI Assistant

The assistant is powered by the **Anthropic Claude API** with tool use and streaming.

**Rules:**
- Every number it states comes from a tool call — it never invents statistics.
- Answers include a confidence level, top 3 factors, and data freshness.
- It never claims certainty, never pressures users to bet, and never uses phrases like "sure win" or "guaranteed."
- If a user shows signs of problem gambling, it responds with empathy and shares support resources.

**Tools available to the model:**

| Tool | Returns |
|---|---|
| `search_entities` | Teams, players, competitions, matches |
| `get_match` | Match details, lineups, absences |
| `get_match_predictions` | Probabilities, confidence, factors |
| `get_player_predictions` | Scorer, assist, decisive, card probabilities |
| `get_team_form` | Recent results and trends |
| `get_standings` | Table and season simulation probabilities |
| `get_odds` | Odds by bookmaker, implied probabilities |
| `find_value` | Value opportunities |
| `analyze_slip` | Combined probability, EV, risk |
| `get_user_context` | Favorite teams and tracker summary |

---

## Deployment

### Frontend → Vercel

```bash
cd apps/web
vercel deploy
```

Set environment variables in the Vercel dashboard.

### Backend → Fly.io or Railway

```bash
# Fly.io
fly launch --dockerfile infra/Dockerfile.api
fly secrets set DATABASE_URL=... REDIS_URL=... SECRET_KEY=...
fly deploy
```

### Managed services

- **Database:** Neon or Supabase (PostgreSQL 16)
- **Redis:** Upstash or Railway Redis
- **Workers:** Same Fly.io app with `[processes]` config, or a separate Railway service

---

## Build Roadmap

| Phase | Duration | Deliverables |
|---|---|---|
| 0. Foundations | 1 week | Monorepo, Docker Compose, CI, design tokens, auth skeleton, mock providers |
| 1. Accounts & onboarding | 1–2 weeks | Sign-up, login, email verification, Google OAuth, onboarding wizard |
| 2. Sports data | 2–3 weeks | Real provider integration, ingestion jobs, competition/team/match/player pages |
| 3. Probability engine v1 | 2–3 weeks | Dixon-Coles, Elo, prediction storage, probability UI, Model page |
| 4. Events & players | 2 weeks | Scorer/assist/card markets, NBA props, season simulations |
| 5. Assistant | 2 weeks | Tool layer, Claude integration, streaming chat, answer cards, guardrails |
| 6. Odds & value | 2 weeks | Odds ingestion, comparison, value finder, slip analyzer, bet tracker |
| 7. Notifications & live | 1–2 weeks | SSE live scores, notification center, email and web push |
| 8. Billing & admin | 1 week | Stripe plans, feature gating, admin area |
| 9. Hardening & launch | 2 weeks | Security review, performance tuning, accessibility, load tests |

---

## Responsible Gambling

- 18+ age gate at sign-up.
- Persistent disclaimer on every probability: *"Estimates based on statistical models. No outcome is guaranteed."*
- Links to professional help organizations in the footer of every page.
- Tracker alerts when many bets are logged in a short time.
- Self-limit setting that hides value pages for a chosen period.
- The assistant never uses language like "sure win", "guaranteed", or "can't lose".

---

## Legal

- Terms of Service, Privacy Policy, and Cookie banner included.
- Data handling follows GDPR principles.
- No affiliate links to bookmakers in version 1.
- Verify the commercial licence of every data provider before going live.
- Seek legal advice for the countries where you plan to market the product.