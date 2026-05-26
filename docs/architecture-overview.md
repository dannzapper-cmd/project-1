# LeadForge Architecture Overview

This document describes how LeadForge-Agentic Core is structured today: a controlled, traceable B2B sales intelligence pipeline with a deterministic baseline, optional backend-only live model comparison, local human review, and safe in-memory telemetry. It aligns with [ADR-001: LangGraph Integration Decision](./adr/langgraph-decision.md) and the [Advanced capabilities roadmap](./roadmap/advanced-capabilities.md).

**The current product is not a fully autonomous LangGraph runtime.** Orchestration is linear, in-process plain Python (`pipeline_service.py`, `live_pipeline_service.py`).

---

## High-level architecture

```
User
  → Next.js Frontend
  → FastAPI Backend
  → Deterministic Pipeline
  → Agent Services
  → Trace + QA Evaluation
  → Human Review (browser-local)
  → Local Export (CSV)
```

### Optional live path (backend-only, opt-in)

```
POST /api/demo/pipeline/live-groq/{lead_id}
  → single lead only
  → GroqModelService (when ENABLE_LIVE_MODEL_PIPELINE=true + GROQ_API_KEY)
  → cost/token limited (MAX_LIVE_TOKENS_PER_RUN = 8000)
  → deterministic-vs-live comparison in response
  → no frontend trigger yet
  → live failures: live_success=false (no silent fallback to “live succeeded”)
```

---

## Next.js frontend

- **Stack:** Next.js (App Router), React, TypeScript, Tailwind CSS, Radix UI components.  
- **Landing:** `/` — product positioning and workflow preview.  
- **Dashboard:** `/demo` — lead table, lead detail drawer, agent outputs, traces, QA, human review, local CSV export.  
- **Data source:** `NEXT_PUBLIC_DATA_SOURCE` — `mock` (bundled demo data) or `api` (FastAPI at `NEXT_PUBLIC_API_URL`).  
- **Human review:** State stored in the browser only; not persisted to the backend.  
- **Not implemented on frontend:** Live Groq button, Excel/PDF/image intake, auth, payments, multi-tenancy.

---

## FastAPI backend

- **Entry:** `backend/app/main.py` — CORS, lifespan, SQLite schema init (`create_all`), route registration.  
- **Routers:** Health (`/health`), demo pipeline and agents (`/api/demo/*`), intake preview (`POST /api/intake/preview` — preview-only, not production intake), telemetry (`/api/demo/telemetry/*`).  
- **ORM:** SQLAlchemy models exist (`Lead`, `Run`, `AgentTrace`, `QAResult`); schema initializes on startup. Pipeline runs and human review are **not** durably persisted for the demo product path described here.  
- **Docs:** OpenAPI at `http://localhost:8000/docs` when running locally.

See [backend/README.md](../backend/README.md) for folder layout and environment variables.

---

## Deterministic pipeline

**Module:** `backend/app/services/pipeline_service.py`

**Order (fixed, single pass per agent per lead):**

1. Research Agent  
2. Qualifier Agent  
3. Strategist Agent  
4. Email Drafter Agent  
5. QA Evaluator Agent  

**Properties:**

- In-process, synchronous, no LangGraph, no Groq in this path.  
- Agents use `MockModelService` (deterministic baselines).  
- Outputs pass forward via explicit Pydantic contracts (`app/schemas/agents.py`).  
- Single-lead: `run_pipeline_for_lead(lead_id)`  
- Batch: `run_pipeline_for_demo_leads()` — up to 10 demo leads, shared `run_id`  
- Demo data loaded from static files under `data/demo/`  
- Each step can emit safe telemetry via `telemetry_service.record_pipeline_step`

---

## Agent services

| Agent | Role |
|-------|------|
| Research | Company summary, signals, pain hypotheses, evidence cards from available demo context |
| Qualifier | Fit score, priority, qualification rationale |
| Strategist | Sales angle, pain hypothesis, core message, personalization notes |
| Email Drafter | Subject and body draft (not sent) |
| QA Evaluator | QA score, recommendation, hallucination-risk signals |

Each agent has unit and contract tests. The deterministic pipeline is the **canonical test oracle** for comparisons with the opt-in live path.

---

## Agent traces

- Pipeline builds a `trace` list: one `TraceEntry` per agent (status, input/output summaries, latency, tokens, model metadata).  
- Traces are returned in API responses and shown in the dashboard lead detail drawer.  
- Trace `simulated=False` on pipeline entries reflects orchestration mode; underlying mock model metadata may still mark simulated execution on agent metadata.

---

## QA evaluation

- QA Evaluator runs after the email draft exists.  
- Consumes draft text, evidence cards, and personalization notes.  
- Produces bounded QA score and recommendation — advisory only.  
- **No email sending** and no automated outreach execution.

---

