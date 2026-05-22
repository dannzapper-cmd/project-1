"""Demo wiring for the Phase 5.5A Research Agent service.

Bridges the existing demo loaders (Phase 4.2) and the
:class:`app.agents.research_agent.ResearchAgentService` so the
agent can be exercised end-to-end against the bundled demo dataset
without any new data dependency.

Hard guarantees:

* Deterministic and read-only. No DB writes, no network I/O, no
  knowledge-file parsing, no LLM call. Internally the agent uses
  ``MockModelService`` (Phase 5.4) only.
* Does not mutate the Phase 5.1 simulation pipeline. This is a
  separate demo path for the first executable agent service and is
  intentionally NOT wired into ``/api/demo/simulation``.
* ``available_context`` is built via ``DemoCompanyResearch.model_dump()``
  so the agent receives a plain ``dict`` matching the
  ``ResearchAgentInput.available_context: dict | None`` contract
  (Phase 5.5A FIX 2).

Public surface:

* :func:`build_demo_research_agent_output(lead_id)` -- single lead.
* :func:`build_all_demo_research_agent_outputs()`   -- every demo lead.
"""

from __future__ import annotations

from app.agents.qualifier_agent import QualifierAgentService
from app.agents.research_agent import ResearchAgentService
from app.agents.strategist_agent import StrategistAgentService
from app.schemas.agents import (
    QualifierAgentInput,
    QualifierAgentOutput,
    ResearchAgentInput,
    ResearchAgentOutput,
    StrategistAgentInput,
    StrategistAgentOutput,
)
from app.schemas.demo import DemoCompanyResearch
from app.schemas.lead import LeadIn
from app.services.demo_data_loader import (
    load_demo_company_research,
    load_demo_leads,
)

_DEMO_RUN_ID: str = "research_agent_demo_run_001"
_DEMO_QUALIFIER_RUN_ID: str = "qualifier_agent_demo_run_001"
_DEMO_STRATEGIST_RUN_ID: str = "strategist_agent_demo_run_001"
_DEMO_STRATEGIST_GROQ_RUN_ID: str = "strategist_agent_groq_demo_run_001"


def _build_available_context(
    research: DemoCompanyResearch | None,
) -> dict | None:
    """Return the plain dict form of a research record (Phase 5.5A FIX 2).

    The :class:`ResearchAgentInput.available_context` field is typed as
    ``dict | None``; passing the Pydantic model directly would be
    rejected by Pydantic v2. ``model_dump()`` is the supported v2 way
    to project a model to a plain dict.
    """

    if research is None:
        return None
    return research.model_dump()


def _run_research_agent_for(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
    *,
    service: ResearchAgentService | None = None,
) -> ResearchAgentOutput:
    agent = service if service is not None else ResearchAgentService()
    agent_input = ResearchAgentInput(
        lead=lead,
        run_id=_DEMO_RUN_ID,
        available_context=_build_available_context(research),
    )
    return agent.run(agent_input)


def build_demo_research_agent_output(lead_id: str) -> ResearchAgentOutput:
    """Run the Research Agent against a single demo lead.

    Raises
    ------
    ValueError
        If ``lead_id`` is not present in the demo lead dataset. The
        route layer translates this into HTTP 404.
    """

    leads = load_demo_leads()
    matching_lead: LeadIn | None = next(
        (lead for lead in leads if lead.lead_id == lead_id), None
    )
    if matching_lead is None:
        raise ValueError(
            f"Lead '{lead_id}' not found in the demo dataset."
        )

    research_records = load_demo_company_research()
    matching_research = next(
        (record for record in research_records if record.lead_id == lead_id),
        None,
    )
    return _run_research_agent_for(matching_lead, matching_research)


def build_all_demo_research_agent_outputs() -> list[ResearchAgentOutput]:
    """Run the Research Agent against every demo lead.

    The output order mirrors :func:`load_demo_leads` (i.e. CSV row
    order), which is deterministic.
    """

    leads = load_demo_leads()
    research_records = load_demo_company_research()
    research_by_id = {record.lead_id: record for record in research_records}

    # Single ResearchAgentService instance so every lead shares the
    # same MockModelService — small allocation, deterministic results.
    service = ResearchAgentService()

    outputs: list[ResearchAgentOutput] = []
    for lead in leads:
        outputs.append(
            _run_research_agent_for(
                lead, research_by_id.get(lead.lead_id), service=service
            )
        )
    return outputs


