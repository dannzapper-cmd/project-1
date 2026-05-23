# LeadForge Advanced Capabilities Roadmap

## Purpose

This document separates **implemented capabilities** from **planned future capabilities** so LeadForge remains honest, extensible, and portfolio-ready. Readers should use the [Capability status table](#capability-status-table) as the single source of truth for what exists today versus what is on the roadmap. Roadmap items are design intent only until they ship in a named block.

## Current capabilities

As of Block 8.3, LeadForge includes:

- **Deterministic AI pipeline:** Research → Qualifier → Strategist → Email Drafter → QA Evaluator
- **Batch deterministic pipeline** for multiple leads in one run
- **Dashboard** with lead table and lead detail drawer
- **Agent traces and QA evaluations** visible in the UI and API responses
- **Local human review** in the browser only — no backend write for review decisions
- **Local reviewed-lead CSV export** (browser download only)
- **Safe in-memory telemetry** from Block 8.2 (summary metadata; no full prompts or raw provider payloads)
- **Read-only telemetry endpoints** for inspection and demo observability
- **Opt-in live Groq single-lead path** from Block 8.3 (`POST /api/demo/pipeline/live-groq/{lead_id}`), disabled by default via `ENABLE_LIVE_MODEL_PIPELINE=false`; requires `GROQ_API_KEY` when enabled; bounded by `MAX_LIVE_TOKENS_PER_RUN=8000`; no retries; no frontend auto-trigger
- **Deterministic-vs-live comparison output** when the live path is used successfully
- **LangGraph deferred** per [`docs/adr/langgraph-decision.md`](../adr/langgraph-decision.md) — linear plain-Python orchestration today

LeadForge does **not** today provide Smart Intake, live web research, PDF/image/Excel parsing, vertical profiles, LangGraph runtime, durable telemetry storage, backend review persistence, CRM integration, email sending, or a frontend live Groq button.

## Capability status table

| Capability | Status | Block introduced | Roadmap timing |
|---|---|---|---|
| Deterministic pipeline | ✅ Implemented | Core | — |
| Batch pipeline | ✅ Implemented | Core | — |
| Dashboard + Lead detail | ✅ Implemented | Block 7 | — |
| Human review (local) | ✅ Implemented | Block 7 | — |
| CSV export (local) | ✅ Implemented | Block 7 | — |
| Telemetry foundation | ✅ Implemented | Block 8.2 | — |
| Live Groq single-lead | ✅ Implemented (opt-in) | Block 8.3 | — |
| Smart Lead Intake | 🗺 Roadmap | — | Future |
| Live Company Research | 🗺 Roadmap | — | Future |
| Vertical Profiles | 🗺 Roadmap | — | Future |
| LangGraph runtime | ⏸ Deferred | — | See ADR |
| Durable telemetry | 🗺 Roadmap | — | Future |
| Frontend live Groq button | 🗺 Roadmap | — | Future |

This table is the single source of truth for current vs planned state. Do not mark roadmap items as implemented until they ship and are reflected here.

---

## 1. Smart Lead Intake & Data Normalization

**Status:** Not implemented.

### Future capability

LeadForge may accept messy lead sources and normalize them into the internal Lead schema before pipeline processing:

- CSV uploads
- Excel workbooks
- Pasted table or plain text
- Copied spreadsheet tables from browsers
- PDF documents
- Images and screenshots of lead lists
- Other ad hoc lead exports from CRMs, events, or spreadsheets

### Future behavior

- Detect columns and infer field types from headers and sample rows
- Map detected fields to the internal Lead schema with explicit mapping UI
- Normalize values (trim, case, phone/email formats, company name cleanup)
- Flag missing or low-confidence fields before processing
- Show a preview and diff before any pipeline run
- Require human confirmation before normalization is applied and leads enter the pipeline

### Not available today

- No OCR
- No PDF parsing
- No Excel parsing
- No upload UI in the dashboard for intake files
- No Smart Intake agent in the production pipeline path

### Guardrails (planned)

- Confidence scores on every mapped field
- Human confirmation required — no silent auto-mapping
- File-size and row-count limits
- No storing arbitrary uploads by default (ephemeral processing or explicit opt-in retention)
- Replay/demo mode that uses fixtures instead of live parsing for portfolio demos

---

## 2. Live Company & Market Research Layer

**Status:** Not implemented.

### Future capability

A live research layer would enrich leads with public company and market context beyond deterministic fixtures:

- Public web research with cited sources
- Source traceability in agent traces
- Cache and replay mode for demos and regression
- Confidence levels per claim
- Rate limits and cost limits per run
- Human review gate before research output flows to Qualifier and downstream agents

### Not available today

- No live web research
- No scraping infrastructure
- No search API integration
- No browser automation for research

The Research agent today uses deterministic/mock synthesis paths appropriate for demo and test oracles.

### Guardrails (planned)

- No fabricated or uncited sources
- No aggressive scraping or terms-of-service violations
- No private or non-public data collection
- Stale-source warnings when cache age exceeds policy
- Citations required for factual claims used downstream
- Live research off by default; explicit opt-in per environment or run

---

## 3. Vertical Profiles / Configurable Context Profiles

**Status:** Not implemented.

### Future capability (B2B-focused)

Vertical profiles would let teams configure **B2B sales context** without turning LeadForge into a generic automation platform:

- B2B vertical profiles (ICP, pains, objections, proof points)
- Playbook and scoring configuration per profile
- Sales context packs loaded into Research, Qualifier, Strategist, and Email Drafter
- Profile-specific scoring thresholds and email style rules

**Example verticals (illustrative):** B2B SaaS, Logistics, Fintech, Cybersecurity, Manufacturing, Professional Services.

This is **not** positioned as healthcare patient workflows, psychology caseload tools, or arbitrary cross-industry email blast automation.

### Not available today

- No profile selector in the UI
- No per-vertical knowledge packs beyond the shared demo knowledge files
- No profile-specific scoring in the Qualifier

### Guardrails (planned)

- No cross-profile data leakage between runs or tenants
- Explicit active profile on every pipeline invocation
- Automated tests per profile for scoring and copy constraints
- Profile-specific knowledge files versioned alongside the profile definition
- No marketing claims that vertical profiles exist until this block ships

---

## 4. Durable Telemetry & Evaluation History

**Status:** Partial — in-memory foundation only (Block 8.2).

### Today

- Safe in-memory telemetry with bounded retention
- Read-only HTTP endpoints for summaries
- Summary-level metadata only — **no** prompts, full inputs, email bodies, or raw provider responses in telemetry payloads

### Future evolution

- Append-only **JSONL** sink for local and CI artifacts
- **SQLite or Postgres** tables for eval run history and aggregations
- Model-vs-deterministic comparison reports over time
- Operational metrics: parse success rate, fallback rate, cost per run, hallucination-risk trends from QA Evaluator signals

### Guardrails (planned)

- Configurable retention policy and purge jobs
- Privacy boundaries — PII minimization and field redaction rules
- No sensitive payload logging without explicit opt-in and access controls
- Durability opt-in per environment (demo stays in-memory by default)

---

## 5. Future LangGraph Runtime

**Status:** Deferred — see [`docs/adr/langgraph-decision.md`](../adr/langgraph-decision.md) (ADR-001).

LangGraph is **not** a dependency today. The five-agent pipeline runs as linear, in-process plain-Python orchestration (`pipeline_service.py`, `live_pipeline_service.py`). That design is sufficient for the current product: deterministic baseline, opt-in live Groq on a single lead, explicit failure surfacing, and no branching or durable checkpoints.

LangGraph should be revisited **only when** the ADR revisit criteria become real requirements, including:

- **Conditional agent branching** based on runtime output (non-trivial routing between downstream agents)
- **Stateful retries** with exponential backoff and crash-safe recovery
- **Durable human review persistence** across sessions and processes (backend review queue)
- **Live research with parallel tool calls** and structured aggregation
- **Smart Intake** with conditional normalization sub-pipelines per source shape
- **Complex failure recovery** that requires graph state rather than fail-fast linear runs

When two or more triggers land in the same delivery block, that is a strong signal to adopt a graph runtime and migrate orchestration per the ADR. This roadmap does not duplicate the full ADR text; read the linked document for decision context and tradeoffs.

**No LangGraph dependency** is added by this roadmap document.

---

## 6. Manual Frontend Live Groq Trigger

**Status:** Not implemented.

### Future UI capability

The dashboard may expose a **manual** control per lead, for example:

> **Run live Groq for this lead**

### Required constraints (when built)

- Manual click only — never on page load or batch selection
- One lead per invocation
- Clear cost and token warning before the request
- Control disabled unless backend live mode is enabled (`ENABLE_LIVE_MODEL_PIPELINE=true` and valid `GROQ_API_KEY`)
- No batch live mode from the UI
- Display deterministic vs live comparison when both are available
- Show failure states honestly (`live_success=false`, failed agent, error codes) — no silent fallback to deterministic output
- Respect human review workflow — live output is advisory; humans still decide

### Not available today

- No frontend live Groq button
- Live Groq is API-only and must be invoked explicitly (e.g. `curl` or API client)

---

## Public claims boundary

**Do not claim today:**

- LeadForge supports PDF/image/Excel intake
- LeadForge performs live web research
- LeadForge uses LangGraph runtime
- LeadForge supports vertical profiles
- LeadForge persists telemetry durably
- LeadForge sends emails
- LeadForge integrates with CRM
- LeadForge can run live Groq from the frontend

**Accurate summary wording:**

LeadForge currently provides a deterministic and opt-in live single-lead AI sales intelligence pipeline with telemetry, QA evaluation, human review, and safe local export. Advanced intake, live research, vertical profiles, durable telemetry, frontend live controls, and graph orchestration are documented roadmap capabilities.

---

## Explicit non-goals (this roadmap block)

This document does **not** authorize or implement:

- Smart Intake, live web research, LangGraph runtime, or a frontend live button
- OCR, PDF parsing, Excel parsing, or browser automation
- CRM integration, email sending, or backend review persistence
- Auth, payments, or multi-tenancy
- Vector DB / RAG architecture changes
- External observability platforms (Datadog, LangSmith, etc.)
- New runtime dependencies, backend behavior changes, or frontend redesign

Implementation of roadmap items will occur in future blocks with their own PRs, tests, and ADR updates as needed.
