# LeadForge-Agentic Core

**Traceable B2B sales intelligence — controlled AI workflow, human decisions.**

LeadForge is an AI sales intelligence product and engineering codebase: a five-agent pipeline that researches demo leads, qualifies fit, shapes strategy, drafts outreach copy, and evaluates quality before anything reaches a human reviewer. The system is designed for transparency, deterministic replay, and honest scope — not for unsupervised outbound automation.

This repository documents the system architecture, implementation decisions, and local demo workflow.

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

Demo leads and company context are **synthetic/curated** — not live company intelligence.

---

## What it does not do

Do not expect the following in the current product:

- Smart Lead Intake (no PDF, image, Excel, or pasted-table normalization in the dashboard)
- Live web research, scraping, or search APIs
- LangGraph runtime or checkpointed agent graphs
- CRM integration or backend sync of review state
- Email sending or deliverability tooling
- Durable telemetry database or long-term eval history store
- Frontend “Run live Groq” button (live path is API-only)
- Authentication, payments, or multi-tenancy
- Backend persistence of human review decisions
- Guaranteed reply rates or “AI replaces SDRs” automation

---

## Demo workflow

1. Start frontend (and optionally backend). Open [`http://localhost:3000/demo`](http://localhost:3000/demo).  
2. Browse the lead table; open a lead detail drawer.  
3. Inspect agent outputs, **agent trace**, and **QA evaluation**.  
4. Mark leads in **local human review** (browser-only state).  
5. **Export reviewed leads** as CSV locally.  
6. *(Optional, technical)* Enable live Groq in `backend/.env`, call `POST /api/demo/pipeline/live-groq/{lead_id}`, compare with deterministic baseline.  
7. *(Optional)* Inspect telemetry via read-only API endpoints.

Full timed scripts: [`docs/demo-script.md`](docs/demo-script.md).

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
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed browser origins |
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
pnpm build
pnpm lint

# Backend
cd backend
pytest -q
```

Groq live smoke tests are opt-in (`RUN_GROQ_LIVE_TESTS` / key present); default CI-style runs use mocks. Backend tests set `DATABASE_URL` and `APP_ENV=test` via `backend/tests/conftest.py`.

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
- **No outbound execution** — drafts are not emailed.  
- **No durable ops stack** — telemetry and review state do not survive as production audit logs.  
- **Single-tenant local demo** — no auth or org isolation.  
- **Intake preview API** exists (`POST /api/intake/preview`) but Smart Intake is **not** a productized dashboard flow.  
- **SQLite** initializes schema; pipeline/review persistence for production workflows is out of scope.  
- **Live Groq** requires explicit env enablement and manual API calls — not a dashboard button.

---

## Roadmap

Post-v1 items are **design intent** until shipped and reflected in the capability table. See [`docs/roadmap/advanced-capabilities.md`](docs/roadmap/advanced-capabilities.md).

| ID | Capability | Status |
|----|------------|--------|
| A1 | Manual frontend live Groq trigger | Roadmap — API-only today |
| A2 | Smart Lead Intake & data normalization | Roadmap |
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
- PDF/image/Excel intake in the dashboard  
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
| [Architecture overview](docs/architecture-overview.md) | System design, diagrams, production gaps |
| [Demo script](docs/demo-script.md) | 60s / 90s / 3min walkthroughs |
| [Screenshots checklist](docs/screenshots-checklist.md) | Capture guide and safety rules |
| [ADR-001: LangGraph](docs/adr/langgraph-decision.md) | Why graph runtime is deferred |
| [Advanced capabilities roadmap](docs/roadmap/advanced-capabilities.md) | Implemented vs future capability table |
| [Backend README](backend/README.md) | API details, live Groq endpoint, tests |

---

## License

See repository license file if present. Otherwise treat as private/demo codebase until a license is added.
