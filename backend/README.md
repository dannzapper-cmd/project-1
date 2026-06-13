# LeadForge Backend

FastAPI backend for LeadForge-Agentic Core. The local demo build currently ships:

- FastAPI app with CORS, lifespan, `/health`, and OpenAPI docs
- Pydantic v2 schemas mirroring the frontend/API contracts
- Deterministic demo pipeline:
  Research → Qualifier → Strategist → Email Drafter → QA Evaluator
- Deterministic batch pipeline for demo leads
- CSV/pasted-table intake preview plus deterministic user-lead batch processing
- Safe in-memory telemetry with read-only inspection endpoints
- Optional live Groq single-lead path, disabled by default and guarded by
  `ENABLE_LIVE_MODEL_PIPELINE=true` plus `GROQ_API_KEY`
- SQLite schema initialization via SQLAlchemy 2.x (`create_all` on startup)

The backend does **not** currently provide PDF/image/Excel intake, live web
research, LangGraph runtime, durable telemetry storage, backend review
persistence, CRM integration, email sending, authentication, payments, or
multi-tenancy.

## Folder layout

```
backend/
├── app/
│   ├── main.py              FastAPI app factory + lifespan
│   ├── core/
│   │   ├── config.py        Pydantic Settings (.env)
│   │   └── logging.py       stdlib logging setup
│   ├── api/
│   │   ├── deps.py          shared dependencies (get_db)
│   │   └── routes/          health, demo pipeline, telemetry, intake preview
│   ├── schemas/             Pydantic v2 DTOs for contracts
│   │   ├── common.py
│   │   ├── lead.py
│   │   ├── qa.py
│   │   ├── run.py
│   │   └── health.py
│   ├── services/            pipeline, telemetry, live pipeline, agents
│   └── db/
│       ├── base.py          DeclarativeBase
│       ├── session.py       engine + SessionLocal
│       ├── models.py        Lead / Run / AgentTrace / QAResult tables
│       └── init_db.py       create_all()
├── tests/                   backend unit and API tests
├── requirements.txt
├── .env.example
└── .gitignore
```

## Quick start

From the repo root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Health: <http://localhost:8000/health>
- OpenAPI docs: <http://localhost:8000/docs>

Expected `/health` response:

```json
{
  "status": "ok",
  "app": "leadforge-backend",
  "version": "0.1.0",
  "env": "development",
  "db": "ok"
}
```

## Tests

```bash
cd backend
pytest -q
```

Real Groq smoke tests are opt-in only and are skipped unless both
`GROQ_API_KEY` and `RUN_GROQ_LIVE_TESTS=1` are set:

```bash
GROQ_API_KEY=... RUN_GROQ_LIVE_TESTS=1 pytest -q tests/test_groq_live_smoke.py
```

## Environment variables

See `.env.example`. Variables below are read by the application code:

