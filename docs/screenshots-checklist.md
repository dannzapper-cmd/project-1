# LeadForge Screenshots Checklist

Use this checklist when capturing public documentation images for LeadForge-Agentic Core. Store finished assets under:

**`docs/assets/screenshots/`**

Replace placeholder references in the [README](../README.md) as screenshots are added.

**Capture against:** [https://v0-project-1-delta-lovat.vercel.app](https://v0-project-1-delta-lovat.vercel.app) (production-like demo) or local `pnpm dev` with the same UI.

---

## Safety rules (all screenshots)

**Do not include:**

- API keys or `GROQ_API_KEY` values  
- `.env` or `.env.local` file contents  
- Terminal tokens, SSH keys, or GitHub personal access tokens  
- Secrets in browser devtools (Network headers, Application storage with keys)  
- Private email addresses or real personal data  
- Sensitive browser tabs (email, banking, admin consoles)  
- Paid provider account dashboards with billing identifiers  
- Real customer or prospect lists (use demo or anonymized B2B sample rows only)

**Do include:**

- Synthetic/curated demo company names or your own anonymized B2B test rows  
- UI states that reflect honest product scope (review local-only, draft email labeled as not sent)

---

## Required screenshots

### 1. Landing hero

| Field | Value |
|-------|--------|
| **Recommended filename** | `01-landing-hero.png` |
| **Purpose** | README hero; first impression |
| **What should be visible** | Headline, subtitle, primary CTA to `/demo` |
| **Safety notes** | Crop personal bookmarks bar |

---

### 2. Full landing page sections

| Field | Value |
|-------|--------|
| **Recommended filename** | `01b-landing-full-sections.png` |
| **Purpose** | Show problem, solution, architecture storytelling |
| **What should be visible** | Stitched or tall capture: hero through architecture/workflow sections |
| **Safety notes** | Full-page capture; no secrets in footer links |

---

### 3. Demo dashboard — initial state

| Field | Value |
|-------|--------|
| **Recommended filename** | `02-dashboard-overview.png` |
| **Purpose** | Operator workspace before or after load |
| **What should be visible** | Replay mode chip, Add Leads CTA, sample/results state, business-value panel if visible |
| **Safety notes** | Show “Live model run unavailable” if present — honest public boundary |

---

### 4. Add Leads panel

| Field | Value |
|-------|--------|
| **Recommended filename** | `02b-add-leads-panel.png` |
| **Purpose** | Intake entry point |
| **What should be visible** | Paste area, upload control, sample CSV link, max-leads note |
| **Safety notes** | No real prospect PII in paste buffer |

---

### 5. Preview table (valid / warning / invalid)

| Field | Value |
|-------|--------|
| **Recommended filename** | `02c-intake-preview-table.png` |
| **Purpose** | Validation UX |
| **What should be visible** | Column mapping summary, at least one row each of valid, warning, invalid badges |
| **Safety notes** | Use demo or synthetic companies only |

---

### 6. B2B profile selector

| Field | Value |
|-------|--------|
| **Recommended filename** | `02d-b2b-profile-selector.png` |
| **Purpose** | Profile pack / contrast-readable selector |
| **What should be visible** | Open dropdown or selected profile with readable contrast |
| **Safety notes** | Light theme capture preferred |

---

### 7. Processing / results dashboard

| Field | Value |
|-------|--------|
| **Recommended filename** | `03-lead-table.png` |
| **Purpose** | Post-process results |
| **What should be visible** | Lead table with fit, priority, QA columns; run summary if shown |
| **Safety notes** | After deterministic process — not live Groq batch |

---

### 8. Lead table (detail context)

| Field | Value |
|-------|--------|
| **Recommended filename** | `03b-lead-table-selected.png` |
| **Purpose** | Row selection state |
| **What should be visible** | Highlighted row before opening drawer |
| **Safety notes** | Same as above |

---

### 9. Lead detail drawer

| Field | Value |
|-------|--------|
| **Recommended filename** | `04-lead-detail-drawer.png` |
| **Purpose** | Core per-lead intelligence |
| **What should be visible** | Research + Qualifier (minimum); fit score; intake warnings if present |
| **Safety notes** | Email section is **draft only** |

---

### 10. Agent trace

| Field | Value |
|-------|--------|
| **Recommended filename** | `05-agent-trace.png` |
| **Purpose** | Traceability |
| **What should be visible** | Per-agent trace entries: status, summaries, latency |
| **Safety notes** | Crop to summary fields if prompts ever appear |

---

### 11. QA evaluation

| Field | Value |
|-------|--------|
| **Recommended filename** | `06-qa-evaluation.png` |
| **Purpose** | QA gate |
| **What should be visible** | QA score, recommendation, risk indicators |
| **Safety notes** | No “sent” or deliverability claims |

---

### 12. Human review state

| Field | Value |
|-------|--------|
| **Recommended filename** | `07-human-review.png` |
| **Purpose** | Human-in-the-loop |
| **What should be visible** | Approve / reject / flag controls; reviewed indicator |
| **Safety notes** | Optional UI copy that review is browser-local |

---

### 13. Export / review-ready state

| Field | Value |
|-------|--------|
| **Recommended filename** | `08-csv-export.png` |
| **Purpose** | Local export path |
| **What should be visible** | Export button and/or download bar with reviewed-leads CSV filename |
| **Safety notes** | Redact CSV contents before publishing if opened |

---

### 14. System status / observability

| Field | Value |
|-------|--------|
| **Recommended filename** | `09-telemetry.png` |
| **Purpose** | Safe ops visibility |
| **What should be visible** | `GET /api/system/status` JSON and/or `GET /api/demo/telemetry/runs` — `storage_mode: ephemeral`, feature flags |
| **Safety notes** | Blur auth headers; no secrets |

---

### 15. Deterministic-vs-live comparison (optional, local only)

| Field | Value |
|-------|--------|
| **Recommended filename** | `10-deterministic-vs-live.png` |
| **Purpose** | Backend comparison path |
| **What should be visible** | API JSON with deterministic + live fields |
| **Safety notes** | Local only; never show API keys |

---

### 16. Architecture docs

| Field | Value |
|-------|--------|
| **Recommended filename** | `11-architecture-docs.png` |
| **Purpose** | Docs credibility |
| **What should be visible** | `docs/architecture-overview.md` rendered |
| **Safety notes** | No secrets in file tree |

---

### 17. Roadmap docs

| Field | Value |
|-------|--------|
| **Recommended filename** | `12-roadmap-docs.png` |
| **Purpose** | Implemented vs future boundary |
| **What should be visible** | Capability table from `docs/roadmap/advanced-capabilities.md` |
| **Safety notes** | Status columns clearly visible |

---

## Responsive captures

### Mobile — landing

| Field | Value |
|-------|--------|
| **Recommended filename** | `13-mobile-landing.png` |
| **Viewport** | ~390×844 (iPhone-class) |
| **What should be visible** | Hero + CTA readable without horizontal scroll |
| **Notes** | Expected to look good |

### Mobile — dashboard (optional)

| Field | Value |
|-------|--------|
| **Recommended filename** | `14-mobile-dashboard.png` |
| **Viewport** | ~390×844 |
| **Honest note** | Dashboard is **desktop-first**. Dense tables and drawer may require horizontal scroll or feel cramped. **Skip publishing** if layout is not acceptable; state “desktop-first operator UI” in README instead. |

---

## Post-capture checklist

- [ ] Filenames match `docs/assets/screenshots/` convention  
- [ ] README screenshot placeholders updated with real paths  
- [ ] No secrets or real PII in any published image  
- [ ] Captions do not claim roadmap items as shipped  
- [ ] Replay vs live boundaries visible where relevant  
- [ ] Alt text describes product behavior, not employment narrative  

---

## Related documentation

- [README](../README.md)  
- [Demo script](./demo-script.md)  
- [Case study](./case-study.md)  
- [Architecture overview](./architecture-overview.md)
