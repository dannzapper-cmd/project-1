# LeadForge screenshot assets

Real local project evidence for README, portfolio, and case-study use. Captures reflect the public Vercel demo and `/demo` dashboard unless noted otherwise.

## Where files live

| Location | Purpose |
|----------|---------|
| **`latest/`** | Current recommended screenshots for README and portfolio (use these paths) |
| **`screenshots.pdf`** | Full stitched capture archive (source bundle) |
| **`_embedded/`** | Extracted frames from `screenshots.pdf` (internal reference; prefer `latest/` names) |

All README image paths are relative to the repository root, e.g. `docs/assets/screenshots/latest/03-lead-table.png`.

## Recommended screenshots (README / portfolio)

| File | Label | Represents |
|------|-------|------------|
| `01-landing-hero.png` | Landing / Positioning | Landing-page agent pipeline and controlled AI sales intelligence positioning |
| `02-dashboard-overview.png` | Demo Dashboard | Replay-safe dashboard — agent workflow strip and review guidance |
| `03-lead-table.png` | Lead Table | Processed leads with fit, priority, QA, and review status |
| `04-lead-detail-drawer.png` | Lead Detail | Evidence-backed lead detail with research cards and agent outputs |
| `05-agent-trace.png` | Agent Trace | Per-agent trace entries across the pipeline |
| `06-qa-evaluation.png` | QA Evaluation | QA scores, hallucination risk, and review recommendation |
| `07-human-review.png` | Human Review | Draft outreach with local approve / reject / needs-edit controls |
| `09-telemetry.png` | Run quality & telemetry | Batch run mode, model, QA aggregates, and cost visibility |
| `10-intake-preview.png` | Intake preview | Column mapping and valid / warning / invalid row validation |

### Not in `latest/` (optional future captures)

| File | Notes |
|------|-------|
| `08-csv-export.png` | Local CSV export confirmation — not yet published as a standalone asset |
| `11-architecture-docs.png` | Architecture markdown render |
| `12-roadmap-docs.png` | Roadmap capability table render |

## Safety rules

- Use synthetic/curated demo company names only — no real prospect PII.
- Do not include API keys, `.env` contents, or auth headers.
- Captions must not claim roadmap items as shipped.
- State replay vs live boundaries where relevant.

## Regenerating assets

1. Capture against [production demo](https://v0-project-1-delta-lovat.vercel.app/demo) or local `pnpm dev`.
2. Follow [`docs/screenshots-checklist.md`](../../screenshots-checklist.md).
3. Save finished PNGs under `latest/` using the filenames above.
4. Update this file and the README visual evidence section if filenames change.

## Related

- [README](../../../README.md)
- [Screenshots checklist](../../screenshots-checklist.md)
- [Portfolio pack](../../portfolio/LEADFORGE_PORTFOLIO_PACK.md)
