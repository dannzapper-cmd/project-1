# LeadForge Demo Script

Product-focused walkthrough scripts for LeadForge-Agentic Core. Use these for a recorded demo video, live presentation, technical review, or architecture discussion. LeadForge is presented as a controlled AI sales intelligence system — not as a fully autonomous sales agent or production SaaS.

**Public demo:** [https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app)

**Before you demo:** Confirm backend is reachable if showing Add Leads → Process (see [deployment.md](./deployment.md)). Prefer synthetic or anonymized B2B sample data. Do not display API keys, `.env` files, or real personal data on screen.

**Recorded demo note:** Recorded demo assets show the stable replay-mode public demo. Later polish may improve controlled live-mode messaging, regenerate draft affordances, selector contrast, and assistant guidance; do not imply the video shows those changes unless it is re-recorded.

---

## 2–4 minute video demo (recommended)

**Goal:** Show the full product story — landing, dashboard, real intake flow, results, trace, review, export — with honest safety boundaries.

| Time | Screen | Action | Say (approx.) |
|------|--------|--------|----------------|
| 0:00 | **Landing (`/`)** — full page | Start at top; slow scroll through hero, problem, solution, architecture preview | "LeadForge helps B2B sales and RevOps teams turn raw lead data into researched, qualified, review-ready opportunities — with humans in control at every step." |
| 0:25 | Landing — continue scroll | Show workflow/architecture sections if visible | "Five agents run in a fixed order: research, qualify, strategize, draft, and QA — every step is traceable." |
| 0:40 | Click **View demo** | Navigate to `/demo` | "This is the operator dashboard — replay mode is the default on the public site: safe, predictable, and zero model cost." |
| 0:50 | **Demo dashboard** — full viewport | Pause on empty or sample state; point at replay vs live copy | "Live batch model runs are intentionally unavailable here. Demo access, rate limits, and max-lead caps protect the deployment." |
| 1:05 | **Add Leads** panel | Scroll to intake; click sample CSV or paste 3–5 B2B rows | "You can paste or upload CSV, Excel, or a text-based PDF — the product is built for B2B fields like company, industry, website, and role." |
| 1:25 | **Preview table** | Show valid, warning, and invalid rows if possible; confirm column mapping | "Preview catches bad rows early. Incomplete data still processes but shows warnings and low-confidence states in the drawer." |
| 1:40 | **B2B profile selector** (if visible) | Select a profile pack | "Profile packs tune messaging context for common B2B segments — still advisory, not autonomous sending." |
| 1:50 | **Process** | Run deterministic process (backend required) | "Processing runs the deterministic pipeline — no public Groq batch spend." |
| 2:05 | **Results dashboard** | Show lead table, fit/priority/QA columns | "Each lead gets fit scores, priority, and QA summaries from the five-agent run." |
| 2:20 | **Lead detail drawer** | Open one lead; scroll agent outputs | "Research, qualification, strategy, and draft email — all structured and inspectable." |
| 2:35 | **Agent trace + QA** | Expand trace; show QA score and recommendation | "Traces show what each agent consumed and produced. QA flags risk before anything would hypothetically be sent — and we don't send email from this product." |
| 2:50 | **Human review** | Approve or flag a lead | "Review state stays in the browser — the system prepares intelligence; people decide." |
| 3:05 | **Export** | Export reviewed CSV | "Export is a local CSV for handoff — no CRM sync." |
| 3:15 | **System status** (optional) | Open `/api/system/status` in new tab or mention observability | "Backend exposes safe status and summary telemetry — ephemeral on Render restart." |
| 3:30 | Close | Return to landing or dashboard | "Try your own B2B data in the demo — expect warnings when fields are thin. Public demo stays replay-safe and cost-controlled by design." |

**Emphasize:** B2B Sales / RevOps focus, intake validation, traceability, QA gate, human review, $0 replay, live model restricted on public demo.

**Do not say:** "Sends emails," "CRM integration," "production SaaS," "guaranteed reply rates," "fully autonomous outbound."

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
| 1:40 | Live Groq (optional) | Terminal with backend running | `curl -X POST .../live-groq/lead_001` only if env enabled | "Live paths are backend-only, opt-in, one lead per request, token-capped or rate-limited. The public UI does not expose live batch Groq; controlled single-lead draft regeneration appears only when backend status says it is safe." |
| 2:10 | LangGraph ADR | `docs/adr/langgraph-decision.md` | Open Status + Decision | "LangGraph is deferred: we don't need branching, durable checkpoints, or parallel tool fan-out today. Revisit when ADR criteria become real requirements." |
| 2:30 | Human review + export | Dashboard | Toggle review, export CSV | "Review state is browser-local; backend does not persist review decisions." |
| 2:50 | Roadmap | `docs/roadmap/advanced-capabilities.md` | Scroll capability table | "Smart Intake, durable telemetry, public batch live controls, and production SaaS features are roadmap — clearly separated from what ships today." |

**Emphasize:** Test oracle (deterministic), explicit failure semantics on live path, ADR-driven deferral of graph runtime.

**Do not say:** "LangGraph-powered runtime," "multi-tenant platform," "PDF/Excel intake works today."

---

## Recommended screen sequence

1. Landing page (`/`) — **full page** scroll (hero → problem → solution → architecture)  
2. Demo dashboard (`/demo`) — **full dashboard** initial state (replay mode, Add Leads CTA)  
3. Add Leads panel — paste or upload sample B2B data  
4. Preview table — valid / warning / invalid rows + mapping confirmation  
5. B2B profile selector (if shown)  
6. Process → results lead table  
7. Lead detail drawer — five agents + trace + QA  
8. Human review controls — local state only  
9. CSV export (after marking at least one lead reviewed)  
10. System status or telemetry JSON — observability without secrets  
11. *(Optional, local only)* `curl` live Groq — never on screen in public demo  
12. Architecture doc or roadmap doc — boundaries and future work  

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
| "Intake works with any data shape" | "B2B Sales / RevOps fields; warnings when data is incomplete" |
| "Click Run Groq for a batch in the UI" | "Public live batch Groq is intentionally not exposed. Single-lead draft regeneration is controlled by backend status, demo access, rate limits, and cost tracking." |
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
