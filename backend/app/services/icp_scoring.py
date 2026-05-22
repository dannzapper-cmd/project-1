"""Pure ICP scoring helpers (Phase 5.6A).

Transcription of the six-dimension rubric from ``knowledge/icp_rules.md``
into stdlib-only Python. Used by the Phase 5.6A Qualifier Agent. Phase
5.1's ``simulation_service.py`` carries its own private copy of the
same rubric; migrating that module to call into this one is a separate
cleanup task and is **explicitly out of scope** for Phase 5.6A — this
PR adds nothing else to ``simulation_service.py``.

Hard rules for this module:

* No I/O of any kind. No DB, no network, no filesystem reads, no LLM,
  no agent runtime, no FastAPI routes imported.
* Only dependencies are ``app.schemas.lead.LeadIn`` (for typing) and
  Python stdlib.
* Every public function is deterministic and returns small, JSON-safe
  values (``tuple[int, str]`` or ``tuple[int, list[str]]``).

Signatures (Phase 5.6A FIX 3):

* ``score_industry(industry)            -> tuple[int, str]``
* ``score_size(employee_count)          -> tuple[int, str]``
* ``score_country(country)              -> tuple[int, str]``
* ``score_contact_role(contact_role)    -> tuple[int, str]``
* ``score_opportunity_signals(signals)  -> tuple[int, str]``
* ``score_data_quality(lead)            -> tuple[int, str]``
* ``apply_override_rules(score, lead, deductions) -> tuple[int, list[str]]``

In addition this module exposes a small set of helpers used by callers
that need to keep the override math in sync with the dimension scores:

* ``compute_data_quality_deductions(lead) -> int``
* ``classify_contact_role(role)          -> str``
"""

from __future__ import annotations

from app.schemas.lead import LeadIn

# --------------------------------------------------------------------------- #
# ICP tables (transcribed from knowledge/icp_rules.md §4–§12).                #
# All lookup keys are normalised (lower-cased, trimmed) so callers can pass   #
# raw demo-data strings.                                                      #
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
        "b2c",
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

# Data-quality deduction values per icp_rules.md §10 (per missing field).
_DEDUCTION_WEBSITE: int = 3
_DEDUCTION_EMPLOYEE_COUNT: int = 3
_DEDUCTION_COUNTRY: int = 3
_DEDUCTION_CONTACT_ROLE: int = 5
_DEDUCTION_NOTES: int = 2
_DEDUCTION_OVERRIDE_THRESHOLD: int = 15  # icp_rules.md §11

# Priority caps used by apply_override_rules. The integers are
# *score caps* (upper bound on the effective fit_score), not raw
# priority enum values, so the caller can keep the score→priority
# mapping in one place.
PRIORITY_CAP_LOW: int = 44
PRIORITY_CAP_MEDIUM: int = 74
PRIORITY_CAP_NONE: int = 100


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _is_blank(value: str | None) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _norm(value: str | None) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


# --------------------------------------------------------------------------- #
# Dimension 1 — Industry Fit (0–25)                                           #
# --------------------------------------------------------------------------- #
def score_industry(industry: str | None) -> tuple[int, str]:
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


# --------------------------------------------------------------------------- #
# Dimension 2 — Company Size Fit (0–15)                                       #
# --------------------------------------------------------------------------- #
def score_size(employee_count: int | None) -> tuple[int, str]:
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


# --------------------------------------------------------------------------- #
# Dimension 3 — Country / Market Fit (0–10)                                   #
# --------------------------------------------------------------------------- #
def score_country(country: str | None) -> tuple[int, str]:
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


# --------------------------------------------------------------------------- #
# Dimension 4 — Contact Role Fit (0–20)                                       #
# --------------------------------------------------------------------------- #
def classify_contact_role(role: str | None) -> str:
    """Return one of:
    ``decision_maker`` / ``influencer`` / ``end_user`` / ``tangential`` /
    ``out_of_scope`` / ``unknown`` / ``missing``.

    All matching is case-insensitive. Public so the qualifier can react
    to ``out_of_scope`` separately (Phase 5.6A FIX 2 d).
    """

    if _is_blank(role):
        return "missing"
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

    return "unknown"


def score_contact_role(contact_role: str | None) -> tuple[int, str]:
    if _is_blank(contact_role):
        return 0, "Contact Role Fit: 0/20 — contact role missing."
    bucket = classify_contact_role(contact_role)
    if bucket == "decision_maker":
        return 18, f"Contact Role Fit: 18/20 — '{contact_role}' is a decision-maker role."
    if bucket == "influencer":
        return 13, (
            f"Contact Role Fit: 13/20 — '{contact_role}' is an influencer / "
            f"champion role."
        )
    if bucket == "end_user":
        return 8, f"Contact Role Fit: 8/20 — '{contact_role}' is an end-user role."
    if bucket == "tangential":
        return 3, (
            f"Contact Role Fit: 3/20 — '{contact_role}' is tangential to the "
            f"ICP buyer profile."
        )
    if bucket == "out_of_scope":
        return 0, (
            f"Contact Role Fit: 0/20 — '{contact_role}' is out of scope "
            f"(HR, Finance, or Engineering)."
        )
    return 0, (
        f"Contact Role Fit: 0/20 — '{contact_role}' has no clear "
        f"sales/revenue context."
    )


