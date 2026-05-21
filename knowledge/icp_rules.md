# LeadForge-Agentic Core — ICP Rules & Qualification Logic

**Version:** 1.0  
**Purpose:** Defines the Ideal Customer Profile and scoring logic for the Qualifier Agent.  
**Used by:** Qualifier Agent, Strategist Agent, QA Evaluator Agent.  
**Dependency:** Must be read alongside `product_knowledge.md`.  
**Do not modify** without recalibrating the scoring rubric and example leads.

---

## 1. ICP Summary

LeadForge is built for **B2B companies with an active outbound sales motion**
that need to improve the quality, speed, and consistency of their pipeline
development process.

The ideal customer is a company where:
- Sales or revenue operations is a defined function (even if small)
- Outbound prospecting is part of the go-to-market strategy
- Lead research and qualification are currently done manually or inconsistently
- The team has more leads than bandwidth to research them properly
- Decision-makers value explainability — they want to know *why* a lead is good,
  not just that it scored high

The sweet spot is **growth-stage companies (50–500 employees)** that are scaling
their sales function and feel the operational friction of manual prospecting.

---

## 2. Best-Fit Company Types

These company profiles represent the highest-probability conversion targets:

- **B2B SaaS companies** with an SDR or outbound sales team
- **Logistics and supply chain operators** expanding routes or entering new markets
- **Fintech and financial services platforms** growing their SMB or enterprise
  client base
- **HR Tech and workforce management platforms** targeting mid-market buyers
- **Cybersecurity solution providers** building pipeline in new verticals
- **E-commerce operations and fulfillment companies** scaling B2B partnerships
- **Professional services firms** (consulting, staffing, managed services) that
  rely on relationship-driven outbound
- **Manufacturing companies** with complex B2B sales cycles and technical buyers

Common characteristics across best-fit companies:
- Active hiring in sales, business development, or revenue operations roles
- Expanding into new geographies or market segments
- Recent funding, merger, acquisition, or partnership announcement
- Visible investment in sales tools, CRM, or revenue infrastructure
- Clear ICP of their own (they sell B2B and understand the problem firsthand)

---

## 3. Poor-Fit Company Types

These profiles should receive Low priority scores regardless of other signals:

- **B2C companies** with no enterprise or B2B sales motion
- **Government agencies or public sector entities** (long procurement cycles,
  regulatory constraints)
- **Non-profit organizations** without a commercial sales function
- **Early-stage startups (under 10 employees)** without a defined sales team
- **Large enterprises (5,000+ employees)** with established sales infrastructure
  and procurement processes that make a demo tool impractical
- **Companies with no outbound sales motion** (inbound-only, marketplace-only,
  or channel-only distribution)
- **Highly regulated industries** where AI-assisted outreach creates compliance
  risk (e.g., healthcare without a clear B2B sales context, financial advisory
  firms with strict communication regulations)
- **Companies outside supported geographies** where B2B sales norms differ
  significantly from the target market

---

## 4. Target Industries

**Tier 1 — Strongest fit:**
- B2B SaaS
- Logistics & Supply Chain
- Fintech & Financial Services (B2B)
- Cybersecurity

**Tier 2 — Good fit:**
- HR Tech & Workforce Management
- E-commerce Operations (B2B)
- Manufacturing (with B2B sales)
- Professional Services (Consulting, Staffing, Managed Services)

**Tier 3 — Conditional fit (requires strong signals):**
- Legal Tech
- MarTech & AdTech
- Real Estate Tech (commercial)
- HealthTech (B2B only, non-clinical)

**Out of scope:**
- Retail (B2C)
- Consumer apps
- Media and entertainment
- Public sector
- Non-profit

---

## 5. Target Company Sizes

| Employee Range | Fit Level | Reasoning |
|---|---|---|
| 1–10 | Poor | No defined sales function. Too early. |
| 11–49 | Low–Medium | May have a founder-led sales motion. Needs strong signals. |
| 50–150 | High | Growing sales team. Manual research friction is acute. |
| 151–500 | High | Established RevOps/SalesOps function. Clear budget. |
| 501–1,000 | Medium | May already have tooling. Needs differentiated angle. |
| 1,001–5,000 | Low | Complex procurement. Long sales cycle. Low priority. |
| 5,000+ | Poor | Enterprise procurement. Not the target. |

**Sweet spot:** 50–500 employees.

---

## 6. Target Geographies

**Tier 1 — Primary markets:**
- United States
- Canada
- United Kingdom
- Germany

**Tier 2 — Secondary markets:**
- Mexico
- Spain
- Netherlands
- Australia

**Tier 3 — Emerging opportunity (requires signals):**
- Brazil
- Colombia
- France
- Japan (requires localization awareness)

**Low priority:**
- Markets where B2B outbound sales is not a standard go-to-market motion
- Markets with significant language/cultural barriers without localization support
- Markets with strict cold outreach regulations without compliance signals

---

## 7. Target Buyer Roles

**Decision-maker roles (highest contact fit):**
- VP of Sales
- VP of Revenue Operations
- Chief Revenue Officer (CRO)
- Head of Sales
- Sales Director

