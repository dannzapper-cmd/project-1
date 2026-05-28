# LeadForge — Portfolio Narrative & CV Guidance

Use this document for interviews, LinkedIn, and portfolio copy. LeadForge is positioned as a **controlled public demo** and **production-like engineering showcase** — not a commercial SaaS or fully autonomous sales agent.

**Demo:** [https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app)

---

## Short project pitch (30 seconds)

LeadForge is a traceable B2B sales intelligence system: five agents research, qualify, strategize, draft outreach, and QA-score each lead before a human reviewer exports approved rows. The public demo runs in cost-safe replay mode with optional backend intake and deterministic processing — live batch model execution is intentionally restricted to protect cost, reliability, and safety.

---

## Technical pitch (60 seconds)

Built with **Next.js** and **FastAPI**, LeadForge uses **Pydantic-typed agent contracts**, a **deterministic pipeline as the test oracle**, summary-safe **telemetry**, and an **opt-in single-lead Groq path** on the backend only. Orchestration is linear plain Python — LangGraph deferred per ADR. CI runs frontend typecheck/unit tests/build and backend pytest. Deployed on **Vercel + Render** with rate limits, optional demo access codes, and ephemeral storage honestly documented.

---

## Product / business pitch (60 seconds)

For B2B sales and RevOps, LeadForge reduces manual research and inconsistent qualification by standardizing intake validation, evidence-backed angles, and QA before review. Humans stay in control: local review state and CSV export — no email sending, no CRM writes. Business-value panels use **illustrative** time-saved estimates from run data, not guaranteed ROI.

---

## CV bullets (pick 3–5)

- Designed and shipped a **five-agent B2B sales intelligence pipeline** (Research → Qualifier → Strategist → Email Drafter → QA) with per-step traces and human-in-the-loop review.  
- Built **Next.js + FastAPI** portfolio deployment on Vercel/Render with **production-safety controls**: rate limits, demo access gate, ephemeral storage disclosure, and **$0 replay demo mode**.  
- Implemented **smart lead intake** (paste, CSV, Excel, text-PDF) with preview validation (`valid` / `warning` / `invalid`) and capped batch processing.  
- Established **deterministic-vs-live model comparison** on a token-bounded, backend-only Groq path with explicit failure semantics — no silent fallback.  
- Delivered **LLMOps-lite observability**: summary telemetry, system status endpoint, and contract-tested agent schemas used as regression oracles in CI.

---

## LinkedIn / portfolio blurb

**LeadForge-Agentic Core** — Traceable B2B sales intelligence with a five-agent pipeline, QA gate, and human review. Public demo: structured intake, deterministic processing, agent traces, and local export — without claiming CRM sync, email sending, or autonomous outbound. Stack: Next.js, FastAPI, Pydantic, controlled Render/Vercel deployment.  
[https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app)

---

## Interview talking points

1. **Why human-in-the-loop?** Outreach and qualification carry compliance and brand risk; AI prepares drafts and evidence, humans approve export.  
2. **Why deterministic baseline?** Replay-safe demos, CI without API spend, and a canonical oracle for live-model comparison.  
3. **Why restrict public live batch Groq?** Cost control, abuse prevention, and honest portfolio boundaries — live path exists API-side for experiments.  
4. **Why defer LangGraph?** Linear orchestration meets current requirements; ADR documents revisit criteria when branching/checkpoints are needed.  
5. **What is ephemeral storage?** Runs and review are not durable across Render restarts — stated upfront to avoid false SaaS claims.  
6. **How do you handle messy intake?** Column mapping, row validation, warnings for incomplete B2B fields — processable with low-evidence flags.  

---

## Trade-off explanation (use verbatim if helpful)

> I intentionally restricted public live model execution to protect cost, reliability, and safety. The dashboard defaults to replay mode; deterministic batch processing is available when the backend is wired; live Groq remains a single-lead, opt-in backend API for comparison experiments — not an open public batch endpoint.

---

## What not to say

| Avoid | Prefer |
|-------|--------|
| "Production SaaS" / "multi-tenant platform" | "Controlled public demo" / "production-like portfolio deployment" |
| "Sends emails" / "writes to CRM" | "Drafts for review; local CSV export" |
| "Guaranteed ROI or reply rates" | "Illustrative estimates from run data and industry benchmarks" |
| "Built this to get hired" | Focus on product value, architecture, and execution quality |
| "Fully autonomous sales agent" | "Prepares review-ready sales intelligence" |

---

## Related documentation

- [Case study](./case-study.md)  
- [Demo script](./demo-script.md)  
- [README](../README.md)  
- [Business case](./business-case.md)
