# LeadForge-Agentic Core — Sales Playbook

**Version:** 1.0  
**Purpose:** Defines sales reasoning, outreach angles, and strategy logic
for the Strategist Agent.  
**Used by:** Strategist Agent, Email Drafter Agent.  
**Dependencies:** Must be read alongside `product_knowledge.md`
and `icp_rules.md`.  
**Do not modify** without reviewing consistency with ICP rules
and email style guide.

---

## 1. Sales Positioning

LeadForge is positioned as an **operational intelligence layer for sales
and revenue teams** — not as a CRM, not as an email tool, and not as
a replacement for human judgment.

The positioning statement for internal strategy reasoning:

> "LeadForge gives Revenue and Sales Operations teams a faster, more
> consistent way to move from a raw lead list to a review-ready pipeline —
> with every qualification decision explained and every outreach draft
> grounded in company-specific context."

**What this means for outreach strategy:**
- Lead with the operational problem, not the technology.
- Speak to the cost of manual research, inconsistent scoring, and
  generic outreach — not to AI features.
- Position LeadForge as a productivity and quality multiplier for the
  team that already exists, not as a replacement for it.
- Always assume the buyer is skeptical of AI tools. Earn credibility
  through specificity, not enthusiasm.

---

## 2. Main Business Pains LeadForge Solves

These are the core pains the system must address. Every outreach angle,
every email draft, every strategy recommendation must connect back to
at least one of these pains.

### Pain 1: Manual research is slow and inconsistent
Sales reps spend 20–40% of their time researching leads before they
can write a single email. The quality of that research varies by rep,
by day, and by how much time pressure they are under. The result is
uneven pipeline quality that compounds over time.

**Implication for outreach:** When a company is scaling its sales team,
this problem gets worse, not better. More reps = more manual research
= more inconsistency.

---

### Pain 2: Qualification logic is not standardized
Without a shared qualification rubric, different reps score the same
lead differently. High-fit leads get deprioritized. Low-fit leads waste
rep time. The pipeline looks full but does not convert.

**Implication for outreach:** RevOps and SalesOps leaders feel this
acutely. They know the problem exists but lack a systematic solution
that does not require a six-figure CRM implementation.

---

### Pain 3: Outreach is generic and does not convert
Template-based email sequences are easy to scale but easy to ignore.
Buyers receive dozens of identical outreach emails every week. The
emails that get replies are specific — they reference something real
about the company and connect it to a relevant problem.

**Implication for outreach:** Personalization at scale is the gap.
Teams know they need it. They cannot afford to do it manually for
every lead.

---

### Pain 4: There is no quality control before outreach goes out
Most teams review output reactively — after a rep sends a bad email
or books a meeting with a low-fit account. There is no systematic
pre-send evaluation layer.

**Implication for outreach:** QA before human review is a structural
advantage that most tools do not offer. Position this as risk reduction,
not just quality improvement.

---

### Pain 5: AI tools create new risks without solving the old ones
Sales teams that have tried AI-assisted outreach often report the same
problems: outputs are generic, sources are fabricated, and the system
operates as a black box. The result is distrust, inconsistent adoption,
and reversion to manual work.

**Implication for outreach:** LeadForge's explainability and
human-in-the-loop design are direct answers to this pain.
Lead with trust, not with capability claims.

---

## 3. Pain Patterns by Industry

Use these patterns to select the most relevant angle for each lead.
These are tendencies, not guarantees. Always check the research context
before selecting an angle.

---

### B2B SaaS
**Common pains:**
- SDR teams scaling faster than research infrastructure
- High lead volume from marketing but poor conversion to qualified pipeline
- Multiple ICPs or product lines creating qualification complexity
- Pressure to reduce CAC while maintaining pipeline quality

**Best angles:**
- Qualifying marketing-sourced leads faster without adding headcount
- Standardizing ICP scoring across a growing SDR team
- Improving email personalization at the volume SaaS outbound requires

---

### Logistics & Supply Chain
**Common pains:**
- Sales motion relies on relationship-building, not volume outreach
- Expanding into new routes or regions requires new account targeting
- Research on potential partners and clients is done manually by ops or sales
- Long sales cycles mean bad early qualification has compounding costs

**Best angles:**
- Prioritizing the highest-fit accounts when entering a new market or region
- Reducing the manual research burden on ops and sales teams simultaneously
- Building a consistent qualification process before entering new territories

---

### Fintech & Financial Services (B2B)
**Common pains:**
- Compliance awareness makes generic outreach risky
- High-value deals require highly personalized, well-researched outreach
- Sales cycles are long — early qualification quality matters enormously
- Limited tolerance for wasted meetings with low-fit prospects

**Best angles:**
- Improving qualification rigor to protect rep time on high-value deals
- Grounding outreach in researched context to reduce compliance risk of
  generic claims
- Building a systematic pre-meeting intelligence layer

