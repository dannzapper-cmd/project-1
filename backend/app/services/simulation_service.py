"""Pipeline Simulation Layer service (Phase 5.1).

Pure, deterministic, in-memory simulation of the LeadForge agent pipeline,
built from the existing demo dataset (`data/demo/leads.csv` and
`data/demo/company_research.json`) plus the rubric transcribed from
`knowledge/icp_rules.md`.

Hard guarantees (any change here would break the Phase 5.1 contract):

* No LLM, agent framework, LangGraph, Chroma, RAG, scraping, network I/O,
  database write, or external service call.
* No new pip dependencies (stdlib + already-installed FastAPI/Pydantic only).
* Every public output is honest: outputs are clearly labelled as simulation
  (`run_mode="simulation"`, `simulated=True` on every trace step,
  `model="none"`, `tokens=0`, `model_calls=0`, `estimated_cost="$0.00"`,
  and the email body itself contains an explicit ``[SIMULATION PLACEHOLDER]``
  marker).
* The scoring rubric (`_qualify_lead`) is a direct transcription of
  `knowledge/icp_rules.md` §4–§12. No regex/NLP parsing of the markdown
  file is performed; the tables are encoded as Python dictionaries and
  conditionals.

Public surface:

* :func:`build_simulation_run` -- the single entry point used by the
  ``GET /api/demo/simulation`` route.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.common import (
    Confidence,
    EvidenceSource,
    HallucinationRisk,
    LeadStatus,
    Priority,
    Recommendation,
    RunMode,
)
from app.schemas.demo import DemoCompanyResearch
from app.schemas.lead import LeadDetail, LeadIn
from app.schemas.qa import EvidenceCard, QAScores
from app.schemas.run import RunSummary, TraceEntry
from app.schemas.simulation import SimulationRunResponse
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
)

# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #
_RUN_ID: str = "simulation_demo_run_001"
_SOURCE_NAME: str = "LeadForge Demo Dataset"
_ESTIMATED_COST: str = "$0.00"
_PROMPT_VERSION: str = "simulation_v1"
_MODEL_NAME: str = "none"
_AGENT_STEPS: tuple[str, ...] = (
    "intake",
    "research",
    "qualify",
    "strategize",
    "draft",
    "evaluate",
)

# --------------------------------------------------------------------------- #
# ICP rubric tables (transcribed from knowledge/icp_rules.md).                #
# Lookup keys are lower-cased so the matching logic is case-insensitive.      #
# --------------------------------------------------------------------------- #
_INDUSTRY_TIER1: frozenset[str] = frozenset(
    {
        "b2b saas",
        "saas",
        "logistics",
        "logistics & supply chain",
        "supply chain",
        "fintech",
        "fintech & financial services",
        "financial services",
        "cybersecurity",
    }
)
_INDUSTRY_TIER2: frozenset[str] = frozenset(
    {
        "hr tech",
        "hr tech & workforce management",
        "workforce management",
        "e-commerce operations",
        "ecommerce operations",
        "e-commerce",
        "ecommerce",
        "manufacturing",
        "professional services",
    }
)
_INDUSTRY_TIER3: frozenset[str] = frozenset(
    {
        "legal tech",
        "martech",
        "adtech",
        "real estate tech",
        "healthtech",
    }
)
_INDUSTRY_OUT_OF_SCOPE: frozenset[str] = frozenset(
    {
        "retail",
        "consumer apps",
        "media",
        "entertainment",
        "public sector",
        "non-profit",
        "nonprofit",
    }
)

_COUNTRY_TIER1: frozenset[str] = frozenset(
    {"united states", "usa", "us", "canada", "united kingdom", "uk", "germany"}
)
_COUNTRY_TIER2: frozenset[str] = frozenset(
    {"mexico", "spain", "netherlands", "australia"}
)
_COUNTRY_TIER3: frozenset[str] = frozenset(
    {"brazil", "colombia", "france", "japan"}
)


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _norm(value: str | None) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def _confidence_from_str(raw: str | None) -> Confidence:
    """Map a lowercase confidence label from the demo JSON to the enum."""

    lookup = {
        "high": Confidence.HIGH,
        "medium": Confidence.MEDIUM,
        "low": Confidence.LOW,
    }
    return lookup.get(_norm(raw), Confidence.LOW)


def _display(value: str | None, *, fallback: str = "Unknown") -> str:
    """Return a non-empty string suitable for required string fields."""

    return value.strip() if isinstance(value, str) and value.strip() else fallback


# --------------------------------------------------------------------------- #
# ICP rubric scorers (knowledge/icp_rules.md §12 — Dimensions 1–6)            #
# --------------------------------------------------------------------------- #
def _score_industry(industry: str | None) -> tuple[int, str]:
    if _is_blank(industry):
        return 0, "Industry Fit: 0/25 — industry missing."
    norm = _norm(industry)
    if norm in _INDUSTRY_TIER1:
        return 25, f"Industry Fit: 25/25 — '{industry}' is a Tier 1 industry."
    if norm in _INDUSTRY_TIER2:
        return 20, f"Industry Fit: 20/25 — '{industry}' is a Tier 2 industry."
    if norm in _INDUSTRY_TIER3:
        return 12, (
            f"Industry Fit: 12/25 — '{industry}' is a Tier 3 (conditional) "
            f"industry."
        )
    if norm in _INDUSTRY_OUT_OF_SCOPE:
        return 1, (
            f"Industry Fit: 1/25 — '{industry}' is present but explicitly "
            f"out of scope."
        )
    return 5, (
        f"Industry Fit: 5/25 — '{industry}' is unrecognized; treated as poor "
        f"fit pending review."
    )


def _score_size(employee_count: int | None) -> tuple[int, str]:
    if employee_count is None:
        return 0, "Company Size Fit: 0/15 — employee count missing."
    if 50 <= employee_count <= 500:
        return 14, (
            f"Company Size Fit: 14/15 — {employee_count} employees is in the "
            f"50–500 sweet spot."
        )
    if 11 <= employee_count <= 49 or 501 <= employee_count <= 1000:
        return 10, (
            f"Company Size Fit: 10/15 — {employee_count} employees is in the "
            f"11–49 or 501–1,000 range."
        )
    if 1001 <= employee_count <= 5000:
        return 5, (
            f"Company Size Fit: 5/15 — {employee_count} employees is in the "
            f"1,001–5,000 range."
        )
    return 1, (
        f"Company Size Fit: 1/15 — {employee_count} employees is outside the "
        f"target range (under 10 or over 5,000)."
    )


def _score_country(country: str | None) -> tuple[int, str]:
    if _is_blank(country):
        return 0, "Country / Market Fit: 0/10 — country missing."
    norm = _norm(country)
    if norm in _COUNTRY_TIER1:
        return 10, f"Country / Market Fit: 10/10 — '{country}' is a Tier 1 market."
    if norm in _COUNTRY_TIER2:
        return 7, f"Country / Market Fit: 7/10 — '{country}' is a Tier 2 market."
    if norm in _COUNTRY_TIER3:
        return 4, (
            f"Country / Market Fit: 4/10 — '{country}' is a Tier 3 "
            f"(conditional) market."
        )
    return 1, (
        f"Country / Market Fit: 1/10 — '{country}' is a low-priority or "
        f"unrecognized market."
    )


def _classify_contact_role(role: str) -> str:
    """Return one of: decision_maker / influencer / end_user / tangential /
    out_of_scope / unknown.

    All matching is case-insensitive; ``role`` is assumed non-blank.
    """

    norm = _norm(role)

    out_of_scope_tokens = (
        "hr",
        "human resources",
        "finance",
        "cfo",
        "cto",
        "engineering",
        "engineer",
        "recruit",
    )
    for token in out_of_scope_tokens:
        if token in norm:
            return "out_of_scope"

    decision_keywords = (
        "vp sales",
        "vp of sales",
        "vp revenue",
        "vp of revenue",
        "vice president of sales",
        "vice president of revenue",
        "chief revenue officer",
        "cro",
        "head of sales",
        "sales director",
        "director of sales",
    )
    for kw in decision_keywords:
        if kw in norm:
            return "decision_maker"

    influencer_keywords = (
        "revops",
        "revenue operations manager",
        "revenue operations director",
        "sales operations manager",
        "sales operations director",
        "head of business development",
        "director of growth",
    )
    for kw in influencer_keywords:
        if kw in norm:
            return "influencer"

    end_user_keywords = (
        "sales manager",
        "sdr manager",
        "senior account executive",
        "business development manager",
    )
    for kw in end_user_keywords:
        if kw in norm:
            return "end_user"

    tangential_keywords = (
        "vp marketing",
        "vp of marketing",
        "ceo",
        "founder",
    )
    for kw in tangential_keywords:
        if kw in norm:
            return "tangential"

    if norm == "manager":
        return "unknown"

    return "unknown"


def _score_contact_role(role: str | None) -> tuple[int, str]:
    if _is_blank(role):
        return 0, "Contact Role Fit: 0/20 — contact role missing."
    bucket = _classify_contact_role(role)  # type: ignore[arg-type]
    if bucket == "decision_maker":
        return 18, (
            f"Contact Role Fit: 18/20 — '{role}' is a decision-maker role."
        )
    if bucket == "influencer":
        return 13, (
            f"Contact Role Fit: 13/20 — '{role}' is an influencer / champion role."
        )
    if bucket == "end_user":
        return 8, (
            f"Contact Role Fit: 8/20 — '{role}' is an end-user role."
        )
    if bucket == "tangential":
        return 3, (
            f"Contact Role Fit: 3/20 — '{role}' is tangential to the ICP buyer "
            f"profile."
        )
    if bucket == "out_of_scope":
        return 0, (
            f"Contact Role Fit: 0/20 — '{role}' is out of scope (HR, Finance, "
            f"or Engineering)."
        )
    return 0, (
        f"Contact Role Fit: 0/20 — '{role}' has no clear sales/revenue context."
    )


def _score_opportunity_signals(
    research: DemoCompanyResearch | None,
) -> tuple[int, str]:
    if research is None or not research.opportunity_signals:
        return 0, "Opportunity Signals: 0/20 — no signals available."
    strong = 0
    moderate = 0
    weak = 0
    for signal in research.opportunity_signals:
        bucket = _norm(signal.confidence)
        if bucket == "high":
            strong += 1
        elif bucket == "medium":
            moderate += 1
        elif bucket == "low":
            weak += 1

    reason = (
        f"Opportunity Signals: {{score}}/20 — {strong} strong / {moderate} "
        f"moderate / {weak} weak signals."
    )
    if strong >= 2:
        return 18, reason.format(score=18)
    if strong >= 1 and moderate >= 1:
        return 13, reason.format(score=13)
    if moderate >= 2:
        return 13, reason.format(score=13)
    if moderate >= 1:
        return 7, reason.format(score=7)
    if weak >= 2:
        return 7, reason.format(score=7)
    if weak >= 1:
        return 3, reason.format(score=3)
    return 0, "Opportunity Signals: 0/20 — no usable signals."


def _score_data_quality(lead: LeadIn) -> tuple[int, str, int]:
    """Score Dimension 6 and also return the *total deduction value* used by
    the data-quality override rule from icp_rules.md §10 / §11.
    """

    base = 10
    deductions = 0
    missing: list[str] = []

    if _is_blank(lead.website):
        base -= 3
        deductions += 3
        missing.append("website")
    if lead.employee_count is None:
        base -= 3
        deductions += 3
        missing.append("employee_count")
    if _is_blank(lead.country):
        base -= 3
        deductions += 3
        missing.append("country")
    if _is_blank(lead.contact_role):
        base -= 5
        deductions += 5
        missing.append("contact_role")
    if _is_blank(lead.notes):
        base -= 2
        deductions += 2
        missing.append("notes")

    score = max(0, base)
    if missing:
        reason = (
            f"Data Quality: {score}/10 — missing fields: "
            f"{', '.join(missing)}."
        )
    else:
        reason = "Data Quality: 10/10 — all key fields present with notes."
        score = 10
    return score, reason, deductions


# --------------------------------------------------------------------------- #
# Qualification (3a)                                                          #
# --------------------------------------------------------------------------- #
def _qualify_lead(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
) -> dict[str, Any]:
    industry_score, industry_reason = _score_industry(lead.industry)
    size_score, size_reason = _score_size(lead.employee_count)
    country_score, country_reason = _score_country(lead.country)
    role_score, role_reason = _score_contact_role(lead.contact_role)
    signals_score, signals_reason = _score_opportunity_signals(research)
    quality_score, quality_reason, deductions = _score_data_quality(lead)

    total = (
        industry_score
        + size_score
        + country_score
        + role_score
        + signals_score
        + quality_score
    )

    reasons: list[str] = [
        industry_reason,
        size_reason,
        country_reason,
        role_reason,
        signals_reason,
        quality_reason,
    ]

    # Tier from raw score.
    if total >= 75:
        fit_tier = "High"
    elif total >= 50:
        fit_tier = "Medium"
    elif total >= 25:
        fit_tier = "Low"
    else:
        fit_tier = "Needs Review"

    # icp_rules.md §11 override rules.
    overrides: list[str] = []
    if _norm(lead.industry) in _INDUSTRY_OUT_OF_SCOPE:
        if fit_tier in ("High", "Medium"):
            overrides.append(
                "Override: industry is out of scope (B2C / public sector / "
                "non-profit) — fit tier capped at Low per ICP rules §11."
            )
            fit_tier = "Low"
    if lead.employee_count is not None and lead.employee_count >= 5000:
        if fit_tier in ("High", "Medium"):
            overrides.append(
                "Override: company size ≥ 5,000 employees — fit tier capped "
                "at Low per ICP rules §11."
            )
            fit_tier = "Low"
    if deductions >= 15 and fit_tier == "High":
        overrides.append(
            f"Override: data quality deductions = {deductions} ≥ 15 — fit "
            f"tier capped at Medium per ICP rules §11."
        )
        fit_tier = "Medium"

    information_risks: list[str] = []
    if _is_blank(lead.industry):
        information_risks.append(
            "Industry is missing; ICP fit cannot be evaluated."
        )
    if _is_blank(lead.country):
        information_risks.append(
            "Country is missing; geographic fit cannot be evaluated."
        )
    if lead.employee_count is None:
        information_risks.append(
            "Employee count is missing; company size fit cannot be evaluated."
        )
    if _is_blank(lead.website):
        information_risks.append(
            "Website is missing; company identity cannot be verified."
        )
    if _is_blank(lead.contact_role):
        information_risks.append(
            "Contact role is missing; contact-role fit cannot be evaluated."
        )
    elif _classify_contact_role(lead.contact_role) in ("unknown", "out_of_scope"):
        information_risks.append(
            f"Contact role '{lead.contact_role}' lacks a clear "
            f"sales/revenue context; treat as low-confidence."
        )
    if research is None:
        information_risks.append(
            "No company research record available; opportunity signals "
            "cannot be scored."
        )

    return {
        "qualification_score": total,
        "fit_tier": fit_tier,
        "qualification_reasons": reasons + overrides,
        "information_risks": information_risks,
        "deductions": deductions,
    }


# --------------------------------------------------------------------------- #
# Research (3b)                                                               #
# --------------------------------------------------------------------------- #
def _simulate_research(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
) -> dict[str, Any]:
    if research is None:
        return {
            "research_summary": "Insufficient data for research summary.",
            "opportunity_signals_objects": [],
            "opportunity_signals_strings": [],
            "pain_hypotheses": [],
            "evidence_cards": [],
        }

    summary = (
        research.recommended_research_summary
        or research.company_summary
        or "Insufficient data for research summary."
    )

    opp_strings = [signal.signal for signal in research.opportunity_signals]

    evidence_cards: list[EvidenceCard] = []
    for idx, card in enumerate(research.evidence_cards, start=1):
        description_parts: list[str] = []
        if card.description:
            description_parts.append(card.description)
        # The demo data already tags every card with
        # source_type="synthetic_demo_context". We preserve that origin in
        # the description (per Phase 5.1 schema correction: the
        # EvidenceSource enum does not accept a "synthetic_demo_context"
        # value, so it goes in the body instead).
        description_parts.append("[Source: synthetic_demo_context]")
        evidence_cards.append(
            EvidenceCard(
                id=f"{lead.lead_id}_evidence_{idx:02d}",
                headline=card.title,
                source_type=EvidenceSource.DEMO_CONTEXT,
                description=" ".join(description_parts),
                confidence=_confidence_from_str(card.confidence),
            )
        )

    return {
        "research_summary": summary,
        "opportunity_signals_objects": list(research.opportunity_signals),
        "opportunity_signals_strings": opp_strings,
        "pain_hypotheses": list(research.pain_hypotheses),
        "evidence_cards": evidence_cards,
    }


# --------------------------------------------------------------------------- #
# Email draft (3c)                                                            #
# --------------------------------------------------------------------------- #
def _simulate_email_draft(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
    qualification: dict[str, Any],
) -> dict[str, Any]:
    company = _display(lead.company_name, fallback="your company")
    contact_first = "there"
    if lead.contact_name:
        contact_first = lead.contact_name.strip().split()[0]
    industry_hint = lead.industry or "your space"
    country_hint = lead.country or "your market"
    role_hint = lead.contact_role or "your role"

    signal_hint: str
    if research is not None and research.opportunity_signals:
        signal_hint = research.opportunity_signals[0].signal
    else:
        signal_hint = "your current pipeline-development priorities"

    subject_line = f"Quick thought for {company}"

    body_lines = [
        f"Hi {contact_first},",
        "",
        (
            "[SIMULATION PLACEHOLDER — not LLM-generated. Review required "
            "before use.]"
        ),
        "",
        (
            f"I noticed {signal_hint} at {company}. Teams in "
            f"{industry_hint} ({country_hint}) often run into research and "
            f"qualification bottlenecks at that stage, particularly when "
            f"{role_hint} is the one accountable for pipeline quality."
        ),
        "",
        (
            f"LeadForge is built to address exactly that workflow — researched, "
            f"qualified, review-ready outbound, with no automatic sending. "
            f"Would a short, exploratory conversation be useful?"
        ),
        "",
        "— LeadForge (simulation draft)",
    ]
    email_body = "\n".join(body_lines)

    personalization_notes: list[str] = [
        f"Used company name: {company}",
        f"Used contact first name: {contact_first}",
        f"Referenced signal: {signal_hint}",
        f"Fit tier at draft time: {qualification['fit_tier']}",
    ]

    return {
        "subject_line": subject_line,
        "email_body": email_body,
        "personalization_notes": personalization_notes,
    }


# --------------------------------------------------------------------------- #
# QA (3d)                                                                     #
# --------------------------------------------------------------------------- #
_TIER_QA_TABLE: dict[str, dict[str, int]] = {
    # Keys mirror the existing QAScores schema field names exactly.
    "High": {
        "personalization": 72,
        "evidence_coverage": 80,
        "cta_quality": 70,
        "tone_match": 78,
        "overall": 75,
    },
    "Medium": {
        "personalization": 55,
        "evidence_coverage": 60,
        "cta_quality": 55,
        "tone_match": 60,
        "overall": 58,
    },
    "Low": {
        "personalization": 35,
        "evidence_coverage": 30,
        "cta_quality": 35,
        "tone_match": 40,
        "overall": 35,
    },
    "Needs Review": {
        "personalization": 20,
        "evidence_coverage": 15,
        "cta_quality": 20,
        "tone_match": 25,
        "overall": 20,
    },
}


def _simulate_qa(
    qualification: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    fit_tier = qualification["fit_tier"]
    table = _TIER_QA_TABLE[fit_tier]

    # Per Phase 5.1 hard rule: no LLM means no hallucination risk surface.
    hallucination_risk = HallucinationRisk.LOW

    if fit_tier in ("High", "Medium"):
        recommendation = Recommendation.REVIEW
    else:
        # Low and Needs Review both regenerate per the schema correction.
        recommendation = Recommendation.REGENERATE

    qa_notes: list[str] = [
        "Scores derived deterministically from the simulated fit tier; "
        "no model output was evaluated.",
    ]
    if not research["evidence_cards"]:
        qa_notes.append("Insufficient evidence for confident evaluation.")

    qa_scores = QAScores(
        personalization=table["personalization"],
        evidence_coverage=table["evidence_coverage"],
        cta_quality=table["cta_quality"],
        tone_match=table["tone_match"],
        hallucination_risk=hallucination_risk,
        recommendation=recommendation,
    )

    return {
        "qa_scores": qa_scores,
        "overall_score": table["overall"],
        "qa_notes": qa_notes,
    }


# --------------------------------------------------------------------------- #
# Strategy (templated, deterministic)                                         #
# --------------------------------------------------------------------------- #
def _simulate_strategy(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
) -> dict[str, Any]:
    company = _display(lead.company_name, fallback="this company")

    if research is not None and research.pain_hypotheses:
        first = research.pain_hypotheses[0]
        pain_hypothesis = first.pain
        pain_confidence = _confidence_from_str(first.confidence)
    else:
        pain_hypothesis = (
            f"Insufficient evidence to state a pain hypothesis for {company}."
        )
        pain_confidence = Confidence.LOW

    if research is not None and research.opportunity_signals:
        signal = research.opportunity_signals[0].signal
        sales_angle = (
            f"Position LeadForge as the research and qualification layer that "
            f"compounds the value of {signal.lower()}."
        )
    else:
        sales_angle = (
            "Soft exploratory outreach only — no documented signals to anchor "
            "a specific angle."
        )

    core_message = (
        f"{company} can improve pipeline quality without adding headcount by "
        f"placing a controlled research and qualification layer in front of "
        f"its existing sales motion."
    )

    likely_objection = (
        "We already have a CRM and outbound process; another tool risks "
        "process overhead without proportional return."
    )

    return {
        "pain_hypothesis": pain_hypothesis,
        "pain_confidence": pain_confidence,
        "sales_angle": sales_angle,
        "core_message": core_message,
        "likely_objection": likely_objection,
    }


# --------------------------------------------------------------------------- #
# Trace (3e)                                                                  #
# --------------------------------------------------------------------------- #
def _simulate_trace(lead_id: str) -> list[TraceEntry]:
    trace: list[TraceEntry] = []
    for step in _AGENT_STEPS:
        trace.append(
            TraceEntry(
                agent=step,
                status="success",  # AgentRunStatus.SUCCESS
                input_summary=f"simulation input for {step} on {lead_id}",
                output_summary=f"simulation output for {step} on {lead_id}",
                latency="0ms",
                tokens=0,
                prompt_version=_PROMPT_VERSION,
                model=_MODEL_NAME,
                simulated=True,
            )
        )
    return trace


# --------------------------------------------------------------------------- #
# Priority / status mapping                                                   #
# --------------------------------------------------------------------------- #
def _priority_and_status(fit_tier: str) -> tuple[Priority, LeadStatus]:
    if fit_tier == "High":
        return Priority.HIGH, LeadStatus.PENDING_REVIEW
    if fit_tier == "Medium":
        return Priority.MEDIUM, LeadStatus.PENDING_REVIEW
    if fit_tier == "Low":
        return Priority.LOW, LeadStatus.PENDING_REVIEW
    # "Needs Review" — per Phase 5.1 schema correction: Priority.LOW +
    # LeadStatus.NEEDS_EDIT (do not add a new Priority enum value).
    return Priority.LOW, LeadStatus.NEEDS_EDIT


# --------------------------------------------------------------------------- #
# Per-lead assembly                                                           #
# --------------------------------------------------------------------------- #
def _build_lead_detail(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
) -> LeadDetail:
    qualification = _qualify_lead(lead, research)
    research_out = _simulate_research(lead, research)
    strategy = _simulate_strategy(lead, research)
    email = _simulate_email_draft(lead, research, qualification)
    qa = _simulate_qa(qualification, research_out)
    trace = _simulate_trace(lead.lead_id)

    priority, status = _priority_and_status(qualification["fit_tier"])

    return LeadDetail(
        id=lead.lead_id,
        company=_display(lead.company_name, fallback="Unknown"),
        website=_display(lead.website, fallback=""),
        industry=_display(lead.industry, fallback=""),
        country=_display(lead.country, fallback=""),
        employees=(
            str(lead.employee_count)
            if lead.employee_count is not None
            else ""
        ),
        contact_name=_display(lead.contact_name, fallback=""),
        contact_role=_display(lead.contact_role, fallback=""),
        fit_score=qualification["qualification_score"],
        priority=priority,
        qa_score=qa["overall_score"],
        status=status,
        est_cost=_ESTIMATED_COST,
        email_subject=email["subject_line"],
        run_mode=RunMode.SIMULATION,
        company_summary=research_out["research_summary"],
        opportunity_signals=research_out["opportunity_signals_strings"],
        evidence_cards=research_out["evidence_cards"],
        fit_reasons=qualification["qualification_reasons"],
        fit_risks=qualification["information_risks"],
        pain_hypothesis=strategy["pain_hypothesis"],
        pain_confidence=strategy["pain_confidence"],
        sales_angle=strategy["sales_angle"],
        core_message=strategy["core_message"],
        likely_objection=strategy["likely_objection"],
        email_body=email["email_body"],
        personalization_notes=email["personalization_notes"] + qa["qa_notes"],
        qa_scores=qa["qa_scores"],
        est_total_latency="0ms",
        model_used=_MODEL_NAME,
        agent_steps=len(_AGENT_STEPS),
        est_tokens=0,
        trace=trace,
    )


# --------------------------------------------------------------------------- #
# Aggregate summary (mirrors run_service.build_replay_run logic)              #
# --------------------------------------------------------------------------- #
def _build_summary(
    leads: list[LeadIn],
    research_by_lead_id: dict[str, DemoCompanyResearch],
) -> RunSummary:
    industries = sorted(
        {lead.industry for lead in leads if not _is_blank(lead.industry)}
    )
    countries = sorted(
        {lead.country for lead in leads if not _is_blank(lead.country)}
    )
    leads_with_research = sum(
        1 for lead in leads if lead.lead_id in research_by_lead_id
    )
    leads_with_contact = sum(
        1 for lead in leads if not _is_blank(lead.contact_name)
    )
    total = len(leads)
    return RunSummary(
        industries_represented=industries,
        countries_represented=countries,
        leads_with_company_research=leads_with_research,
        leads_without_company_research=total - leads_with_research,
        leads_with_contact=leads_with_contact,
        leads_without_contact=total - leads_with_contact,
    )


# --------------------------------------------------------------------------- #
# Public entry point (3f)                                                     #
# --------------------------------------------------------------------------- #
def build_simulation_run() -> SimulationRunResponse:
    """Build the deterministic simulation response for ``GET /api/demo/simulation``."""

    leads = load_demo_leads()
    research_records = load_demo_company_research()
    research_by_lead_id: dict[str, DemoCompanyResearch] = {
        record.lead_id: record for record in research_records
    }

    results: list[LeadDetail] = []
    for lead in leads:
        research = research_by_lead_id.get(lead.lead_id)
        results.append(_build_lead_detail(lead, research))

    summary = _build_summary(leads, research_by_lead_id)

    return SimulationRunResponse(
        run_id=_RUN_ID,
        run_mode="simulation",
        status="completed",
        data_source="demo",
        source_name=_SOURCE_NAME,
        generated_at=datetime.utcnow(),
        total_leads=len(leads),
        model_calls=0,
        estimated_cost=_ESTIMATED_COST,
        summary=summary,
        results=results,
    )