# --------------------------------------------------------------------------- #
# Phase 5.6A — Qualifier Agent demo wiring                                    #
# --------------------------------------------------------------------------- #
def _build_qualifier_input(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
) -> QualifierAgentInput:
    """Project demo data onto a ``QualifierAgentInput``.

    Demo opportunity signals (``DemoOpportunitySignal``) are projected
    to plain strings since the Phase 5.2 contract types
    ``opportunity_signals`` as ``list[str]``. Information risks pass
    through unchanged.
    """

    research_summary: str | None = None
    opportunity_signals: list[str] = []
    information_risks: list[str] = []

    if research is not None:
        research_summary = (
            research.recommended_research_summary
            or research.company_summary
            or None
        )
        for signal in research.opportunity_signals:
            if isinstance(signal.signal, str) and signal.signal.strip():
                opportunity_signals.append(signal.signal)
        for risk in research.information_risks:
            if isinstance(risk, str) and risk.strip():
                information_risks.append(risk)

    return QualifierAgentInput(
        lead=lead,
        research_summary=research_summary,
        opportunity_signals=opportunity_signals,
        information_risks=information_risks,
        run_id=_DEMO_QUALIFIER_RUN_ID,
    )


def _run_qualifier_for(
    lead: LeadIn,
    research: DemoCompanyResearch | None,
    *,
    service: QualifierAgentService | None = None,
) -> QualifierAgentOutput:
    agent = service if service is not None else QualifierAgentService()
    return agent.run(_build_qualifier_input(lead, research))


def build_demo_qualifier_agent_output(lead_id: str) -> QualifierAgentOutput:
    """Run the Qualifier Agent against a single demo lead.

    Raises
    ------
    ValueError
        If ``lead_id`` is not present in the demo lead dataset. The
        route layer translates this into HTTP 404.
    """

    leads = load_demo_leads()
    matching_lead: LeadIn | None = next(
        (lead for lead in leads if lead.lead_id == lead_id), None
    )
    if matching_lead is None:
        raise ValueError(
            f"Lead '{lead_id}' not found in the demo dataset."
        )

    research_records = load_demo_company_research()
    matching_research = next(
        (record for record in research_records if record.lead_id == lead_id),
        None,
    )
    return _run_qualifier_for(matching_lead, matching_research)


def build_all_demo_qualifier_agent_outputs() -> list[QualifierAgentOutput]:
    """Run the Qualifier Agent against every demo lead.

    Output ordering mirrors :func:`load_demo_leads` (CSV row order).
    Reuses a single :class:`QualifierAgentService` instance — the
    service holds no per-lead state, so this is purely an allocation
    optimisation.
    """

    leads = load_demo_leads()
    research_records = load_demo_company_research()
    research_by_id = {record.lead_id: record for record in research_records}

    service = QualifierAgentService()

    outputs: list[QualifierAgentOutput] = []
    for lead in leads:
        outputs.append(
            _run_qualifier_for(
                lead, research_by_id.get(lead.lead_id), service=service
            )
        )
    return outputs


# --------------------------------------------------------------------------- #
# Phase 5.7 — Strategist Agent demo wiring                                    #
# --------------------------------------------------------------------------- #
def _build_strategist_input(
    lead: LeadIn,
    research_output: ResearchAgentOutput,
    qualifier_output: QualifierAgentOutput,
    *,
    run_id: str,
) -> StrategistAgentInput:
    """Combine deterministic Research + Qualifier outputs into a
    StrategistAgentInput. The Phase 5.2 contract types
    ``company_summary`` as a required ``str``; we fall back to a
    conservative empty string when the research path produced nothing
    usable (the strategist's deterministic baseline already handles
    empty context safely)."""

    company_summary = research_output.company_summary or ""
    return StrategistAgentInput(
        lead=lead,
        company_summary=company_summary,
        opportunity_signals=list(research_output.opportunity_signals),
        pain_hypotheses=list(research_output.pain_hypotheses),
        fit_score=qualifier_output.fit_score,
        priority=qualifier_output.priority,
        run_id=run_id,
    )