## Local browser-only human review

- Operators mark leads reviewed/approved/rejected in the UI.  
- State lives in browser storage for the session/device.  
- **No backend write** for review decisions in the current product.  
- Live Groq output, when used, remains advisory; humans still decide.

---

## Local reviewed-lead CSV export

- Browser-initiated download of reviewed leads.  
- **Not** CRM sync, not server-side export persistence, not email delivery.

---

## Safe in-memory telemetry

**Module:** `backend/app/services/telemetry_service.py`

- Bounded in-memory retention of **summary-level** run and step metadata.  
- Records after deterministic (and live) pipeline steps: run/lead/agent ids, status, latency, token estimates, cost estimates, fallback flags, QA score, hallucination risk — **not** full prompts, email bodies, or raw provider payloads.  
- **Not** a durable telemetry database; data is lost on process restart.

---

## Read-only telemetry endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/demo/telemetry/runs` | Recent run summaries (`limit` query param) |
| `GET /api/demo/telemetry/runs/{run_id}` | Agent-step detail for one run |

Inspection and demo observability only — no write APIs for external observability platforms in scope today.

---

## Backend-only opt-in Groq single-lead endpoint

**Endpoint:** `POST /api/demo/pipeline/live-groq/{lead_id}`  
**Module:** `backend/app/services/live_pipeline_service.py`

**Gates:**

- `ENABLE_LIVE_MODEL_PIPELINE=true`  
- `GROQ_API_KEY` set  
- One lead per request; no batch live endpoint  
- Hard token budget: `MAX_LIVE_TOKENS_PER_RUN` (8000)  
- No retry on failure or rate limit  

**Behavior:**

- Reuses the same five-agent chain and contracts.  
- `GroqModelService` only where agents support `use_model_synthesis=True`.  
- Returns deterministic baseline alongside live result for comparison.  
- On live failure: `live_success=false` with `failed_agent`, `failure_stage`, `error_code` — deterministic baseline still returned as context, never masquerading as a successful live run.

---

## Deterministic-vs-live comparison

When the live path succeeds, the response includes both deterministic and live outputs so operators and engineers can compare behavior, cost, and QA signals side by side. The deterministic path remains the default for dashboard `mock` mode and for safe CI/demo runs without network calls.

---

## LangGraph ADR and why runtime is deferred

[ADR-001](./adr/langgraph-decision.md) **defers LangGraph adoption**. The product’s linear pipeline (deterministic baseline + opt-in single-lead live path) does not require branching, durable checkpoints, per-agent retry with backoff, or parallel tool fan-out today.

**Revisit when** (among others): conditional agent branching, stateful retries, durable backend review queues, live research with parallel tools, Smart Intake with conditional sub-pipelines, or complex failure recovery requiring graph state. Two or more triggers in one delivery block is a strong signal to adopt a graph runtime and migrate orchestration.

**Today:** No `langgraph` dependency; no graph compiler or checkpoint store.

---

## Production gaps

LeadForge-Agentic Core is an engineering demo product, not a production SaaS. Notable gaps:

| Area | Today | Gap |
|------|-------|-----|
| Auth / tenancy | None | No users, roles, or multi-tenant isolation |
| Review persistence | Browser-local | No backend review queue or audit trail |
| Telemetry | In-memory summaries | No durable DB, JSONL sink, or external APM |
| Outreach | Drafts only | No SMTP, no CRM write |
| Research | Demo/fixture context | No live web research or scraping |
| Intake | CSV/paste preview and max-10 deterministic processing | No PDF/Excel/OCR |
| Live model | API-only Groq | No frontend live button |
| Orchestration | Linear Python | LangGraph deferred per ADR |
| Data | Synthetic demo leads | Not real-time company intelligence |

---

## Security and cost boundaries

- **Secrets:** Keep `GROQ_API_KEY` in `backend/.env`; never commit keys or pass them inline in shell history.  
- **Live pipeline off by default:** `ENABLE_LIVE_MODEL_PIPELINE=false` unless explicitly enabled for comparison experiments.  
- **Cost control:** Single-lead requests, token cap per run, no automatic retries on 429.  
- **Telemetry privacy:** Summary metadata only in telemetry payloads.  
- **CORS:** Configured for local frontend origin (`CORS_ORIGINS`).  
- **No auth:** Do not expose an internet-facing instance without additional hardening.  
- **Demo data:** Use curated/synthetic leads; avoid real PII in screenshots and recordings.

---

## Related documentation

- [README](../README.md) — setup, capabilities, and claims boundary  
- [Demo script](./demo-script.md) — timed walkthroughs  
- [Screenshots checklist](./screenshots-checklist.md)  
- [Advanced capabilities roadmap](./roadmap/advanced-capabilities.md)  
- [ADR-001: LangGraph decision](./adr/langgraph-decision.md)  
