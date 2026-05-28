# LeadForge-Agentic Core

**Traceable B2B sales intelligence — controlled AI workflow, human decisions.**

LeadForge is a **production-like portfolio deployment** of an AI sales intelligence product: a five-agent pipeline that researches leads, qualifies fit, shapes strategy, drafts outreach copy, and evaluates quality before anything reaches a human reviewer. It is built for **B2B sales and revenue operations teams** who need consistent qualification, evidence-backed personalization, and review-ready outputs — without unsupervised outbound automation.

### The problem it targets

Revenue teams lose time to manual research, inconsistent qualification, generic outreach, and weak visibility into *why* a lead matters. LeadForge addresses that with a **controlled, traceable workflow**: structured intake, agent collaboration in a fixed order, QA before review, and humans retaining final authority.

### Live demo

**[https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app)** — landing and `/demo` dashboard. Add Leads → Preview → Process requires the Render backend (`NEXT_PUBLIC_API_URL`). The public demo uses **replay/cost-controlled behavior** by default; **live batch Groq execution is intentionally unavailable** in the UI.

### Core user flow

```
Landing → Demo dashboard → Add Leads (paste/upload) → Preview (valid/warning/invalid)
  → Process → Results table → Lead detail → Agent trace + QA
  → Human review (browser-local) → Export reviewed leads (CSV)
```

This repository documents architecture, implementation decisions, deployment, and the local demo workflow.

---

## What LeadForge does

LeadForge runs a **deterministic sales intelligence pipeline** over curated demo leads:

**Research → Qualifier → Strategist → Email Drafter → QA Evaluator**

Each step produces structured outputs and trace metadata. A Next.js dashboard surfaces leads, agent results, traces, QA scores, **local human review**, and **local CSV export** of reviewed leads. A FastAPI backend serves demo data, runs the pipeline, exposes **read-only telemetry**, and optionally supports a **backend-only, opt-in Groq single-lead path** with **deterministic-vs-live comparison**.

---

## Why it matters

B2B outreach fails when teams cannot see *why* an AI recommended a message, whether evidence supports claims, or who approved sending. LeadForge treats sales intelligence as a **controlled workflow**: agents collaborate in a fixed order, QA gates risky copy, telemetry stays summary-safe, and humans retain final authority. The deterministic baseline doubles as a **test oracle**; the optional live path exists to compare model behavior without hiding failures or silently substituting deterministic output for a failed live run.

---

## Implemented today

| Capability | Notes |
|------------|--------|
| Deterministic five-agent pipeline | Plain-Python orchestration; see `backend/app/services/pipeline_service.py` |
| Batch deterministic pipeline | Up to 10 demo leads per batch run |
| Next.js dashboard | `/demo` — lead table, lead detail drawer |
| Smart lead intake foundation | CSV, Excel, PDF, and pasted table preview/validation in `/demo`; max 10 processed leads per run |
| Production-safety layer | In-memory rate limiting, optional demo access code, request IDs, security headers, safe system status |
| Demo onboarding + business-value panel | `/demo` explains replay vs Add Leads; illustrative ROI-style metrics from run data |
| Backend-unavailable UX for Add Leads | Clear message when preview cannot reach the API (public Vercel without backend) |
| Research, Qualifier, Strategist, Email Drafter, QA Evaluator agents | Contract-tested services |
| Agent traces | Per-step input/output summaries in API and UI |
| QA evaluations | Scores and recommendations visible in UI |
| Local browser-only human review | Not persisted to backend |
| Local reviewed-lead CSV export | Browser download only |
| FastAPI backend | Health, demo pipeline, agents, intake preview, telemetry |
| Safe in-memory telemetry | Summary metadata only; bounded retention |
| Read-only telemetry endpoints | `GET /api/demo/telemetry/runs`, `.../runs/{run_id}` |
| Backend-only opt-in live Groq (single lead) | `POST /api/demo/pipeline/live-groq/{lead_id}`; off by default |
| Deterministic-vs-live comparison | When live path enabled and succeeds |
| Advanced roadmap documentation | [`docs/roadmap/advanced-capabilities.md`](docs/roadmap/advanced-capabilities.md) |
| LangGraph deferred | Per [`docs/adr/langgraph-decision.md`](docs/adr/langgraph-decision.md) — **not** a graph runtime today |

