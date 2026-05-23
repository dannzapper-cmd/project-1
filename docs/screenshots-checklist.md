# LeadForge Screenshots Checklist

Use this checklist when capturing public documentation images for LeadForge-Agentic Core. Store finished assets under:

**`docs/assets/screenshots/`**

Replace placeholder references in the [README](../README.md) as screenshots are added.

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
- Real customer or prospect lists (use demo leads only)

**Do include:**

- Synthetic/curated demo company and lead names from the bundled dataset  
- UI states that reflect honest product scope (review local-only, no “Sent” email status unless clearly labeled as draft)

---

## Required screenshots

### 1. Landing page / hero

| Field | Value |
|-------|--------|
| **Recommended filename** | `01-landing-hero.png` |
| **Purpose** | GitHub README hero; first impression of product positioning |
| **What should be visible** | Hero headline, subtitle, primary CTA toward demo (`/demo`), clean viewport (no browser chrome clutter) |
| **Safety notes** | Full-page capture; crop out bookmarks bar if it shows personal accounts |

---

### 2. Dashboard overview

| Field | Value |
|-------|--------|
| **Recommended filename** | `02-dashboard-overview.png` |
| **Purpose** | Show operator workspace and summary metrics |
| **What should be visible** | Lead table header, row count or summary cards, navigation to demo |
| **Safety notes** | Use `mock` or `api` with demo data only; no real company names added ad hoc |

---

### 3. Lead table

| Field | Value |
|-------|--------|
| **Recommended filename** | `03-lead-table.png` |
| **Purpose** | Illustrate lead list, priority/fit columns, selection state |
| **What should be visible** | Multiple demo leads, sort/filter if present, one row highlighted |
| **Safety notes** | Avoid scrolling to rows with accidentally pasted real data |

---

### 4. Lead detail drawer

| Field | Value |
|-------|--------|
| **Recommended filename** | `04-lead-detail-drawer.png` |
| **Purpose** | Core product surface — per-lead intelligence |
| **What should be visible** | Drawer open on a single lead; agent output sections visible (at least Research + Qualifier) |
| **Safety notes** | Email draft is **draft** content for demo personas — label mentally as not sent |

---

### 5. Agent trace section

| Field | Value |
|-------|--------|
| **Recommended filename** | `05-agent-trace.png` |
| **Purpose** | Demonstrate traceability per agent step |
| **What should be visible** | Trace list or expanded trace entry: agent name, status, input/output summaries, latency |
| **Safety notes** | Traces should not expose full prompts if UI ever shows them — crop to summary fields only |

---

### 6. QA evaluation section

| Field | Value |
|-------|--------|
| **Recommended filename** | `06-qa-evaluation.png` |
| **Purpose** | Show QA gate before any hypothetical send |
| **What should be visible** | QA score, recommendation, risk indicators from QA Evaluator |
| **Safety notes** | Do not imply emails were delivered |

---

### 7. Local human review state

| Field | Value |
|-------|--------|
| **Recommended filename** | `07-human-review.png` |
| **Purpose** | Human-in-the-loop control |
| **What should be visible** | Review controls (approve/reject/flag or equivalent), reviewed indicator on a lead |
| **Safety notes** | Optional: show browser-only hint in UI if present; no backend “synced to CRM” copy |

---

### 8. CSV export (if visually demonstrable)

| Field | Value |
|-------|--------|
| **Recommended filename** | `08-csv-export.png` |
| **Purpose** | Local export path for reviewed leads |
| **What should be visible** | Export button and/or browser download bar with `reviewed-leads.csv` (or actual filename from app) |
| **Safety notes** | Open downloaded CSV in an editor off-screen or redact before publish; file may contain demo emails |

---

### 9. Telemetry endpoint or telemetry UI

| Field | Value |
|-------|--------|
| **Recommended filename** | `09-telemetry.png` |
| **Purpose** | Observability story — safe summaries |
| **What should be visible** | Either Swagger/`/docs` for `GET /api/demo/telemetry/runs` JSON, or a future telemetry UI — run ids, step counts, latencies, token estimates |
| **Safety notes** | No full prompts or raw Groq responses in frame; blur `Authorization` headers if using browser network tab |

---

### 10. Deterministic-vs-live comparison (if available)

| Field | Value |
|-------|--------|
| **Recommended filename** | `10-deterministic-vs-live.png` |
| **Purpose** | Optional live path documentation |
| **What should be visible** | JSON or formatted UI showing `live_success`, comparison fields, and deterministic baseline alongside live (success or failure state) |
| **Safety notes** | Capture from local API only; never show `GROQ_API_KEY`; prefer a failed or success response without env file in terminal |

---

### 11. Architecture docs / diagram

| Field | Value |
|-------|--------|
| **Recommended filename** | `11-architecture-docs.png` |
| **Purpose** | README / docs credibility |
| **What should be visible** | `docs/architecture-overview.md` rendered (GitHub or editor preview) with ASCII diagrams, or landing page architecture section |
| **Safety notes** | Docs-only capture; no secrets in sidebar file tree |

---

### 12. Roadmap docs

| Field | Value |
|-------|--------|
| **Recommended filename** | `12-roadmap-docs.png` |
| **Purpose** | Honest implemented-vs-roadmap boundary |
| **What should be visible** | Capability status table from `docs/roadmap/advanced-capabilities.md` |
| **Safety notes** | Ensure screenshot shows ✅ vs 🗺 vs ⏸ statuses clearly |

---

## Post-capture checklist

- [ ] Filenames match `docs/assets/screenshots/` convention  
- [ ] README screenshot placeholders updated with real paths  
- [ ] No secrets or real PII in any published image  
- [ ] Captions do not claim roadmap items as shipped  
- [ ] Alt text describes product behavior, not employment narrative  

---

## Related documentation

- [README](../README.md)  
- [Architecture overview](./architecture-overview.md)  
- [Demo script](./demo-script.md)  