def build_demo_strategist_agent_output(lead_id: str) -> StrategistAgentOutput:
    """Run the deterministic Strategist Agent against a single demo lead.

    Reuses the existing Phase 5.5A Research and Phase 5.6A Qualifier
    demo functions so the strategist sees the exact same inputs an
    orchestration layer would. Raises ``ValueError`` on unknown
    ``lead_id`` (route translates to HTTP 404).
    """

    research_output = build_demo_research_agent_output(lead_id)
    qualifier_output = build_demo_qualifier_agent_output(lead_id)

    leads = load_demo_leads()
    matching_lead = next(
        (lead for lead in leads if lead.lead_id == lead_id), None
    )
    if matching_lead is None:  # pragma: no cover — Research already raised
        raise ValueError(
            f"Lead '{lead_id}' not found in the demo dataset."
        )

    strategist_input = _build_strategist_input(
        matching_lead,
        research_output,
        qualifier_output,
        run_id=_DEMO_STRATEGIST_RUN_ID,
    )
    return StrategistAgentService().run(strategist_input)


def build_all_demo_strategist_agent_outputs() -> list[StrategistAgentOutput]:
    """Run the deterministic Strategist Agent against every demo lead.

    Output ordering mirrors :func:`load_demo_leads` (CSV row order).
    Reuses a single :class:`StrategistAgentService` instance.
    """

    leads = load_demo_leads()
    service = StrategistAgentService()
    outputs: list[StrategistAgentOutput] = []
    for lead in leads:
        # Per-lead Research + Qualifier calls keep the demo path
        # deterministic and self-contained; the qualifier itself is
        # deterministic so per-call cost is negligible.
        research_output = build_demo_research_agent_output(lead.lead_id)
        qualifier_output = build_demo_qualifier_agent_output(lead.lead_id)
        strategist_input = _build_strategist_input(
            lead,
            research_output,
            qualifier_output,
            run_id=_DEMO_STRATEGIST_RUN_ID,
        )
        outputs.append(service.run(strategist_input))
    return outputs


def build_demo_strategist_agent_groq_output(
    lead_id: str,
) -> StrategistAgentOutput:
    """Run the Strategist Agent against a single demo lead via Groq.

    Raises ``ValueError`` on unknown ``lead_id``. Raises ``ValueError``
    (originating from :class:`GroqModelService`) when ``GROQ_API_KEY``
    is missing — the route layer translates that into HTTP 503.

    No all-leads Groq function is provided on purpose (cost control).
    """

    # Local import so the FastAPI startup path stays independent of the
    # Groq SDK availability — same defensive pattern Phase 5.5C and
    # Phase 5.6B routes use.
    from app.services.model_service import GroqModelService

    research_output = build_demo_research_agent_output(lead_id)
    qualifier_output = build_demo_qualifier_agent_output(lead_id)

    leads = load_demo_leads()
    matching_lead = next(
        (lead for lead in leads if lead.lead_id == lead_id), None
    )
    if matching_lead is None:  # pragma: no cover — Research already raised
        raise ValueError(
            f"Lead '{lead_id}' not found in the demo dataset."
        )

    groq_service = GroqModelService(default_model="llama-3.1-8b-instant")
    agent = StrategistAgentService(
        model_service=groq_service, use_model_synthesis=True
    )
    strategist_input = _build_strategist_input(
        matching_lead,
        research_output,
        qualifier_output,
        run_id=_DEMO_STRATEGIST_GROQ_RUN_ID,
    )
    return agent.run(strategist_input)


__all__ = [
    "build_demo_research_agent_output",
    "build_all_demo_research_agent_outputs",
    "build_demo_qualifier_agent_output",
    "build_all_demo_qualifier_agent_outputs",
    "build_demo_strategist_agent_output",
    "build_all_demo_strategist_agent_outputs",
    "build_demo_strategist_agent_groq_output",
]
