# LeadForge-Agentic Core — Case Study

A controlled B2B sales intelligence workflow for revenue teams who need traceable AI assistance, not unsupervised automation.

**Live demo:** [https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app)

**Demo video playlist:** [LeadForge production-like walkthrough and product demo](https://youtube.com/playlist?list=PLWHDR1oCK8kv8BKlhIce515TlO6OkWOVP&si=FNxQ2KqgrcAjoSHL) — the recorded demo shows the stable replay-mode public demo; some final polish may differ slightly from the latest deployed version, including controlled regenerate/live-mode affordances. See [`demo-video.md`](./demo-video.md).

---

## Problem

B2B sales and RevOps teams routinely face:

- **Manual research overload** — reps spend large portions of the week gathering company context, signals, and role fit before outreach.
- **Inconsistent qualification** — without a shared pipeline, fit criteria vary by person, polluting pipeline quality and forecasts.
- **Generic outreach** — drafts without grounded evidence underperform and erode brand trust.
- **Poor prioritization** — volume-driven chasing dilutes focus on high-fit opportunities.
- **No audit trail** — leadership and reviewers cannot quickly see *why* an angle was chosen.
- **AI trust barriers** — hallucinations, runaway cost, and lack of observability block adoption of generative tools in production-like settings.

LeadForge targets these pains for **B2B Sales and Revenue Operations** workflows — not general-purpose CRM replacement or consumer lead gen.

---

## Target users

| Persona | How they use LeadForge |
|---------|-------------------------|
| **SDRs / outbound reps** | Turn lists into researched, scored, draft-ready opportunities before CRM entry |
| **RevOps / Sales Ops** | Standardize intake validation, QA visibility, and batch hygiene on messy imports |
| **Founder-led sales** | Get defensible intelligence without a large research team |
| **Hiring reviewers / architects** | Evaluate agentic design, safety boundaries, and LLMOps-lite patterns in a controlled demo |

---

## Product solution

LeadForge runs a **linear five-agent pipeline** over each lead:

**Research → Qualifier → Strategist → Email Drafter → QA Evaluator**

Outputs are structured (Pydantic contracts), traced per step, and surfaced in a Next.js dashboard. Humans approve, reject, or flag leads in **browser-local review state**, then **export reviewed leads as CSV** — no email sending, no CRM writes.

**Smart intake** supports paste, CSV, Excel (`.xlsx`), and text-based PDF preview with row-level `valid` / `warning` / `invalid` states before processing (max 10 leads per deterministic run).

---

## User journey

1. **Landing** — product positioning and architecture preview  
2. **Demo dashboard** — sample replay results or empty state prompting Add Leads  
3. **Add Leads** — paste or upload B2B-oriented fields (`company_name`, `industry`, plus recommended columns)  
4. **Preview** — column mapping confirmation, validation badges, warnings for incomplete context  
5. **Process** — deterministic pipeline run (public demo: cost-safe, no live batch Groq in UI)  
6. **Results** — lead table with fit, priority, QA summaries  
7. **Lead detail** — five agent outputs, trace, intake warnings, QA evaluation  
8. **Human review** — local approve/reject/flag  
9. **Export** — CSV download of reviewed leads only  

Users may try their own B2B lead data; the product is curated for B2B Sales / RevOps fields and will surface **warnings and low-confidence states** when data is incomplete.

---

## Architecture overview

```
User
  → Next.js (App Router) — landing + /demo
  → FastAPI backend
  → Deterministic pipeline (plain Python orchestration)
  → Five agent services (contract-tested)
  → Trace + QA evaluation
  → Human review (browser-local)
  → Local CSV export
```

**Optional (backend-only, opt-in):** `POST /api/demo/pipeline/live-groq/{lead_id}` — single-lead Groq comparison with deterministic baseline; token-capped; failures explicit.

**Observability:** `GET /api/system/status`, read-only telemetry summaries (`/api/demo/telemetry/*`), in-memory and **ephemeral** on Render restart.

**Storage:** Ephemeral for demo runs, review state, and telemetry — not a durable multi-tenant data plane.

Details: [architecture-overview.md](./architecture-overview.md).

---

## Agent workflow

| Step | Agent | Output (summary) |
|------|--------|------------------|
| 1 | Research | Company summary, signals, pains, evidence cards |
| 2 | Qualifier | Fit score, priority, rationale |
| 3 | Strategist | Angle, hypothesis, core message, personalization notes |
| 4 | Email Drafter | Subject and body **draft** (not sent) |
| 5 | QA Evaluator | QA score, recommendation, risk signals |

Orchestration is **linear in-process Python** — LangGraph is **deferred** per [ADR-001](./adr/langgraph-decision.md).

---

## Human-in-the-loop design

- AI prepares **review-ready intelligence**; humans decide what to trust or export.  
- Review state is **not persisted to the backend** — intentional scope boundary for the public demo.  
- QA Evaluator acts as a **structured gate** before review, not an autonomous send trigger.  
- Export is **local CSV** — handoff to CRM or email tools is manual and out of scope.

---

## LLMOps / DevOps-lite decisions

| Decision | Rationale |
|----------|-----------|
| **Deterministic baseline as test oracle** | Replay-safe demos, CI without provider spend, regression comparison |
| **Typed schemas (Pydantic v2)** | Contract tests per agent; failures visible in API and UI |
| **Summary-only telemetry** | No full prompts or raw provider payloads in public-safe endpoints |
| **Rate limits + demo access code** | Protect public Render deployment from abuse |
| **Render + Vercel split** | Cheap controlled preview; CORS and env documented in [deployment.md](./deployment.md) |
| **CI on frontend + backend** | Typecheck, unit tests, build, `pytest -q` — see [CI workflow](../.github/workflows/ci.yml) |

---

## Demo safety and cost control

| Control | Effect |
|---------|--------|
| Replay mode default on Vercel | **$0** model spend for dashboard storytelling |
| Live batch model run **disabled in UI** | Prevents uncontrolled public Groq batch cost |
| `MAX_LEADS_PER_RUN` (10) | Caps intake/process volume |
| In-memory rate limiting | Throttles abuse; resets on instance restart |
| Optional `DEMO_ACCESS_CODE` | Private demo gate for protected actions |
| Ephemeral storage | No long-lived PII store on server |

---

## Estimated business impact (illustrative)

The following are **illustrative estimates** or **industry benchmark ranges** — not measured outcomes from LeadForge production deployments.

| Area | Illustrative value |
|------|---------------------|
| **Time saved per lead** | Industry-style ranges often cite **20–60 minutes** for manual research + qualification + first draft (varies by segment and data quality) |
| **Manual research reduction** | Teams adopting structured agentic prep often target **70–90%** reduction on automated pipeline steps — adoption-dependent |
| **Qualification consistency** | Standardized scoring/QA can improve consistency on the order of **20–40%** vs ad-hoc spreadsheets — illustrative |
| **Cost visibility** | In-product metrics surface run cost labels; replay demo is **$0** incremental model cost |
| **Prioritization** | Fit scores and priority tiers focus rep time on higher-potential leads |
| **Review-ready outputs** | QA scores and evidence cards reduce time-to-confidence before outreach |

Based on industry benchmarks, teams using similar tooling report meaningful research-time reduction — LeadForge **targets** that range through deterministic batch prep and transparent traces. See [business-case.md](./business-case.md) for scenario ROI models (all labeled illustrative).

**Salesforce State of Sales, 2026** (projected/expected, rep self-reporting, not controlled experiments): sellers using AI agents report an expected **34%** reduction in prospect research time and **36%** reduction in email drafting time.

**Gartner, 2024:** sales reps who effectively use AI tools are **3.7×** more likely to meet quota than those who do not — directional benchmark for AI-assisted selling maturity, not a LeadForge guarantee.

---

## Trade-offs (intentional)

| Trade-off | Why |
|-----------|-----|
| **Replay mode for public demo** | Zero API cost, predictable UX for portfolio viewers |
| **Live model restricted** | Public batch Groq would risk cost, reliability, and safety |
| **Ephemeral storage** | Simpler ops; no false persistence claims |
| **No email sending** | Compliance and scope honesty |
| **No CRM writes** | Avoid implying production integrations |
| **Browser-local human review** | Fast demo UX without auth/multi-tenant backend |
| **Desktop-first dashboard** | Mobile landing is acceptable; dense operator UI is desktop-oriented |

---

## What I would improve next

1. **Controlled live single-lead model run** in the UI (behind env + rate limits), mirroring existing backend API.  
2. **Stronger persistence** for runs, review, and telemetry — only when paired with auth and data retention policy.  
3. **Optional custom domain** for portfolio polish.  
4. **Always-on backend tier** during interview/demo windows (Render paid instance).  
5. **Deeper intake formats** (e.g. richer enrichment) — only with clear OCR/enrichment boundaries documented.

---

## Related documentation

- [README](../README.md)  
- [Business case](./business-case.md)  
- [Demo script](./demo-script.md)  
- [Demo video](./demo-video.md)  
- [Portfolio narrative](./portfolio-narrative.md)  
- [Deployment](./deployment.md)  
- [Operations runbook](./operations.md)