| Variable        | Default                          | Purpose                       |
|-----------------|----------------------------------|-------------------------------|
| `APP_NAME`      | `leadforge-backend`              | Reported by `/health`         |
| `APP_ENV`       | `development`                    | Reported by `/health`         |
| `APP_VERSION`   | `0.1.0`                          | Reported by `/health`         |
| `APP_HOST`      | `0.0.0.0`                        | Bind host (for `uvicorn`)     |
| `APP_PORT`      | `8000`                           | Bind port (for `uvicorn`)     |
| `LOG_LEVEL`     | `INFO`                           | Root logger level             |
| `DATABASE_URL`  | `sqlite:///./leadforge.db`       | SQLAlchemy connection URL     |
| `CORS_ORIGINS`  | `http://localhost:3000`          | Comma-separated allowed origins; production rejects `*` |
| `GROQ_API_KEY`  | (unset)                          | Optional Groq API key (not required for demo) |
| `GROQ_DEFAULT_MODEL` | `llama-3.1-8b-instant`      | Default Groq model when key is set |
| `GROQ_TIMEOUT_SECONDS` | `30`                      | Groq request timeout |
| `ENABLE_LIVE_MODEL_PIPELINE` | `false`             | Block 8.3 opt-in for the live Groq single-lead pipeline |
| `LIVE_MODE_ENABLED` | `false` | Opt-in for `/api/demo/live/*` Groq Live Demo Mode |
| `LIVE_DEMO_UNLOCK_CODE` | (server default; override in env) | Unlock code for Groq Live Demo Mode (server-validated, never returned to clients) |
| `MAX_LIVE_LEADS_PER_RUN` | `3` | Max leads per `POST /api/demo/live/run` |
| `MAX_LIVE_RUNS_PER_SESSION_PER_DAY` | `3` | Session daily cap |
| `MAX_LIVE_RUNS_PER_IP_PER_DAY` | `10` | IP daily cap (best-effort) |
| `DAILY_LIVE_DEMO_BUDGET_USD` | `1.00` | In-process daily spend cap (estimate-based) |
| `RATE_LIMIT_ENABLED` | `true`                     | Enables in-memory public-demo throttling |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `30`             | Default protected-action per-IP minute limit |
| `RATE_LIMIT_LIVE_REQUESTS_PER_MINUTE` | `5`        | Live Groq/research/assistant per-IP minute limit |
| `DEMO_ACCESS_CODE` | (unset)                     | Optional server-side code required by protected demo actions |
| `MAX_LEADS_PER_RUN` | `10`                       | Deterministic batch lead cap |
| `INTAKE_MAX_UPLOAD_MB` | `5`                     | Intake upload cap |

Optional Groq settings (`GROQ_API_KEY`, `GROQ_DEFAULT_MODEL`,
`GROQ_TIMEOUT_SECONDS`) are read when set; the app runs without them.
Commented future-phase variables in `.env.example` remain documentation only.

## Public backend deployment

Recommended Block 11A target: Render Web Service.

From the repository root, the Render service should use:

```text
Build Command: pip install -r backend/requirements.txt
Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

Required public env:

```text
APP_ENV=production
ENABLE_LIVE_MODEL_PIPELINE=false
CORS_ORIGINS=https://YOUR_VERCEL_PROJECT_DOMAIN,http://localhost:3000,http://127.0.0.1:3000
```

Set Vercel `NEXT_PUBLIC_API_URL` to the Render backend base URL and redeploy
Vercel after changing the env var. Full step-by-step deployment instructions,
including Render Free cold-start limitations and SQLite filesystem warnings,
are in [`../docs/deployment.md`](../docs/deployment.md).

## Block 8.3 — Live Groq single-lead pipeline (optional, off by default)

`POST /api/demo/pipeline/live-groq/{lead_id}` runs the existing five-agent
chain for **exactly one** demo lead with `GroqModelService` backing the
agents that already support `use_model_synthesis=True`. It also runs (or
re-uses) the deterministic baseline for the same lead and returns both
results side by side so the live output can be compared with the
deterministic one in a single response.

* **Off by default.** The endpoint refuses to call Groq unless
  `ENABLE_LIVE_MODEL_PIPELINE=true` *and* `GROQ_API_KEY` is set.
* **One lead per request.** No batch live endpoint is exposed.
* **No silent fallback.** When the live run fails at any stage, the
  response carries `live_success: false`, the failed agent name, the
  failure stage, and an error code. The deterministic baseline is still
  returned as comparison context but never replaces a "live" outcome.
* **Hard token budget.** A `MAX_LIVE_TOKENS_PER_RUN` constant
  (default 8,000 tokens) caps total tokens across all agent steps in a
  single request. The cap is not configurable from the request body.
* **No retry.** Block 8.3 never retries a rate-limited or failed Groq
  call. HTTP 429 surfaces as `error_code: "rate_limited"` in the
  response.
* **Model selection.** The Groq model is resolved from
  `Settings.groq_default_model` (env: `GROQ_DEFAULT_MODEL`, default
  `llama-3.1-8b-instant`) at request time. Switching models is a
  one-line env-var change; no live pipeline code edit is required.
  The `live_model_used` field on the response always reports the
  actual model the request was configured to call.
* **Telemetry-safe.** Only summary-level fields (run/lead/agent ids,
  status, latency, token estimates, cost estimates, fallback flags,
  QA score, hallucination risk) are recorded via the Block 8.2
  telemetry foundation. Prompts, full lead payloads, generated email
  bodies, and raw provider responses are never stored.

Run it locally without exposing your API key on the command line:

```bash
# 1. Put GROQ_API_KEY in backend/.env (or export it from a sourced env
#    file). NEVER pass it inline to curl or your shell history.
echo 'GROQ_API_KEY=...' >> backend/.env
echo 'ENABLE_LIVE_MODEL_PIPELINE=true' >> backend/.env

