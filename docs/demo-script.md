# LeadForge Demo Script

Product-focused walkthrough scripts for LeadForge-Agentic Core. Use these for a product demo, technical review, or architecture discussion. LeadForge is presented as a controlled AI sales intelligence system — not as a fully autonomous sales agent or production SaaS.

**Before you demo:** Run the app locally (see [README](../README.md)). Prefer synthetic demo data. Do not display API keys, `.env` files, or real personal data on screen.

---

## 60-second product demo

**Goal:** Show what LeadForge does and why human review matters.

| Time | Screen | Action | Say (approx.) |
|------|--------|--------|----------------|
| 0:00 | Landing (`/`) | Scroll briefly to hero | "LeadForge runs a traceable B2B sales intelligence pipeline — research, qualification, strategy, email drafts, and QA — with humans in control." |
| 0:15 | Dashboard (`/demo`) | Open dashboard | "This is the operator view: leads, priorities, and pipeline outputs from our deterministic baseline." |
| 0:25 | Lead table | Click one lead | "Each lead opens a detail drawer with agent outputs, traces, and QA scores." |
| 0:40 | Lead detail drawer | Expand trace + QA | "Every step is visible: what went in, what came out, and how QA scored the draft." |
| 0:50 | Human review | Toggle review state | "Review decisions stay in the browser — the system prepares intelligence; people decide what to use." |
| 0:58 | — | Stop | "Export is a local CSV for reviewed leads — no CRM sync, no email sending." |

**Emphasize:** Traceability, QA gate, human-in-the-loop.

**Do not say:** "AI replaces SDRs," "fully autonomous," "sends emails," "live web research," "LangGraph-powered."

---

## 90-second product demo

Extend the 60-second script with:

| Time | Screen | Action | Say (approx.) |
|------|--------|--------|----------------|
| 1:00 | Dashboard overview | Point at summary metrics | "Batch deterministic runs process multiple demo leads with consistent, replay-safe outputs." |
| 1:15 | Agent trace section | Walk one trace entry | "Traces summarize inputs and outputs per agent — latency and token metadata without dumping full prompts in telemetry." |
| 1:25 | QA evaluation | Show QA score and recommendation | "QA Evaluator flags risk before anything would be sent — and nothing is sent from this product today." |
| 1:35 | CSV export (if visible) | Trigger export after marking reviewed | "Reviewed leads export locally as CSV — advisory output only." |
| 1:45 | — | Optional: mention roadmap link | "Advanced intake, live research, and durable telemetry are documented separately — not claimed as shipped." |

**Emphasize:** Deterministic baseline as the default safe path; demo data is synthetic/curated.

**Do not say:** "Production SaaS," "CRM integration," "portfolio project for recruiters."

---

## 3-minute technical walkthrough

**Goal:** Architecture, pipeline, optional live path, and honest boundaries.

| Time | Topic | Screen / doc | Action | Say (approx.) |
|------|-------|--------------|--------|----------------|
| 0:00 | Architecture | `docs/architecture-overview.md` or landing architecture section | Show diagram | "User → Next.js → FastAPI → linear five-agent pipeline → traces and QA → local human review → local CSV export." |
| 0:30 | Deterministic pipeline | Dashboard (`api` or `mock` mode) | Open lead, show five agent sections | "Orchestration is plain Python: Research → Qualifier → Strategist → Email Drafter → QA Evaluator. No LangGraph runtime — deferred per ADR when linear orchestration is enough." |
| 1:00 | Agent contracts | Lead detail drawer | Point at structured fields | "Agents share explicit contracts; outputs feed forward deterministically for tests and demos." |
| 1:20 | Telemetry | `GET /api/demo/telemetry/runs` (browser or curl) **or** mention if no UI | Show JSON summaries | "In-memory telemetry records summary metadata only — no full prompts or raw provider payloads. Read-only endpoints; not a durable observability DB." |
| 1:40 | Live Groq (optional) | Terminal with backend running | `curl -X POST .../live-groq/lead_001` only if env enabled | "Live path is backend-only, opt-in, one lead per request, token-capped, with deterministic-vs-live comparison. No frontend button yet. Failures surface explicitly — no silent fallback to live success." |
| 2:10 | LangGraph ADR | `docs/adr/langgraph-decision.md` | Open Status + Decision | "LangGraph is deferred: we don't need branching, durable checkpoints, or parallel tool fan-out today. Revisit when ADR criteria become real requirements." |
| 2:30 | Human review + export | Dashboard | Toggle review, export CSV | "Review state is browser-local; backend does not persist review decisions." |
| 2:50 | Roadmap | `docs/roadmap/advanced-capabilities.md` | Scroll capability table | "Smart Intake, live research, vertical profiles, durable telemetry, and frontend live controls are roadmap — clearly separated from what ships today." |