# --------------------------------------------------------------------------- #
# Dimension 5 — Opportunity Signals (0–20)                                    #
#                                                                             #
# Phase 5.6A FIX 4: QualifierAgentInput carries ``opportunity_signals`` as    #
# ``list[str]``, so we can't classify strong/moderate/weak from a confidence  #
# field. Use a simple, honest count-based heuristic instead — a richer        #
# classifier can ship in Phase 5.6B alongside Groq synthesis.                 #
# --------------------------------------------------------------------------- #
def score_opportunity_signals(signals: list[str]) -> tuple[int, str]:
    count = sum(1 for signal in signals if isinstance(signal, str) and signal.strip())
    if count == 0:
        return 0, "Opportunity Signals: 0/20 — No opportunity signals found."
    if count == 1:
        return 8, "Opportunity Signals: 8/20 — 1 signal detected."
    return 15, f"Opportunity Signals: 15/20 — 2+ signals detected ({count})."


# --------------------------------------------------------------------------- #
# Dimension 6 — Data Quality / Confidence (0–10)                              #
# --------------------------------------------------------------------------- #
def compute_data_quality_deductions(lead: LeadIn) -> int:
    """Return the total deduction points implied by missing lead fields.

    Used by both ``score_data_quality`` (to bound the dimension at 10
    minus deductions) and ``apply_override_rules`` (to trigger the
    ``deductions >= 15`` Medium-cap override per icp_rules.md §11).
    """

    total = 0
    if _is_blank(lead.website):
        total += _DEDUCTION_WEBSITE
    if lead.employee_count is None:
        total += _DEDUCTION_EMPLOYEE_COUNT
    if _is_blank(lead.country):
        total += _DEDUCTION_COUNTRY
    if _is_blank(lead.contact_role):
        total += _DEDUCTION_CONTACT_ROLE
    if _is_blank(lead.notes):
        total += _DEDUCTION_NOTES
    return total


def score_data_quality(lead: LeadIn) -> tuple[int, str]:
    deductions = compute_data_quality_deductions(lead)
    missing: list[str] = []
    if _is_blank(lead.website):
        missing.append("website")
    if lead.employee_count is None:
        missing.append("employee_count")
    if _is_blank(lead.country):
        missing.append("country")
    if _is_blank(lead.contact_role):
        missing.append("contact_role")
    if _is_blank(lead.notes):
        missing.append("notes")

    if not missing:
        return 10, "Data Quality: 10/10 — all key fields present with notes."

    score = max(0, 10 - deductions)
    return score, (
        f"Data Quality: {score}/10 — missing fields: " + ", ".join(missing) + "."
    )


# --------------------------------------------------------------------------- #
# Override rules (icp_rules.md §11)                                           #
# --------------------------------------------------------------------------- #
def apply_override_rules(
    score: int,
    lead: LeadIn,
    deductions: int,
) -> tuple[int, list[str]]:
    """Return ``(score_cap, override_risk_notes)``.

    ``score_cap`` is an upper bound on the effective fit score:

    * ``PRIORITY_CAP_LOW`` (44)    -- the lead is forced into the Low band.
    * ``PRIORITY_CAP_MEDIUM`` (74) -- the lead is capped at Medium.
    * ``PRIORITY_CAP_NONE`` (100)  -- no cap from override rules.

    The caller derives the final score with ``min(raw_score, cap)`` and
    maps that to the priority enum. Override notes are returned so the
    qualifier can surface them as fit_risks (Phase 5.6A FIX 2 a/b/c).
    Contact-role out-of-scope handling (FIX 2 d) is enforced inside
    ``score_contact_role`` already.
    """

    cap = PRIORITY_CAP_NONE
    notes: list[str] = []

    if _norm(lead.industry) in _INDUSTRY_OUT_OF_SCOPE:
        cap = min(cap, PRIORITY_CAP_LOW)
        notes.append(
            "B2C/out-of-scope industry: priority capped at Low."
        )

    if lead.employee_count is not None and lead.employee_count >= 5000:
        cap = min(cap, PRIORITY_CAP_LOW)
        notes.append(
            "Company too large (5000+ employees): capped at Low."
        )

    if deductions >= _DEDUCTION_OVERRIDE_THRESHOLD:
        cap = min(cap, PRIORITY_CAP_MEDIUM)
        notes.append(
            "Data quality deductions ≥15: priority capped at Medium."
        )

    return cap, notes


__all__ = [
    "PRIORITY_CAP_LOW",
    "PRIORITY_CAP_MEDIUM",
    "PRIORITY_CAP_NONE",
    "apply_override_rules",
    "classify_contact_role",
    "compute_data_quality_deductions",
    "score_contact_role",
    "score_country",
    "score_data_quality",
    "score_industry",
    "score_opportunity_signals",
    "score_size",
]