# 2. Start the backend in one terminal.
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. From another terminal, hit the endpoint for one lead.
curl -X POST http://localhost:8000/api/demo/pipeline/live-groq/lead_001
```

This call may incur a real Groq API cost (typically a few cents per
lead at the default `llama-3.1-8b-instant` model). The deterministic
pipeline at `GET /api/demo/pipeline/{lead_id}` is unaffected and
remains the safe, network-free baseline.

The architecture decision to defer LangGraph for this block is recorded
in [`docs/adr/langgraph-decision.md`](../docs/adr/langgraph-decision.md).

## Block 11C.4 — Controlled live draft regeneration

`POST /api/demo/email/regenerate-draft/{lead_id}` regenerates one reviewable
email draft for the selected lead context. It is the only frontend-triggered
Groq demo action and remains disabled unless all of these server-side gates are
configured:

```text
ENABLE_LIVE_MODEL_PIPELINE=true
GROQ_API_KEY=<server-side key>
RATE_LIMIT_ENABLED=true
DEMO_ACCESS_CODE=<code shared with the demo link>
```

The frontend checks `/api/system/status` and enables the lead-drawer control
only when `live_email_regenerate_configured=true`,
`live_single_lead_only=true`, and `public_live_batch_enabled=false`.

Safety boundaries:

* The request accepts structured lead context only; there is no arbitrary
  prompt field.
* The endpoint returns one draft only. It never sends email and never writes to
  a CRM.
* `GROQ_API_KEY` stays backend-only and is never returned by status or
  regenerate responses.
* Invalid JSON or guardrail failures are labeled
  `status: "deterministic_fallback"` / `mode: "deterministic_fallback"` and
  the replay draft remains available.
* Rate limits are in-memory per process and reset on backend restart. This is
  suitable for the portfolio demo, not production SaaS authentication or quota
  accounting.

## Block 10A — Real intake preview and user-lead batch processing

Preview endpoints:

- `POST /api/intake/preview` for `csv_text`, `pasted_table`,
  `records_json`, or `raw_text`.
- `POST /api/intake/preview-file/csv` for a single UTF-8 `.csv` upload up to
  1 MB.

Required normalized fields are `company_name` and `industry`. Missing
recommended fields (`website`, `country`, `contact_role`) and missing optional
context (`employee_count`, `notes`) produce warnings but do not block processing
when required fields are present. Unknown extra columns are reported as
unmapped and skipped.

Processing endpoint:

- `POST /api/demo/pipeline/batch`

The request body is:

```json
{
  "leads": [
    {
      "lead_id": "preview_001",
      "company_name": "Example Co",
      "industry": "B2B SaaS",
      "website": "example.com",
      "country": "US",
      "employee_count": 120,
      "contact_name": "Avery Lane",
      "contact_role": "VP Sales",
      "notes": "Exploring outbound operations."
    }
  ]
}
```

The endpoint reuses the deterministic five-agent pipeline, processes at most
10 normalized leads, does not call Groq, does not perform live research, and
does not write CRM/email/database side effects. If a user-provided lead does
not match curated `company_research`, the response carries intake
`validation_flags` such as `low_evidence` and the research output remains
cautious with no fabricated evidence cards.

## Notes

- No migration tool yet. Schema is created via `Base.metadata.create_all()`
  on app startup. Alembic will be introduced in a later phase if needed.
- ORM models exist (`Lead`, `Run`, `AgentTrace`, `QAResult`) and the schema is
  initialized on startup, but review decisions and pipeline runs are not
  durably persisted in this local demo build.
- The dashboard can read deterministic backend pipeline data in API mode.
  Human review changes and reviewed-lead export remain browser-local.
