# LeadForge Portfolio Pack

Structured facts for README, CV, interview prep, and cross-project portfolio assembly (e.g. Project 4).

## Identity

| Field | Value |
|-------|--------|
| Project number | Project 1 |
| Title | LeadForge |
| Full title | LeadForge — Agentic B2B Sales Intelligence |
| Subtitle | Traceable B2B sales intelligence with controlled AI workflow and human decisions. |
| Category | Agentic AI / Revenue Ops / B2B Sales Intelligence |
| Status | Completed / Portfolio Release |
| GitHub | https://github.com/dannzapper-cmd/project-1 |
| Demo | https://v0-project-1-delta-lovat.vercel.app/demo |
| Video | https://youtube.com/playlist?list=PLWHDR1oCK8kv8BKlhIce515TlO6OkWOVP&si=FNxQ2KqgrcAjoSHL |

## One-liner

Controlled AI sales intelligence workflow for B2B lead qualification, strategy, outreach drafting, QA evaluation, and human review — without unsupervised outbound automation.

## Problem

Revenue teams lose time to manual account research, inconsistent qualification, generic outreach, and low visibility into why an AI suggested a message or priority.

## Solution

Traceable, review-first workflow: structured lead intake, deterministic agent collaboration, QA scoring, transparent traces, local human review, and exportable reviewed outputs — no email sending, no CRM writes.

## Technical signals

- Five core intelligence agents — Research, Qualifier, Strategist, Email Drafter, QA Evaluator — preceded by intake/normalization
- Next.js demo dashboard with lead table, detail drawer, traces, QA, and review state
- FastAPI backend with health, demo pipeline, intake preview, and telemetry endpoints
- Smart intake: paste, CSV, Excel, and text-based PDF preview/validation
- Replay/cost-safe public demo mode
- Backend-only opt-in Groq single-lead comparison path
- Local browser-only human review and CSV export
- Rate limits, optional demo access code, request IDs, security headers, safe status endpoints
- Summary-safe, in-memory telemetry with capped recent-run listing

## Boundaries (safe claims)

- Controlled workflow, traceable agent pipeline, review-first sales intelligence
- Draft-only outreach copy, local human review, replay/cost-safe public demo
- Backend-only opt-in Groq comparison
- No email sending or CRM writes, portfolio release, production-minded demo
- Applied AI product engineering

## Do not claim

- Sends emails automatically, writes to CRM, replaces SDRs, guarantees reply rates
- LangGraph runtime today, live web research by default, public live Groq batch automation
- Production multi-tenant SaaS, fully autonomous outbound
- Real company intelligence when data is synthetic/demo context

## Screenshot evidence (`docs/assets/screenshots/latest/`)

Local PNG assets derived from real LeadForge demo captures.

| File | Label | Caption |
|------|-------|---------|
| `01-landing-hero.png` | Landing / Positioning | Landing page evidence showing controlled sales intelligence positioning and agent-pipeline narrative |
| `02-dashboard-overview.png` | Demo Workflow | Demo workflow section showing agent stages and review guidance |
| `03-lead-table.png` | Lead Table | Processed leads with fit, priority, and QA-oriented outputs |
| `04-lead-detail-drawer.png` | Lead Detail | Evidence-backed lead detail with agent outputs |
| `05-agent-trace.png` | Agent Trace | Partial trace view showing visible agent execution steps and structured outputs |
| `06-qa-evaluation.png` | QA Evaluation | Quality gate, recommendation, and risk signals before human review |
| `07-human-review.png` | Human Review | Local human review of draft outreach before export |
| `09-telemetry.png` | Run quality & telemetry | Summary-safe run metadata: mode, model, QA aggregates, and cost visibility |
| `10-intake-preview.png` | Intake preview | Smart intake foundation with column mapping and row-level validation |

Skipped: `08-csv-export.png` (no standalone asset yet).

## Stack

Next.js, TypeScript, Tailwind CSS, Radix UI · FastAPI, Pydantic, SQLAlchemy, SQLite · plain-Python orchestration · optional Groq (backend-only).

## Key docs

- [README](../../README.md)
- [Case study](../case-study.md)
- [Portfolio narrative](../portfolio-narrative.md)
- [Architecture overview](../architecture-overview.md)
- [Screenshot assets](../assets/screenshots/README.md)