**Influencer / Champion roles (strong contact fit):**
- Revenue Operations Manager
- Sales Operations Manager
- Head of Business Development
- Director of Growth
- VP of Marketing (when outbound is marketing-led)

**End-user roles (moderate contact fit — useful but not ideal for first outreach):**
- Sales Manager
- SDR Manager
- Account Executive (Senior)
- Business Development Manager

**Low-value contact roles for initial outreach:**
- Founder/CEO at companies with 100+ employees (usually not handling sales ops)
- Technical roles (CTO, Engineering Manager) — wrong entry point
- HR or Finance roles — wrong department
- Generic "Manager" without department context

---

## 8. Buying Signals

These signals increase fit score. Each signal must be supported by evidence
in the research context. Do not assign signal points without evidence.

**Strong signals (high confidence required):**
- Company is actively hiring SDR, BDR, or Sales Operations roles
- Company recently announced market expansion or new product launch
- Company recently closed a funding round (Series A or later)
- Company is entering a new geography or vertical
- Job postings mention "manual research," "pipeline quality," or "lead scoring"

**Moderate signals (medium confidence acceptable):**
- Company uses a CRM (Salesforce, HubSpot) — suggests sales ops maturity
- Company has a dedicated Revenue Operations or Sales Operations team
- Company has 3+ active sales job postings simultaneously
- Company blog or content mentions outbound sales challenges
- Company recently underwent a merger, acquisition, or partnership

**Weak signals (low confidence — do not score alone):**
- Company has a sales page on their website
- Company is in a relevant industry
- Contact role is sales-adjacent
- Company size is in range

---

## 9. Negative Signals

These signals reduce fit score or trigger a Low priority override:

- **No sales team visible** — no sales roles, no sales-related job postings,
  no commercial motion visible
- **B2C-only business model** — consumer product, no enterprise or B2B offering
- **Regulatory red flags** — highly regulated communication environment without
  explicit compliance signals
- **Inbound-only model** — company explicitly states inbound or product-led
  growth only, no outbound motion
- **Competitor signals** — company already uses a direct competitor to LeadForge
  (note as risk, do not automatically disqualify)
- **Data quality failure** — missing company name, missing industry, missing
  country, or conflicting data across fields
- **No employee count data + no website + no notes** — insufficient evidence
  to qualify reliably
- **Company size too large** (5,000+) — procurement complexity outweighs
  opportunity value for this version

---

## 10. Data Quality Rules

Data quality affects both the fit score and the confidence level of the output.

| Data Condition | Effect on Score | Effect on Output |
|---|---|---|
| All required fields present | No penalty | Full qualification |
| Missing website | –3 points from data quality dimension | Flag as low_confidence |
| Missing employee count | –3 points | Flag, use industry average as proxy |
| Missing contact role | –5 points | Flag, cannot score contact fit dimension |
| Missing country | –3 points | Flag, cannot score geography dimension |
| Missing notes | –2 points | Flag, signals dimension will be limited |
| Conflicting data (e.g., size vs. industry) | –5 points | Flag, mark as needs_review |
| No website AND no notes AND no employee count | –10 points | Mark as low_evidence |

**If total data quality deductions exceed 15 points**, the lead is automatically
flagged as `low_evidence` regardless of other dimensions.

---

## 11. Priority Tiers

| Tier | Fit Score Range | Meaning |
|---|---|---|
| High | 75–100 | Strong ICP match. Prioritize for outreach. |
| Medium | 45–74 | Partial match. Proceed with adjusted expectations. |
| Low | 0–44 | Weak or poor match. Human review required before any action. |

**Override rules:**
- Any lead with a negative signal override (B2C, 5,000+ employees, no sales team)
  is automatically capped at Low priority regardless of calculated score.
- Any lead with data quality deductions ≥ 15 points is capped at Medium priority
  regardless of other signals.
- Any lead with a contact role that is explicitly out of scope (HR, Finance,
  Technical) receives a 0 in the contact role dimension.

---

## 12. Fit Score Rubric (0–100)

The fit score is the sum of six weighted dimensions.
Every dimension must be scored independently with a stated reason.

---

### Dimension 1: Industry Fit — 25 points

| Score | Condition |
|---|---|
| 23–25 | Tier 1 industry (B2B SaaS, Logistics, Fintech, Cybersecurity) |
| 16–22 | Tier 2 industry (HR Tech, E-commerce Ops, Manufacturing, Professional Services) |
| 8–15 | Tier 3 industry (conditional fit, requires supporting signals) |
| 1–7 | Industry present but poor fit (e.g., retail, media) |
| 0 | Industry missing, unknown, or explicitly out of scope |

---

### Dimension 2: Company Size Fit — 15 points

| Score | Condition |
|---|---|
| 13–15 | 50–500 employees (sweet spot) |
| 8–12 | 11–49 or 501–1,000 employees |
| 3–7 | 1,001–5,000 employees |
| 0–2 | Under 10 or over 5,000 employees |
| 0 | Employee count missing (apply data quality deduction separately) |

---

### Dimension 3: Country / Market Fit — 10 points