---

### Cybersecurity
**Common pains:**
- Highly technical buyers require credible, specific outreach
- Generic "we protect your data" messaging is actively distrusted
- Multiple buyer personas (CISO, IT Director, VP Engineering) require
  different messaging
- Market is crowded — differentiation requires account-specific research

**Best angles:**
- Enabling specific, technically credible outreach without requiring
  each rep to do deep research manually
- Adapting messaging to the specific buyer role detected in each account
- Qualifying accounts by their current security posture signals

---

### HR Tech & Workforce Management
**Common pains:**
- Buyer personas span HR, Operations, and Finance — targeting varies
- Market is fragmented with many competing tools
- Growth is often tied to specific hiring events or workforce changes
- Outreach without a clear trigger signal performs poorly

**Best angles:**
- Using workforce expansion or hiring signals as outreach triggers
- Targeting the right buyer role within a complex organization
- Building a qualification layer that surfaces only the leads with
  active workforce change signals

---

### Manufacturing (B2B)
**Common pains:**
- Long sales cycles require careful account selection upfront
- Buyers are technical and skeptical of generic vendor outreach
- Sales teams are often small relative to account complexity
- Account research is done manually and inconsistently

**Best angles:**
- Reducing the cost of manual research per account for a small sales team
- Building qualification logic that reflects the complexity of
  manufacturing buying decisions
- Prioritizing accounts showing expansion or operational change signals

---

### Professional Services (Consulting, Staffing, Managed Services)
**Common pains:**
- Business development is often relationship-driven but still requires
  systematic pipeline management
- Outreach quality directly reflects on firm reputation
- Capacity constraints mean every qualified lead must be genuinely worth pursuing
- Generic outreach is inconsistent with a premium professional positioning

**Best angles:**
- Quality over volume — every outreach should be worth the firm's reputation
- Systematic qualification to protect senior partner time
- Research-grounded drafts that reflect the firm's standard of preparation

---

## 4. Signal-to-Angle Mapping

When a specific signal is found in the research context, use the
corresponding angle as the primary strategy recommendation.

| Signal Found | Recommended Angle |
|---|---|
| Company is actively hiring SDRs or BDRs | Scale outbound without adding manual research burden per rep |
| Company recently closed a funding round | Growing pipeline infrastructure to match new growth targets |
| Company is entering a new market or geography | Prioritize highest-fit accounts in unfamiliar territory with less manual work |
| Company recently announced a new product | Align outreach strategy to the new ICP the product creates |
| Job posting mentions "pipeline quality" or "lead scoring" | They already feel the pain — lead with the specific solution |
| Company uses Salesforce or HubSpot (visible signal) | Position LeadForge as the research and qualification layer before CRM entry |
| Multiple sales roles open simultaneously | Team is scaling — research and qualification bottleneck is near |
| Recent merger or acquisition | New combined entity needs a unified qualification approach |
| Company blog or content mentions outbound challenges | They have articulated the pain publicly — reference the pattern, not the specific post |
| Contact role is RevOps or SalesOps | Speak to operational efficiency and process consistency, not just speed |
| Contact role is VP Sales or CRO | Speak to pipeline quality, rep productivity, and revenue predictability |
| Contact role is SDR Manager | Speak to rep ramp time and research burden reduction |
| Low data quality in the lead itself | Angle around structured validation and human review — demonstrate the solution |

---

## 5. Recommended Outreach Angles

These are the approved first-contact angles. Each email draft should
use exactly one primary angle. Do not combine multiple angles in the
same email — it creates a diluted message.

**Angle A: Scaling without adding headcount**
For companies growing their sales team. The core message is that manual
research does not scale linearly — each new rep adds research burden,
not just capacity.

**Angle B: Pipeline quality before CRM entry**
For companies with RevOps or SalesOps leadership. The core message is
that the quality of what enters the CRM determines the quality of what
comes out as revenue. LeadForge is the quality layer before entry.

**Angle C: Consistent qualification across the team**
For companies where multiple reps are scoring the same leads differently.
The core message is that inconsistent qualification is a structural
problem, not a rep performance problem.

**Angle D: Personalization at the volume outbound requires**
For companies where outreach volume is high but reply rates are low.
The core message is that generic emails are not a template problem —
they are a research bandwidth problem.

**Angle E: Explainable AI for skeptical sales teams**
For companies that have tried AI tools and been burned by black-box
outputs or hallucinated content. The core message is that LeadForge
explains every recommendation and keeps humans in control of every
decision.

**Angle F: Research layer for high-value, long-cycle deals**
For companies where every deal is large and every wasted meeting is
costly. The core message is that the investment in upfront research
pays for itself in avoided bad meetings.

---

## 6. Recommended CTAs

All CTAs must be soft. Do not use aggressive or commitment-heavy language
in first-contact outreach.

