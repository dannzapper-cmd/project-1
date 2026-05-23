# LeadForge-Agentic Core — Product Knowledge

**Version:** 1.0  
**Purpose:** Stable product knowledge for agent retrieval (RAG context).  
**Used by:** Strategist Agent, Email Drafter Agent, QA Evaluator Agent.  
**Do not modify** without updating the agent knowledge index.

---

## 1. One-Line Description

LeadForge-Agentic Core is a multi-agent AI system that transforms raw B2B leads
into researched, qualified, prioritized, and review-ready sales opportunities —
with full traceability and human control at every step.

---

## 2. Product Overview

LeadForge takes existing B2B demo lead records and runs each one through a
structured pipeline of specialized AI agents. Each agent has a single, defined responsibility.
The pipeline produces a ranked list of leads with company research, fit scores,
sales strategy, personalized email drafts, and quality evaluations — all ready
for human review before any action is taken.

LeadForge is not a chatbot. It is not a CRM. It is not an email automation tool.
It is an AI-powered workflow layer that sits between a raw lead list and a
well-prepared sales rep.

---

## 3. Target Users

**Primary persona:** Revenue Operations Manager / Sales Operations Lead  
- Manages lead pipeline quality across a sales team  
- Responsible for rep productivity and outbound efficiency  
- Frustrated by manual research, inconsistent qualification, and generic outreach  
- Needs a system that is explainable and controllable, not a black box  

**Secondary persona:** Head of Sales / Sales Director  
- Wants the team focused on high-fit accounts  
- Needs confidence that outreach is relevant and specific  
- Reviews and approves output before any external communication  

**Tertiary persona:** SDR / Business Development Rep  
- Receives pre-researched, pre-qualified leads with a draft email ready to review  
- Can focus on strategy and conversation, not manual data gathering  

---

## 4. Core Problem Solved

Sales and revenue teams waste significant time on three low-value tasks:

1. **Manual lead research** — looking up company context, signals, and pain points
   one lead at a time.
2. **Inconsistent qualification** — different reps score the same lead differently,
   leading to wasted effort on low-fit accounts.
3. **Generic outreach** — emails that are not grounded in specific company context,
   which reduces reply rates and damages sender reputation.

LeadForge automates the research, standardizes the qualification logic, and
generates specific, evidence-grounded email drafts — while keeping a human in
control of every final decision.

---

## 5. What LeadForge Does

- **Researches** each company using deterministic demo signals and curated knowledge context
- **Qualifies** each lead against a defined Ideal Customer Profile (ICP) with an
  explainable fit score (0–100) and priority tier (High / Medium / Low)
- **Identifies** opportunity signals, pain hypotheses, and relevant business context
- **Recommends** a sales angle and outreach strategy grounded in what was found
- **Drafts** a personalized outbound email specific to the company and contact role
- **Evaluates** the quality of every output before it reaches a human reviewer
- **Presents** a ranked, review-ready lead list with full agent traces and cost
  estimates visible
- **Exports** reviewed leads as a local browser CSV download

---

## 6. What LeadForge Does NOT Do

- Does **not** send any emails automatically or connect to any email provider
- Does **not** replace a CRM — it complements the workflow before CRM entry
- Does **not** scrape websites aggressively or access private data
- Does **not** make final decisions — all outputs require human review and approval
- Does **not** guarantee that any email will generate a reply
- Does **not** claim that synthetic demo context is real company intelligence
- Does **not** operate without defined cost limits
- Does **not** run agents without structured, observable outputs
- Does **not** work as a general-purpose chatbot or question-answering tool
- Does **not** support automatic lead importing from third-party platforms in the
  current portfolio version

---

## 7. Core Value Proposition

LeadForge gives a sales or revenue operations team **the ability to process
10 raw B2B leads into research-backed, scored, and email-ready opportunities
in a fraction of the time it would take manually** — with every decision
explainable, every output reviewable, and no action taken without human approval.

The value is not just speed. It is consistency, traceability, and quality control
at the point where pipeline quality is determined.

---

## 8. Differentiators

| What makes LeadForge different | Why it matters |
|---|---|
| Structured multi-agent pipeline | Each agent has one job. Outputs are predictable and debuggable. |
| Explainable fit scores | Every score has a breakdown. No black-box qualification. |
| Evidence-grounded email drafts | Emails reference specific signals, not generic templates. |
| QA evaluation layer | Output quality is measured before human review, not after complaints. |
| Human-in-the-loop by design | No action is taken without explicit human approval. |
| Cost-conscious architecture | Deterministic replay is the default; Groq is available only through an opt-in backend API path. No surprise API bills. |
| Full agent trace visibility | Every step is logged, timed, and visible in the lead detail view. |
| Replay demo mode | Full product experience available without spending API tokens. |