| Score | Condition |
|---|---|
| 9–10 | Tier 1 geography (US, Canada, UK, Germany) |
| 6–8 | Tier 2 geography (Mexico, Spain, Netherlands, Australia) |
| 3–5 | Tier 3 geography (conditional markets) |
| 0–2 | Low-priority geography or conflicting market signals |
| 0 | Country missing (apply data quality deduction separately) |

---

### Dimension 4: Contact Role Fit — 20 points

| Score | Condition |
|---|---|
| 17–20 | Decision-maker role (VP Sales, CRO, Head of Sales, Sales Director) |
| 11–16 | Influencer/Champion role (RevOps Manager, SalesOps Manager, Head of BD) |
| 5–10 | End-user role (Sales Manager, SDR Manager, Senior AE) |
| 1–4 | Tangential role (Founder at small company, VP Marketing) |
| 0 | Role missing, out of scope (HR, Finance, Engineering), or explicitly wrong |

---

### Dimension 5: Opportunity Signals — 20 points

| Score | Condition |
|---|---|
| 17–20 | 2+ strong signals with high confidence evidence |
| 11–16 | 1 strong signal + 1 moderate signal, or 2+ moderate signals |
| 5–10 | 1 moderate signal or 2+ weak signals |
| 1–4 | Weak signals only, no strong or moderate signals |
| 0 | No signals found or all signals unsupported by evidence |

---

### Dimension 6: Data Quality / Confidence — 10 points

| Score | Condition |
|---|---|
| 9–10 | All key fields present, no conflicts, notes add context |
| 6–8 | 1–2 minor fields missing (e.g., no notes), no conflicts |
| 3–5 | Multiple fields missing or one significant gap (no website, no employee count) |
| 1–2 | Severe data gaps (missing 3+ fields, conflicting data) |
| 0 | Insufficient data to qualify reliably |

---

## 13. Scoring Examples

### High-Fit Lead Example

**Company:** Mid-size B2B SaaS in the US, 120 employees, VP of Revenue Operations
as contact, currently hiring 4 SDRs, recently closed Series B.

| Dimension | Score | Reason |
|---|---|---|
| Industry Fit | 25 | B2B SaaS — Tier 1 |
| Company Size Fit | 14 | 120 employees — sweet spot |
| Country / Market Fit | 10 | United States — Tier 1 |
| Contact Role Fit | 18 | VP Revenue Operations — decision influencer |
| Opportunity Signals | 18 | Hiring SDRs + Series B = 2 strong signals |
| Data Quality | 9 | All fields present, good notes |
| **Total** | **94** | **High priority** |

---

### Medium-Fit Lead Example

**Company:** Logistics company in Mexico, 300 employees, Sales Manager as contact,
no recent signals, limited notes.

| Dimension | Score | Reason |
|---|---|---|
| Industry Fit | 23 | Logistics — Tier 1 |
| Company Size Fit | 14 | 300 employees — sweet spot |
| Country / Market Fit | 7 | Mexico — Tier 2 |
| Contact Role Fit | 8 | Sales Manager — end-user role |
| Opportunity Signals | 5 | No strong signals, weak industry signal only |
| Data Quality | 5 | Missing website, limited notes |
| **Total** | **62** | **Medium priority** |

---

### Low-Fit Lead Example

**Company:** Consumer electronics retailer in Japan, 2,000 employees, HR Manager
as contact, no sales context.

| Dimension | Score | Reason |
|---|---|---|
| Industry Fit | 2 | Retail — poor fit industry |
| Company Size Fit | 4 | 2,000 employees — low fit range |
| Country / Market Fit | 4 | Japan — Tier 3, localization gap |
| Contact Role Fit | 0 | HR Manager — out of scope |
| Opportunity Signals | 0 | No relevant signals found |
| Data Quality | 6 | Fields present but context irrelevant |
| **Total** | **16** | **Low priority** |

---

## 14. Rules for Uncertainty

When the Qualifier Agent is uncertain, it must follow these rules:

- **Never inflate a score to appear helpful.** Uncertainty is a legitimate output.
- **State the specific reason for uncertainty** in the qualification reasoning field.
- **Use the lower bound of a score range** when evidence is ambiguous.
- **Flag the lead for priority human review** when uncertainty is high.
- **Do not guess industry** if the company description is insufficient.
  Use `industry: unknown` and score Dimension 1 as 0.
- **Do not estimate employee count** beyond what the data supports.
  If missing, score Dimension 2 as 0 and apply data quality deduction.

---

## 15. Rules for Incomplete Evidence

When key evidence is missing:

- Score the dimension at the lowest defensible value, not zero by default.
- If a dimension truly cannot be scored (e.g., no contact role means Dimension 4
  cannot be scored), assign 0 and note it explicitly as `unscored_missing_data`.
- Include an `information_risks` list in the output that names every gap.
- Recommend specific research steps the human reviewer could take to improve
  the score.
- Do not fabricate signals to fill gaps. An empty signal list is a valid output.

---

*This document is part of the LeadForge-Agentic Core knowledge base.  
All scoring logic is designed for portfolio demonstration purposes.  
Adjust thresholds based on real ICP data before production use.*