**Emphasize:** Test oracle (deterministic), explicit failure semantics on live path, ADR-driven deferral of graph runtime.

**Do not say:** "LangGraph-powered runtime," "multi-tenant platform," "PDF/Excel intake works today."

---

## Recommended screen sequence

1. Landing page (`/`) — product framing  
2. Demo dashboard (`/demo`) — lead table and summary  
3. Lead detail drawer — all five agents + trace + QA  
4. Human review controls — local state only  
5. CSV export (after marking at least one lead reviewed)  
6. *(Optional)* OpenAPI `/docs` or telemetry JSON — observability without secrets  
7. *(Optional)* `curl` live Groq response — only with `ENABLE_LIVE_MODEL_PIPELINE=true` and key in `.env`, never on screen  
8. Architecture doc or roadmap doc — boundaries and future work  

---

## What to click

| Step | Where | Click / action |
|------|-------|----------------|
| 1 | `/` | "View demo" or navigate to `/demo` |
| 2 | `/demo` | Sort or scan lead table; select medium/high priority lead |
| 3 | Lead row | Open lead detail drawer |
| 4 | Drawer tabs/sections | Agent outputs → Trace → QA |
| 5 | Human review | Approve / reject / flag (labels per UI) |
| 6 | Export | Export reviewed leads (CSV download) |
| 7 | *(Technical)* | New tab: `http://localhost:8000/docs` or telemetry URL |

---

## What to emphasize

- **Controlled workflow:** Five named agents, fixed order, visible traces.  
- **Deterministic baseline:** Default path is replay-safe, network-free, and used as the test oracle.  
- **QA before action:** Evaluator scores drafts; product does not send email.  
- **Human-in-the-loop:** Local review and export; AI prepares, humans decide.  
- **Honest scope:** Demo leads and research context are synthetic/curated — not live company intelligence.  
- **Optional live comparison:** Backend-only Groq path when explicitly enabled; comparison with deterministic output.  
- **Documentation:** ADR for LangGraph; roadmap for future capabilities.

---

## What not to say

| Avoid | Prefer instead |
|-------|----------------|
| "Fully autonomous sales agent" | "Prepares review-ready sales intelligence" |
| "Sends emails / CRM sync" | "Generates drafts for human review; local CSV export only" |
| "Live web research" | "Deterministic research path today; live research on roadmap" |
| "LangGraph-powered" | "Linear plain-Python orchestration; LangGraph deferred per ADR" |
| "Production SaaS / multi-tenant" | "Local demo product with explicit limitations" |
| "Smart Intake / PDF / Excel upload" | "Standard lead schema today; intake on roadmap" |
| "Click Run Groq in the UI" | "Live Groq is API-only until frontend control ships" |
| "I built this so recruiters…" | *(omit — keep focus on product and architecture)* |
| "Guaranteed reply rates" | "QA scores and recommendations are advisory" |
| "Real company intelligence" (when using demo data) | "Synthetic/curated demo dataset" |

---

## Related documentation

- [Architecture overview](./architecture-overview.md)  
- [ADR-001: LangGraph decision](./adr/langgraph-decision.md)  
- [Advanced capabilities roadmap](./roadmap/advanced-capabilities.md)  
- [Screenshots checklist](./screenshots-checklist.md)  
- [README](../README.md)  
