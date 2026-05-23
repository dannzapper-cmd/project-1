# LeadForge Backend

FastAPI backend for LeadForge-Agentic Core. The portfolio demo currently ships:

- FastAPI app with CORS, lifespan, `/health`, and OpenAPI docs
- Pydantic v2 schemas mirroring the frontend/API contracts
- Deterministic demo pipeline:
  Research → Qualifier → Strategist → Email Drafter → QA Evaluator
- Deterministic batch pipeline for demo leads
- Safe in-memory telemetry with read-only inspection endpoints
- Optional live Groq single-lead path, disabled by default and guarded by
  `ENABLE_LIVE_MODEL_PIPELINE=true` plus `GROQ_API_KEY`
- SQLite schema initialization via SQLAlchemy 2.x (`create_all` on startup)

The backend does **not** currently provide Smart Intake, live web research,
LangGraph runtime, durable telemetry storage, backend review persistence, CRM
integration, email sending, authentication, payments, or multi-tenancy.

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
| `CORS_ORIGINS`  | `http://localhost:3000`          | Comma-separated allowed origins |
| `GROQ_API_KEY`  | (unset)                          | Optional Groq API key (not required for demo) |
| `GROQ_DEFAULT_MODEL` | `llama-3.1-8b-instant`      | Default Groq model when key is set |
| `GROQ_TIMEOUT_SECONDS` | `30`                      | Groq request timeout |
| `ENABLE_LIVE_MODEL_PIPELINE` | `false`             | Block 8.3 opt-in for the live Groq single-lead pipeline |

Optional Groq settings (`GROQ_API_KEY`, `GROQ_DEFAULT_MODEL`,
`GROQ_TIMEOUT_SECONDS`) are read when set; the app runs without them.
Other future-phase variables (cost caps, feature flags) in `.env.example`
are documented but not read yet.

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

## Notes

- No migration tool yet. Schema is created via `Base.metadata.create_all()`
  on app startup. Alembic will be introduced in a later phase if needed.
- ORM models exist (`Lead`, `Run`, `AgentTrace`, `QAResult`) and the schema is
  initialized on startup, but review decisions and pipeline runs are not
  durably persisted in this portfolio demo.
- The dashboard can read deterministic backend pipeline data in API mode.
  Human review changes and reviewed-lead export remain browser-local.
