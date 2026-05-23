# LeadForge-Agentic Core

LeadForge is a portfolio-grade B2B sales intelligence demo: a deterministic agentic pipeline that researches leads, qualifies fit, drafts strategy and email copy, runs QA evaluation, and surfaces everything for human review in a dashboard. AI recommends; humans decide.

## Current demo status

- Deterministic mock-first demo pipeline (default dashboard data source is mock)
- Frontend/backend integration via `NEXT_PUBLIC_DATA_SOURCE` (`mock` or `api`)
- Local human review in the browser (not persisted to the backend)
- Local CSV export of reviewed leads (browser download only)
- Agent trace and QA evaluation visible in the UI
- Safe in-memory telemetry with read-only `/api/demo/telemetry/*` endpoints
- Opt-in live Groq single-lead API path: `POST /api/demo/pipeline/live-groq/{lead_id}` (disabled by default; no frontend trigger)
- No email sending, no CRM integration, no live web research
- No backend persistence for human review decisions
- No Smart Intake UI (server preview endpoints exist; no dashboard intake flow yet)

For planned advanced capabilities (intake, live research, vertical profiles, durable telemetry, LangGraph, frontend live controls), see [`docs/roadmap/advanced-capabilities.md`](docs/roadmap/advanced-capabilities.md).

## Local setup

From the repository root:

```bash
# Frontend (Next.js)
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). The demo dashboard is at `/demo`.

Backend (optional, for API mode):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

To point the dashboard at the backend, set `NEXT_PUBLIC_DATA_SOURCE=api` in `.env.local` (see `.env.example`) and restart the frontend.

Build and test:

```bash
pnpm build
cd backend && RUN_GROQ_LIVE_TESTS=0 python -m pytest -q
```

## Environment variables

Variables below are read by the application code. Use placeholders only; never commit real API keys.

### Frontend (`.env.local`, see `.env.example`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_DATA_SOURCE` | `mock` | `mock` uses bundled mock data; `api` calls the FastAPI backend |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL when `NEXT_PUBLIC_DATA_SOURCE=api` |

### Backend (`backend/.env`, see `backend/.env.example`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | `leadforge-backend` | Reported by `/health` |
| `APP_ENV` | `development` | Runtime environment label |
| `APP_VERSION` | `0.1.0` | Reported by `/health` |
| `APP_HOST` | `0.0.0.0` | Uvicorn bind host |
| `APP_PORT` | `8000` | Uvicorn bind port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DATABASE_URL` | `sqlite:///./leadforge.db` | SQLAlchemy URL (schema init only; no review/pipeline writes in demo) |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed browser origins |
| `GROQ_API_KEY` | (unset) | Optional. Required only for opt-in Groq smoke/live tests and `/api/demo/model-service/groq-check`. Not required for mock/demo mode. |
| `GROQ_DEFAULT_MODEL` | `llama-3.1-8b-instant` | Default Groq model when the key is set |
| `GROQ_TIMEOUT_SECONDS` | `30` | Groq request timeout |
| `ENABLE_LIVE_MODEL_PIPELINE` | `false` | Opt-in gate for `POST /api/demo/pipeline/live-groq/{lead_id}`; requires `GROQ_API_KEY` |

Backend tests set `DATABASE_URL` and `APP_ENV=test` via `backend/tests/conftest.py`; you do not need to set those for normal local development.