Demo leads and company context are **synthetic/curated** — not live company intelligence. User-provided leads can be processed through the deterministic pipeline, but LeadForge does not invent missing company research for them.

---

## What it does not do

Do not expect the following in the current product:

- Image/OCR intake (CSV, Excel, text-based PDF, and paste **are** supported for preview/process)
- LangGraph runtime or checkpointed agent graphs
- CRM integration or backend sync of review state
- Email sending or deliverability tooling
- Durable telemetry database or long-term eval history store
- Frontend “Run live Groq” button (live path is API-only)
- Full authentication, payments, or multi-tenancy
- Backend persistence of human review decisions
- Guaranteed reply rates or “AI replaces SDRs” automation

---

## Demo workflow

1. Start frontend (and optionally backend). Open [`http://localhost:3000/demo`](http://localhost:3000/demo).  
2. Use the curated sample results, or add leads in the **Add Leads** panel by pasting CSV/spreadsheet rows or uploading a UTF-8 `.csv`, `.xlsx`, or text-based `.pdf` file.  
3. Confirm the detected column mapping, review row-level validation, then process valid rows through the deterministic pipeline.  
4. Browse the lead table; open a lead detail drawer.  
5. Inspect agent outputs, **agent trace**, intake warnings, and **QA evaluation**.  
6. Mark leads in **local human review** (browser-only state).  
7. **Export reviewed leads** as CSV locally.  
8. *(Optional, technical)* Enable live Groq in `backend/.env`, call `POST /api/demo/pipeline/live-groq/{lead_id}`, compare with deterministic baseline.  
9. *(Optional)* Inspect telemetry via read-only API endpoints.

Full timed scripts: [`docs/demo-script.md`](docs/demo-script.md).

### Public preview vs local backend

| Mode | What works | Notes |
|------|------------|--------|
| **Replay demo** (default `NEXT_PUBLIC_DATA_SOURCE=mock`) | Sample dashboard, traces, human review, local CSV export | Safe on Vercel — no model calls, zero API cost |
| **Add Leads** (paste / CSV preview + process) | Requires a reachable FastAPI backend and `NEXT_PUBLIC_API_URL` | On public Vercel without backend config, preview shows a clear “backend unavailable” message instead of a generic fetch error |
| **Business metrics** on `/demo` | Derived in the browser from run data | Illustrative estimates (e.g. 30–45 min manual research per lead); not guaranteed ROI |

Controlled backend deployment steps are documented in [`docs/deployment.md`](docs/deployment.md), with runbook checks in [`docs/operations.md`](docs/operations.md). This repo does not send emails or write to a CRM in any mode.

---

## Architecture overview

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

**Optional live path (backend-only, opt-in):**

```
POST /api/demo/pipeline/live-groq/{lead_id}
  → single lead
  → token/cost limited
  → deterministic-vs-live comparison
  → no frontend trigger yet
```

Details: [`docs/architecture-overview.md`](docs/architecture-overview.md).

---

## Agent pipeline

| Step | Agent | Output (summary) |
|------|--------|------------------|
| 1 | Research | Company summary, signals, pains, evidence cards |
| 2 | Qualifier | Fit score, priority, rationale |
| 3 | Strategist | Angle, hypothesis, core message, personalization |
| 4 | Email Drafter | Subject and body **draft** (not sent) |
| 5 | QA Evaluator | QA score, recommendation, risk signals |

Orchestration is **linear** and **in-process** — not a LangGraph graph.

---

## Smart intake foundation

The dashboard supports two user-provided lead input paths:

- Paste CSV-like or tab-separated spreadsheet rows with headers.
- Upload a UTF-8 `.csv`, `.xlsx`, or text-based `.pdf` file up to 5 MB by default.

Required columns after mapping:

- `company_name`
- `industry`

Recommended columns:

- `website`
- `country`
- `contact_role`

Optional columns:

- `employee_count`
- `contact_name`
- `notes`

Common aliases are detected, for example `company`, `account`, or
`organization` -> `company_name`; `site`, `url`, or `domain` -> `website`;
`sector` or `vertical` -> `industry`; and `title`, `role`, or `job title` ->
`contact_role`.

Before processing, the UI shows the detected mapping and requires confirmation.
Rows are marked `valid`, `warning`, or `invalid`; invalid rows are not submitted
to the pipeline. Rows with required fields but missing recommended/optional
context are still processable and carry low-evidence warnings into the lead
detail drawer. Batch processing is capped at 10 leads per deterministic run.

Current limitations: no image/OCR intake, CRM writes, email sending, or hidden
model/API calls are included in this intake flow.

---

## Deterministic vs live model path

| Aspect | Deterministic (default) | Live Groq (opt-in) |
|--------|-------------------------|---------------------|
| Trigger | Dashboard `mock`/`api` demo endpoints; batch/single GET pipeline | `POST /api/demo/pipeline/live-groq/{lead_id}` only |
| Model | `MockModelService` baselines | `GroqModelService` where synthesis is supported |
| Network | No provider calls in deterministic path | Real Groq API when enabled |
| Scope | Single + batch demo leads | **One lead per request** |
| Comparison | N/A | Returns deterministic + live side by side |
| Failures | Standard agent failure semantics | `live_success=false`; explicit `failed_agent`, `failure_stage`, `error_code` — no silent live fallback |
| Frontend | Supported via data APIs | **No UI button yet** |

Enable live path only with `ENABLE_LIVE_MODEL_PIPELINE=true` and `GROQ_API_KEY` in `backend/.env`. Token budget: `MAX_LIVE_TOKENS_PER_RUN=8000` (constant in code, not request-configurable).

---

## Telemetry and evaluation

- **Telemetry:** In-memory, summary-only records (status, latency, token/cost estimates, QA score, hallucination risk flags). **No** full prompts, email bodies, or raw provider payloads in telemetry payloads.  
- **Endpoints:** Read-only under `/api/demo/telemetry/*`. Data is lost on backend restart.  
- **QA:** Per-lead evaluation in the pipeline; visible in the drawer alongside traces.

---

## Human review model

- Review actions (approve / reject / flag — per UI labels) update **browser-local state only**.  
- The backend does not store review decisions or enforce send gates.  
- Live model output, when used, is **advisory**; humans still decide what to trust or export.  
- Export produces a **local CSV** — not CRM sync.

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS, Radix UI |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.x (schema init), SQLite |
| Agents | Python services with explicit contracts and pytest coverage |
| Optional live model | Groq API via `GroqModelService` (backend-only, gated) |
| Orchestration | Plain Python (`pipeline_service.py`, `live_pipeline_service.py`) — LangGraph **not** used |

---

## Local setup

### Prerequisites

- Node.js 18+ and [pnpm](https://pnpm.io/)  
- Python 3.11+ (for backend)  
- *(Optional)* Groq API key for live comparison experiments only  

### Frontend

From the repository root:

```bash
pnpm install
cp .env.example .env.local   # optional; defaults to mock data
pnpm dev
```

- Landing: [http://localhost:3000](http://localhost:3000)  
- Dashboard: [http://localhost:3000/demo](http://localhost:3000/demo)

### Backend (for API mode and telemetry)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)  
- OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)

### Connect dashboard to backend

In `.env.local`:

```env
NEXT_PUBLIC_DATA_SOURCE=api
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart `pnpm dev` after changing env vars.

More detail: [`backend/README.md`](backend/README.md).

---

## Environment variables

Use placeholders in docs and commits — **never commit real API keys**.

### Frontend (`.env.local`, see `.env.example`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_DATA_SOURCE` | `mock` | `mock` = bundled demo data; `api` = FastAPI backend |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL when `DATA_SOURCE=api` |

### Backend (`backend/.env`, see `backend/.env.example`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_NAME` | `leadforge-backend` | `/health` metadata |
| `APP_ENV` | `development` | Environment label |
| `APP_VERSION` | `0.1.0` | Version string |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | Uvicorn bind |
| `LOG_LEVEL` | `INFO` | Logging |
| `DATABASE_URL` | `sqlite:///./leadforge.db` | Schema initialization (no review/pipeline durable writes in demo) |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins; production must use explicit origins, not `*` |
| `RATE_LIMIT_ENABLED` | `true` | In-memory public-demo rate limiting; resets on Render restart/spin-down |
| `DEMO_ACCESS_CODE` | *(unset)* | Optional private demo access code for protected actions; never put in frontend env |
| `MAX_LEADS_PER_RUN` | `10` | Public-demo preview/process cap |
| `INTAKE_MAX_UPLOAD_MB` | `5` | Public-demo upload cap |
| `GROQ_API_KEY` | *(unset)* | Required only when enabling live Groq path or live smoke tests |
| `GROQ_DEFAULT_MODEL` | `llama-3.1-8b-instant` | Groq model id |
| `GROQ_TIMEOUT_SECONDS` | `30` | Request timeout |
| `ENABLE_LIVE_MODEL_PIPELINE` | `false` | Gate for `POST .../live-groq/{lead_id}` |

Example live invocation (after setting env in `backend/.env`):

```bash
curl -X POST http://localhost:8000/api/demo/pipeline/live-groq/lead_001
```

May incur real API cost. Deterministic `GET /api/demo/pipeline/{lead_id}` remains the safe baseline.

---

## Testing / verification

```bash
# Frontend
pnpm install
pnpm typecheck
pnpm test:unit
pnpm build
pnpm lint

# Backend
cd backend
pip install -r requirements.txt
pytest -q
```

GitHub Actions runs frontend typecheck, unit tests, and build plus backend `pytest -q` on pushes and PRs (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)). **See CI output for the current test count**; a recent local backend run reported **624 passed, 6 skipped** (Groq live smoke tests opt-in only).

Groq live smoke tests are opt-in (`RUN_GROQ_LIVE_TESTS` / key present); default CI-style runs use mocks. Backend tests set `DATABASE_URL` and `APP_ENV=test` via `backend/tests/conftest.py`.

---

## Cost, safety, and public demo boundaries

| Mode | Cost | Behavior |
|------|------|----------|
| **Replay demo** (default on Vercel) | **$0** | Bundled sample results; no live model batch runs |
| **Add Leads + deterministic process** | **$0** (no Groq in deterministic path) | Requires reachable backend; capped at 10 leads per run |
| **Live Groq** (backend API only) | Provider usage | Opt-in env flag; single-lead; not exposed as public batch UI |

Public deployment protections: optional **demo access code**, **in-memory rate limits** (reset on Render restart), **max leads per run**, upload size caps, and **ephemeral storage** (pipeline/review/telemetry not durable across restarts). See [`docs/operations.md`](docs/operations.md).

---

## Deployment

Use [`docs/deployment.md`](docs/deployment.md) for the controlled public setup:

- **Frontend (Vercel):** [https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app)
- Render Web Service for the FastAPI backend.
- Vercel for the Next.js frontend.
- Vercel variable: `NEXT_PUBLIC_API_URL=<public backend base URL>`.
- Render variable: `CORS_ORIGINS=<vercel origin>,http://localhost:3000,http://127.0.0.1:3000`.

Render Free is acceptable for a controlled preview, but it sleeps after about
15 minutes of inactivity and can cold-start for about 50 seconds to one minute.
The cheapest paid Render web service instance is the optional upgrade for
smoother live demos.

---

## Repository structure

```
.
├── app/                    # Next.js App Router (landing, /demo)
├── components/             # UI (dashboard, landing, shared)
├── lib/                    # API client, mock data, types
├── data/demo/              # Curated demo leads and research fixtures
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── api/routes/     # health, demo, intake preview, telemetry
│   │   ├── agents/         # Five agent services
│   │   └── services/       # pipeline, live pipeline, telemetry, …
│   └── tests/
├── docs/
│   ├── adr/                # Architecture decision records
│   ├── roadmap/            # Advanced capabilities (implemented vs future)
│   ├── architecture-overview.md
│   ├── demo-script.md
│   ├── screenshots-checklist.md
│   └── assets/screenshots/ # Place screenshots here (see checklist)
└── README.md
```

---

## Screenshot placeholders

Add captures under `docs/assets/screenshots/` per [`docs/screenshots-checklist.md`](docs/screenshots-checklist.md).

| Placeholder | File (when captured) |
|-------------|----------------------|
| Landing / hero | `docs/assets/screenshots/01-landing-hero.png` |
| Dashboard overview | `docs/assets/screenshots/02-dashboard-overview.png` |
| Lead table | `docs/assets/screenshots/03-lead-table.png` |
| Lead detail drawer | `docs/assets/screenshots/04-lead-detail-drawer.png` |
| Agent trace | `docs/assets/screenshots/05-agent-trace.png` |
| QA evaluation | `docs/assets/screenshots/06-qa-evaluation.png` |
| Human review | `docs/assets/screenshots/07-human-review.png` |
| CSV export | `docs/assets/screenshots/08-csv-export.png` |
| Telemetry | `docs/assets/screenshots/09-telemetry.png` |
| Deterministic vs live | `docs/assets/screenshots/10-deterministic-vs-live.png` |
| Architecture docs | `docs/assets/screenshots/11-architecture-docs.png` |
| Roadmap docs | `docs/assets/screenshots/12-roadmap-docs.png` |

---

## Limitations

- **Demo data only** for default intelligence — not real-time market research.  
- **User-provided lead context is limited to supplied fields** unless the lead id matches curated demo research; missing context is surfaced as low evidence.  
- **No outbound execution** — drafts are not emailed.  
- **No durable ops stack** — telemetry and review state do not survive as production audit logs.  
- **Single-tenant local demo** — no auth or org isolation.  
- **Smart intake does not support image/OCR**; CSV, Excel, text-based PDF, and paste remain preview-first.  
- **SQLite** initializes schema; pipeline/review persistence for production workflows is out of scope.  
- **Live Groq** requires explicit env enablement and manual API calls — not a dashboard button.

---

## Roadmap

Post-v1 items are **design intent** until shipped and reflected in the capability table. See [`docs/roadmap/advanced-capabilities.md`](docs/roadmap/advanced-capabilities.md).

| ID | Capability | Status |
|----|------------|--------|
| A1 | Manual frontend live Groq trigger | Roadmap — API-only today |
| A2 | Smart Lead Intake & data normalization | **Partial** — paste/CSV/XLSX/text-PDF preview + batch process (see capability table) |
| A3 | Live company & market research layer | Roadmap |
| A4 | Vertical profiles / configurable context | Roadmap |
| A5 | Durable telemetry / eval history | Roadmap (in-memory foundation only today) |
| A6 | LangGraph runtime | **Deferred** — [ADR-001](docs/adr/langgraph-decision.md) |

---

## Safety and honesty notes

- LeadForge **prepares review-ready sales intelligence**; it does **not** run a fully autonomous outbound program.  
- **Human review stays in control** — local state, local export.  
- **LangGraph is deferred** — orchestration is linear plain Python until ADR revisit criteria are met.  
- **Telemetry is intentionally shallow** — safe summaries, not a full prompt store.  
- **Live Groq is opt-in, backend-only, single-lead, and cost-bounded** — compare with deterministic output; failures are explicit.  
- **Advanced capabilities** are documented separately; do not describe roadmap items as shipped.

### Claims safety checklist

**Do not claim:**

- Fully autonomous sales agent  
- Production SaaS or multi-tenant commercial platform  
- Sends emails or integrates with CRM  
- Live web research  
- Image/OCR intake in the dashboard  
- LangGraph-powered runtime  
- Durable backend review persistence  
- Guaranteed reply rate  
- Real company intelligence when using synthetic demo data  
- AI replaces SDRs  

**Safer alternatives:**

- “Prepares review-ready sales intelligence”  
- “Generates outreach drafts for human review”  
- “Runs a deterministic sales intelligence pipeline”  
- “Includes backend-only opt-in live model comparison”  
- “Keeps human review in control”  
- “Documents future capabilities separately in the roadmap”  

---

## Documentation index

| Document | Description |
|----------|-------------|
| [Case study](docs/case-study.md) | Problem, architecture, impact, trade-offs |
| [Portfolio narrative](docs/portfolio-narrative.md) | CV bullets, interview talking points |
| [Architecture overview](docs/architecture-overview.md) | System design, diagrams, production gaps |
| [Demo script](docs/demo-script.md) | 2–4 min video script + shorter walkthroughs |
| [Deployment guide](docs/deployment.md) | Render backend deployment and Vercel wiring |
| [Operations runbook](docs/operations.md) | Env vars, smoke checks, rollback, rate-limit notes |
| [Screenshots checklist](docs/screenshots-checklist.md) | Capture guide and safety rules |
| [ADR-001: LangGraph](docs/adr/langgraph-decision.md) | Why graph runtime is deferred |
| [Advanced capabilities roadmap](docs/roadmap/advanced-capabilities.md) | Implemented vs future capability table |
| [Backend README](backend/README.md) | API details, live Groq endpoint, tests |

---

## License

See repository license file if present. Otherwise treat as private/demo codebase until a license is added.