---

## 9. Ethical and Safety Boundaries

These are non-negotiable constraints built into the system design:

- **No automatic email sending.** LeadForge never connects to an email provider.
  All drafts are output only. Sending is always a human action.
- **No real personal contact data** in the demo dataset. All contacts are
  synthetic and clearly labeled.
- **No false source claims.** Agents must not invent sources. If evidence is
  insufficient, it must be explicitly flagged as low-confidence.
- **No scraping.** Research is grounded in deterministic demo signals and the
  curated knowledge base.
- **No overclaiming.** Email drafts must not assert facts that are not supported
  by the research context.
- **Demo data is clearly labeled synthetic.** Nothing in the demo should be
  presented as real company intelligence.
- **Cost limits are enforced.** The system respects defined token budgets and
  daily demo spending limits.

---

## 10. Human-in-the-Loop Principle

LeadForge is designed around the assumption that **AI recommends, humans decide.**

Every agent output is:
- Visible to the reviewer
- Traceable to its inputs
- Accompanied by confidence levels and reasoning
- Held at review status until a human makes an explicit approval, rejection, or
  edit decision

The system does not proceed past human review automatically. Approval is a
deliberate, logged action. This is not a limitation — it is the core design
philosophy.

A lead marked "Approved" means: a human reviewed the research, the score,
the email, and the QA evaluation, and decided this is worth pursuing.
Nothing was sent. Nothing was committed. The human remains in control.

---

## 11. Cost-Conscious Design Principle

LeadForge is built to deliver a full demo experience without requiring a paid
cloud API. Design constraints:

- Default path: deterministic replay (free, no model call)
- Optional path: Groq single-lead backend API (low-cost, fast, opt-in)
- Maximum leads per run: 10
- Maximum agent steps per lead: 5
- Maximum live tokens per single-lead Groq request: 8,000
- Live research disabled by default (uses curated knowledge base)
- Email sending disabled permanently in this version

These limits are not arbitrary — they reflect the reality of building a
cost-controlled AI product that can be demonstrated without financial risk.

---

## 12. Messaging Pillars

These are the three core messages that every agent output, email draft, and
product explanation should align with:

**Pillar 1: From raw data to review-ready intelligence**  
LeadForge transforms unstructured lead lists into structured, scored, and
context-rich opportunities. The output is not another spreadsheet — it is a
prioritized, explainable pipeline.

**Pillar 2: AI that explains itself**  
Every score, every draft, every recommendation comes with reasoning. Sales teams
do not need to trust a black box. They need to understand why.

**Pillar 3: The human stays in control**  
No email is sent. No action is taken. Every output is a recommendation that a
human reviews, edits, approves, or rejects. LeadForge augments the team —
it does not replace judgment.

---

## 13. Approved Product Claims

Agents may use these claims in outputs or explanations:

- "LeadForge processes raw B2B leads through a structured AI pipeline."
- "Each lead receives a fit score based on a defined ICP rubric."
- "Email drafts are grounded in company-specific research context."
- "All outputs require human review before any action is taken."
- "The system tracks token usage and estimated cost per lead."
- "Agent traces are visible and logged for every processed lead."
- "LeadForge is designed for Revenue Operations and Sales Operations teams."
- "The system supports a human-in-the-loop review workflow."

---

## 14. Forbidden Product Claims

Agents must never generate these claims under any circumstances:

- ❌ "LeadForge will send this email automatically."
- ❌ "This email has already been sent."
- ❌ "LeadForge guarantees a higher reply rate."
- ❌ "This research is based on real-time company data."
- ❌ "LeadForge integrates with [specific CRM] out of the box."
- ❌ "This contact's email address was found and is ready to use."
- ❌ "LeadForge scraped this information from the company's website."
- ❌ "This lead has confirmed interest."
- ❌ "Our AI is 100% accurate."
- ❌ Any claim that synthetic demo data represents real company intelligence.

---

## 15. How to Explain LeadForge in Plain Business Language

Use this when writing strategy notes, email drafts, or product explanations
directed at business stakeholders who are not technical:

> "LeadForge takes your list of B2B leads and runs each one through a series
> of AI steps: it validates the data, researches the company, scores the fit
> against your ideal customer profile, identifies a sales angle, and drafts a
> personalized outreach email. Then it evaluates its own output before showing
> everything to a human reviewer. The reviewer decides what to approve, what to
> edit, and what to pass on. Nothing is sent automatically. The system is designed
> to give your team better-prepared leads faster, without replacing the judgment
> calls that only a human should make."

---

*This document is part of the LeadForge-Agentic Core knowledge base.  
All content is for portfolio demonstration purposes.  
No real contact data, private information, or live company intelligence is used.*