**Approved CTAs:**
- "Would a 15-minute conversation make sense to see if this fits your
  current workflow?"
- "Happy to share how a similar team used this — worth a quick look?"
- "If the problem resonates, I can walk you through the approach in 20 minutes."
- "Does this match anything on your current ops roadmap?"
- "Would it be worth a brief call to see if this is relevant for [company name]?"

**CTAs to avoid:**
- "Book a demo now" — too transactional for first contact
- "Sign up for free" — implies a SaaS product, not a workflow tool
- "Let me know if you're interested" — too passive, no clear next step
- "I'd love to jump on a call" — informal, overused
- "Click here to learn more" — wrong channel, wrong tone
- Any CTA that implies urgency or scarcity — not appropriate for B2B ops tools

---

## 7. Discovery Questions

Use these in strategy notes or follow-up context. Do not include
full discovery question lists in cold outreach emails.

**For RevOps / SalesOps contacts:**
- How do you currently handle lead research before your reps reach out?
- How consistent is your qualification process across the team?
- What does your lead-to-meeting conversion rate look like today?
- How do you currently QA outreach before it goes out?

**For VP Sales / CRO contacts:**
- What percentage of your pipeline do you consider well-qualified
  at the time of entry?
- How much rep time is going to research versus actual selling?
- What is your current approach to outbound personalization at scale?

**For SDR / BDR Manager contacts:**
- How long does it take a new SDR to get to full research capacity?
- What tools are your reps using today for lead research?
- What would it mean for your team if every rep started a call
  with a pre-researched brief?

---

## 8. Value Propositions by Persona

| Persona | Core Value Proposition |
|---|---|
| RevOps Manager | "A structured qualification layer that standardizes how leads are scored and documented before they touch the CRM." |
| VP Sales / CRO | "More pipeline meetings with higher-fit accounts, without adding research headcount." |
| Sales Director | "A system that makes every rep's outreach as prepared as your best rep's outreach." |
| SDR Manager | "Reduce per-rep research time and improve first-contact relevance for every account." |
| Head of Business Development | "Research-grounded outreach that reflects the quality standard of the firm." |

---

## 9. What to Avoid in Strategy Outputs

The Strategist Agent must not:

- **Recommend a generic angle** when a specific signal exists in the
  research context. If a signal is present, use it.
- **Combine more than one primary angle** in a single outreach strategy.
  Pick the strongest one and commit.
- **Invent signals** that are not present in the research context.
  If the context is thin, flag it explicitly and select the most
  defensible angle available.
- **Recommend aggressive or high-commitment CTAs** for first-contact
  outreach to cold leads.
- **Use buzzwords or AI hype** in strategy notes. Avoid: "leverage
  cutting-edge AI," "revolutionary," "game-changer," "disruptive."
- **Assume decision-making authority** based on a contact's role alone.
  A Sales Manager may be the champion but not the decision-maker.
  Note the distinction.
- **Overclaim product capabilities** beyond what is defined in
  `product_knowledge.md`.

---

## 10. How to Handle Uncertainty in Strategy

When the research context is thin or signals are ambiguous:

1. **State the uncertainty explicitly** in the strategy output.
   Do not paper over it with confident-sounding language.
2. **Select the most defensible angle** given what is available —
   typically Angle A (scaling) or Angle C (qualification consistency),
   which apply broadly across ICP-fit companies.
3. **Recommend specific research gaps** the human reviewer could
   address before approving the outreach.
4. **Lower the CTA ambition** — a low-evidence lead should receive
   a softer, more exploratory CTA than a high-evidence lead.
5. **Flag the lead for priority human review** with a note explaining
   what evidence is missing and why it matters.

---

## 11. How to Avoid Generic Sales Language

Generic language makes outreach invisible. These are the patterns
to detect and eliminate:

| Generic Pattern | Replace With |
|---|---|
| "I came across your company and was impressed" | Reference a specific signal from the research context |
| "We help companies like yours" | Name the specific type of company and the specific problem |
| "Our AI-powered solution" | Describe what the system actually does in one sentence |
| "I'd love to connect" | State a specific reason for the connection |
| "We've helped hundreds of companies" | If no specific evidence, do not make the claim |
| "Reaching out to see if there's a fit" | State the hypothesis about the fit based on signals found |
| "Let me know your thoughts" | Ask a specific, answerable question |
| "Hope this finds you well" | Remove entirely — adds no value |
| "Quick question for you" | Remove — implies your time is more important than theirs |
| "As you may know" | Remove — condescending opening |

**The test for generic language:**
Could this sentence appear in an email to a completely different
company in a different industry without changing a word?
If yes, it is generic. Remove it or replace it with something specific.

---

*This document is part of the LeadForge-Agentic Core knowledge base.  
All sales angles and messaging patterns are for portfolio
demonstration purposes.  
Adjust signal mappings and angles based on real market feedback
before production use.*